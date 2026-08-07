#!/usr/bin/env python3
"""Client-path latency runner (Python AiClient → mock). GOV-007 Bench B."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import statistics
import sys
import time
from pathlib import Path


def _ensure_python_path(root: str | None) -> None:
    if not root:
        return
    src = Path(root) / "src"
    if src.is_dir():
        sys.path.insert(0, str(src))


async def run_samples(mock_url: str, samples: int, model: str) -> dict:
    from ai_lib_python.client import AiClient
    from ai_lib_python.types.message import Message

    client = await AiClient.create(model, api_key="sk-test", base_url=mock_url)
    latencies: list[float] = []
    errors = 0
    for _ in range(samples):
        t0 = time.perf_counter()
        try:
            resp = await client.chat().messages([Message.user("Hello")]).execute()
            if not getattr(resp, "content", None):
                errors += 1
        except Exception as exc:  # noqa: BLE001
            errors += 1
            print(f"error: {exc}", file=sys.stderr)
        latencies.append((time.perf_counter() - t0) * 1000)
    return {
        "harness": "client-path-mock",
        "runtime": "ai-lib-python",
        "path": "AiClient.chat.execute",
        "mock_url": mock_url,
        "model": model,
        "samples": samples,
        "ok": samples - errors,
        "errors": errors,
        "latency_ms": {
            "mean": round(statistics.mean(latencies), 2),
            "min": round(min(latencies), 2),
            "max": round(max(latencies), 2),
        },
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--mock-url", default=os.getenv("MOCK_HTTP_URL", "http://127.0.0.1:4010"))
    p.add_argument("--samples", type=int, default=int(os.getenv("SAMPLES", "5")))
    p.add_argument("--model", default="openai/gpt-4o")
    p.add_argument("--python-root", default=os.getenv("AI_LIB_PYTHON_ROOT"))
    args = p.parse_args()
    _ensure_python_path(args.python_root)
    result = asyncio.run(run_samples(args.mock_url.rstrip("/"), args.samples, args.model))
    print(json.dumps(result, indent=2))
    if result["errors"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
