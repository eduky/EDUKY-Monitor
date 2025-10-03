@echo off
chcp 65001 >nul
:: 设置变量
set "APP_NAME=EdUKYMonitor"
set "SCRIPT_DIR=%~dp0"
set "APP_DIR=%SCRIPT_DIR%..\.."
set "SERVICE_NAME=EdUKYMonitorService"
set "PYTHON_EXE=python"nul
echo.
echo ========================================
echo   EDUKY-商品监控系统 - Windows服务部署
echo ========================================
echo.

:: 检查管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [错误] 需要管理员权限运行此脚本
    echo 请右键点击脚本并选择"以管理员身份运行"
    pause
    exit /b 1
)

:: 设置变量
set "APP_NAME=EdUKYMonitor"
set "SCRIPT_DIR=%~dp0"
set "APP_DIR=%SCRIPT_DIR%..\.."
set "SERVICE_NAME=EdUKYMonitorService"
set "PYTHON_EXE=py"

echo [信息] 开始部署EDUKY-商品监控系统...
echo.

:: 检查Python
%PYTHON_EXE% --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [错误] 未找到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

echo [信息] Python环境检查通过

:: 检查并安装依赖
echo [信息] 安装Python依赖包...
%PYTHON_EXE% -m pip install --upgrade pip
%PYTHON_EXE% -m pip install -r requirements.txt

:: 检查NSSM (Non-Sucking Service Manager)
where nssm >nul 2>&1
if %errorLevel% neq 0 (
    echo [警告] 未找到NSSM，将下载并安装...
    call :download_nssm
)

:: 停止现有服务
sc query "%SERVICE_NAME%" >nul 2>&1
if %errorLevel% equ 0 (
    echo [信息] 停止现有服务...
    nssm stop "%SERVICE_NAME%"
    timeout /t 3 /nobreak >nul
    nssm remove "%SERVICE_NAME%" confirm
)

:: 创建Windows服务
echo [信息] 创建Windows服务...
nssm install "%SERVICE_NAME%" "%PYTHON_EXE%" "%APP_DIR%app_production.py"
nssm set "%SERVICE_NAME%" AppDirectory "%APP_DIR%"
nssm set "%SERVICE_NAME%" DisplayName "EDUKY-商品监控系统"
nssm set "%SERVICE_NAME%" Description "EDUKY-商品监控系统"
nssm set "%SERVICE_NAME%" Start SERVICE_AUTO_START
nssm set "%SERVICE_NAME%" AppStdout "%APP_DIR%logs\service.log"
nssm set "%SERVICE_NAME%" AppStderr "%APP_DIR%logs\error.log"
nssm set "%SERVICE_NAME%" AppRotateFiles 1
nssm set "%SERVICE_NAME%" AppRotateOnline 1
nssm set "%SERVICE_NAME%" AppRotateSeconds 86400
nssm set "%SERVICE_NAME%" AppRotateBytes 10485760

:: 创建日志目录
if not exist "%APP_DIR%logs" mkdir "%APP_DIR%logs"

:: 启动服务
echo [信息] 启动服务...
nssm start "%SERVICE_NAME%"

:: 检查服务状态
timeout /t 5 /nobreak >nul
sc query "%SERVICE_NAME%" | find "RUNNING" >nul
if %errorLevel% equ 0 (
    echo.
    echo [成功] 服务部署完成！
    echo.
    echo 服务信息:
    echo   - 服务名称: %SERVICE_NAME%
    echo   - 显示名称: EDUKY-商品监控系统
    echo   - 访问地址: http://localhost:5000
    echo   - 日志文件: %APP_DIR%logs\service.log
    echo.
    echo 管理命令:
    echo   - 启动服务: nssm start %SERVICE_NAME%
    echo   - 停止服务: nssm stop %SERVICE_NAME%
    echo   - 重启服务: nssm restart %SERVICE_NAME%
    echo   - 查看状态: sc query %SERVICE_NAME%
    echo   - 服务配置: nssm edit %SERVICE_NAME%
    echo.
) else (
    echo [错误] 服务启动失败
    nssm status "%SERVICE_NAME%"
)

pause
exit /b 0

:: 下载NSSM函数
:download_nssm
echo [信息] 下载NSSM工具...
if not exist "%TEMP%\nssm.zip" (
    echo 请手动下载NSSM: https://nssm.cc/download
    echo 解压后将nssm.exe放置在系统PATH中
    pause
    exit /b 1
)
goto :eof