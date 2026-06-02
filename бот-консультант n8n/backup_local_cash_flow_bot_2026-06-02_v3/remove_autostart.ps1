$ErrorActionPreference = 'Stop'

$startupDir = [Environment]::GetFolderPath('Startup')
$target = Join-Path $startupDir 'cash_flow_lifesaver_bot.vbs'

if (Test-Path -LiteralPath $target) {
    Remove-Item -LiteralPath $target
    Write-Host 'Autostart is disabled.'
}
else {
    Write-Host 'Autostart is already disabled.'
}
