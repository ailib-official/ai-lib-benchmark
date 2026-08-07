# ai-lib-benchmark

Benchmark toolkit for the ai-lib ecosystem (includes an honest **raw vendor HTTP** baseline; true Client-path cross-runtime runs are separate).

This repository is extracted from benchmark-related work in `ailib-media` and is now the canonical place for benchmark scripts, baseline artifacts, and analysis tooling.

## Scope

- Benchmark execution scripts (PowerShell + Bash)
- Baseline and sample result artifacts
- Report generation and regression analysis helpers
- Raw vendor HTTP baseline via autocannon (`scripts/run_benchmark.ps1`) — **not** labeled as per-runtime Client scores ([GOV-007])
- Client-path benchmarks via `scripts/run_client_path_benchmark.py` (AiClient/Client against mock; label `client-path-mock`)

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
.\scripts\run_benchmark.ps1 -runs 1 -duration 30
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

## Post-v1.0.0 matrix (BENCH-003)

Historical cross-runtime pin table (Wave-5 / BENCH-003):

| Component | Pin |
|-----------|-----|
| ai-protocol | `v1.0.0` |
| ai-lib-rust / python / ts / go | `1.0.0` |
| ai-protocol-mock | `1.0.1` (protocol-driven SSE) |

Baseline artifact: `benchmarks/v1.0.0-matrix-baseline.json`.

## GOV-007 release-train matrix (Bench A + Bench B)

Train pins:

| Component | Pin |
|-----------|-----|
| ai-protocol | `v1.2.0` (`d61b701…`) |
| ai-lib-rust | `1.3.0` |
| ai-lib-python / ts / go | `1.2.0` |
| ai-protocol-mock | `1.1.0` |

Matrix artifact: `benchmarks/v1.2.0-train-matrix.json`.

| Harness | Script | Result label |
|---------|--------|--------------|
| Bench A raw vendor HTTP | `scripts/run_benchmark.ps1` | `raw-vendor-http` only |
| Bench B Client-path (mock) | `scripts/run_client_path_benchmark.py` | `client-path-mock` only |

```powershell
$env:MOCK_HTTP_URL = "http://127.0.0.1:4010"
python scripts/run_client_path_benchmark.py --samples 5
```

Requires sibling checkouts (or `AI_LIB_*_ROOT` env) and a running mock server.

## Governance

- Managed under `ai-lib-constitution` rules and `ai-lib-plans` task tracking.
- Cross-runtime behavior must remain consistent with `[ARCH-003]`.
- Benchmark execution and baseline update should be reproducible and traceable.
- Do not label raw HTTP harness output as ai-lib Client / runtime performance (`GOV-007`).

## License

MIT


