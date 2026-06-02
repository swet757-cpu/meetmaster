$ErrorActionPreference = 'Stop'

$startupDir = [Environment]::GetFolderPath('Startup')
$source = Join-Path $PSScriptRoot 'start_bot_hidden.vbs'
$target = Join-Path $startupDir 'cash_flow_lifesaver_bot.vbs'

Copy-Item -LiteralPath $source -Destination $target -Force

Write-Host ''
Write-Host 'Autostart is enabled.'
Write-Host 'The bot will start after Windows sign-in.'
Write-Host 'Keep this computer powered on and connected to the internet.'
