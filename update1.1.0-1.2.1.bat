@echo off
chcp 65001
setlocal enabledelayedexpansion

set "CURRENT_DIR=%~dp0"
set "CURRENT_DIR=%CURRENT_DIR:~0,-1%"
set "PYTHON_RUN=%CURRENT_DIR%\Python\python.exe"

echo 升级Python pip版本
echo 检查安装源。。
set "TEST_DIR=%TEMP%\pip_test_%RANDOM%"
mkdir "%TEST_DIR%" >nul 2>&1
set "sources=https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple https://mirrors.aliyun.com/pypi/simple https://mirrors.huaweicloud.com/repository/pypi/simple https://mirrors.cloud.tencent.com/pypi/simple https://pypi.org/simple"
set "available_source="
echo 正在自动测试PyPI源可用性（使用真实pip协议）...

for %%s in (%sources%) do (
    set "test_url=%%s"
    "%PYTHON_RUN%" -m pip download -i "%%s" --no-deps --only-binary=:all: pip -d "%TEST_DIR%" >nul 2>&1
    if !errorlevel! == 0 (
        set "available_source=%%s"
        echo 源 %%s 可用！（真实pip测试通过）
        goto :source_found
    ) else (
        echo 源 %%s 不可用（错误码: !errorlevel!）
    )
)
:source_found
if not defined available_source (
    echo 所有源均不可用！请检查：
    echo  1、网络是否正常（ping www.baidu.com）
    echo  2、防火墙是否阻止HTTPS（端口443）
    exit /b 1
)
rmdir /s /q "%TEST_DIR%" >nul 2>&1
"%PYTHON_RUN%" -m pip install --upgrade pip -i %available_source% --no-warn-script-location

set DJANGO_VERSION="5.2.9"
echo 检查当前 Django 版本...
for /f "tokens=*" %%i in ('%PYTHON_RUN% -m pip show Django 2^>nul ^| findstr "Version:"') do (
    set CURRENT_VERSION_LINE=%%i
)
for /f "tokens=2" %%j in ("%CURRENT_VERSION_LINE%") do (
    set CURRENT_VERSION=%%j
)

if defined CURRENT_VERSION (
    echo 当前 Django 版本: %CURRENT_VERSION%
) else (
    echo 未检测到已安装的 Django
)

if %CURRENT_VERSION% == "5.2.9" (
    :: 执行升级
    echo 正在升级 Django...
    "%PYTHON_RUN%" -m pip install --upgrade "Django==%DJANGO_VERSION%"

    if %ERRORLEVEL% EQU 0 (
        echo Django 已成功升级到版本 %DJANGO_VERSION%
        :: 验证新版本
        echo 验证安装...
        python -c "import django; print('当前 Django 版本: ' + django.get_version())"
    ) else (
        echo 错误: Django 升级失败
        exit /b 1
    )
) else (
    echo Django版本不需要升级
)
pause
endlocal