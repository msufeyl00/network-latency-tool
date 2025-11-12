@echo off
REM Auto commit and push script for Windows
REM This script will automatically commit and push changes

cd /d "%~dp0"

REM Add all changes
git add .

REM Check if there are changes
git diff-index --quiet HEAD
if %errorlevel% neq 0 (
    REM Commit with timestamp
    git commit -m "Auto-commit: %date% %time%"
    
    REM Push to GitHub
    git push origin main
    
    echo Changes pushed to GitHub successfully!
) else (
    echo No changes to commit
)
