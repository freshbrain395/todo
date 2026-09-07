@echo off
setlocal
cd /d "%~dp0"

set "EXE_PATH=release\todo-agent.exe"
set "DO_BUILD=0"

if "%~1"=="--rebuild" (
    set "DO_BUILD=1"
) else if "%~1"=="-b" (
    set "DO_BUILD=1"
)

if not exist "%EXE_PATH%" (
    set "DO_BUILD=1"
)

if "%DO_BUILD%"=="1" (
    echo =======================================================
    echo [*] Packaging Todo Agent EXE...
    echo =======================================================
    call pnpm run build:exe
    if %ERRORLEVEL% neq 0 (
        echo.
        echo [ERROR] Build failed! Please check logs above.
        pause
        exit /b %ERRORLEVEL%
    )
    echo.
    echo [*] Build completed successfully.
) else (
    echo [*] Found existing %EXE_PATH%, skipping build...
    echo [*] Hint: Use 'run.bat --rebuild' if you want to rebuild.
)

echo.
echo =======================================================
echo [*] Launching %EXE_PATH% (Native GUI Mode)...
echo =======================================================
echo.

if "%~1"=="--rebuild" (
    set "ARGS="
    for /f "tokens=1* delims= " %%a in ("%*") do set "ARGS=%%b"
    if not defined ARGS set "ARGS=gui"
    "%EXE_PATH%" %ARGS%
) else if "%~1"=="-b" (
    set "ARGS="
    for /f "tokens=1* delims= " %%a in ("%*") do set "ARGS=%%b"
    if not defined ARGS set "ARGS=gui"
    "%EXE_PATH%" %ARGS%
) else if "%~1"=="" (
    "%EXE_PATH%" gui
) else (
    "%EXE_PATH%" %*
)

endlocal
