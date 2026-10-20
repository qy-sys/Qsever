@echo off
chcp 65001 >nul
echo ============================================
echo   Qsever Build Script
echo ============================================
echo.

cd /d "%~dp0."

echo [1/4] Checking PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)
echo Done.
echo.

echo [2/4] Building main program (PyInstaller onefile)...
pyinstaller build.spec --clean --noconfirm
if errorlevel 1 (
    echo Build failed!
    pause
    exit /b 1
)
echo Done.
echo.

echo [3/4] Generating installer source...
python make_installer.py
if errorlevel 1 (
    echo Installer generation failed!
    pause
    exit /b 1
)
echo Done.
echo.

echo [4/4] Building installer (PyInstaller onefile)...
pyinstaller --onefile --name Qsever_Setup --console --noconfirm dist\installer_filled.py
if errorlevel 1 (
    echo Installer build failed!
    pause
    exit /b 1
)
echo Done.
echo.

echo ============================================
echo   Build Complete!
echo ============================================
echo.

for %%F in (dist\Qsever_Setup.exe) do echo Installer: %%F (%%~zF bytes)
for %%F in (dist\Qsever.exe) do echo Main EXE:  %%F (%%~zF bytes)
echo.
echo Output: dist\Qsever_Setup.exe
echo.
pause
