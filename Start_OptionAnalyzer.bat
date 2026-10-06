@echo off
cd /d "%~dp0"
python Script\OptionAnalyzer.py
if errorlevel 1 (
    echo.
    echo The app could not start. Run: python -m pip install -r requirements.txt
    echo See Logs\application.log for scan errors.
    pause
)
