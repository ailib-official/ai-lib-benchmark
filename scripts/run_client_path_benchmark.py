#!/usr/bin/env python3
"""Orchestrate GOV-007 Bench B Client-path runners against ai-protocol-mock.

Labels results as ``client-path-mock`` only (never raw-vendor-http / never fake Client).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT_PATH = ROOT / "scripts" / "client_path"
DEFAULT_ROOTS = {
    "python": Path(os.environ.get("AI_LIB_PYTHON_ROOT", r"D:\rustapp\ai-lib-python")),
    "ts": Path(os.environ.get("AI_LIB_TS_ROOT", r"D:\rustapp\ai-lib-ts")),
    "go": Path(os.environ.get("AI_LIB_GO_ROOT", r"D:\rustapp\ai-lib-go")),
    "rust": Path(os.environ.get("AI_LIB_RUST_ROOT", r"D:\rustapp\ai-lib-rust")),
}


def run_cmd(cmd: list[str], env: dict[str, str], cwd: Path | None = None) -> dict:
    t0 = time.perf_counter()
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    wall_ms = (time.perf_counter() - t0) * 1000
    stdout = proc.stdout.strip()
    payload = None
    if stdout:
        try:
            # last JSON object in stdout
            start = stdout.rfind("{")
            if start >= 0:
                payload = json.loads(stdout[start:])
        except json.JSONDecodeError:
            payload = None
    return {
        "exit_code": proc.returncode,
        "wall_ms": round(wall_ms, 2),
        "stdout_tail": stdout[-2000:],
        "stderr_tail": (proc.stderr or "")[-2000:],
        "result": payload,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock-url", default=os.getenv("MOCK_HTTP_URL", "http://127.0.0.1:4010"))
    ap.add_argument("--samples", type=int, default=int(os.getenv("SAMPLES", "5")))
    ap.add_argument(
        "--runtimes",
        default="python,ts,go,rust",
        help="Comma list: python,ts,go,rust",
    )
    ap.add_argument(
        "--out",
        default=str(ROOT / "results" / "client-path-mock_summary.json"),
    )
    args = ap.parse_args()

    env = os.environ.copy()
    env["MOCK_HTTP_URL"] = args.mock_url.rstrip("/")
    env["SAMPLES"] = str(args.samples)
    env["NO_PROXY"] = "localhost,127.0.0.1"
    env["AI_LIB_PYTHON_ROOT"] = str(DEFAULT_ROOTS["python"])
    env["AI_LIB_TS_ROOT"] = str(DEFAULT_ROOTS["ts"])
    env["AI_LIB_GO_ROOT"] = str(DEFAULT_ROOTS["go"])
    env["AI_LIB_RUST_ROOT"] = str(DEFAULT_ROOTS["rust"])

    selected = [x.strip() for x in args.runtimes.split(",") if x.strip()]
    summary: dict = {
        "harness": "client-path-mock",
        "note": "Each runtime invokes AiClient/Client equivalent against mock [GOV-007]",
        "mock_url": env["MOCK_HTTP_URL"],
        "samples": args.samples,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "runtimes": {},
    }

    if "python" in selected:
        summary["runtimes"]["ai-lib-python"] = run_cmd(
            [
                sys.executable,
                str(CLIENT_PATH / "run_python.py"),
                "--python-root",
                str(DEFAULT_ROOTS["python"]),
                "--mock-url",
                env["MOCK_HTTP_URL"],
                "--samples",
                str(args.samples),
            ],
            env,
        )

    if "ts" in selected:
        tsx = ["npx", "--yes", "tsx", str(CLIENT_PATH / "run_ts.mjs")]
        summary["runtimes"]["ai-lib-ts"] = run_cmd(tsx, env, cwd=DEFAULT_ROOTS["ts"])

    if "go" in selected:
        go_dir = CLIENT_PATH / "run_go"
        # refresh replace to local checkout
        run_cmd(
            [
                "go",
                "mod",
                "edit",
                f"-replace=github.com/ailib-official/ai-lib-go={DEFAULT_ROOTS['go']}",
            ],
            env,
            cwd=go_dir,
        )
        run_cmd(["go", "mod", "tidy"], env, cwd=go_dir)
        summary["runtimes"]["ai-lib-go"] = run_cmd(["go", "run", "."], env, cwd=go_dir)

    if "rust" in selected:
        rust_dir = CLIENT_PATH / "run_rust"
        summary["runtimes"]["ai-lib-rust"] = run_cmd(
            ["cargo", "run", "--quiet", "--release"],
            env,
            cwd=rust_dir,
        )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))

    failed = [
        name
        for name, row in summary["runtimes"].items()
        if row.get("exit_code", 1) != 0 or not row.get("result")
    ]
    if failed:
        print(f"FAILED: {', '.join(failed)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
