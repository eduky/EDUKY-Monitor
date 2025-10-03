# EDUKY-Monitor

[![CI/CD](https://github.com/eduky/EDUKY-Monitor/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/eduky/EDUKY-Monitor/actions/workflows/ci-cd.yml)
[![Docker](https://github.com/eduky/EDUKY-Monitor/actions/workflows/docker.yml/badge.svg)](https://github.com/eduky/EDUKY-Monitor/actions/workflows/docker.yml)
[![Code Quality](https://github.com/eduky/EDUKY-Monitor/actions/workflows/code-quality.yml/badge.svg)](https://github.com/eduky/EDUKY-Monitor/actions/workflows/code-quality.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

一个用于监控库存的Web应用程序。

## 功能特性

- 产品库存管理
- 实时监控界面
- 用户认证系统
- 数据库迁移功能
- 系统服务部署

## 安装和运行

### 环境要求

- Python 3.7+
- Flask
- SQLite

### 快速开始

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 运行应用：
```bash
python run_app.py
```

3. 访问 http://localhost:5000

## 部署

### Windows服务部署
运行 `deploy_service.bat` 将应用部署为Windows服务。

### Linux服务部署
使用 `scripts/linux/` 目录下的脚本进行systemd服务部署。

### Docker部署
使用 `scripts/docker/` 目录下的Docker配置文件。

## 项目结构

```
├── app_v2_fixed.py      # 主应用文件
├── run_app.py           # 启动脚本
├── requirements.txt     # 依赖列表
├── migrate_database.py  # 数据库迁移
├── web/                 # Web资源
│   ├── static/         # 静态文件
│   ├── templates/      # 模板文件
│   └── instance/       # 实例配置
└── scripts/            # 部署脚本
    ├── windows/        # Windows脚本
    ├── linux/          # Linux脚本
    └── docker/         # Docker配置
```

## 贡献

欢迎提交Issues和Pull Requests。

## 许可证

MIT License