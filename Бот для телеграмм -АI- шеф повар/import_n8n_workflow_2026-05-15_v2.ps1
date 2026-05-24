param(
    [string]$N8nUrl = $env:N8N_URL,
    [string]$WorkflowPath = ".\n8n_ai_chef_bot_workflow_2026-05-15_v2.json"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

if ([string]::IsNullOrWhiteSpace($N8nUrl)) {
    $N8nUrl = Read-Host "Enter n8n URL, for example https://n8n.example.ru"
}

if ([string]::IsNullOrWhiteSpace($env:N8N_API_KEY)) {
    $secure = Read-Host "Paste n8n API key" -AsSecureString
    $env:N8N_API_KEY = [System.Net.NetworkCredential]::new("", $secure).Password
}

if ([string]::IsNullOrWhiteSpace($N8nUrl)) {
    throw "n8n URL is empty."
}

if ([string]::IsNullOrWhiteSpace($env:N8N_API_KEY)) {
    throw "n8n API key is empty."
}

if (-not (Test-Path -LiteralPath $WorkflowPath)) {
    throw "Workflow file not found: $WorkflowPath"
}

$workflow = Get-Content -LiteralPath $WorkflowPath -Raw -Encoding UTF8 | ConvertFrom-Json

$payload = [ordered]@{
    name        = $workflow.name
    nodes       = $workflow.nodes
    connections = $workflow.connections
    settings    = $workflow.settings
    tags        = @()
}

$baseUrl = $N8nUrl.TrimEnd("/")
$headers = @{
    "X-N8N-API-KEY" = $env:N8N_API_KEY
}

Write-Host "Checking n8n..."
$health = Invoke-RestMethod -Method Get -Uri "$baseUrl/healthz"
Write-Host "n8n status: $($health.status)"

Write-Host "Creating workflow..."
$created = Invoke-RestMethod `
    -Method Post `
    -Uri "$baseUrl/api/v1/workflows" `
    -Headers $headers `
    -ContentType "application/json; charset=utf-8" `
    -Body ($payload | ConvertTo-Json -Depth 100)

Write-Host "Workflow created: $($created.name)"
Write-Host "ID: $($created.id)"
Write-Host "Open: $baseUrl/workflow/$($created.id)"
Write-Host ""
Write-Host "Next, select credentials in n8n nodes: Telegram Trigger, Send Telegram Message, OpenAI Chat Model."
Write-Host "Then save the workflow and turn Active on."
