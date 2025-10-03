#!/bin/bash

# EDUKY-商品监控系统 - 服务管理脚本

APP_NAME="eduky-monitor"
INSTALL_DIR="/opt/eduky-monitor"
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

show_status() {
    echo ""
    echo "=== EDUKY-商品监控系统状态 ==="
    echo ""
    
    if systemctl is-active --quiet $APP_NAME; then
        log_info "🟢 服务状态: 运行中"
    else
        log_warn "🔴 服务状态: 已停止"
    fi
    
    if systemctl is-enabled --quiet $APP_NAME; then
        log_info "🔄 自启动: 已启用"
    else
        log_warn "⏸️  自启动: 已禁用"
    fi
    
    echo ""
    echo "📊 详细状态:"
    systemctl status $APP_NAME --no-pager --lines=5
    
    echo ""
    echo "💾 磁盘使用:"
    if [[ -d $INSTALL_DIR ]]; then
        echo "  应用目录: $(du -sh $INSTALL_DIR 2>/dev/null | cut -f1)"
    fi
    if [[ -d $LOG_DIR ]]; then
        echo "  日志目录: $(du -sh $LOG_DIR 2>/dev/null | cut -f1)"
    fi
}

show_logs() {
    echo ""
    log_info "查看服务日志 (按 Ctrl+C 退出):"
    echo ""
    journalctl -u $APP_NAME -f
}

show_app_logs() {
    local log_file="$LOG_DIR/app.log"
    if [[ -f $log_file ]]; then
        echo ""
        log_info "查看应用日志 (按 Ctrl+C 退出):"
        echo ""
        tail -f $log_file
    else
        log_warn "应用日志文件不存在: $log_file"
    fi
}

restart_service() {
    echo ""
    log_info "重启服务..."
    systemctl restart $APP_NAME
    sleep 2
    
    if systemctl is-active --quiet $APP_NAME; then
        log_info "✅ 服务重启成功"
        show_status
    else
        log_error "❌ 服务重启失败"
        systemctl status $APP_NAME --no-pager
    fi
}

stop_service() {
    echo ""
    log_info "停止服务..."
    systemctl stop $APP_NAME
    
    if ! systemctl is-active --quiet $APP_NAME; then
        log_info "✅ 服务已停止"
    else
        log_error "❌ 服务停止失败"
    fi
}

start_service() {
    echo ""
    log_info "启动服务..."
    systemctl start $APP_NAME
    sleep 2
    
    if systemctl is-active --quiet $APP_NAME; then
        log_info "✅ 服务启动成功"
        show_status
    else
        log_error "❌ 服务启动失败"
        systemctl status $APP_NAME --no-pager
    fi
}

enable_service() {
    echo ""
    log_info "启用开机自启..."
    systemctl enable $APP_NAME
    log_info "✅ 开机自启已启用"
}

disable_service() {
    echo ""
    log_info "禁用开机自启..."
    systemctl disable $APP_NAME
    log_info "✅ 开机自启已禁用"
}

show_help() {
    echo ""
    echo "EDUKY-商品监控系统 - 服务管理工具"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  status      显示服务状态 (默认)"
    echo "  start       启动服务"
    echo "  stop        停止服务"
    echo "  restart     重启服务"
    echo "  enable      启用开机自启"
    echo "  disable     禁用开机自启"
    echo "  logs        查看系统日志"
    echo "  app-logs    查看应用日志"
    echo "  help        显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 status"
    echo "  $0 restart"
    echo "  $0 logs"
    echo ""
}

# 检查是否安装了systemd
if ! command -v systemctl &> /dev/null; then
    log_error "此系统不支持systemd"
    exit 1
fi

# 检查服务是否存在
if ! systemctl list-unit-files | grep -q $APP_NAME; then
    log_error "服务 $APP_NAME 未安装"
    echo "请先运行安装脚本: sudo ./install_systemd.sh"
    exit 1
fi

# 处理命令行参数
case "${1:-status}" in
    "status")
        show_status
        ;;
    "start")
        start_service
        ;;
    "stop")
        stop_service
        ;;
    "restart")
        restart_service
        ;;
    "enable")
        enable_service
        ;;
    "disable")
        disable_service
        ;;
    "logs")
        show_logs
        ;;
    "app-logs")
        show_app_logs
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        log_error "未知命令: $1"
        show_help
        exit 1
        ;;
esac