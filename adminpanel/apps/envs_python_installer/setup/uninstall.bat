@echo off
chcp 65001 >nul

echo 卸载Python全局环境管理组件...
..\..\..\..\python\python.exe .\uninstall.py
echo 按任意键关闭窗口...
pause >nul