@echo off
chcp 65001 >nul
echo ===========================================
echo          Quick GitHub Sync
echo ===========================================
echo.

echo Checking git status...
git status

echo.
echo Adding all changes...
git add .

echo.
set /p COMMIT_MSG="Enter commit message (or press Enter for default): "
if "%COMMIT_MSG%"=="" set COMMIT_MSG=Update project files

echo.
echo Committing with message: %COMMIT_MSG%
git commit -m "%COMMIT_MSG%"

echo.
echo Pushing to GitHub...
git push

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Success! Changes have been pushed to GitHub
) else (
    echo.
    echo Push failed! You may need to pull first:
    echo   git pull origin main
    echo Then try pushing again.
)

echo.
pause