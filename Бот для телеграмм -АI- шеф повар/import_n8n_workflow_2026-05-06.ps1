param(
    [string]$N8nUrl = $env:N8N_URL,
    [string]$WorkflowPath = ".\n8n_ai_chef_bot_workflow_v2.json",
    [switch]$Activate
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

if ([string]::IsNullOrWhiteSpace($N8nUrl)) {
    throw "Set n8n URL in N8N_URL or pass -N8nUrl."
}

if ([string]::IsNullOrWhiteSpace($env:N8N_API_KEY)) {
    throw "Set n8n API key in N8N_API_KEY. Do not store the key in files."
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

$created = Invoke-RestMethod `
    -Method Post `
    -Uri "$baseUrl/api/v1/workflows" `
    -Headers $headers `
    -ContentType "application/json; charset=utf-8" `
    -Body ($payload | ConvertTo-Json -Depth 100)

Write-Host "Workflow created: $($created.name)"
Write-Host "ID: $($created.id)"
Write-Host "Open: $baseUrl/workflow/$($created.id)"

if ($Activate) {
    $activated = Invoke-RestMethod `
        -Method Post `
        -Uri "$baseUrl/api/v1/workflows/$($created.id)/activate" `
        -Headers $headers `
        -ContentType "application/json; charset=utf-8" `
        -Body "{}"

    Write-Host "Workflow activated: $($activated.active)"
} else {
    Write-Host "Workflow created as inactive. Select credentials in n8n, then activate it manually."
}
