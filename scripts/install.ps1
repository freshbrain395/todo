# Todo Agent Windows 一键安装脚本
[CmdletBinding()]
param(
    [string]$SourceExe = "",
    [string]$InstallDir = "$env:LOCALAPPDATA\Programs\Todo Agent"
)

if (-not $PSScriptRoot) {
    $PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
}
if (-not $SourceExe) {
    $projectRoot = Split-Path -Parent $PSScriptRoot
    $SourceExe = Join-Path $projectRoot "release\todo.exe"
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "       Todo Agent 安装程序              " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. 检查可执行文件是否存在
$resolvedExe = Resolve-Path $SourceExe -ErrorAction SilentlyContinue
if (-not $resolvedExe -or -not (Test-Path $resolvedExe)) {
    Write-Host "[错误] 未找到构建好的二进制文件: $SourceExe" -ForegroundColor Red
    Write-Host "请先在项目根目录运行: pnpm run build:exe" -ForegroundColor Yellow
    exit 1
}

# 2. 创建安装目录
Write-Host "[*] 正在创建安装目录: $InstallDir ..." -ForegroundColor Gray
if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}

# 3. 拷贝程序文件
$targetExe = Join-Path $InstallDir "todo.exe"
Write-Host "[*] 正在部署可执行文件到 $targetExe ..." -ForegroundColor Gray
Copy-Item -Path $resolvedExe -Destination $targetExe -Force

# 4. 创建桌面快捷方式 (双击 -> todo.exe gui)
$desktopPath = [System.Environment]::GetFolderPath('Desktop')
$desktopShortcutPath = Join-Path $desktopPath "Todo Agent.lnk"
$wscript = New-Object -ComObject WScript.Shell
$shortcut = $wscript.CreateShortcut($desktopShortcutPath)
$shortcut.TargetPath = $targetExe
$shortcut.Arguments = "gui"
$shortcut.WorkingDirectory = $InstallDir
$shortcut.IconLocation = "$targetExe,0"
$shortcut.Description = "Todo Agent 智能桌面客户端"
$shortcut.Save()
Write-Host "(OK) 已创建桌面图标: $desktopShortcutPath" -ForegroundColor Green

# 5. 创建开始菜单快捷方式
$startMenuDir = Join-Path ([System.Environment]::GetFolderPath('Programs')) "Todo Agent"
if (-not (Test-Path $startMenuDir)) {
    New-Item -ItemType Directory -Path $startMenuDir -Force | Out-Null
}
$startMenuShortcutPath = Join-Path $startMenuDir "Todo Agent.lnk"
$smShortcut = $wscript.CreateShortcut($startMenuShortcutPath)
$smShortcut.TargetPath = $targetExe
$smShortcut.Arguments = "gui"
$smShortcut.WorkingDirectory = $InstallDir
$smShortcut.IconLocation = "$targetExe,0"
$smShortcut.Description = "Todo Agent"
$smShortcut.Save()
Write-Host "(OK) 已创建开始菜单图标: $startMenuShortcutPath" -ForegroundColor Green

# 6. 将安装目录加入用户 PATH
$userPath = [System.Environment]::GetEnvironmentVariable('Path', 'User')
$paths = $userPath -split ';' | Where-Object { $_ -ne '' }
if ($paths -notcontains $InstallDir) {
    $newPath = ($paths + $InstallDir) -join ';'
    [System.Environment]::SetEnvironmentVariable('Path', $newPath, 'User')
    $env:Path = "$InstallDir;$env:Path"
    Write-Host "(OK) 已将安装目录写入用户 PATH 环境变量" -ForegroundColor Green
} else {
    Write-Host "[*] 安装目录已在 PATH 中" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Todo Agent 安装成功！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "1. 桌面图标: 双击即可启动原生 GUI 桌面客户端" -ForegroundColor Cyan
Write-Host "2. 命令行: 打开任意终端即可使用以下命令:" -ForegroundColor Cyan
Write-Host "     todo          -> 直接进入 CLI 聊天 + 待办管理" -ForegroundColor White
Write-Host "     todo gui      -> 启动桌面客户端" -ForegroundColor White
Write-Host "     todo web      -> 启动 Web 服务并自动打开浏览器" -ForegroundColor White
Write-Host "     todo server   -> 仅在后台启动 API 服务" -ForegroundColor White
Write-Host ""
