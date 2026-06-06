$ErrorActionPreference = "Stop"

Set-Location -Path $PSScriptRoot

$launcherLog = Join-Path $PSScriptRoot "bot_launcher.log"
$pidPath = Join-Path $PSScriptRoot "bot.pid"
$scriptPath = Join-Path $PSScriptRoot "run_bot_hidden.py"

function Write-LauncherLog {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $launcherLog -Value "$timestamp $Message" -Encoding UTF8
}

if (Test-Path $pidPath) {
    $oldPidLine = Get-Content -Path $pidPath -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not [string]::IsNullOrWhiteSpace($oldPidLine)) {
        $oldPid = $oldPidLine.Trim()
    }
    else {
        $oldPid = ""
    }

    if ($oldPid -match '^\d+$') {
        $existingProcess = Get-Process -Id ([int]$oldPid) -ErrorAction SilentlyContinue
        if ($existingProcess) {
            Write-LauncherLog "Bot is already running. PID: $oldPid"
            exit 0
        }
    }
}

$token = [Environment]::GetEnvironmentVariable("TELEGRAM_BOT_TOKEN", "Process")
if ([string]::IsNullOrWhiteSpace($token)) {
    $token = [Environment]::GetEnvironmentVariable("TELEGRAM_BOT_TOKEN", "User")
}
if ([string]::IsNullOrWhiteSpace($token)) {
    $token = [Environment]::GetEnvironmentVariable("TELEGRAM_BOT_TOKEN", "Machine")
}

if ([string]::IsNullOrWhiteSpace($token)) {
    Write-LauncherLog "TELEGRAM_BOT_TOKEN is not set. Run set_bot_token.ps1 first."
    exit 2
}

$env:TELEGRAM_BOT_TOKEN = $token

$pythonw = Get-Command pythonw.exe -ErrorAction SilentlyContinue
if ($pythonw) {
    $pythonPath = $pythonw.Source
    $windowStyle = "Hidden"
}
else {
    $python = Get-Command python.exe -ErrorAction SilentlyContinue
    if (-not $python) {
        Write-LauncherLog "python.exe/pythonw.exe was not found."
        exit 3
    }

    $pythonPath = $python.Source
    $windowStyle = "Hidden"
}

Start-Process `
    -FilePath $pythonPath `
    -ArgumentList @($scriptPath) `
    -WorkingDirectory $PSScriptRoot `
    -WindowStyle $windowStyle

Write-LauncherLog "Hidden bot start command was sent."
