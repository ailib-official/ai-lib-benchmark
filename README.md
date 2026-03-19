# ai-lib-benchmark

Cross-runtime benchmark toolkit for the ai-lib ecosystem.

This repository is extracted from benchmark-related work in `ailib-media` and is now the canonical place for benchmark scripts, baseline artifacts, and analysis tooling.

## Scope

- Benchmark execution scripts (PowerShell + Bash)
- Baseline and sample result artifacts
- Report generation and regression analysis helpers
- Cross-runtime coverage: `ai-lib-rust`, `ai-lib-python`, `ai-lib-ts`, `ai-lib-go`

## Quick Start

### Prerequisites

- Node.js + `autocannon`
- PowerShell (Windows) and/or Bash (Linux/macOS/WSL)
- Python 3.10+
- API keys in environment variables (`DEEPSEEK_API_KEY`, optional `GROQ_API_KEY`)

Install autocannon:

```bash
npm install -g autocannon
```

### 1) Verify API Format

```powershell
.\scripts\test_deepseek_format.ps1
```

### 2) Run Benchmark (Windows)

```powershell
.\scripts\run_benchmark.ps1 -repo all -runs 1 -duration 30
```

Results are written to `results/`.

### 3) Analyze Results

```bash
python tools/analyze_benchmarks.py --results-dir results --format both
```

This generates:

- `benchmark_report.csv`
- `BENCHMARK_ANALYSIS.md`

## Repository Layout

```text
ai-lib-benchmark/
  benchmarks/
    benchmark_config.template.json
  scripts/
    run_benchmark.ps1
    test_deepseek_format.ps1
  tools/
    analyze_benchmarks.py
    orchestrate_benchmarks.sh
  examples/
    results/
      benchmark_baseline.json
      groq_benchmark_results.sample.json
  results/                  # generated at runtime, ignored by git
```

## Governance

- Managed under `ai-lib-constitution` rules and `ai-lib-plans` task tracking.
- Cross-runtime behavior must remain consistent with `[ARCH-003]`.
- Benchmark execution and baseline update should be reproducible and traceable.

## License

MIT
