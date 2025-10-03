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
    --name eduky-monitor-linux \
    --add-data "web:web" \
    --hidden-import=APScheduler \
    --hidden-import=flask \
    --hidden-import=requests \
    --hidden-import=flask_sqlalchemy \
    --hidden-import=sqlalchemy \
    --hidden-import=beautifulsoup4 \
    --hidden-import=telegram \
    --hidden-import=lxml \
    --hidden-import=werkzeug \
    --hidden-import=pytz \
    --hidden-import=ntplib \
    run_app.py

if [ $? -ne 0 ]; then
    echo "错误: 构建失败"
    exit 1
fi

echo
echo "正在创建启动脚本..."
cat > dist/start-eduky-monitor.sh << 'EOF'
#!/bin/bash
echo "正在启动 EDUKY-Monitor..."
echo "启动后请访问: http://localhost:5000"
echo "默认用户名: admin, 密码: admin123"
echo
./eduky-monitor-linux
EOF
chmod +x dist/start-eduky-monitor.sh

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