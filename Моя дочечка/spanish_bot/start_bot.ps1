$ErrorActionPreference = "Stop"

Set-Location -Path $PSScriptRoot

$token = $env:TELEGRAM_BOT_TOKEN

if ([string]::IsNullOrWhiteSpace($token)) {
    Write-Host "Paste BotFather token. It will not be saved to a file."
    $secureToken = Read-Host "TELEGRAM_BOT_TOKEN" -AsSecureString
    $tokenPtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureToken)

    try {
        $token = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($tokenPtr)
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($tokenPtr)
    }
}

if ([string]::IsNullOrWhiteSpace($token)) {
    throw "Token is empty. Bot start stopped."
}

$env:TELEGRAM_BOT_TOKEN = $token
python main.py
