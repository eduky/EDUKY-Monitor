# GitHub上传工具 - PowerShell版本
# 设置控制台编码为UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$Host.UI.RawUI.WindowTitle = "FAKA Monitor GitHub 上传工具"

Clear-Host
Write-Host ""
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "          FAKA Monitor GitHub 上传工具" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "请确保你已经：" -ForegroundColor Yellow
Write-Host "1. 在GitHub上创建了一个新的仓库" -ForegroundColor White
Write-Host "2. 复制了仓库的HTTPS或SSH地址" -ForegroundColor White
Write-Host ""

$repoUrl = Read-Host "请输入GitHub仓库地址 (例如: https://github.com/username/faka-monitor.git)"

if ([string]::IsNullOrWhiteSpace($repoUrl)) {
    Write-Host "错误：请提供有效的仓库地址！" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

Write-Host ""
Write-Host "正在添加远程仓库..." -ForegroundColor Green
git remote remove origin 2>$null
git remote add origin $repoUrl

if ($LASTEXITCODE -ne 0) {
    Write-Host "添加远程仓库时出错！" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

Write-Host ""
Write-Host "检查git状态..." -ForegroundColor Green
$gitStatus = git status --porcelain 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "错误：不是git仓库！" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

Write-Host ""
Write-Host "添加所有文件..." -ForegroundColor Green
git add .

Write-Host ""
Write-Host "提交更改..." -ForegroundColor Green
git commit -m "Update project files" 2>$null

Write-Host ""
Write-Host "设置分支为main..." -ForegroundColor Green
git branch -M main

Write-Host ""
Write-Host "推送到GitHub..." -ForegroundColor Green
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ 成功！项目已上传到GitHub" -ForegroundColor Green
    Write-Host "你可以访问以下地址查看你的项目：" -ForegroundColor Cyan
    Write-Host $repoUrl -ForegroundColor Blue
} else {
    Write-Host ""
    Write-Host "❌ 上传失败！请检查：" -ForegroundColor Red
    Write-Host "1. 网络连接是否正常" -ForegroundColor White
    Write-Host "2. 仓库地址是否正确" -ForegroundColor White
    Write-Host "3. 是否有推送权限" -ForegroundColor White
    Write-Host "4. GitHub上的仓库是否存在" -ForegroundColor White
    Write-Host ""
    Write-Host "如果是第一次使用，可能需要登录GitHub账号" -ForegroundColor Yellow
}

Write-Host ""
Read-Host "按回车键退出"