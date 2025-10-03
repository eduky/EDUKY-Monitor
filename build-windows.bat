@echo off
chcp 65001 >nul
echo ======================================
echo    EDUKY-Monitor 本地构建脚本
echo ======================================
echo.

echo 正在检查 Python 环境...
python --version
if %errorlevel% neq 0 (
    echo 错误: 未找到 Python，请先安装 Python 3.7+
    pause
    exit /b 1
)

echo.
echo 正在检测Python版本...
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python版本: %PYTHON_VERSION%

echo.
echo 正在安装构建依赖...
pip install "pyinstaller>=6.10.0"
if %errorlevel% neq 0 (
    echo 错误: 安装 PyInstaller 失败
    pause
    exit /b 1
)

echo.
echo 正在安装项目依赖...
:: 检查是否为Python 3.13+，使用兼容的requirements文件
echo %PYTHON_VERSION% | findstr /C:"3.13" >nul
if %errorlevel% equ 0 (
    echo 检测到Python 3.13，使用兼容版本的依赖...
    pip install -r requirements-py313.txt
) else (
    pip install -r requirements.txt
)
if %errorlevel% neq 0 (
    echo 错误: 安装项目依赖失败
    echo 尝试单独安装依赖包...
    pip install Flask Flask-SQLAlchemy requests APScheduler beautifulsoup4 python-telegram-bot lxml Werkzeug pytz ntplib
    if %errorlevel% neq 0 (
        echo 错误: 依赖安装彻底失败
        pause
        exit /b 1
    )
)

echo.
echo 正在清理旧的构建文件...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

echo.
echo 正在构建可执行文件...
pyinstaller --onefile ^
    --console ^
    --name eduky-monitor-windows ^
    --add-data "web;web" ^
    --hidden-import=APScheduler ^
    --hidden-import=apscheduler.schedulers.background ^
    --hidden-import=apscheduler.triggers.interval ^
    --hidden-import=flask ^
    --hidden-import=flask.templating ^
    --hidden-import=flask.json ^
    --hidden-import=requests ^
    --hidden-import=flask_sqlalchemy ^
    --hidden-import=sqlalchemy ^
    --hidden-import=sqlalchemy.sql.default_comparator ^
    --hidden-import=beautifulsoup4 ^
    --hidden-import=bs4 ^
    --hidden-import=telegram ^
    --hidden-import=lxml ^
    --hidden-import=werkzeug ^
    --hidden-import=werkzeug.security ^
    --hidden-import=pytz ^
    --hidden-import=ntplib ^
    --hidden-import=logging.handlers ^
    --hidden-import=sqlite3 ^
    --hidden-import=json ^
    --hidden-import=datetime ^
    --hidden-import=threading ^
    run_app.py

if %errorlevel% neq 0 (
    echo 错误: 构建失败
    pause
    exit /b 1
)

echo.
echo 正在创建启动脚本...
echo @echo off > dist\start-eduky-monitor.bat
echo chcp 65001 ^>nul >> dist\start-eduky-monitor.bat
echo title EDUKY-Monitor 库存监控系统 >> dist\start-eduky-monitor.bat
echo echo. >> dist\start-eduky-monitor.bat
echo echo ======================================== >> dist\start-eduky-monitor.bat
echo echo      EDUKY-Monitor 库存监控系统 >> dist\start-eduky-monitor.bat
echo echo ======================================== >> dist\start-eduky-monitor.bat
echo echo 启动后请访问: http://localhost:5000 >> dist\start-eduky-monitor.bat
echo echo 默认用户名: admin, 密码: admin123 >> dist\start-eduky-monitor.bat
echo echo 按 Ctrl+C 停止程序 >> dist\start-eduky-monitor.bat
echo echo ======================================== >> dist\start-eduky-monitor.bat
echo echo. >> dist\start-eduky-monitor.bat
echo eduky-monitor-windows.exe >> dist\start-eduky-monitor.bat
echo echo. >> dist\start-eduky-monitor.bat
echo echo 程序已关闭 >> dist\start-eduky-monitor.bat
echo pause >> dist\start-eduky-monitor.bat

echo.
echo 正在创建说明文件...
echo # EDUKY-Monitor Windows 本地构建版 > dist\README.txt
echo. >> dist\README.txt
echo ## 使用方法 >> dist\README.txt
echo 1. 双击 start-eduky-monitor.bat 启动程序 >> dist\README.txt
echo 2. 等待程序启动完成 >> dist\README.txt
echo 3. 打开浏览器访问 http://localhost:5000 >> dist\README.txt
echo 4. 使用默认账号登录: admin / admin123 >> dist\README.txt
echo. >> dist\README.txt
echo ## 注意事项 >> dist\README.txt
echo - 首次运行会自动创建数据库文件 >> dist\README.txt
echo - 建议首次登录后立即修改默认密码 >> dist\README.txt
echo - 关闭命令行窗口即可停止程序 >> dist\README.txt
echo - 程序数据保存在 exe 文件同目录下 >> dist\README.txt

echo.
mkdir dist\logs 2>nul
echo. > dist\logs\.gitkeep

echo ======================================
echo          构建完成！
echo ======================================
echo.
echo 可执行文件位置: dist\eduky-monitor-windows.exe
echo 启动脚本: dist\start-eduky-monitor.bat
echo.
echo 可以将 dist 目录下的所有文件打包分发
echo.
pause