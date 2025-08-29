@echo off
REM Check if we should launch in Windows Terminal
where /q wt >nul 2>&1
if %errorlevel% equ 0 (
    REM Check if we're already in Windows Terminal (avoid infinite loop)
    if not "%WT_SESSION%"=="" goto :skip_terminal_launch
    REM Launch in Windows Terminal and exit this CMD window
    wt --title "PySeed Manager" cmd /c ""%~f0""
    exit
)

:skip_terminal_launch
REM This script's only job is to launch the appmanager.py script using the system's
REM Python interpreter. The Python script itself will then handle creating and
REM managing its own virtual environment.

REM Get the directory where the script is located.
set "PROJECT_ROOT=%~dp0"

:start_detection
REM Check if Python is installed and in the PATH.
set "PYTHON_EXE=python"
REM The 'py.exe' launcher is often more reliable on Windows for selecting Python 3
%SystemRoot%\System32\where.exe /q py >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_EXE=py -3"
)

%PYTHON_EXE% --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [SETUP REQUIRED] Python 3 is not installed on your system.
    echo PySeed requires Python 3 to run.
    call :install_python
    REM If we reach here, installation failed or was skipped
    exit /b 1
)

REM Check for Windows Terminal and offer installation
call :check_terminal

REM Clear console and change to the project root
cls
cd /d "%PROJECT_ROOT%"
if defined TERMINAL_CHOICE (
    %PYTHON_EXE% -m appmanager --terminal-choice=%TERMINAL_CHOICE%
) else (
    %PYTHON_EXE% -m appmanager
)
pause
exit /b 0

REM Function to install Python on Windows
:install_python
echo [SETUP] Python 3 is not installed.
set /p "install_choice=Would you like to install Python 3 automatically? [Y/n]: "
if "%install_choice%"=="" (
    echo [INFO] Please enter Y or N.
    goto :install_python
)
if /i "%install_choice%"=="n" (
    echo [INFO] Python installation skipped. Please install Python 3 manually.
    start https://www.python.org/downloads/windows/
    echo Make sure to check "Add python.exe to PATH" during installation.
    pause
    exit /b 1
)
if /i not "%install_choice%"=="y" (
    echo [INFO] Invalid input. Please enter Y or N.
    goto :install_python
)

echo [SETUP] Attempting automatic installation...

REM Try winget first (Windows 10+ with App Installer)
winget --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] Using winget to install Python...
    winget install --id Python.Python.3.12 -e --source winget --silent --accept-package-agreements --accept-source-agreements
    if %errorlevel% equ 0 (
        echo [SUCCESS] Python installed via winget!
        echo [INFO] Refreshing PATH and checking again...
        call :refresh_path
        powershell -command "Start-Sleep -Seconds 2" >nul 2>&1
        goto :start_detection
    )
)

REM Try chocolatey as fallback
choco --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] Using chocolatey to install Python...
    choco install python -y
    if %errorlevel% equ 0 (
        echo [SUCCESS] Python installed via chocolatey!
        echo [INFO] Refreshing PATH and checking again...
        call :refresh_path
        powershell -command "Start-Sleep -Seconds 2" >nul 2>&1
        goto :start_detection
    )
)

REM Manual installation fallback
echo [INFO] Automatic installation failed. Opening Python download page...
start https://www.python.org/downloads/windows/
echo Please download and install Python, then restart this script.
echo Make sure to check "Add python.exe to PATH" during installation.
pause
exit /b 1

:check_terminal
REM Check if Windows Terminal is available
where /q wt >nul 2>&1
if %errorlevel% equ 0 (
    exit /b 0
)

REM Check if running on Windows 11 (Terminal is built-in)
for /f "tokens=4-5 delims=. " %%i in ('ver') do set VERSION=%%i.%%j
if "%VERSION%" geq "10.0" (
    for /f "tokens=3" %%k in ('reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v CurrentBuild 2^>nul') do (
        if %%k geq 22000 exit /b 0
    )
)

REM Check if user already declined Windows Terminal installation
for %%i in ("%PROJECT_ROOT%.") do set "PROJECT_NAME=%%~ni"
%PYTHON_EXE% -c "import json, os; from pathlib import Path; app_data = Path(os.environ.get('LOCALAPPDATA')) / '%PROJECT_NAME%'.lower(); config_file = app_data / 'project_config.json'; config = json.load(open(config_file)) if config_file.exists() else {}; exit(0 if config.get('skip_terminal_install') == True else 1)" 2>nul
if %errorlevel% equ 0 (
    exit /b 0
)

echo [SETUP] Windows Terminal is not installed.
echo Windows Terminal provides better emoji and Unicode support for PySeed.
echo Benefits: Full emoji display, better fonts, modern interface, tabs support.
echo.
:terminal_prompt
set /p "install_terminal=Would you like to install Windows Terminal? [Y/n]: "
if "%install_terminal%"=="" (
    echo [INFO] Please enter Y or N.
    goto :terminal_prompt
)
if /i "%install_terminal%"=="n" (
    echo [INFO] Windows Terminal installation skipped.
    echo Note: Emojis may not display correctly in Command Prompt.
    set "TERMINAL_CHOICE=declined"
    exit /b 0
)
if /i not "%install_terminal%"=="y" (
    echo [INFO] Invalid input. Please enter Y or N.
    goto :terminal_prompt
)

echo [SETUP] Installing Windows Terminal...
winget --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] Using winget to install Windows Terminal...
    winget install --id Microsoft.WindowsTerminal -e --source winget --silent --accept-package-agreements --accept-source-agreements
    if %errorlevel% equ 0 (
        echo [SUCCESS] Windows Terminal installed!
        echo [INFO] Relaunching in Windows Terminal for better emoji support...
        timeout /t 2 /nobreak >nul
        wt --title "PySeed Manager" cmd /c ""%~f0""
        REM Exit this CMD window completely to avoid double execution
        exit
    )
)

echo [INFO] Automatic installation failed. Opening Microsoft Store...
start ms-windows-store://pdp/?ProductId=9n0dx20hk701
echo Please install Windows Terminal from the Store, then restart this script.
pause
exit /b 0



:refresh_path
REM Refresh PATH from registry
for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH 2^>nul') do set "SYSTEM_PATH=%%b"
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "USER_PATH=%%b"
if defined SYSTEM_PATH if defined USER_PATH (
    set "PATH=%SYSTEM_PATH%;%USER_PATH%"
) else if defined SYSTEM_PATH (
    set "PATH=%SYSTEM_PATH%"
) else if defined USER_PATH (
    set "PATH=%USER_PATH%"
)
exit /b 0

