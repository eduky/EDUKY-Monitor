# EDUKY 商品监控系统 (EDUKY-Monitor)

一个轻量级网页商品库存监控与 Telegram 通知系统，支持定时抓取商品页面，通过 CSS 选择器提取库存数字，自动识别库存增减并推送补货 / 销售通知到 Telegram 频道、群组或个人。

---
## 📋完全开源支持二开

## ✨下个版本规划:
- 👥支持多用户管理
- 🛒增加会员模块

<div align="center">

## 🎉 立即开始

### 选择您的系统，3分钟部署完成！

| 💻 **Windows** | 🐧 **Linux** | 
|----------------|---------------|
| `下载WIN版本 点击 启动监控系统.bat` | `sudo ./run.sh` |

### 🌟 如果这个项目对您有帮助，请给一个 ⭐ Star！

**🦄 现在就开始监控您的商品库存吧！让每一次补货都不再错过！**

</div>

### 🎯 适用场景


| 🏪 使用场景 | 👥 用户类型 | 📊 收益提升 |
|-------------|-------------|-------------|
| 🛒 **独角卡** | 个人用户 | 库存通知 |
| 🛒 **异次元卡** | 个人用户 | 库存通知 |
| 🎮 **游戏卡商城** | 游戏工作室、代理商 | 抢购成功率 +300% |
| 💳 **充值卡监控** | 电商卖家、批发商 | 库存周转率 +200% |
| 🎁 **礼品卡代购** | 代购商、个人用户 | 利润率 +150% |
| 🛒 **限量商品** | 潮玩收藏、数码产品 | 成功购买率 +400% |

## ✨ 功能特性

### 📊 智能监控系统
- ✅ **实时库存监控** - 自定义间隔检测（最快10秒）
- ✅ **多站点支持** - 支持任意网站通过CSS选择器监控
- ✅ **智能变化检测** - 补货/售罄/价格变动自动识别
- ✅ **历史数据分析** - 库存趋势图表和统计报告

### 🔔 多渠道通知
- 📢 **Telegram频道** - 公开商品信息推送
- 👥 **Telegram群组** - 团队内部通知分享
- 👤 **私人消息** - 个性化通知服务
- 🧪 **一键测试** - 快速验证通知渠道连通性

### 💻 Web管理界面  
- 🎨 **现代UI** - Bootstrap 5 + 自定义动画效果
- 📱 **响应式设计** - 完美适配各种屏幕尺寸
- 🔐 **安全认证** - 用户登录和密码保护
- 📋 **商品管理** - 添加/编辑/删除/批量操作

---
## ✨ 功能特性
- 多商品监控：支持添加任意数量的商品，独立启用/暂停
- CSS 选择器抽取：自定义选择器定位库存数字（提供测试接口）
- 自动检测库存变化：区分补货 (increase) 与销售 (decrease)
- Telegram 多渠道通知：频道 / 群组 / 个人 / 用户 ID（支持多个开启）
- 自定义通知模板：补货、销售消息内容可自定义变量
- 库存变化历史：记录每次变化（仅在变化时写入，减少冗余）
- 通知日志：记录发送状态、失败原因
- 手动/自动检测：定时任务 + 单次手动触发
- 导入 / 导出：支持 JSON 备份与恢复商品 + 配置
- 首次登录强制改密：默认账号 admin/admin123 登录后需修改密码
- NTP 网络时间：优先使用互联网时间（多 NTP 源容错）
- 监控间隔可配置：支持以秒为单位（10s~3600s）
- 购买链接按钮：Telegram 通知支持内联 “前往购买” 按钮

---
## 🗂 项目结构
```
main.py                  # 主程序 (Flask + 任务调度 + 业务逻辑)
requirements.txt         # Python 依赖
run.sh                   # Linux 一键部署/运行脚本
web/
  static/                # 前端静态资源
  templates/             # Jinja2 模板页面
  instance/
    inventory_monitor_v2.db  # SQLite 数据库 (自动生成)
```

---
## 🚀 快速开始
### 1. 克隆 / 下载
```bash
# 直接克隆 
git clone https://github.com/eduky/EDUKY-Monitor.git
cd EDUKY-Monitor
```

### 2. Python 环境要求
- Python 3.9+ (建议)
- 已安装 sqlite3（大多数系统自带）

### 3. 安装依赖 (通用方式)
```bash
pip install -r requirements.txt
```

### 4. 启动服务
```bash
python main.py
```
访问：http://localhost:5000

### 5. 默认账号
```
用户名: admin
密码: admin123  (首次登录会强制修改)
```

---
## 🖥 Linux 一键脚本使用 (run.sh)
脚本支持：依赖安装 / 开发模式 / 生产后台 / 日志 / 重启 / systemd 模板。

```bash
# 授权
chmod +x run.sh

# 安装依赖 (系统 + Python)
./run.sh install

# 前台开发模式 (Ctrl+C 退出)
./run.sh dev

# 后台生产模式启动
./run.sh prod start

# 查看状态
./run.sh prod status

# 查看后台实时日志
./run.sh logs

# 停止后台
./run.sh prod stop
```

可执行 `./run.sh` 进入交互菜单。

---
## 🪟 Windows 快速启动
1. [下载win版本](https://github.com/eduky/EDUKY-Monitor/releases)
2. 解压后双击 `启动监控系统.bat` 文件
3. 浏览器访问：http://127.0.0.1:5000
4. 默认账号：admin / admin123 (首次登录会强制修改)

---
## 🪟 Windows 手动启动说明
1. 安装 Python 3.9+，勾选 "Add to PATH"
2. 进入项目目录：
```powershell
cd C:\path\to\faka-monitor
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```
3. 浏览器访问：http://127.0.0.1:5000

如需后台运行可使用：
```powershell
Start-Process -NoNewWindow -FilePath python -ArgumentList 'main.py'
```

---
## ⚙️ 系统配置步骤 (首次登录后)
1. 登录后台 → 进入“设置”页
2. 填写 Telegram Bot Token
3. 按需求勾选启用的通知渠道：频道 / 群组 / 用户 ID / 个人
4. 填写对应 ID（见下方获取方式）
5. 设置检测间隔（秒）
6. 可自定义通知模板（支持变量）
7. 保存并在首页确认“系统状态”展示正常

---
## 🤖 Telegram 配置说明
### 创建机器人 (Bot)
1. 在 Telegram 搜索 @BotFather
2. `/start` → `/newbot` → 依提示创建
3. 复制生成的 `Bot Token` 填入设置页

### 获取频道 / 群组 / 用户 ID
| 类型 | 获取方式 |
|------|----------|
| 用户私聊 | 与 @userinfobot 对话获取 ID |
| 群组 | 把机器人拉进群，给群发送消息，用 https://api.telegram.org/bot<TOKEN>/getUpdates 查看 `chat.id` |
| 频道 | 机器人设为频道管理员，然后发一条消息并用 getUpdates 获取 `chat.id` (频道一般为负数或 `-100...`) |

示例：
```
https://api.telegram.org/bot123456:ABCDEF/getUpdates
```

### 测试通知
设置保存后，在“设置”页面或调用接口：
```
POST /api/test_notification
Body: { "type": "channel" | "group" | "user" } (可选)
```

---
## 🛒 添加商品与 CSS 选择器
1. 进入“商品管理”→“添加商品”
2. 填写：
   - 商品名称：可自动根据 URL 获取网页标题
   - 监控 URL：商品详情页
   - CSS 选择器：指向库存数字的元素
   - 购买链接：为空则默认使用监控 URL
3. 可使用“测试 CSS 选择器”按钮测试是否能解析到库存数字

### 编写 CSS 选择器技巧
| 目标 | 示例 HTML | 选择器 | 说明 |
|------|-----------|--------|------|
| 文本在 span | `<span id="stock">库存：23 件</span>` | `#stock` | 直接 ID |
| 有类名 | `<div class="number stock-count">23</div>` | `.stock-count` | 使用类 |
| 层级定位 | `<div class="info"><b>库存</b><span>15</span></div>` | `.info span` | 取内部 span |
| data 属性 | `<div data-stock="52">` | `div[data-stock]` | 先取元素再用 JS 方案（当前程序仅读取文本） |

系统会从选择到的元素中提取第一个出现的数字 (正则 \d+) 作为库存。

---
## 🧪 手动触发与接口说明 (后端已内置)
| 功能 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 检查所有商品 | POST | `/api/manual_check` | 后台线程执行 |
| 测试单个商品 | POST | `/api/test_monitor/<product_id>` | 返回当前库存 |
| 获取系统状态 | GET | `/api/system_status` | 包含时间/监控/配置统计 |
| 最近通知 | GET | `/api/recent_notifications` | 最近 50 条 |
| 库存历史 | GET | `/api/stock_history/<id>` | 最近 30 条 |
| 导出数据 | GET | `/api/export_data` | JSON 包含商品+配置+部分历史 |
| 导入数据 | POST | `/api/import_data` | Form-Data 上传 `backup_file` |
| 清除日志 | POST | `/api/clear_logs` | 清空库存历史+通知日志 |
| 测试通知 | POST | `/api/test_notification` | 可选 type 参数 |

(所有接口需先登录，有会话 Cookie)

---
## 🔄 数据导入 / 导出
### 导出
进入“设置”或调用：`GET /api/export_data`

### 导入
1. 后台点击导入上传 JSON
2. 或接口：`POST /api/import_data` (Form-Data: backup_file)

导入时：
- 已存在同名商品跳过
- 配置将覆盖现有配置

---
## 🛡 安全建议 (生产环境)
- 更换 `app.config['SECRET_KEY']` 为随机强值
- 使用反向代理 (Nginx) + HTTPS
- 限制访问来源 IP (防止外网滥用)
- 定期备份 `web/instance/inventory_monitor_v2.db`
- 加固默认管理员：改复杂密码 & 另外创建新管理员 (可扩展逻辑)
- 如果量大/频繁目标站点：合理设置检测间隔，避免被封

---
## 🧩 可用模板变量 (通知模板)
| 变量 | 含义 |
|------|------|
| `{product_name}` | 商品名称 |
| `{current_stock}` | 当前库存 |
| `{previous_stock}` | 上次库存 |
| `{stock_difference}` | 变化数量 (正=补货 / 负=销售) |
| `{check_time}` | 检测时间 |
| `{product_url}` | 监控页面 URL |
| `{buy_url}` | 购买按钮 URL |

示例（补货模板）：
```
🎉 补货通知\n📦 商品名称: {product_name}\n📈 补货数量: {stock_difference}\n📊 当前库存: {current_stock}\n🕐 时间: {check_time}\n🛒 {buy_url}
```

---
## 🐞 常见问题 FAQ
| 问题 | 说明 / 解决 |
|------|--------------|
| CSS 选择器测试失败 | 检查是否需要登录 / 页面是否异步加载 (当前不执行 JS) |
| Telegram 没消息 | 确认 Bot 已加入频道/群并有权限；检查 getUpdates 返回是否有 chat.id |
| 库存一直是 0 | 选择器未匹配或文本不含数字；用“测试”功能查看提取文本 |
| 定时任务不运行 | 查看日志；确保未被多进程方式重复启动；检查 APScheduler 是否报错 |
| Windows 中文路径问题 | 建议路径不含空格和中文；或使用 UTF-8 终端 |
| 数据库锁异常 | 任务高频 + 访问量大时可适当增大间隔或迁移到 MySQL (需改 SQLAlchemy URI) |

---
## 🧭 后续可扩展建议
- 支持 JS 渲染页面 (Playwright) 以抓取动态库存
- 增加 WebSocket 实时推送前端刷新
- 多用户/角色与操作审计
- 商品分组与批量导入
- Prometheus 指标导出 + Grafana 展示
- Docker 镜像封装

---
## 📄 开源协议

本项目采用 **MIT License** 开源协议，支持个人和商业用途。

---
## 📞 技术支持
- 🐛 **问题反馈**: [GitHub Issues](https://github.com/eduky/EDUKY-Monitor/issues)
- 💬 **社区讨论**: [Telegram群组](https://t.me/eduKaiYuan)
- 📧 **商业合作**: 

遇到问题可：
1. 查看浏览器控制台 / 网络请求
2. 查看后台日志 (`run.sh logs`)
3. 打开 `/debug/config` 检查通知配置
4. 增加临时日志排查

祝使用愉快！🚀
