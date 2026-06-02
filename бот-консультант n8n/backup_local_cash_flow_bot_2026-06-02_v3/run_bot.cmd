@echo off
cd /d "%~dp0"
python bot.py
if errorlevel 1 (
  echo.
  echo The bot did not start. Check the error message above.
  pause
)
