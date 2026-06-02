$ErrorActionPreference = 'Stop'

$match = '*local_cash_flow_bot*bot.py*'
$processes = Get-CimInstance Win32_Process |
    Where-Object {
        $_.Name -match '^pythonw?\.exe$' -and
        $_.CommandLine -like $match
    }

if (-not $processes) {
    Write-Host 'The bot is not running.'
    exit 0
}

foreach ($process in $processes) {
    Stop-Process -Id $process.ProcessId -Force
}

Write-Host 'The bot is stopped.'
