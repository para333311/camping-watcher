@echo off
chcp 65001 >nul
cd /d "%USERPROFILE%\camping-watcher"
powercfg /change standby-timeout-ac 0 >nul 2>&1
powercfg /change hibernate-timeout-ac 0 >nul 2>&1
:loop
"%USERPROFILE%\camping-watcher\.venv\Scripts\python.exe" watch.py
timeout /t 10 >nul
goto loop
