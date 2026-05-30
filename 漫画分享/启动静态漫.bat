@echo off
chcp 65001 >nul
cd /d "%~dp0"

:: 启动后端服务
start "静态漫-服务" python 静态漫_server.py

:: 等待1秒后打开前端
timeout /t 1 /nobreak >nul
start "" 静态漫.html

exit