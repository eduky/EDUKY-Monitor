# 🚀 EDUKY-Monitor 构建和发布指南

## 自动构建发布 (推荐)

### 1. 创建新版本标签
```bash
# 创建并推送版本标签
git tag v1.0.0
git push origin v1.0.0
```

### 2. GitHub Actions 自动构建
- 推送标签后，GitHub Actions 会自动触发构建
- 构建完成后会自动创建 Release
- 包含 Windows 和 Linux 的可执行文件

### 3. 手动触发构建
在 GitHub 仓库的 Actions 页面，可以手动运行 "Build and Release" 工作流

## 本地构建测试

### Windows 本地构建
```batch
# 运行构建脚本
build-windows.bat
```

### Linux 本地构建
```bash
# 给脚本执行权限
chmod +x build-linux.sh
# 运行构建脚本
./build-linux.sh
```

## 发布流程

1. **开发完成** → 测试功能
2. **提交代码** → `git add . && git commit -m "更新说明"`
3. **推送代码** → `git push origin main`
4. **创建标签** → `git tag v1.0.1 && git push origin v1.0.1`
5. **等待构建** → GitHub Actions 自动构建
6. **检查发布** → GitHub Releases 页面确认

## 构建输出

### Windows 版本
- `eduky-monitor-windows.exe` - 主程序
- `start-eduky-monitor.bat` - 启动脚本
- `README.txt` - 使用说明
- `logs/` - 日志目录

### Linux 版本
- `eduky-monitor-linux` - 主程序
- `start-eduky-monitor.sh` - 启动脚本
- `README.md` - 使用说明
- `logs/` - 日志目录

## 用户使用指南

### Windows 用户
1. 下载 `eduky-monitor-windows.tar.gz`
2. 解压文件
3. 双击 `start-eduky-monitor.bat`
4. 浏览器访问 http://localhost:5000

### Linux 用户
1. 下载 `eduky-monitor-linux.tar.gz`
2. 解压文件: `tar -xzf eduky-monitor-linux.tar.gz`
3. 运行启动脚本: `./start-eduky-monitor.sh`
4. 浏览器访问 http://localhost:5000

## 注意事项

- 默认用户名: `admin`
- 默认密码: `admin123`
- 首次运行会自动创建数据库
- 建议首次登录后立即修改密码