@echo off
chcp 65001 >nul
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo 未找到Python。普通用户请下载Windows免安装版，解压后双击EXE。
  echo 下载地址：https://github.com/cdlnet168-afk/probably-stolen-lab/releases/latest
  pause
  exit /b 1
)
python server.py
pause
