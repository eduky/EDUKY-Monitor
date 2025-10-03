@echo off
chcp 65001 >nul
echo ===========================================
echo          FAKA Monitor GitHub Upload Tool
echo ===========================================
echo.

echo Please ensure you have:
echo 1. Created a new repository on GitHub
echo 2. Copied the HTTPS or SSH address of the repository
echo.

set /p REPO_URL="Enter GitHub repository URL (e.g., https://github.com/username/faka-monitor.git): "

if "%REPO_URL%"=="" (
    echo Error: Please provide a valid repository address!
    pause
    exit /b 1
)

echo.
echo Adding remote repository...
git remote remove origin 2>nul
git remote add origin "%REPO_URL%"

if %ERRORLEVEL% NEQ 0 (
    echo Error adding remote repository!
    pause
    exit /b 1
)

echo.
echo Checking git status...
git status --porcelain > nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Not a git repository!
    pause
    exit /b 1
)

echo.
echo Adding all files...
git add .

echo.
echo Committing changes...
git commit -m "Update project files" 2>nul

echo.
echo Setting branch to main...
git branch -M main

echo.
echo Pushing to GitHub...
git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Success! Project has been uploaded to GitHub
    echo You can visit your project at:
    echo %REPO_URL%
) else (
    echo.
    echo Upload failed! Please check:
    echo 1. Network connection
    echo 2. Repository address is correct
    echo 3. You have push permissions
    echo 4. Repository exists on GitHub
    echo.
    echo If this is your first time, you may need to login to GitHub
)

echo.
pause