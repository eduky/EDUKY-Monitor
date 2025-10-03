@echo off
chcp 65001 >nul
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
git remote remove origin 2>nul
git remote add origin "%REPO_URL%"

if %ERRORLEVEL% NEQ 0 (
    echo 添加远程仓库时出错！
    pause
    exit /b 1
)

echo.
echo 检查git状态...
git status --porcelain > nul
if %ERRORLEVEL% NEQ 0 (
    echo 错误：不是git仓库！
    pause
    exit /b 1
)

echo.
echo 添加所有文件...
git add .

echo.
echo 提交更改...
git commit -m "Update project files" 2>nul

echo.
echo 设置分支为main...
git branch -M main

echo.
echo 推送到GitHub...
git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo 成功！项目已上传到GitHub
    echo 你可以访问以下地址查看你的项目：
    echo %REPO_URL%
) else (
    echo.
    echo 上传失败！请检查：
    echo 1. 网络连接是否正常
    echo 2. 仓库地址是否正确
    echo 3. 是否有推送权限
    echo 4. GitHub上的仓库是否存在
    echo.
    echo 如果是第一次使用，可能需要登录GitHub账号
)

echo.
pause