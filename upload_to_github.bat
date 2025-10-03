@echo off
echo ===========================================
echo          FAKA Monitor GitHub 上传工具
echo ===========================================
echo.

echo 请确保你已经：
echo 1. 在GitHub上创建了一个新的仓库
echo 2. 复制了仓库的HTTPS或SSH地址
echo.

set /p REPO_URL="请输入GitHub仓库地址 (例如: https://github.com/username/faka-monitor.git): "

if "%REPO_URL%"=="" (
    echo 错误：请提供有效的仓库地址！
    pause
    exit /b 1
)

echo.
echo 正在添加远程仓库...
git remote add origin %REPO_URL%

echo.
echo 正在推送到GitHub...
git branch -M main
git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ 成功！项目已上传到GitHub
    echo 你可以访问以下地址查看你的项目：
    echo %REPO_URL%
) else (
    echo.
    echo ❌ 上传失败！请检查：
    echo 1. 网络连接是否正常
    echo 2. 仓库地址是否正确
    echo 3. 是否有推送权限
    echo.
    echo 如果是第一次使用，可能需要登录GitHub账号
)

echo.
pause