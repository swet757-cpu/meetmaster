@echo off
cd /d "%~dp0"
for /d %%D in ("*n8n") do (
  if exist "%%D\local_cash_flow_bot\SETUP_AND_START.cmd" (
    cd /d "%%D\local_cash_flow_bot"
    call ".\SETUP_AND_START.cmd"
    exit /b
  )
)
echo Local bot folder was not found.
pause
exit /b 1
