#!/bin/bash

# EDUKY-商品监控系统 - systemd 服务卸载脚本

set -e

# 配置变量
APP_NAME="eduky-monitor"
INSTALL_DIR="/opt/eduky-monitor"
SERVICE_FILE="/etc/systemd/system/${APP_NAME}.service"
LOG_DIR="/var/log/eduky-monitor"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查root权限
if [[ $EUID -ne 0 ]]; then
    log_error "此脚本需要root权限运行"
    echo "请使用: sudo $0"
    exit 1
fi

echo ""
log_info "开始卸载EDUKY-商品监控系统..."
echo ""

# 停止并禁用服务
if systemctl is-active --quiet $APP_NAME 2>/dev/null; then
    log_step "停止服务..."
    systemctl stop $APP_NAME
    log_info "服务已停止"
fi

if systemctl is-enabled --quiet $APP_NAME 2>/dev/null; then
    log_step "禁用服务..."
    systemctl disable $APP_NAME
    log_info "服务已禁用"
fi

# 删除服务文件
if [[ -f $SERVICE_FILE ]]; then
    log_step "删除服务文件..."
    rm -f $SERVICE_FILE
    systemctl daemon-reload
    log_info "服务文件已删除"
fi

# 询问是否删除应用文件
read -p "是否删除应用文件? ($INSTALL_DIR) [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [[ -d $INSTALL_DIR ]]; then
        log_step "删除应用文件..."
        rm -rf $INSTALL_DIR
        log_info "应用文件已删除"
    fi
fi

# 询问是否删除日志文件
read -p "是否删除日志文件? ($LOG_DIR) [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [[ -d $LOG_DIR ]]; then
        log_step "删除日志文件..."
        rm -rf $LOG_DIR
        log_info "日志文件已删除"
    fi
fi

echo ""
log_info "卸载完成！"