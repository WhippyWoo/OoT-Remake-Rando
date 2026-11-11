@echo off
rem Double-click to build output\release\OoT-Remake-Rando.exe. The full log is saved to build\build_log.txt.
cd /d "%~dp0"
if not exist build mkdir build
echo Building the randomizer program, this takes a few minutes...
powershell -NoProfile -ExecutionPolicy Bypass -File build_exe.ps1 > build\build_log.txt 2>&1
if errorlevel 1 (echo. & echo BUILD FAILED - see build\build_log.txt) else (echo. & echo Build finished.)
echo Log: build\build_log.txt
pause
