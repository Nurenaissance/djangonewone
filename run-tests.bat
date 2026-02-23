@echo off
REM ============================================================================
REM Pre-commit test suite — runs all 4 service test suites sequentially.
REM Exits on first failure. Run from whatsapp_latest_final-mainjunk/ root.
REM ============================================================================

setlocal enabledelayedexpansion

set PASS=0
set FAIL=0
set ROOT=%~dp0

echo.
echo ============================================================
echo   WhatsApp CRM Platform — Pre-Commit Test Suite
echo ============================================================
echo.

REM ── 1. Django Tests ──
echo [1/4] Running Django tests...
echo ------------------------------------------------------------
cd /d "%ROOT%whatsapp_latest_final_withclaude"
python -m pytest tests/ -v --tb=short -q
if !ERRORLEVEL! NEQ 0 (
    echo.
    echo FAIL: Django tests failed!
    set FAIL=1
    goto :summary
)
set /a PASS+=1
echo PASS: Django tests passed.
echo.

REM ── 2. Node.js Tests ──
echo [2/4] Running Node.js tests...
echo ------------------------------------------------------------
cd /d "%ROOT%whatsapp_bot_server_withclaude"
call node --experimental-vm-modules node_modules/jest/bin/jest.js --forceExit --detectOpenHandles 2>nul
if !ERRORLEVEL! NEQ 0 (
    echo.
    echo FAIL: Node.js tests failed!
    set FAIL=1
    goto :summary
)
set /a PASS+=1
echo PASS: Node.js tests passed.
echo.

REM ── 3. FastAPI Tests ──
echo [3/4] Running FastAPI tests...
echo ------------------------------------------------------------
cd /d "%ROOT%fastAPIWhatsapp_withclaude"
python -m pytest tests/ -v --tb=short -q
if !ERRORLEVEL! NEQ 0 (
    echo.
    echo FAIL: FastAPI tests failed!
    set FAIL=1
    goto :summary
)
set /a PASS+=1
echo PASS: FastAPI tests passed.
echo.

REM ── 4. Frontend Tests ──
echo [4/4] Running Frontend tests...
echo ------------------------------------------------------------
cd /d "%ROOT%whatsappBusinessAutomation_withclaude"
call npx vitest run 2>nul
if !ERRORLEVEL! NEQ 0 (
    echo.
    echo FAIL: Frontend tests failed!
    set FAIL=1
    goto :summary
)
set /a PASS+=1
echo PASS: Frontend tests passed.
echo.

:summary
echo.
echo ============================================================
if !FAIL! EQU 0 (
    echo   ALL %PASS%/4 SUITES PASSED — safe to push!
    echo ============================================================
    cd /d "%ROOT%"
    exit /b 0
) else (
    echo   FAILED — fix failing tests before pushing.
    echo   Passed: %PASS%/4
    echo ============================================================
    cd /d "%ROOT%"
    exit /b 1
)
