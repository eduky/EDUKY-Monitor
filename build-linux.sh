#!/bin/bash

echo "======================================"
echo "    EDUKY-Monitor 本地构建脚本"
echo "======================================"
echo

echo "正在检查 Python 环境..."
python3 --version
if [ $? -ne 0 ]; then
    echo "错误: 未找到 Python3，请先安装 Python 3.7+"
    exit 1
fi

echo
echo "正在安装构建依赖..."
pip3 install pyinstaller
if [ $? -ne 0 ]; then
    echo "错误: 安装 PyInstaller 失败"
    exit 1
fi

echo
echo "正在安装项目依赖..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "错误: 安装项目依赖失败"
    exit 1
fi

echo
echo "正在清理旧的构建文件..."
rm -rf dist build

echo
echo "正在构建可执行文件..."
pyinstaller --onefile \
    --console \
    --name eduky-monitor-linux \
    --add-data "web:web" \
    --hidden-import=APScheduler \
    --hidden-import=apscheduler.schedulers.background \
    --hidden-import=apscheduler.triggers.interval \
    --hidden-import=flask \
    --hidden-import=flask.templating \
    --hidden-import=flask.json \
    --hidden-import=requests \
    --hidden-import=flask_sqlalchemy \
    --hidden-import=sqlalchemy \
    --hidden-import=sqlalchemy.sql.default_comparator \
    --hidden-import=beautifulsoup4 \
    --hidden-import=bs4 \
    --hidden-import=telegram \
    --hidden-import=lxml \
    --hidden-import=werkzeug \
    --hidden-import=werkzeug.security \
    --hidden-import=pytz \
    --hidden-import=ntplib \
    --hidden-import=logging.handlers \
    --hidden-import=sqlite3 \
    --hidden-import=json \
    --hidden-import=datetime \
    --hidden-import=threading \
    run_app.py

if [ $? -ne 0 ]; then
    echo "错误: 构建失败"
    exit 1
fi

echo
echo "正在创建启动脚本..."
cat > dist/start-eduky-monitor.sh << 'EOF'
#!/bin/bash

echo "======================================"
echo "      EDUKY-Monitor 启动器"
echo "======================================"
echo "启动后请访问: http://localhost:5000"
echo "默认用户名: admin, 密码: admin123"
echo "======================================"
echo

# 检查可执行文件是否存在
if [ ! -f "./eduky-monitor-linux" ]; then
    echo "错误: 找不到 eduky-monitor-linux 可执行文件"
    echo "请确保在正确的目录下运行此脚本"
    exit 1
fi

# 确保可执行文件有执行权限
chmod +x ./eduky-monitor-linux

# 创建logs目录
mkdir -p logs

echo "正在启动 EDUKY-Monitor..."
echo "提示: 按 Ctrl+C 停止程序"
echo

# 启动程序并捕获错误
./eduky-monitor-linux
exit_code=$?

echo
if [ $exit_code -ne 0 ]; then
    echo "程序异常退出，退出码: $exit_code"
    echo "请检查错误信息并确保所有依赖都已正确安装"
else
    echo "程序正常退出"
fi

echo "按任意键继续..."
read -n 1
EOF
chmod +x dist/start-eduky-monitor.sh

echo
echo "正在创建调试启动脚本..."
cat > dist/start-eduky-monitor-debug.sh << 'EOF'
#!/bin/bash

echo "======================================"
echo "   EDUKY-Monitor 调试模式启动器"
echo "======================================"
echo

# 检查可执行文件是否存在
if [ ! -f "./eduky-monitor-linux" ]; then
    echo "错误: 找不到 eduky-monitor-linux 可执行文件"
    exit 1
fi

# 确保可执行文件有执行权限
chmod +x ./eduky-monitor-linux

# 创建logs目录
mkdir -p logs

echo "系统信息:"
echo "操作系统: $(uname -a)"
echo "Python路径: $(which python3)"
echo "当前目录: $(pwd)"
echo "文件权限: $(ls -la eduky-monitor-linux)"
echo

echo "正在以调试模式启动 EDUKY-Monitor..."
echo "这将显示详细的错误信息"
echo

# 以详细模式启动
strace -o trace.log ./eduky-monitor-linux 2>&1 | tee run.log
exit_code=$?

echo
echo "程序退出码: $exit_code"
echo "运行日志已保存到: run.log"
echo "系统调用跟踪已保存到: trace.log"

if [ $exit_code -ne 0 ]; then
    echo
    echo "程序异常退出，请检查以下文件获取详细信息:"
    echo "- run.log: 程序输出日志"
    echo "- trace.log: 系统调用跟踪"
    echo "- logs/: 应用程序日志目录"
fi

echo "按任意键继续..."
read -n 1
EOF
chmod +x dist/start-eduky-monitor-debug.sh

echo
echo "正在创建说明文件..."
cat > dist/README.md << 'EOF'
# EDUKY-Monitor Linux 本地构建版

## 使用方法
1. 运行启动脚本: `./start-eduky-monitor.sh`
2. 等待程序启动完成
3. 打开浏览器访问 http://localhost:5000
4. 使用默认账号登录: admin / admin123

## 注意事项
- 首次运行会自动创建数据库文件
- 建议首次登录后立即修改默认密码
- 按 Ctrl+C 停止程序
- 程序数据保存在可执行文件同目录下

## 系统服务安装 (可选)
如需安装为系统服务，请下载完整源码:
```bash
git clone https://github.com/eduky/EDUKY-Monitor.git
cd EDUKY-Monitor/scripts/linux
sudo ./install_systemd.sh
```
EOF

echo
mkdir -p dist/logs
touch dist/logs/.gitkeep

echo "======================================"
echo "          构建完成！"
echo "======================================"
echo
echo "可执行文件位置: dist/eduky-monitor-linux"
echo "启动脚本: dist/start-eduky-monitor.sh"
echo
echo "可以将 dist 目录下的所有文件打包分发"
echo