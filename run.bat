@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
echo ==========================================
echo Stock Valuation Percentile Analysis Tool
echo ==========================================
echo.

if exist ".venv\Scripts\python.exe" (
    set "PYTHON_CMD=.venv\Scripts\python.exe"
    echo [Info] Using virtual environment Python
) else (
    set "PYTHON_CMD=python"
    echo [Info] Using system Python
)
echo.

echo [Starting] Launching application...
echo.

!PYTHON_CMD! main.py

if errorlevel 1 (
    echo.
    echo [Error] Program exited with error
    echo.
    pause
    exit /b 1
)

echo.
echo [Done] Program exited normally
echo.
pause
