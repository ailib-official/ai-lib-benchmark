# Deepseek API format verification
# Deepseek 接口格式验证脚本

$ErrorActionPreference = "Stop"

$apiKey = [Environment]::GetEnvironmentVariable("DEEPSEEK_API_KEY")
if (-not $apiKey) { $apiKey = [Environment]::GetEnvironmentVariable("API_KEY") }
if (-not $apiKey) { $apiKey = [Environment]::GetEnvironmentVariable("OPENAI_API_KEY") }

if (-not $apiKey) {
    Write-Error "No API key found. Set DEEPSEEK_API_KEY (or API_KEY/OPENAI_API_KEY)."
}

$headers = @{
    "Authorization" = "Bearer $apiKey"
    "Content-Type" = "application/json"
}

$body = @{
    model = "deepseek-chat"
    messages = @(@{
        role = "user"
        content = "What is 2+2?"
    })
    max_tokens = 64
    temperature = 0.2
} | ConvertTo-Json -Depth 10 -Compress

$url = "https://api.deepseek.com/v1/chat/completions"
Write-Host "Testing API format against $url ..."

$response = Invoke-WebRequest -Uri $url -Method POST -Headers $headers -Body $body -ContentType "application/json" -TimeoutSec 30
$json = $response.Content | ConvertFrom-Json

Write-Host "HTTP: $($response.StatusCode)"
Write-Host "Model: $($json.model)"
if ($json.choices -and $json.choices[0].message) {
    Write-Host "Reply: $($json.choices[0].message.content)"
}
Write-Host "Format verification passed."
