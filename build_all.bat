@echo off
chcp 65001 >nul
echo ============================================
echo   Qsever 打包构建脚本
echo ============================================
echo.

cd /d "%~dp0"

echo [1/4] 检查 PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo 安装 PyInstaller...
    pip install pyinstaller
)
echo 完成
echo.

echo [2/4] 打包主程序 (PyInstaller onefile)...
pyinstaller build.spec --clean --noconfirm
if errorlevel 1 (
    echo 主程序打包失败！
    pause
    exit /b 1
)
echo 完成
echo.

echo [3/4] 生成安装程序源码...
python make_installer.py
if errorlevel 1 (
    echo 安装程序生成失败！
    pause
    exit /b 1
)
echo 完成
echo.

echo [4/4] 打包安装程序 (PyInstaller onefile)...
pyinstaller --onefile --name Qsever_Setup --console --noconfirm dist/installer_filled.py
if errorlevel 1 (
    echo 安装程序打包失败！
    pause
    exit /b 1
)
echo 完成
echo.

echo ============================================
echo   构建完成！
echo ============================================
echo.

for %%F in (dist\Qsever_Setup.exe) do echo 安装程序: %%F (%%~zF bytes)
for %%F in (dist\Qsever.exe) do echo 主程序:   %%F (%%~zF bytes)
echo.
echo 运行 dist\Qsever_Setup.exe 即可安装到桌面
echo.
pause
