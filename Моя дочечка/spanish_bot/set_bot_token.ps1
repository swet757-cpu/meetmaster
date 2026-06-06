$ErrorActionPreference = "Stop"

Write-Host "Token will be saved to the Windows user environment variable TELEGRAM_BOT_TOKEN."
Write-Host "It will not be written to bot files or logs."

$secureToken = Read-Host "Paste BotFather token" -AsSecureString
$tokenPtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureToken)

try {
    $token = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($tokenPtr)
}
finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($tokenPtr)
}

if ([string]::IsNullOrWhiteSpace($token)) {
    throw "Token is empty. Nothing was saved."
}

[Environment]::SetEnvironmentVariable("TELEGRAM_BOT_TOKEN", $token, "User")
$env:TELEGRAM_BOT_TOKEN = $token

Write-Host "Done. Now you can run start_bot_hidden.vbs."
