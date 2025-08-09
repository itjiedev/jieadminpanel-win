@echo off
chcp 65001 >nul

echo 安装组件依赖项...
..\..\..\..\python\python.exe -m pip install -r .\requirements.txt
..\..\..\..\python\python.exe .\install.py
echo 按任意键关闭窗口...
pause >nul