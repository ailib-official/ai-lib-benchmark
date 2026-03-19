# Benchmark runner for ai-lib runtimes
# ai-lib 多运行时基准测试脚本

param(
    [string]$repo = "all",      # all | rust | python | ts | go
    [int]$runs = 1,
    [int]$duration = 30,
    [int]$connections = 5
)

$ErrorActionPreference = "Stop"

$apiKey = [Environment]::GetEnvironmentVariable("DEEPSEEK_API_KEY")
if (-not $apiKey) { $apiKey = [Environment]::GetEnvironmentVariable("API_KEY") }
if (-not $apiKey) { $apiKey = [Environment]::GetEnvironmentVariable("OPENAI_API_KEY") }
if (-not $apiKey) { throw "No API key found. Set DEEPSEEK_API_KEY (or API_KEY/OPENAI_API_KEY)." }

$endpoint = "https://api.deepseek.com/v1/chat/completions"
$repos = switch ($repo) {
    "all" { @("rust","python","ts","go") }
    "rust" { @("rust") }
    "python" { @("python") }
    "ts" { @("ts") }
    "go" { @("go") }
    default { @("rust") }
}

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

foreach ($r in $repos) {
    for ($i = 1; $i -le $runs; $i++) {
        Write-Host "[$r] run $i/$runs ..."
        $jsonPath = "results/${r}_run_${i}.json"
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
            repo = "ai-lib-$r"
            run = $i
            duration = $duration
            connections = $connections
            output_file = $jsonPath
            timestamp = (Get-Date -Format "o")
        }
    }
}

$summaryPath = "results/benchmark_runs_index.json"
$all | ConvertTo-Json -Depth 8 | Set-Content $summaryPath -Encoding UTF8
Remove-Item $payloadFile -Force -ErrorAction SilentlyContinue

Write-Host "Done. Results in results/"
