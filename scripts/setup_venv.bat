@echo off
REM ============================================================
REM  ARC-AGI-Explorations - one-shot venv setup for Windows CMD
REM ============================================================
REM  Usage (from repo root):
REM      scripts\setup_venv.bat
REM
REM  What it does:
REM    1. Creates .venv/ under the repo root if it doesn't exist.
REM    2. Upgrades pip inside the venv (avoids the GBK-decode bug on
REM       older pip versions running under Chinese Windows locales).
REM    3. Installs runtime + dev deps from requirements-dev.txt.
REM
REM  After running this, activate the venv in every new terminal with:
REM      .venv\Scripts\activate
REM  and deactivate with:
REM      deactivate
REM ============================================================

setlocal

REM cd to repo root (parent of this script)
cd /d "%~dp0.."

if not exist ".venv" (
    echo [1/3] Creating .venv ...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: failed to create venv. Is python on PATH?
        exit /b 1
    )
) else (
    echo [1/3] .venv already exists, skipping creation.
)

echo [2/3] Upgrading pip inside .venv ...
call .venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 (
    echo ERROR: pip upgrade failed.
    exit /b 1
)

echo [3/3] Installing dev + runtime dependencies ...
call .venv\Scripts\python.exe -m pip install -r requirements-dev.txt
if errorlevel 1 (
    echo ERROR: dependency install failed.
    exit /b 1
)

echo.
echo ============================================================
echo  Done. To use the venv in a new terminal, run:
echo      .venv\Scripts\activate
echo  Then verify with:
echo      python -m solver.tests.test_smoke
echo ============================================================

endlocal
