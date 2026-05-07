param(
    [string]$N8nUrl = $env:N8N_URL
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

if ([string]::IsNullOrWhiteSpace($N8nUrl)) {
    $N8nUrl = Read-Host "Введите URL n8n, например https://n8n1.sweevottak.pro"
}

if ([string]::IsNullOrWhiteSpace($env:N8N_API_KEY)) {
    $secure = Read-Host "Вставьте API key n8n" -AsSecureString
    $env:N8N_API_KEY = [System.Net.NetworkCredential]::new("", $secure).Password
}

$baseUrl = $N8nUrl.TrimEnd("/")
$headers = @{
    "X-N8N-API-KEY" = $env:N8N_API_KEY
}

Write-Host "1. Проверяю n8n /healthz..."
$health = Invoke-RestMethod -Method Get -Uri "$baseUrl/healthz"
Write-Host "   Статус: $($health.status)"

Write-Host "2. Проверяю доступ к n8n API..."
$workflows = Invoke-RestMethod -Method Get -Uri "$baseUrl/api/v1/workflows" -Headers $headers
Write-Host "   API доступен."

$items = @()
if ($null -ne $workflows.data) {
    $items = @($workflows.data)
} elseif ($workflows -is [array]) {
    $items = @($workflows)
}

$matches = @($items | Where-Object { $_.name -eq "AI chef Telegram bot" })

if ($matches.Count -eq 0) {
    Write-Host "3. Workflow 'AI chef Telegram bot' не найден."
    Write-Host "   Значит импорт не прошёл или workflow назван иначе."
    exit 2
}

Write-Host "3. Найдены workflow:"
$matches | ForEach-Object {
    Write-Host "   Name: $($_.name)"
    Write-Host "   ID: $($_.id)"
    Write-Host "   Active: $($_.active)"
    Write-Host "   Open: $baseUrl/workflow/$($_.id)"
}

Write-Host "4. Если Active = False, откройте workflow, выберите Telegram/OpenAI credentials, сохраните и включите Active."
