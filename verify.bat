@echo off
echo Checking which fixes are present in this project...
echo.

if not exist "Main.py" (
    echo ERROR: Main.py not found. Run this script from inside your
    echo project folder ^(the one with Main.py, Frontend, Backend, Data^).
    pause
    exit /b 1
)

findstr /c:"IsStopCommand" Main.py >nul
if errorlevel 1 (
    echo [FAIL] Voice-stop fix          - NOT in Main.py
) else (
    echo [OK]   Voice-stop fix          - present
)

findstr /c:"sidebarCard" Frontend\GUI.py >nul 2>&1
if errorlevel 1 (
    echo [FAIL] GUI styling fix         - NOT in Frontend\GUI.py
) else (
    echo [OK]   GUI styling fix         - present
)

findstr /c:"site search" Backend\Model.py >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Site search fix         - NOT in Backend\Model.py
) else (
    echo [OK]   Site search fix         - present
)

findstr /c:"SiteSearch" Backend\Automation.py >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Site search automation  - NOT in Backend\Automation.py
) else (
    echo [OK]   Site search automation  - present
)

findstr /c:"CreateFile" Backend\Automation.py >nul 2>&1
if errorlevel 1 (
    echo [FAIL] File commands           - NOT in Backend\Automation.py
) else (
    echo [OK]   File commands           - present
)

findstr /c:"_language_instruction" Backend\Chatbot.py >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Urdu language fix       - NOT in Backend\Chatbot.py
) else (
    echo [OK]   Urdu language fix       - present
)

findstr /c:"SENTENCE_SPLIT_RE" Backend\TextToSpeech.py >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Urdu TTS fix            - NOT in Backend\TextToSpeech.py
) else (
    echo [OK]   Urdu TTS fix            - present
)

findstr /c:"_ttsShouldContinue" Main.py >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Stop-interrupts-speech  - NOT in Main.py
) else (
    echo [OK]   Stop-interrupts-speech  - present
)

findstr /c:"_voice_params" Backend\TextToSpeech.py >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Urdu pitch/rate fix     - NOT in Backend\TextToSpeech.py
) else (
    echo [OK]   Urdu pitch/rate fix     - present
)

findstr /c:"GetStopFlag" Backend\Chatbot.py >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Stop-interrupts-reply   - NOT in Backend\Chatbot.py
) else (
    echo [OK]   Stop-interrupts-reply   - present
)

findstr /c:"_contains_devanagari" Backend\Chatbot.py >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Urdu-not-Hindi fix      - NOT in Backend\Chatbot.py
) else (
    echo [OK]   Urdu-not-Hindi fix      - present
)

echo.
echo If anything above says [FAIL], re-run install.bat from the
echo update package to fix it -- do not copy files by hand.
echo.
pause

findstr /c:"def _save" Backend\Chatbot.py >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Error-fix in Chatbot    - NOT in Backend\Chatbot.py
) else (
    echo [OK]   Error-fix in Chatbot    - present
)
