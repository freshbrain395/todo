@echo off
chcp 65001 >nul
title Todo Agent 安装程序
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
pause
