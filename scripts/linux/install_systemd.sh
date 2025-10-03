#!/bin/bash

# EDUKY-商品监控系统 - systemd 服务安装脚本
# 适用于Ubuntu/Debian/CentOS等Linux系统

set -e

# 配置变量
APP_NAME="eduky-monitor"
APP_USER="www-data"
APP_GROUP="www-data" 
INSTALL_DIR="/opt/eduky-monitor"
SERVICE_FILE="/etc/systemd/system/${APP_NAME}.service"
LOG_DIR="/var/log/eduky-monitor"
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 输出函数
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

# 检查是否以root权限运行
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要root权限运行"
        echo "请使用: sudo $0"
        exit 1
    fi
}

# 检查系统类型
check_system() {
    if ! command -v systemctl &> /dev/null; then
        log_error "此系统不支持systemd"
        exit 1
    fi
    
    log_info "检测到systemd系统"
}

# 安装Python和依赖
install_dependencies() {
    log_step "安装系统依赖..."
    
    if command -v apt-get &> /dev/null; then
        # Debian/Ubuntu
        apt-get update
        apt-get install -y python3 python3-pip python3-venv sqlite3 curl
    elif command -v yum &> /dev/null; then
        # CentOS/RHEL
        yum update -y
        yum install -y python3 python3-pip sqlite curl
    elif command -v dnf &> /dev/null; then
        # Fedora
        dnf update -y
        dnf install -y python3 python3-pip sqlite curl
    else
        log_warn "未识别的包管理器，请手动安装: python3, python3-pip, python3-venv, sqlite3"
    fi
}

# 创建用户和组
create_user() {
    log_step "创建应用用户..."
    
    if ! getent group $APP_GROUP > /dev/null 2>&1; then
        groupadd $APP_GROUP
        log_info "创建组: $APP_GROUP"
    fi
    
    if ! getent passwd $APP_USER > /dev/null 2>&1; then
        useradd -r -g $APP_GROUP -d $INSTALL_DIR -s /bin/bash $APP_USER
        log_info "创建用户: $APP_USER"
    else
        log_info "用户 $APP_USER 已存在"
    fi
}

# 创建目录结构
setup_directories() {
    log_step "创建目录结构..."
    
    # 创建安装目录
    mkdir -p $INSTALL_DIR
    mkdir -p $LOG_DIR
    
    # 设置权限
    chown -R $APP_USER:$APP_GROUP $INSTALL_DIR
    chown -R $APP_USER:$APP_GROUP $LOG_DIR
    chmod 755 $INSTALL_DIR
    chmod 755 $LOG_DIR
    
    log_info "目录创建完成: $INSTALL_DIR"
    log_info "日志目录: $LOG_DIR"
}

# 复制应用文件
copy_application() {
    log_step "复制应用文件..."
    
    # 复制所有应用文件
    cp -r "$CURRENT_DIR"/* $INSTALL_DIR/
    
    # 确保权限正确
    chown -R $APP_USER:$APP_GROUP $INSTALL_DIR
    chmod +x $INSTALL_DIR/app_production.py
    
    log_info "应用文件复制完成"
}

# 设置Python虚拟环境
setup_virtualenv() {
    log_step "设置Python虚拟环境..."
    
    cd $INSTALL_DIR
    
    # 创建虚拟环境
    sudo -u $APP_USER python3 -m venv venv
    
    # 激活虚拟环境并安装依赖
    sudo -u $APP_USER bash -c "
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
    "
    
    log_info "Python虚拟环境设置完成"
}

# 安装systemd服务
install_service() {
    log_step "安装systemd服务..."
    
    # 修改服务文件中的路径
    sed -i "s|ExecStart=.*|ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/app_production.py|g" "$CURRENT_DIR/eduky-monitor.service"
    
    # 复制服务文件
    cp "$CURRENT_DIR/eduky-monitor.service" $SERVICE_FILE
    
    # 重新加载systemd
    systemctl daemon-reload
    
    # 启用服务
    systemctl enable $APP_NAME
    
    log_info "systemd服务安装完成"
}

# 初始化数据库
init_database() {
    log_step "初始化数据库..."
    
    cd $INSTALL_DIR
    sudo -u $APP_USER bash -c "
        source venv/bin/activate
        python -c 'from app_v2_fixed import db; db.create_all(); print(\"数据库初始化完成\")'
    "
    
    log_info "数据库初始化完成"
}

# 启动服务
start_service() {
    log_step "启动服务..."
    
    systemctl start $APP_NAME
    sleep 3
    
    if systemctl is-active --quiet $APP_NAME; then
        log_info "服务启动成功！"
        systemctl status $APP_NAME --no-pager
    else
        log_error "服务启动失败"
        systemctl status $APP_NAME --no-pager
        exit 1
    fi
}

# 显示使用说明
show_usage() {
    echo ""
    log_info "=== EDUKY-商品监控系统安装完成 ==="
    echo ""
    echo "📁 安装目录: $INSTALL_DIR"
    echo "📋 日志目录: $LOG_DIR"
    echo "🔧 服务名称: $APP_NAME"
    echo ""
    echo "🎯 常用命令:"
    echo "  启动服务: sudo systemctl start $APP_NAME"
    echo "  停止服务: sudo systemctl stop $APP_NAME"
    echo "  重启服务: sudo systemctl restart $APP_NAME"
    echo "  查看状态: sudo systemctl status $APP_NAME"
    echo "  查看日志: sudo journalctl -u $APP_NAME -f"
    echo "  应用日志: sudo tail -f $LOG_DIR/app.log"
    echo ""
    echo "🌐 访问地址: http://localhost:5000"
    echo ""
    log_info "服务已设置为开机自启动"
}

# 主函数
main() {
    echo ""
    log_info "开始安装EDUKY-商品监控系统..."
    echo ""
    
    check_root
    check_system
    install_dependencies
    create_user
    setup_directories
    copy_application
    setup_virtualenv
    init_database
    install_service
    start_service
    show_usage
    
    echo ""
    log_info "安装完成！🎉"
}

# 如果直接运行此脚本
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi