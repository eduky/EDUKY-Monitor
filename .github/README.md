# GitHub Actions 构建配置说明

本项目包含完整的CI/CD流水线，支持自动构建、测试、安全扫描和部署。

## 🚀 工作流概览

### 1. CI/CD Pipeline (`.github/workflows/ci-cd.yml`)
**触发条件：** 推送到 `main`/`develop` 分支或创建PR

**功能：**
- ✅ 多Python版本测试 (3.8, 3.9, 3.10, 3.11)
- ✅ 代码质量检查 (flake8)
- ✅ 应用启动测试
- ✅ 数据库迁移测试
- 🔒 安全扫描 (safety, bandit)
- 🐳 Docker镜像构建和推送

### 2. Docker Build (`.github/workflows/docker.yml`)
**触发条件：** 推送到 `main` 分支或创建标签

**功能：**
- 🐳 多架构Docker镜像构建 (amd64, arm64)
- 📦 推送到GitHub Container Registry
- 🏷️ 自动标签管理

### 3. Release (`.github/workflows/release.yml`)
**触发条件：** 创建版本标签 (如 `v1.0.0`)

**功能：**
- 📋 自动生成更改日志
- 🎁 创建GitHub Release
- 📦 构建可执行文件 (Linux/Windows)

### 4. Code Quality (`.github/workflows/code-quality.yml`)
**触发条件：** 推送或PR

**功能：**
- 🎨 代码格式检查 (Black, isort)
- 📊 静态分析 (pylint, mypy)
- 🔍 依赖漏洞扫描

## 📋 使用指南

### 启用GitHub Actions
1. 确保你的仓库中有 `.github/workflows/` 目录
2. 推送代码到GitHub
3. Actions会自动运行

### 查看构建状态
访问仓库的 **Actions** 标签页查看所有工作流运行状态。

### Docker镜像
构建成功后，Docker镜像会推送到：
```
ghcr.io/eduky/eduky-monitor:latest
ghcr.io/eduky/eduky-monitor:main
ghcr.io/eduky/eduky-monitor:sha-<commit-hash>
```

### 使用Docker镜像
```bash
# 拉取最新镜像
docker pull ghcr.io/eduky/eduky-monitor:latest

# 运行容器
docker run -d -p 5000:5000 ghcr.io/eduky/eduky-monitor:latest

# 或使用docker-compose
cd scripts/docker
docker-compose -f docker-compose.prod.yml up -d
```

### 创建发布版本
```bash
# 创建并推送标签
git tag v1.0.0
git push origin v1.0.0
```

这会触发发布工作流，自动创建GitHub Release并构建可执行文件。

## 🔧 本地开发

### 运行测试
```bash
# 安装开发依赖
pip install pytest pytest-cov flake8 black isort pylint mypy safety bandit

# 运行所有检查
flake8 .
black --check .
isort --check-only .
pylint *.py
mypy --ignore-missing-imports *.py
safety check
bandit -r .
```

### 本地Docker构建
```bash
cd scripts/docker
docker build -t eduky-monitor:local -f Dockerfile ../..
```

## 📊 状态徽章

可以在README中添加这些徽章来显示构建状态：

```markdown
[![CI/CD](https://github.com/eduky/EDUKY-Monitor/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/eduky/EDUKY-Monitor/actions/workflows/ci-cd.yml)
[![Docker](https://github.com/eduky/EDUKY-Monitor/actions/workflows/docker.yml/badge.svg)](https://github.com/eduky/EDUKY-Monitor/actions/workflows/docker.yml)
[![Code Quality](https://github.com/eduky/EDUKY-Monitor/actions/workflows/code-quality.yml/badge.svg)](https://github.com/eduky/EDUKY-Monitor/actions/workflows/code-quality.yml)
```

## 🛠️ 配置选项

### 环境变量
可以在仓库设置中添加以下Secrets：
- `DOCKER_USERNAME` - Docker Hub用户名 (可选)
- `DOCKER_PASSWORD` - Docker Hub密码 (可选)

### 自定义构建
修改 `.github/workflows/` 中的YAML文件来自定义构建流程。