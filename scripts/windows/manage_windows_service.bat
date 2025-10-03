@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set "SERVICE_NAME=EdUKYMonitorService"
set "APP_DIR=%~dp0"

:: 显示菜单
:menu
cls
echo.
echo ========================================
echo      EDUKY-商品监控系统 - 服务管理
echo ========================================
echo.
echo 1. 查看服务状态
echo 2. 启动服务
echo 3. 停止服务  
echo 4. 重启服务
echo 5. 查看实时日志
echo 6. 打开Web界面
echo 7. 服务配置
echo 8. 卸载服务
echo 0. 退出
echo.
set /p choice="请选择操作 [0-8]: "

if "%choice%"=="1" goto :status
if "%choice%"=="2" goto :start
if "%choice%"=="3" goto :stop
if "%choice%"=="4" goto :restart
if "%choice%"=="5" goto :logs
if "%choice%"=="6" goto :web
if "%choice%"=="7" goto :config
if "%choice%"=="8" goto :uninstall
if "%choice%"=="0" goto :exit
echo 无效选择，请重试...
timeout /t 2 /nobreak >nul
goto :menu

:status
echo.
echo [信息] 查看服务状态...
echo.
sc query "%SERVICE_NAME%" 2>nul
if %errorLevel% neq 0 (
    echo [错误] 服务未安装
) else (
    nssm status "%SERVICE_NAME%" 2>nul
    echo.
    echo 详细信息:
    sc qc "%SERVICE_NAME%" | findstr "BINARY_PATH_NAME DISPLAY_NAME START_TYPE"
)
echo.
pause
goto :menu

:start
echo.
echo [信息] 启动服务...
nssm start "%SERVICE_NAME%"
timeout /t 3 /nobreak >nul
sc query "%SERVICE_NAME%" | find "RUNNING" >nul
if %errorLevel% equ 0 (
    echo [成功] 服务已启动
) else (
    echo [错误] 服务启动失败
)
echo.
pause
goto :menu

:stop
echo.
echo [信息] 停止服务...
nssm stop "%SERVICE_NAME%"
timeout /t 3 /nobreak >nul
sc query "%SERVICE_NAME%" | find "STOPPED" >nul
if %errorLevel% equ 0 (
    echo [成功] 服务已停止
) else (
    echo [警告] 服务可能未完全停止
)
echo.
pause
goto :menu

:restart
echo.
echo [信息] 重启服务...
nssm restart "%SERVICE_NAME%"
echo [完成] 重启命令已发送
echo.
pause
goto :menu

:logs
echo.
echo [信息] 查看实时日志 (按Ctrl+C退出)...
echo.
if exist "%APP_DIR%logs\service.log" (
    powershell -Command "Get-Content '%APP_DIR%logs\service.log' -Wait -Tail 50"
) else (
    echo 日志文件不存在: %APP_DIR%logs\service.log
    pause
)
goto :menu

:web
echo.
echo [信息] 打开Web界面...
start http://localhost:5000
echo.
pause
goto :menu

:config
echo.
echo [信息] 打开服务配置界面...
nssm edit "%SERVICE_NAME%"
echo.
pause
goto :menu

:uninstall
echo.
set /p confirm="确认要卸载服务吗? [y/N]: "
if /i "%confirm%"=="y" (
    echo [信息] 停止并卸载服务...
    nssm stop "%SERVICE_NAME%"
    timeout /t 3 /nobreak >nul
    nssm remove "%SERVICE_NAME%" confirm
    echo [完成] 服务已卸载
) else (
    echo [取消] 未执行卸载操作
)
echo.
pause
goto :menu

:exit
echo.
echo 再见！
timeout /t 1 /nobreak >nul
exit /b 0