@echo off
chcp 65001

set "CURRENT_DIR=%~dp0"
set "CURRENT_DIR=%CURRENT_DIR:~0,-1%"
set "PYTHON_RUN=%CURRENT_DIR%\Python\python.exe"

echo 创建用户data文件夹...
mkdir "%CURRENT_DIR%\data"

echo 安装系统依赖项...
"%PYTHON_RUN%" -m pip install -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple -r "%CURRENT_DIR%\requirements.txt" --no-warn-script-location
"%PYTHON_RUN%" -m pip install -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple -r "%CURRENT_DIR%\adminpanel\apps\envs_python\setup\requirements.txt" --no-warn-script-location
"%PYTHON_RUN%" -m pip install -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple -r "%CURRENT_DIR%\adminpanel\apps\sharedkit\setup\requirements.txt" --no-warn-script-location
"%PYTHON_RUN%" -m pip install -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple -r "%CURRENT_DIR%\adminpanel\apps\envs_python_runtime\setup\requirements.txt" --no-warn-script-location
"%PYTHON_RUN%" -m pip install -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple -r "%CURRENT_DIR%\adminpanel\apps\envs_python_installer\setup\requirements.txt" --no-warn-script-location
"%PYTHON_RUN%" -m pip install -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple -r "%CURRENT_DIR%\adminpanel\apps\db_mysql\setup\requirements.txt" --no-warn-script-location

echo 组件初始化
"%PYTHON_RUN%" "%CURRENT_DIR%\adminpanel\apps\sharedkit\setup\install.py"
"%PYTHON_RUN%" "%CURRENT_DIR%\adminpanel\apps\envs_python\setup\install.py"
"%PYTHON_RUN%" "%CURRENT_DIR%\adminpanel\apps\envs_python_runtime\setup\install.py"
"%PYTHON_RUN%" "%CURRENT_DIR%\adminpanel\apps\envs_python_installer\setup\install.py"
"%PYTHON_RUN%" "%CURRENT_DIR%\adminpanel\apps\db_mysql\setup\install.py"

echo 生成密钥...
"%PYTHON_RUN%" "%CURRENT_DIR%\adminpanel\manage.py" secretkey

set "TARGET_EXE=RunJieAdminPanel.bat"
set "TARGET_PATH=%CURRENT_DIR%\%TARGET_EXE%"
if not exist "%TARGET_PATH%" (
    echo 错误: 找不到目标可执行文件 "%TARGET_EXE%"
    echo 请确保文件存在于当前目录中
    pause
    exit /b 1
)

set "VBS_SCRIPT=%TEMP%\CreateShortcut.vbs"
(
    echo Set oWS = WScript.CreateObject^("WScript.Shell"^)
    echo Set oLink = oWS.CreateShortcut^(oWS.SpecialFolders^("Desktop"^) ^& "\%TARGET_EXE:.bat=%.lnk"^)
    echo oLink.TargetPath = "%TARGET_PATH%"
    echo oLink.WorkingDirectory = "%CURRENT_DIR%"
    echo oLink.IconLocation = "%CURRENT_DIR%\logo.ico, 0"
    echo oLink.Save
) > "%VBS_SCRIPT%"
cscript /nologo "%VBS_SCRIPT%"
del "%VBS_SCRIPT%"
echo 运行快捷方式已创建在桌面

for /f "tokens=2*" %%i in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders" /v Desktop ^| findstr Desktop') do set "DESKTOP_PATH=%%j"
if not defined DESKTOP_PATH set "DESKTOP_PATH=%USERPROFILE%\Desktop"
set "URL_SHORTCUT=%DESKTOP_PATH%\JieAdminPanel-win.url"
echo 创建URL快捷方式...
(
    echo [InternetShortcut]
    echo URL=http://localhost:8000/
    echo IconFile="%CURRENT_DIR%\favicon.ico"
    echo IconIndex=0
) > "%URL_SHORTCUT%"

if exist "%URL_SHORTCUT%" (
    echo 访问系统快捷方式已创建于桌面
) else (
    echo 错误: 创建URL快捷方式失败
)

echo 安装脚本执行完毕，请关闭运行窗口并刷新桌面。。。
pause