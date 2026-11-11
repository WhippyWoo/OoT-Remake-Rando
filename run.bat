@echo off
title OoT Remake Randomizer
cd /d "%~dp0"
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY where python >nul 2>nul && set "PY=python"
if not defined PY (
  echo Python 3 is not installed. Get it from https://www.python.org/downloads/ ^(tick "Add python.exe to PATH"^), then run this again.
  pause
  exit /b 1
)
%PY% -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" || (echo Python 3.8 or newer is needed. & pause & exit /b 1)
%PY% -c "from lib import zst; import sys; sys.exit(0 if zst.BACKEND else 1)" 2>nul || (
  echo Installing the zstandard package ^(one time^)...
  %PY% -m pip install --user zstandard || (echo Could not install zstandard. Check your internet connection. & pause & exit /b 1)
)
%PY% gui.py
pause
