# FAKA Monitor

一个用于监控和管理发卡系统的Web应用程序。

## 功能特性

- 🚀 **产品监控** - 实时监控产品库存状态
- 📊 **数据统计** - 全面的销售和库存数据分析
- 🔐 **用户管理** - 安全的用户认证和权限管理
- 📱 **响应式设计** - 支持多种设备访问
- 🐳 **容器化支持** - 提供Docker部署方案
- 🖥️ **多平台支持** - 支持Windows、Linux多种部署方式

## 快速开始

### 环境要求

- Python 3.8+
- Flask 2.0+
- SQLite3

### 安装步骤

1. 克隆项目
```bash
git clone https://github.com/your-username/faka-monitor.git
cd faka-monitor
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 运行应用
```bash
python run_app.py
```

4. 访问应用
打开浏览器访问 `http://localhost:5000`

## 部署方式

### Docker部署
```bash
cd scripts/docker
docker-compose up -d
```

### Windows服务
```bash
scripts\windows\deploy_windows_service.bat
```

### Linux系统服务
```bash
cd scripts/linux
chmod +x install_systemd.sh
sudo ./install_systemd.sh
```

## 项目结构

```
faka-monitor/
├── app_v2_fixed.py          # 主应用程序
├── run_app.py               # 启动脚本
├── requirements.txt         # Python依赖
├── migrate_database.py      # 数据库迁移
├── web/                     # Web界面
│   ├── static/             # 静态文件
│   ├── templates/          # HTML模板
│   └── instance/           # 数据库文件
└── scripts/                # 部署脚本
    ├── docker/             # Docker配置
    ├── linux/              # Linux脚本
    └── windows/            # Windows脚本
```

## 配置说明

默认配置文件位于应用程序内部，如需自定义配置，请修改相应的配置参数。

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

此项目采用MIT许可证。