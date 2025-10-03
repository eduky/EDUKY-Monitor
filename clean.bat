@echo off
chcp 65001 >nul
echo ======================================
echo    EDUKY-Monitor 清理工具
echo ======================================
echo.

echo 正在清理临时文件和缓存...

:: 清理Python缓存
if exist "__pycache__" (
    echo 清理Python缓存目录...
    rmdir /s /q "__pycache__"
)

:: 清理PyInstaller文件
if exist "build" (
    echo 清理构建临时目录...
    rmdir /s /q "build"
)

if exist "dist" (
    echo 清理发布目录...
    rmdir /s /q "dist"
)

:: 清理spec文件
if exist "*.spec" (
    echo 清理PyInstaller配置文件...
    del /q "*.spec" 2>nul
)

:: 清理日志文件
if exist "logs\*.log" (
    echo 清理日志文件...
    del /q "logs\*.log" 2>nul
)

:: 清理临时数据库文件
if exist "web\instance\*.db" (
    echo 清理临时数据库文件...
    del /q "web\instance\*.db" 2>nul
)

:: 清理其他临时文件
if exist "*.tmp" (
    del /q "*.tmp" 2>nul
)

if exist "*.temp" (
    del /q "*.temp" 2>nul
)

echo.
echo ======================================
echo         清理完成！
echo ======================================
echo 已清理以下内容:
echo - Python缓存文件
echo - 构建临时文件
echo - 日志文件
echo - 临时数据库文件
echo - PyInstaller配置文件
echo.
pause