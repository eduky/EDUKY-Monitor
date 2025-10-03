@echo off
chcp 65001 >nul
title EDUKY-Monitor 库存监控系统

echo.
echo ========================================
echo     EDUKY-Monitor 库存监控系统
echo ========================================
echo.
echo 正在启动应用程序...
echo 启动后请访问: http://localhost:5000
echo 默认登录账号: admin / admin123
echo.
echo 按 Ctrl+C 停止程序
echo ========================================
echo.

:: 启动Python应用
python run_app.py

echo.
echo 程序已关闭
pause