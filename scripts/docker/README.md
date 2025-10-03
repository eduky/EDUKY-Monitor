# 🐳 Docker 部署指南

## 快速启动

### 方法1：使用 docker-compose（推荐）
```bash
# 1. 下载配置文件
curl -O https://raw.githubusercontent.com/eduky/faka-monitor/main/deployment/docker/docker-compose.yml

# 2. 启动服务
docker-compose up -d

# 3. 查看状态
docker-compose ps

# 4. 查看日志
docker-compose logs -f
```

### 方法2：直接运行Docker镜像
```bash
# 快速启动（使用默认配置）
docker run -d \
  --name eduky-monitor \
  -p 5000:5000 \
  -v $(pwd)/data:/app/instance \
  yourdockerhub/eduky-monitor

# 带环境变量启动
docker run -d \
  --name eduky-monitor \
  -p 5000:5000 \
  -v $(pwd)/data:/app/instance \
  -e TELEGRAM_BOT_TOKEN="your_bot_token" \
  -e TELEGRAM_CHANNEL_ID="your_channel_id" \
  yourdockerhub/eduky-monitor
```

### 方法3：自建镜像
```bash
# 1. 克隆项目
git clone https://github.com/eduky/faka-monitor.git
cd faka-monitor

# 2. 构建镜像
docker build -f deployment/docker/Dockerfile -t eduky-monitor .

# 3. 运行容器
docker run -d --name eduky-monitor -p 5000:5000 eduky-monitor
```

## 环境变量配置

| 变量名 | 作用 | 必填 | 默认值 | 示例 |
|--------|------|------|--------|------|
| `TELEGRAM_BOT_TOKEN` | Telegram机器人Token | 否 | 无 | `123456:ABC-DEF...` |
| `TELEGRAM_CHANNEL_ID` | 频道ID | 否 | 无 | `-1001234567890` |
| `TELEGRAM_GROUP_ID` | 群组ID | 否 | 无 | `-1001234567890` |
| `TELEGRAM_PRIVATE_ID` | 私聊ID | 否 | 无 | `123456789` |
| `CHECK_INTERVAL` | 检查间隔(分钟) | 否 | `2` | `5` |
| `DJK_HOST` | 监听地址 | 否 | `0.0.0.0` | `127.0.0.1` |
| `DJK_PORT` | 监听端口 | 否 | `5000` | `8080` |

## 数据持久化

建议挂载数据目录以保持数据：
```bash
docker run -d \
  --name eduky-monitor \
  -p 5000:5000 \
  -v /path/to/data:/app/instance \
  yourdockerhub/eduky-monitor
```

## 管理命令

```bash
# 启动容器
docker start eduky-monitor

# 停止容器
docker stop eduky-monitor

# 重启容器
docker restart eduky-monitor

# 查看日志
docker logs -f eduky-monitor

# 进入容器
docker exec -it eduky-monitor bash

# 删除容器
docker rm -f eduky-monitor
```

## 网络访问

部署成功后，访问以下地址：
- 本地访问：http://localhost:5000
- 局域网访问：http://your-server-ip:5000

默认登录账号：
- 用户名：`admin`
- 密码：`admin123`

⚠️ **安全提醒**：首次登录后请及时修改密码！