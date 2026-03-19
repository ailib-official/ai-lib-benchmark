#!/usr/bin/env bash
# Cross-runtime benchmark orchestrator
# 跨运行时基准测试编排脚本

set -euo pipefail

MODE="${1:-smoke}" # smoke | full
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RESULTS_DIR="${ROOT_DIR}/results"
mkdir -p "${RESULTS_DIR}"

if [[ -z "${DEEPSEEK_API_KEY:-}" ]]; then
  echo "DEEPSEEK_API_KEY is required"
  exit 1
fi

case "${MODE}" in
  smoke)
    DURATION=20
    CONNECTIONS=3
    ;;
  full)
    DURATION=60
    CONNECTIONS=5
    ;;
  *)
    echo "Unknown mode: ${MODE} (use smoke|full)"
    exit 1
    ;;
esac

echo "Running ${MODE} benchmark (${DURATION}s, c=${CONNECTIONS})"
pwsh -File "${ROOT_DIR}/scripts/run_benchmark.ps1" -repo all -runs 1 -duration "${DURATION}" -connections "${CONNECTIONS}"
python "${ROOT_DIR}/tools/analyze_benchmarks.py" --results-dir "${RESULTS_DIR}" --format both
echo "Done. See ${RESULTS_DIR}, benchmark_report.csv, BENCHMARK_ANALYSIS.md"
