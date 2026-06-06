$ErrorActionPreference = "Stop"

Set-Location -Path $PSScriptRoot

$launcherLog = Join-Path $PSScriptRoot "bot_launcher.log"
$pidPath = Join-Path $PSScriptRoot "bot.pid"

function Write-LauncherLog {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $launcherLog -Value "$timestamp $Message" -Encoding UTF8
}

if (-not (Test-Path $pidPath)) {
    Write-LauncherLog "Stop requested, but bot.pid was not found."
    exit 0
}

$pidLine = Get-Content -Path $pidPath -ErrorAction SilentlyContinue | Select-Object -First 1
if ([string]::IsNullOrWhiteSpace($pidLine) -or $pidLine.Trim() -notmatch '^\d+$') {
    Write-LauncherLog "Stop requested, but bot.pid does not contain a valid PID."
    exit 0
}

$botPid = [int]$pidLine.Trim()
$process = Get-Process -Id $botPid -ErrorAction SilentlyContinue
if (-not $process) {
    Write-LauncherLog "Stop requested, but process $botPid is not running."
    Set-Content -Path $pidPath -Value "stopped" -Encoding UTF8
    exit 0
}

Stop-Process -Id $botPid
Set-Content -Path $pidPath -Value "stopped" -Encoding UTF8
Write-LauncherLog "Bot process stopped. PID: $botPid"
