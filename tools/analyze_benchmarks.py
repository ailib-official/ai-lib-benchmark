#!/usr/bin/env python3
"""
Benchmark analysis utility.
基准结果分析工具。
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean


def extract_metrics(raw: dict) -> dict:
    requests = raw.get("requests", {})
    latency = raw.get("latency", {})
    throughput = raw.get("throughput", {})
    return {
        # Support both autocannon JSON schema and archived custom result schema.
        "rps_avg": float(requests.get("average", raw.get("requestsPerSecond", 0.0))),
        "latency_p99": float(latency.get("p99", 0.0)),
        "latency_mean": float(latency.get("mean", latency.get("average", 0.0))),
        "total_requests": int(requests.get("total", 0)),
        "throughput_avg": float(throughput.get("average", 0.0)),
        "errors": int(raw.get("errors", 0)),
    }


def load_results(results_dir: Path) -> list[tuple[str, dict]]:
    loaded: list[tuple[str, dict]] = []
    for file in sorted(results_dir.glob("*.json")):
        if file.name == "benchmark_runs_index.json":
            continue
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                loaded.append((file.name, data))
        except Exception:
            continue
    return loaded


def write_csv(rows: list[dict], path: Path) -> None:
    fields = [
        "test_name",
        "rps_avg",
        "latency_p99",
        "latency_mean",
        "total_requests",
        "throughput_avg",
        "errors",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: list[dict], path: Path) -> None:
    rps = [r["rps_avg"] for r in rows] or [0.0]
    p99 = [r["latency_p99"] for r in rows] or [0.0]
    lines = [
        "# Benchmark Analysis",
        "",
        f"- Samples: {len(rows)}",
        f"- Avg RPS: {mean(rps):.2f}",
        f"- Avg P99: {mean(p99):.2f} ms",
        "",
        "## Results",
        "",
        "| Test | RPS | P99 (ms) | Total Requests | Errors |",
        "|---|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['test_name']} | {r['rps_avg']:.2f} | {r['latency_p99']:.2f} | {r['total_requests']} | {r['errors']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze benchmark JSON results.")
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    parser.add_argument("--csv-output", type=Path, default=Path("benchmark_report.csv"))
    parser.add_argument("--markdown-output", type=Path, default=Path("BENCHMARK_ANALYSIS.md"))
    parser.add_argument("--format", choices=["csv", "markdown", "both"], default="both")
    args = parser.parse_args()

    loaded = load_results(args.results_dir)
    if not loaded:
        print(f"No result JSON found in {args.results_dir}")
        return 1

    rows = []
    for name, raw in loaded:
        metrics = extract_metrics(raw)
        metrics["test_name"] = name
        rows.append(metrics)

    if args.format in ("csv", "both"):
        write_csv(rows, args.csv_output)
        print(f"CSV report written: {args.csv_output}")
    if args.format in ("markdown", "both"):
        write_markdown(rows, args.markdown_output)
        print(f"Markdown report written: {args.markdown_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
