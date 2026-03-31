@echo off

echo ========================================
echo  ChatViewPlayGame Build Script
echo ========================================
echo.

echo [0/5] Detecting Python path...
for /f "delims=" %%i in ('where python') do set PYTHON_PATH=%%i
if "%PYTHON_PATH%"=="" (
    echo ERROR: Python not found. Please install Python first.
    pause
    exit /b 1
)
echo    Python: %PYTHON_PATH%
echo.

echo [1/5] Installing dependencies...
"%PYTHON_PATH%" -m pip install pillow numpy pyinstaller
if %errorlevel% neq 0 (
    echo ERROR: pip install failed.
    pause
    exit /b 1
)
echo.

echo [2/5] Generating icon...
"%PYTHON_PATH%" build_icon.py
if %errorlevel% neq 0 (
    echo ERROR: Icon generation failed.
    pause
    exit /b 1
)
echo.

echo [3/5] Building exe (this may take a few minutes)...
"%PYTHON_PATH%" -m PyInstaller ChatViewPlayGame.spec --clean --noconfirm
if %errorlevel% neq 0 (
    echo ERROR: Build failed.
    pause
    exit /b 1
)
echo.

echo [4/5] Packaging release...
copy /y token_guide.html dist\token_guide.html > nul
if %errorlevel% neq 0 (
    echo ERROR: Could not copy token_guide.html
    pause
    exit /b 1
)

if not exist dist\img mkdir dist\img
xcopy /e /y /q img dist\img > nul
if %errorlevel% neq 0 (
    echo ERROR: Could not copy img directory
    pause
    exit /b 1
)

set ZIP_NAME=ChatViewPlayGame_release.zip
if exist %ZIP_NAME% del %ZIP_NAME%
powershell -Command "Compress-Archive -Path 'dist\ChatViewPlayGame.exe','dist\token_guide.html','dist\img' -DestinationPath '%ZIP_NAME%'"
if %errorlevel% neq 0 (
    echo ERROR: ZIP creation failed.
    pause
    exit /b 1
)

echo.
echo ========================================
echo  Build complete!
echo  Exe    : dist\ChatViewPlayGame.exe
echo  Images : dist\img\
echo  Guide  : dist\token_guide.html
echo  Release: %ZIP_NAME%
echo ========================================
pause
explorer dist
