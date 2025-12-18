@echo off
chcp 65001
setlocal enabledelayedexpansion

set "CURRENT_DIR=%~dp0"
set "CURRENT_DIR=%CURRENT_DIR:~0,-1%"

if exist "%CURRENT_DIR%\RunJieAdminPanel.bat" (
    del "%CURRENT_DIR%\RunJieAdminPanel.bat"
)
if exist "%CURRENT_DIR%\JieAdminPanel-win.url" (
    del "%CURRENT_DIR%\JieAdminPanel-win.url"
)

echo 正在寻找可用端口...

set /a startPort=8000
set /a maxPort=65535
set /a maxAttempts=1000
set /a attempt=0
set /a port=%startPort%

:loop
set /a attempt+=1
if !attempt! gtr %maxAttempts% (
    echo ⚠️ 1000次尝试失败！可能端口范围已满（8001-65535），建议检查系统占用。
    echo ❌ JieAdminPanel 启动终止：
    exit /b 1
)
if %port% gtr %maxPort% (
    echo ⚠️ 端口范围已满（8000-65535），建议检查系统占用。
    echo ❌ JieAdminPanel 启动终止：
    exit /b 1
)
set /a port=8000 + %random% %% 65535
netstat -ano | findstr /c:": %port% " >nul

if %errorlevel% equ 0 (
    goto loop
) else (
    echo ✅ 找到可用端口: %port%
)
echo 重建服务启动文件...
(
    echo [InternetShortcut]
    echo URL=http://127.0.0.1:%port%
    echo IconFile=%~dp0favicon.ico
    echo IconIndex=0
) > "%CURRENT_DIR%\JieAdminPanel-win.url"

(
    echo .\python\python.exe .\adminpanel\manage.py runserver 127.0.0.1:%port%
) > "%CURRENT_DIR%\RunJieAdminPanel.bat"

set "TARGET_EXE=RunJieAdminPanel.bat"
set "TARGET_PATH=%CURRENT_DIR%\%TARGET_EXE%"
if not exist "%TARGET_PATH%" (
    echo 错误: 找不到目标可执行文件 "%TARGET_EXE%"
    echo 请确保文件存在于当前目录中
    pause
    exit /b 1
)
echo 重建桌面启动快捷方式...
for /f "tokens=2*" %%i in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders" /v Desktop ^| findstr Desktop') do set "DESKTOP_PATH=%%j"
set "URL_SHORTCUT=%DESKTOP_PATH%\RunJieAdminPanel.url"
if exist "%URL_SHORTCUT%" (
    del "%URL_SHORTCUT%"
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

set "URL_SHORTCUT=%DESKTOP_PATH%\JieAdminPanel-win.url"
if exist "%URL_SHORTCUT%" (
    del "%URL_SHORTCUT%"
)

set "VBS_SCRIPT=%TEMP%\CreateShortcut.vbs"
(
    echo Set oWS = WScript.CreateObject^("WScript.Shell"^)
    echo Set oLink = oWS.CreateShortcut^(oWS.SpecialFolders^("Desktop"^) ^& "\JieAdminPanel-win.url"^)
    echo oLink.TargetPath = "http://127.0.0.1:%port%"
    echo Set oFS = CreateObject^("Scripting.FileSystemObject"^)
    echo Set oFile = oFS.CreateTextFile^(oLink.FullName, True^)
    echo oFile.WriteLine ^("[InternetShortcut]"^)
    echo oFile.WriteLine ^("URL=http://127.0.0.1:%port%"^)
    echo oFile.WriteLine ^("IconFile=%CURRENT_DIR%\favicon.ico"^)
    echo oFile.WriteLine ^("IconIndex=0"^)
    echo oFile.Close
) > "%VBS_SCRIPT%"
cscript /nologo "%VBS_SCRIPT%"
del "%VBS_SCRIPT%"

echo 端口重置完成...

endlocal