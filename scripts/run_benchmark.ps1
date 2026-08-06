# Raw vendor HTTP baseline (NOT a cross-runtime ai-lib Client benchmark)
# 原始供应商 HTTP 基线（不经过各语言 AiClient / pipeline）
#
# [GOV-007] This script POSTs chat/completions via autocannon only. Results must
# never be labeled as ai-lib-rust/python/ts/go performance. For true cross-runtime
# Client benchmarks, call each runtime CLI/SDK separately (future work).

param(
    [int]$runs = 1,
    [int]$duration = 30,
    [int]$connections = 5,
    # Kept for CLI compatibility; ignored — all runs are the same raw-HTTP path.
    [string]$repo = "raw-http"
)

$ErrorActionPreference = "Stop"

$apiKey = [Environment]::GetEnvironmentVariable("DEEPSEEK_API_KEY")
if (-not $apiKey) { $apiKey = [Environment]::GetEnvironmentVariable("API_KEY") }
if (-not $apiKey) { $apiKey = [Environment]::GetEnvironmentVariable("OPENAI_API_KEY") }
if (-not $apiKey) { throw "No API key found. Set DEEPSEEK_API_KEY (or API_KEY/OPENAI_API_KEY)." }

if ($repo -ne "raw-http" -and $repo -ne "all") {
    Write-Warning (
        "[GOV-007] -repo '$repo' is ignored. This harness is a raw vendor HTTP baseline only; " +
        "it does not exercise ai-lib-$repo Client. Results are labeled raw-vendor-http."
    )
}

$endpoint = "https://api.deepseek.com/v1/chat/completions"
$label = "raw-vendor-http"

if (-not (Test-Path "results")) {
    New-Item -ItemType Directory -Path "results" | Out-Null
}

$payloadObj = @{
    model = "deepseek-chat"
    messages = @(@{ role = "user"; content = "What is 2+2?" })
    max_tokens = 100
    temperature = 0.5
}
$payload = $payloadObj | ConvertTo-Json -Depth 10 -Compress
$payloadFile = "temp_payload.json"
$payload | Set-Content $payloadFile -Encoding UTF8

$all = @()

for ($i = 1; $i -le $runs; $i++) {
    Write-Host "[$label] run $i/$runs (autocannon → vendor HTTP, not ai-lib Client) ..."
    $jsonPath = "results/${label}_run_${i}.json"
    $cmd = @(
        "-d", "$duration",
        "-c", "$connections",
        "-p", "1",
        "--method", "POST",
        "-H", "Content-Type: application/json",
        "-H", "Authorization: Bearer $apiKey",
        "--input", $payloadFile,
        "--json",
        $endpoint
    )
    $output = & autocannon @cmd 2>&1 | Out-String
    $output | Set-Content $jsonPath -Encoding UTF8

    $all += @{
        harness = $label
        path = "raw-vendor-http"
        note = "autocannon POST only; does not call ai-lib-rust/python/ts/go Client"
        run = $i
        duration = $duration
        connections = $connections
        output_file = $jsonPath
        timestamp = (Get-Date -Format "o")
    }
}

$summaryPath = "results/benchmark_runs_index.json"
$all | ConvertTo-Json -Depth 8 | Set-Content $summaryPath -Encoding UTF8
Remove-Item $payloadFile -Force -ErrorAction SilentlyContinue

Write-Host "Done. Raw-vendor-HTTP baseline results in results/ (not cross-runtime Client scores)."
