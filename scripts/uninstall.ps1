# Todo Agent Windows 卸载脚本
[CmdletBinding()]
param(
    [string]$InstallDir = "$env:LOCALAPPDATA\Programs\Todo Agent"
)

Write-Host "========================================" -ForegroundColor Yellow
Write-Host "       Todo Agent 卸载程序              " -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow

# 1. 移除桌面快捷方式
$desktopShortcut = Join-Path ([System.Environment]::GetFolderPath('Desktop')) "Todo Agent.lnk"
if (Test-Path $desktopShortcut) {
    Remove-Item $desktopShortcut -Force
    Write-Host "(OK) 已移除桌面快捷方式" -ForegroundColor Gray
}

# 2. 移除开始菜单快捷方式
$startMenuDir = Join-Path ([System.Environment]::GetFolderPath('Programs')) "Todo Agent"
if (Test-Path $startMenuDir) {
    Remove-Item $startMenuDir -Recurse -Force
    Write-Host "(OK) 已移除开始菜单快捷方式" -ForegroundColor Gray
}

# 3. 移除安装目录
if (Test-Path $InstallDir) {
    Remove-Item $InstallDir -Recurse -Force
    Write-Host "(OK) 已清理安装目录: $InstallDir" -ForegroundColor Gray
}

# 4. 从用户 PATH 中移除
$userPath = [System.Environment]::GetEnvironmentVariable('Path', 'User')
$paths = $userPath -split ';' | Where-Object { $_ -ne '' -and $_ -ne $InstallDir }
$newPath = $paths -join ';'
[System.Environment]::SetEnvironmentVariable('Path', $newPath, 'User')
Write-Host "(OK) 已从用户 PATH 中清理" -ForegroundColor Gray

Write-Host ""
Write-Host "[提示] 用户的待办数据与配置仍安全保留在 %APPDATA%\Todo Agent" -ForegroundColor Cyan
Write-Host "卸载完成！" -ForegroundColor Green
