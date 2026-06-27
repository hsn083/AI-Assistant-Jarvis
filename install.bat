@echo off
setlocal enabledelayedexpansion

echo ================================================================
echo  JARVIS update installer
echo  This will REPLACE your Frontend, Backend, and Main.py completely.
echo  Your .env and Data folder are left untouched.
echo ================================================================
echo.

REM ---- Figure out where this script is running from ----
set SCRIPT_DIR=%~dp0
set NEW_FRONTEND=%SCRIPT_DIR%jarvis-ai-assistant-main\Frontend
set NEW_BACKEND=%SCRIPT_DIR%jarvis-ai-assistant-main\Backend
set NEW_MAIN=%SCRIPT_DIR%jarvis-ai-assistant-main\Main.py

if not exist "%NEW_FRONTEND%" (
    echo ERROR: Could not find jarvis-ai-assistant-main\Frontend next to this script.
    echo Make sure install.bat is in the same folder as jarvis-ai-assistant-main\
    pause
    exit /b 1
)

if not exist "%NEW_BACKEND%" (
    echo ERROR: Could not find jarvis-ai-assistant-main\Backend next to this script.
    pause
    exit /b 1
)

echo This script needs to know your EXISTING project folder
echo ^(the one with your real .env and Data folder^).
echo.
set /p TARGET_DIR="Paste the full path to your existing project folder, then press Enter: "

if not exist "%TARGET_DIR%\.env" (
    echo.
    echo WARNING: No .env found at "%TARGET_DIR%".
    echo Double check this is the right folder.
    set /p CONFIRM="Continue anyway? (y/n): "
    if /i not "!CONFIRM!"=="y" (
        echo Cancelled.
        pause
        exit /b 1
    )
)

echo.
echo Step 1: Removing old Frontend, Backend, and Main.py...
if exist "%TARGET_DIR%\Frontend" rmdir /s /q "%TARGET_DIR%\Frontend"
if exist "%TARGET_DIR%\Backend" rmdir /s /q "%TARGET_DIR%\Backend"
if exist "%TARGET_DIR%\Main.py" del /q "%TARGET_DIR%\Main.py"

echo Step 2: Removing stale __pycache__ folders...
for /d /r "%TARGET_DIR%" %%d in (__pycache__) do (
    if exist "%%d" rmdir /s /q "%%d"
)

echo Step 3: Copying new Frontend, Backend, and Main.py...
xcopy "%NEW_FRONTEND%" "%TARGET_DIR%\Frontend\" /e /i /y /q
xcopy "%NEW_BACKEND%" "%TARGET_DIR%\Backend\" /e /i /y /q
copy /y "%NEW_MAIN%" "%TARGET_DIR%\Main.py" >nul

echo.
echo Step 4: Verifying the fixes actually landed...
set ALL_OK=1

findstr /c:"IsStopCommand" "%TARGET_DIR%\Main.py" >nul
if errorlevel 1 (
    echo [FAIL] Voice-stop fix not found in Main.py
    set ALL_OK=0
) else (
    echo [OK]   Voice-stop fix present in Main.py
)

findstr /c:"sidebarCard" "%TARGET_DIR%\Frontend\GUI.py" >nul 2>&1
if errorlevel 1 (
    echo [FAIL] GUI styling fix not found in Frontend\GUI.py
    set ALL_OK=0
) else (
    echo [OK]   GUI styling fix present in Frontend\GUI.py
)

findstr /c:"site search" "%TARGET_DIR%\Backend\Model.py" >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Site search fix not found in Backend\Model.py
    set ALL_OK=0
) else (
    echo [OK]   Site search fix present in Backend\Model.py
)

findstr /c:"SiteSearch" "%TARGET_DIR%\Backend\Automation.py" >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Site search fix not found in Backend\Automation.py
    set ALL_OK=0
) else (
    echo [OK]   Site search fix present in Backend\Automation.py
)

findstr /c:"_language_instruction" "%TARGET_DIR%\Backend\Chatbot.py" >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Urdu language fix not found in Backend\Chatbot.py
    set ALL_OK=0
) else (
    echo [OK]   Urdu language fix present in Backend\Chatbot.py
)

findstr /c:"_ttsShouldContinue" "%TARGET_DIR%\Main.py" >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Stop-interrupts-speech fix not found in Main.py
    set ALL_OK=0
) else (
    echo [OK]   Stop-interrupts-speech fix present in Main.py
)

findstr /c:"_voice_params" "%TARGET_DIR%\Backend\TextToSpeech.py" >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Urdu pitch/rate fix not found in Backend\TextToSpeech.py
    set ALL_OK=0
) else (
    echo [OK]   Urdu pitch/rate fix present in Backend\TextToSpeech.py
)

findstr /c:"_contains_devanagari" "%TARGET_DIR%\Backend\Chatbot.py" >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Urdu-not-Hindi fix not found in Backend\Chatbot.py
    set ALL_OK=0
) else (
    echo [OK]   Urdu-not-Hindi fix present in Backend\Chatbot.py
)

echo.
if "%ALL_OK%"=="1" (
    echo ============================================================
    echo  SUCCESS: All fixes confirmed present.
    echo ============================================================
) else (
    echo ============================================================
    echo  FAILED: One or more fixes did not copy correctly.
    echo  Please contact support with this message instead of
    echo  re-running on your own.
    echo ============================================================
    pause
    exit /b 1
)

echo.
echo Step 5: Installing/updating Python dependencies...
cd /d "%TARGET_DIR%"
pip install -r Requirements.txt

echo.
echo ================================================================
echo  Done. You can now run: python Main.py
echo ================================================================
pause

