@echo off
chcp 65001 >nul

echo 安装 Python installer环境管理 前提依赖项
..\..\..\..\python\python.exe -m pip install -r requirements.txt
..\..\..\..\python\python.exe .\install.py
echo 安装完成...
echo 按任意键关闭窗口...
pause >nul