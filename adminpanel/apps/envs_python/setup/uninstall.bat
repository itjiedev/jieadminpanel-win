@echo off
chcp 65001 >nul

echo 卸载 python环境管理基础（envs_python） 组件...
..\..\..\..\python\python.exe .\uninstall.py
echo 按任意键关闭窗口...
pause >nul