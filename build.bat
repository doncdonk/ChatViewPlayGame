@echo off

echo ========================================
echo  ChatViewPlayGame Build Script
echo ========================================
echo.

:: Detect Python path
echo [0/3] Detecting Python path...
for /f "delims=" %%i in ('where python') do set PYTHON_PATH=%%i
if "%PYTHON_PATH%"=="" (
    echo ERROR: Python not found. Please install Python first.
    pause
    exit /b 1
)
echo    Python: %PYTHON_PATH%
echo.

:: Install dependencies
echo [1/3] Installing dependencies...
"%PYTHON_PATH%" -m pip install pillow pyinstaller
if %errorlevel% neq 0 (
    echo ERROR: pip install failed.
    pause
    exit /b 1
)
echo.

:: Generate icon
echo [2/3] Generating icon...
"%PYTHON_PATH%" build_icon.py
if %errorlevel% neq 0 (
    echo ERROR: Icon generation failed.
    pause
    exit /b 1
)
echo.

:: Build exe
echo [3/3] Building exe (this may take a few minutes)...
"%PYTHON_PATH%" -m PyInstaller ChatViewPlayGame.spec --clean --noconfirm
if %errorlevel% neq 0 (
    echo ERROR: Build failed.
    pause
    exit /b 1
)

echo.
echo ========================================
echo  Build complete!
echo  Output: dist\ChatViewPlayGame.exe
echo ========================================
pause
explorer dist
