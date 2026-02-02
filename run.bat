@echo off
title Jarvis 2.0 - Neural Interface
color 0B
cd /d "%~dp0"

:: Check if venv exists
if not exist venv (
    echo [*] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [!] Failed to create venv. Make sure Python is installed.
        pause
        exit /b 1
    )
    
    echo [*] Installing dependencies...
    call venv\Scripts\activate
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [!] Failed to install dependencies.
        pause
        exit /b 1
    )
) else (
    call venv\Scripts\activate
    
    :: Only check dependencies if requirements.txt is newer than last check
    if not exist .deps_installed (
        echo [*] First run - checking dependencies...
        pip install -q -r requirements.txt
        echo installed > .deps_installed
    )
)

:: Clear screen and run
cls
python -m app.main
