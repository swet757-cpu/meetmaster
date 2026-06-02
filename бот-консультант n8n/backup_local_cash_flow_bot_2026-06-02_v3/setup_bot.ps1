$ErrorActionPreference = 'Stop'

Add-Type -AssemblyName System.Security

$baseDir = $PSScriptRoot
$credentialsDir = Join-Path $baseDir 'credentials'
$tokenFile = Join-Path $credentialsDir 'telegram_token.dpapi'

New-Item -ItemType Directory -Path $credentialsDir -Force | Out-Null

Write-Host ''
Write-Host 'Cash Flow Lifesaver Telegram bot setup'
Write-Host 'The token will stay hidden and will not be stored as plain text.'
Write-Host ''

$secureToken = Read-Host 'Enter the Telegram bot token from BotFather' -AsSecureString
$pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureToken)

try {
    $token = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
    if ([string]::IsNullOrWhiteSpace($token)) {
        throw 'The token was not entered.'
    }

    try {
        $result = Invoke-RestMethod `
            -Uri ("https://api.telegram.org/bot{0}/getMe" -f $token) `
            -Method Get `
            -TimeoutSec 20
    }
    catch {
        throw 'Telegram rejected the token. Check the token in BotFather and run setup again.'
    }

    if (-not $result.ok) {
        throw 'Telegram did not confirm the token.'
    }

    $bytes = [Text.Encoding]::UTF8.GetBytes($token)
    $encrypted = [Security.Cryptography.ProtectedData]::Protect(
        $bytes,
        $null,
        [Security.Cryptography.DataProtectionScope]::CurrentUser
    )
    [IO.File]::WriteAllBytes($tokenFile, $encrypted)
}
finally {
    if ($pointer -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)
    }
    Remove-Variable token -ErrorAction SilentlyContinue
}

Write-Host ''
Write-Host ('Ready. Connected bot: @{0}.' -f $result.result.username)
Write-Host 'Now run run_bot.cmd.'
