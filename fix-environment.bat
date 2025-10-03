@echo off
chcp 65001 >nul
echo ======================================
echo    EDUKY-Monitor 环境检测和修复工具
echo ======================================
echo.

echo 正在检测Python环境...
python --version
if %errorlevel% neq 0 (
    echo 错误: 未找到Python，请先安装Python
    echo 推荐下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo.
echo 正在检测pip...
pip --version
if %errorlevel% neq 0 (
    echo 错误: pip不可用
    pause
    exit /b 1
)

echo.
echo 正在运行环境测试...
python test_environment.py
if %errorlevel% neq 0 (
    echo.
    echo 环境测试失败，正在尝试修复...
    echo.
    
    echo 正在升级pip...
    python -m pip install --upgrade pip
    
    echo.
    echo 正在清除pip缓存...
    pip cache purge
    
    echo.
    echo 正在重新安装依赖...
    
    :: 检测Python版本
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo 检测到Python版本: %PYTHON_VERSION%
    
    echo %PYTHON_VERSION% | findstr /C:"3.13" >nul
    if %errorlevel% equ 0 (
        echo 使用Python 3.13兼容的依赖版本...
        pip install -r requirements-py313.txt --force-reinstall
    ) else (
        echo 使用标准依赖版本...
        pip install -r requirements.txt --force-reinstall
    )
    
    if %errorlevel% neq 0 (
        echo.
        echo 批量安装失败，尝试逐个安装...
        pip install Flask
        pip install Flask-SQLAlchemy
        pip install requests
        pip install APScheduler
        pip install beautifulsoup4
        pip install python-telegram-bot
        pip install "lxml>=4.9.0" --only-binary=lxml
        pip install Werkzeug
        pip install pytz
        pip install ntplib
        pip install "pyinstaller>=6.10.0"
    )
    
    echo.
    echo 重新运行环境测试...
    python test_environment.py
    if %errorlevel% neq 0 (
        echo.
        echo 环境修复失败，请手动检查以下问题:
        echo 1. Python版本是否兼容 (建议使用Python 3.8-3.12)
        echo 2. 网络连接是否正常
        echo 3. 是否有足够的磁盘空间
        echo 4. 是否需要管理员权限
        pause
        exit /b 1
    )
)

echo.
echo ======================================
echo        环境检测完成！
echo ======================================
echo 环境配置正常，可以开始构建
echo.
pause