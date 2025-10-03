#!/bin/bash

# EDUKY-商品监控系统 - 快速部署脚本
# 适用于测试和快速部署

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
APP_NAME="eduky-monitor"
INSTALL_DIR="/opt/eduky-monitor"
SERVICE_FILE="/etc/systemd/system/${APP_NAME}.service"

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

# 检查root权限
if [[ $EUID -ne 0 ]]; then
    log_error "需要root权限，请使用: sudo $0"
    exit 1
fi

echo ""
log_info "🚀 快速部署EDUKY-商品监控系统"
echo ""

# 创建安装目录
log_info "创建目录..."
mkdir -p $INSTALL_DIR
mkdir -p /var/log/eduky-monitor

# 复制文件
log_info "复制应用文件..."
cp -r "$SCRIPT_DIR"/* $INSTALL_DIR/

# 创建用户
if ! id "djk" &>/dev/null; then
    log_info "创建应用用户..."
    useradd -r -d $INSTALL_DIR -s /bin/bash djk
fi

# 设置权限
chown -R djk:djk $INSTALL_DIR
chown -R djk:djk /var/log/eduky-monitor
chmod +x $INSTALL_DIR/app_production.py

# 安装Python依赖
log_info "安装Python依赖..."
cd $INSTALL_DIR

if [[ ! -d "venv" ]]; then
    sudo -u djk python3 -m venv venv
fi

sudo -u djk bash -c "
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
"

# 创建优化的服务文件
log_info "创建systemd服务..."
cat > $SERVICE_FILE << EOF
[Unit]
Description=EDUKY-商品监控系统
After=network.target
Wants=network.target

[Service]
Type=simple
User=djk
Group=djk
WorkingDirectory=$INSTALL_DIR
Environment="PYTHONPATH=$INSTALL_DIR"
Environment="FLASK_ENV=production"
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/app_production.py
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=eduky-monitor

# 性能优化
LimitNOFILE=65535
LimitNPROC=32768

# 安全设置
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ReadWritePaths=$INSTALL_DIR /var/log/eduky-monitor
ProtectHome=yes

[Install]
WantedBy=multi-user.target
EOF

# 重新加载systemd
systemctl daemon-reload
systemctl enable $APP_NAME

# 初始化数据库
log_info "初始化数据库..."
cd $INSTALL_DIR
sudo -u djk bash -c "
    source venv/bin/activate
    python -c 'from app_v2_fixed import db; db.create_all()'
"

# 启动服务
log_info "启动服务..."
systemctl start $APP_NAME
sleep 3

# 检查状态
if systemctl is-active --quiet $APP_NAME; then
    log_info "✅ 部署成功！"
    echo ""
    echo "📋 服务信息:"
    echo "  • 服务名称: $APP_NAME"
    echo "  • 安装目录: $INSTALL_DIR"
    echo "  • 访问地址: http://localhost:5000"
    echo ""
    echo "🔧 管理命令:"
    echo "  • 查看状态: systemctl status $APP_NAME"
    echo "  • 查看日志: journalctl -u $APP_NAME -f"
    echo "  • 重启服务: systemctl restart $APP_NAME"
    echo "  • 管理脚本: $INSTALL_DIR/manage_service.sh"
    echo ""
else
    log_error "❌ 服务启动失败"
    systemctl status $APP_NAME --no-pager
    exit 1
fi