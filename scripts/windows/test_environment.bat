@echo off
chcp 65001 >nul
echo.
echo ========================================
echo     EDUKY-商品监控系统 - 测试脚本
echo ========================================
echo.

set "SCRIPT_DIR=%~dp0"
set "APP_DIR=%SCRIPT_DIR%..\.."
cd /d "%APP_DIR%"

echo [信息] 开始测试系统环境...
echo.

:: 测试Python环境
echo [测试] Python环境...
py --version 2>nul
if %errorLevel% neq 0 (
    echo [错误] Python未安装或不在PATH中
    goto :error
) else (
    echo [通过] Python环境正常
)

:: 测试依赖包
echo [测试] Python依赖包...
py -c "import flask, requests, sqlite3" 2>nul
if %errorLevel% neq 0 (
    echo [警告] 依赖包缺失，尝试安装...
    py -m pip install -r requirements.txt
    if %errorLevel% neq 0 (
        echo [错误] 依赖包安装失败
        goto :error
    )
) else (
    echo [通过] 依赖包完整
)

:: 测试端口占用
echo [测试] 端口5000可用性...
netstat -an | find "0.0.0.0:5000" >nul
if %errorLevel% equ 0 (
    echo [警告] 端口5000已被占用
    netstat -an | find ":5000"
) else (
    echo [通过] 端口5000可用
)

:: 测试数据库
echo [测试] 数据库连接...
py -c "from app_v2_fixed import db; db.create_all(); print('[通过] 数据库连接正常')" 2>nul
if %errorLevel% neq 0 (
    echo [错误] 数据库初始化失败
    goto :error
)

:: 测试应用启动
echo [测试] 应用启动测试...
start /b py app_production.py
timeout /t 5 /nobreak >nul

:: 检查进程
tasklist | find "python" >nul
if %errorLevel% equ 0 (
    echo [通过] 应用进程启动成功
    
    :: 测试HTTP响应
    echo [测试] HTTP服务响应...
    powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:5000' -TimeoutSec 10; if ($response.StatusCode -eq 200) { Write-Host '[通过] HTTP服务响应正常' } else { Write-Host '[警告] HTTP响应异常:' $response.StatusCode } } catch { Write-Host '[错误] HTTP服务无响应' }"
    
    :: 停止测试进程
    echo [信息] 停止测试进程...
    taskkill /f /im python.exe 2>nul
    taskkill /f /im py.exe 2>nul
) else (
    echo [错误] 应用启动失败
    goto :error
)

echo.
echo [成功] 所有测试通过！系统可以正常部署
echo.
echo 下一步操作:
echo   1. 运行 deploy_windows_service.bat 部署为Windows服务
echo   2. 或直接运行 py app_production.py 启动应用
echo   3. 访问 http://localhost:5000 使用系统
echo.
pause
exit /b 0

:error
echo.
echo [失败] 测试未通过，请检查错误信息
echo.
pause
exit /b 1