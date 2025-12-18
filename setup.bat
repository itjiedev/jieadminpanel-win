@echo off
chcp 65001
setlocal enabledelayedexpansion

set "CURRENT_DIR=%~dp0"
set "CURRENT_DIR=%CURRENT_DIR:~0,-1%"
set "PYTHON_RUN=%CURRENT_DIR%\Python\python.exe"

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

echo 创建用户data文件夹...
mkdir "%CURRENT_DIR%\data"

echo 安装系统依赖项...
"%PYTHON_RUN%" -m pip install --upgrade pip -i %available_source% --no-warn-script-location
"%PYTHON_RUN%" -m pip install -i %available_source% -r "%CURRENT_DIR%\requirements.txt" --no-warn-script-location
@REM "%PYTHON_RUN%" -m pip install -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple -r "%CURRENT_DIR%\adminpanel\apps\envs_python\setup\requirements.txt" --no-warn-script-location
@REM "%PYTHON_RUN%" -m pip install -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple -r "%CURRENT_DIR%\adminpanel\apps\sharedkit\setup\requirements.txt" --no-warn-script-location
@REM "%PYTHON_RUN%" -m pip install -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple -r "%CURRENT_DIR%\adminpanel\apps\envs_python_runtime\setup\requirements.txt" --no-warn-script-location
@REM "%PYTHON_RUN%" -m pip install -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple -r "%CURRENT_DIR%\adminpanel\apps\envs_python_installer\setup\requirements.txt" --no-warn-script-location
@REM "%PYTHON_RUN%" -m pip install -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple -r "%CURRENT_DIR%\adminpanel\apps\db_mysql\setup\requirements.txt" --no-warn-script-location

echo 组件模块初始化...
"%PYTHON_RUN%" "%CURRENT_DIR%\adminpanel\apps\sharedkit\setup\install.py"
"%PYTHON_RUN%" "%CURRENT_DIR%\adminpanel\apps\envs_python\setup\install.py"
"%PYTHON_RUN%" "%CURRENT_DIR%\adminpanel\apps\envs_python_runtime\setup\install.py"
"%PYTHON_RUN%" "%CURRENT_DIR%\adminpanel\apps\envs_python_installer\setup\install.py"
"%PYTHON_RUN%" "%CURRENT_DIR%\adminpanel\apps\db_mysql\setup\install.py"

echo 生成密钥...
"%PYTHON_RUN%" "%CURRENT_DIR%\adminpanel\manage.py" secretkey

call "%CURRENT_DIR%\port.bat"

echo 安装脚本执行完毕，请运行RunJieAdminPanle启动服务。。。
pause

endlocal