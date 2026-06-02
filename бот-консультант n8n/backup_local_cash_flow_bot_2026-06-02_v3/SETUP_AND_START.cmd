@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\setup_bot.ps1"
if errorlevel 1 (
  echo.
  echo Setup failed. Check the message above.
  pause
  exit /b 1
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\install_autostart.ps1"
wscript.exe ".\start_bot_hidden.vbs"
echo.
echo Ready. Open Telegram and send /start to @cash_gap_buster_bot.
pause
