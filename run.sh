#!/usr/bin/env bash
# =============================================================
# EDUKY-Monitor 部署与运行管理脚本 (Linux)
# 功能:
#   1) 环境依赖检测
#   2) 一键安装系统依赖 + Python依赖
#   3) 启动开发模式 (前台, 可见日志)
#   4) 启动生产模式 (后台, nohup + PID 管理)
#   5) 查看运行状态
#   6) 查看日志 (tail 实时)
#   7) 停止生产模式
#   8) 重启生产模式
# 扩展:
#   - 支持虚拟环境 (.venv) 自动创建与使用 (默认启用)
#   - 支持参数直接调用, 也可进入交互菜单
#   - 可生成 systemd service (预留函数, 默认不执行)
# =============================================================

set -euo pipefail
export LC_ALL=C

APP_NAME="eduky-monitor"
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
PY_MAIN="${BASE_DIR}/main.py"
REQUIRE_FILE="${BASE_DIR}/requirements.txt"
LOG_DIR="${BASE_DIR}/logs"
RUN_DIR="${BASE_DIR}/run"
PID_FILE="${RUN_DIR}/${APP_NAME}.pid"
VENV_DIR="${BASE_DIR}/.venv"
PYTHON_BIN=""
USE_VENV="1"          # 如不想使用虚拟环境，可 export USE_VENV=0
COLOR_DISABLE="${NO_COLOR:-0}"  # export NO_COLOR=1 可禁用彩色

mkdir -p "${LOG_DIR}" "${RUN_DIR}" || true

# ------------------------- 彩色输出 -------------------------
if [[ "${COLOR_DISABLE}" != "1" ]]; then
	C_RESET='\033[0m'; C_RED='\033[31m'; C_GREEN='\033[32m'; C_YELLOW='\033[33m'; C_BLUE='\033[34m'; C_CYAN='\033[36m'; C_MAG='\033[35m'
else
	C_RESET=''; C_RED=''; C_GREEN=''; C_YELLOW=''; C_BLUE=''; C_CYAN=''; C_MAG=''
fi
TICK="${C_GREEN}✓${C_RESET}"
CROSS="${C_RED}✗${C_RESET}"
INFO()  { echo -e "${C_CYAN}[INFO]${C_RESET} $*"; }
WARN()  { echo -e "${C_YELLOW}[WARN]${C_RESET} $*"; }
ERR()   { echo -e "${C_RED}[ERROR]${C_RESET} $*" >&2; }
OK()    { echo -e "${C_GREEN}[OK]${C_RESET} $*"; }

# ------------------------- 工具函数 -------------------------
command_exists() { command -v "$1" >/dev/null 2>&1; }

detect_python() {
	if command_exists python3; then PYTHON_BIN="python3"; elif command_exists python; then PYTHON_BIN="python"; else PYTHON_BIN=""; fi
}

ensure_python() {
	detect_python
	if [[ -z "${PYTHON_BIN}" ]]; then
		ERR "未检测到 python3，请先执行: $0 install"
		exit 1
	fi
}

ensure_venv() {
	ensure_python
	if [[ "${USE_VENV}" != "1" ]]; then
		INFO "未启用虚拟环境 (USE_VENV=0)"
		return 0
	fi
	if [[ ! -d "${VENV_DIR}" ]]; then
		INFO "创建虚拟环境: ${VENV_DIR}"
		"${PYTHON_BIN}" -m venv "${VENV_DIR}" || { ERR "虚拟环境创建失败"; exit 1; }
	fi
	# shellcheck disable=SC1091
	source "${VENV_DIR}/bin/activate"
	PYTHON_BIN="python"
	OK "已激活虚拟环境 (${VENV_DIR})"
}

current_os_pkg() {
	# 输出包管理器: apt / dnf / yum / unknown
	if [[ -f /etc/os-release ]]; then
		. /etc/os-release
		ID_LIKE_ALL="${ID_LIKE:-} ${ID:-}" | tr ' ' '\n' >/dev/null 2>&1 || true
		if echo "${ID_LIKE} ${ID}" | grep -qi 'debian'; then echo apt; return; fi
		if echo "${ID_LIKE} ${ID}" | grep -qi 'ubuntu'; then echo apt; return; fi
		if echo "${ID_LIKE} ${ID}" | grep -Eqi 'rhel|centos|alma|rocky|fedora'; then
			if command_exists dnf; then echo dnf; else echo yum; fi
			return
		fi
	fi
	if command_exists apt-get; then echo apt; return; fi
	if command_exists dnf; then echo dnf; return; fi
	if command_exists yum; then echo yum; return; fi
	echo unknown
}

print_banner() {
	cat <<EOF
${C_MAG}=============================================================${C_RESET}
	EDUKY Monitor 管理脚本  |  目录: ${BASE_DIR}
	日志目录: ${LOG_DIR}
	PID 文件: ${PID_FILE}
${C_MAG}=============================================================${C_RESET}
EOF
}

# ------------------------- 1. 依赖检测 -------------------------
check_env() {
	print_banner
	INFO "开始检测系统与Python依赖..."
	local -a BIN_LIST=(python3 python pip3 pip sqlite3 curl wget git)
	local -a PY_MODS=(Flask flask_sqlalchemy requests apscheduler bs4 telegram lxml werkzeug pytz ntplib)

	echo -e "\n${C_BLUE}系统命令检测:${C_RESET}"
	for b in "${BIN_LIST[@]}"; do
		if command_exists "$b"; then printf " %-12s %b\n" "$b" "$TICK"; else printf " %-12s %b\n" "$b" "$CROSS"; fi
	done

	detect_python
	if [[ -z "${PYTHON_BIN}" ]]; then
		WARN "未找到 Python，后续请执行安装 install。"
	fi

	echo -e "\n${C_BLUE}Python 模块检测:${C_RESET}"; local py="${PYTHON_BIN:-python3}"; local missing=0
	for m in "${PY_MODS[@]}"; do
		if "$py" -c "import $m" >/dev/null 2>&1; then printf " %-20s %b\n" "$m" "$TICK"; else printf " %-20s %b\n" "$m" "$CROSS"; missing=$((missing+1)); fi
	done

	echo -e "\n${C_BLUE}requirements.txt 校验:${C_RESET}";
	if [[ -f "${REQUIRE_FILE}" && -n "${PYTHON_BIN}" ]]; then
		local need=$(grep -E '^[A-Za-z0-9_-]+' "${REQUIRE_FILE}" | cut -d'=' -f1 | cut -d'<' -f1 | cut -d'>' -f1 || true)
		for p in $need; do
			if "${PYTHON_BIN}" -m pip show "$p" >/dev/null 2>&1; then printf " %-25s %b\n" "$p" "$TICK"; else printf " %-25s %b\n" "$p" "$CROSS"; fi
		done
	else
		WARN "requirements.txt 不存在或未找到Python"
	fi

	echo -e "\n${C_BLUE}SQLite 数据文件检测:${C_RESET}";
	local db_file="${BASE_DIR}/web/instance/inventory_monitor_v2.db"
	if [[ -f "$db_file" ]]; then printf " DB 文件 %-40s %b\n" "$(basename "$db_file")" "$TICK"; else printf " DB 文件 %-40s %b\n" "$(basename "$db_file")" "$CROSS"; fi

	echo -e "\n${C_BLUE}虚拟环境:${C_RESET}";
	if [[ -d "${VENV_DIR}" ]]; then echo -e " 已存在: ${VENV_DIR} ${TICK}"; else echo -e " 未创建: ${VENV_DIR} ${CROSS}"; fi

	echo
	if [[ $missing -gt 0 ]]; then WARN "存在 $missing 个缺失 Python 模块，可执行: $0 install"; else OK "Python 模块齐全"; fi
	OK "依赖检测完成"
}

# ------------------------- 2. 安装依赖 -------------------------
install_env() {
	print_banner
	local pkg_mgr="$(current_os_pkg)"
	INFO "检测到包管理器: ${pkg_mgr}"
	if [[ "${pkg_mgr}" == "unknown" ]]; then
		ERR "无法识别包管理器，请手动安装 python3 / pip / sqlite3 等依赖"
	else
		case "${pkg_mgr}" in
			apt)
				sudo apt-get update -y
				sudo apt-get install -y python3 python3-pip python3-venv sqlite3 curl wget git
				;;
			dnf)
				sudo dnf install -y python3 python3-pip python3-virtualenv sqlite sqlite-devel curl wget git
				;;
			yum)
				sudo yum install -y python3 python3-pip python3-virtualenv sqlite sqlite-devel curl wget git
				;;
		esac
	fi

	ensure_venv
	INFO "升级 pip..."
	"${PYTHON_BIN}" -m pip install --upgrade pip setuptools wheel
	if [[ -f "${REQUIRE_FILE}" ]]; then
		INFO "安装 Python 依赖 (requirements.txt)..."
		"${PYTHON_BIN}" -m pip install -r "${REQUIRE_FILE}"
	else
		WARN "未找到 requirements.txt"
	fi
	OK "安装完成"
}

# ------------------------- 生产后台进程管理 -------------------------
is_running() {
	if [[ -f "${PID_FILE}" ]]; then
		local pid; pid=$(cat "${PID_FILE}" 2>/dev/null || true)
		if [[ -n "$pid" && -d "/proc/$pid" ]]; then return 0; fi
	fi
	return 1
}

start_prod() {
	print_banner
	if is_running; then
		WARN "生产模式已运行 (PID: $(cat "${PID_FILE}"))"
		return 0
	fi
	ensure_venv
	ensure_python
	INFO "启动生产模式 (后台)..."
	local ts; ts=$(date +%Y%m%d_%H%M%S)
	local out_log="${LOG_DIR}/app_${ts}.log"
	ln -sf "${out_log}" "${LOG_DIR}/app.log"
	(cd "${BASE_DIR}" && nohup "${PYTHON_BIN}" "${PY_MAIN}" >>"${out_log}" 2>&1 & echo $! > "${PID_FILE}")
	sleep 1
	if is_running; then OK "启动成功 PID=$(cat "${PID_FILE}") 日志: ${LOG_DIR}/app.log"; else ERR "启动失败，请查看日志"; fi
}

start_dev() {
	print_banner
	ensure_venv
	ensure_python
	INFO "启动开发模式 (前台，Ctrl+C 退出)..."
	export PYTHONUNBUFFERED=1
	echo -e "${C_YELLOW}--- 实时输出开始 ---${C_RESET}"
	"${PYTHON_BIN}" "${PY_MAIN}"
}

stop_prod() {
	print_banner
	if ! is_running; then WARN "未发现运行中的生产进程"; rm -f "${PID_FILE}"; return 0; fi
	local pid; pid=$(cat "${PID_FILE}")
	INFO "停止进程 PID=${pid} ..."
	kill "$pid" 2>/dev/null || true
	for i in {1..20}; do
		if ! kill -0 "$pid" 2>/dev/null; then break; fi
		sleep 0.3
	done
	if kill -0 "$pid" 2>/dev/null; then
		WARN "正常停止失败，尝试强制 kill -9"
		kill -9 "$pid" 2>/dev/null || true
	fi
	rm -f "${PID_FILE}" || true
	OK "已停止"
}

status_prod() {
	print_banner
	if is_running; then
		local pid; pid=$(cat "${PID_FILE}")
		OK "运行中 PID=${pid}"
		ps -o pid,ppid,cmd -p "$pid" || true
	else
		WARN "未运行"
	fi
}

logs_tail() {
	print_banner
	local log_file="${LOG_DIR}/app.log"
	if [[ ! -f "$log_file" ]]; then ERR "日志文件不存在: $log_file"; exit 1; fi
	INFO "实时查看日志 (Ctrl+C 退出)"
	tail -n 50 -f "$log_file"
}

restart_prod() {
	print_banner
	stop_prod || true
	start_prod
}

# ------------------------- 预留: 生成 systemd -------------------------
generate_systemd_unit() {
	local unit="/etc/systemd/system/${APP_NAME}.service"
	cat <<EOF | sudo tee "$unit" >/dev/null
[Unit]
Description=EDUKY Monitor Service
After=network.target

[Service]
Type=simple
WorkingDirectory=${BASE_DIR}
ExecStart=${VENV_DIR}/bin/python ${PY_MAIN}
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1
StandardOutput=append:${LOG_DIR}/systemd.log
StandardError=append:${LOG_DIR}/systemd.err

[Install]
WantedBy=multi-user.target
EOF
	OK "systemd 单元已生成: $unit (需要: sudo systemctl enable --now ${APP_NAME})"
}

# ------------------------- 交互菜单 -------------------------
menu() {
	while true; do
		print_banner
		cat <<M
	1) 检测环境依赖
	2) 安装依赖 (系统 + Python)
	3) 启动开发模式 (前台)
	4) 启动生产模式 (后台)
	5) 查看状态
	6) 查看日志 (tail)
	7) 停止生产模式
	8) 重启生产模式
	9) 生成 systemd (可选)
	0) 退出
M
		read -rp "请选择操作: " opt
		case "$opt" in
			1) check_env; read -rp "按回车继续..." _ ;;
			2) install_env; read -rp "按回车继续..." _ ;;
			3) start_dev ;;
			4) start_prod; read -rp "按回车继续..." _ ;;
			5) status_prod; read -rp "按回车继续..." _ ;;
			6) logs_tail ;;
			7) stop_prod; read -rp "按回车继续..." _ ;;
			8) restart_prod; read -rp "按回车继续..." _ ;;
			9) generate_systemd_unit; read -rp "按回车继续..." _ ;;
			0) exit 0 ;;
			*) echo "无效选择"; sleep 1 ;;
		esac
	done
}

# ------------------------- 参数解析 -------------------------
usage() {
	cat <<EOF
用法: $0 <命令>

命令列表:
	check                 检测依赖
	install               安装系统与Python依赖
	dev                   启动开发模式 (前台)
	prod start            启动生产模式 (后台)
	prod stop             停止生产模式
	prod restart          重启生产模式
	prod status           查看生产模式状态
	prod logs             查看后台日志 (tail)
	logs                  查看后台日志 (tail)
	systemd               生成 systemd 单元文件 (不自动启用)
	menu                  进入交互菜单 (默认)
	help                  显示帮助

可用环境变量:
	USE_VENV=1|0          是否启用虚拟环境 (默认1)
	NO_COLOR=1            禁用彩色输出

示例:
	$0 install
	$0 prod start
	USE_VENV=0 $0 dev
EOF
}

main() {
	local cmd="${1:-menu}"; shift || true
	case "$cmd" in
		check)      check_env ;;
		install)    install_env ;;
		dev)        start_dev ;;
		prod)
			local sub="${1:-}"; shift || true
			case "$sub" in
				start)   start_prod ;;
				stop)    stop_prod ;;
				restart) restart_prod ;;
				status)  status_prod ;;
				logs)    logs_tail ;;
				*) usage; exit 1 ;;
			esac
			;;
		logs)       logs_tail ;;
		systemd)    generate_systemd_unit ;;
		menu)       menu ;;
		help|-h|--help) usage ;;
		*) usage; exit 1 ;;
	esac
}

main "$@"

# ------------------------- 结束 & 后续优化建议 -------------------------
# 可进一步扩展:
#   - 集成 gunicorn / uvicorn (需改 main.py 结构使其在被 import 时完成初始化)
#   - 增加健康检查 HTTP 端点查询 (curl /status)
#   - 增加备份/恢复 DB 的命令 (sqlite3 dump)
#   - 增加日志轮转 (logrotate 配置或内置简单轮转)
#   - 增加 --json 输出模式便于外部编排工具调用
# =============================================================

