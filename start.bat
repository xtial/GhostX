@echo off
echo Starting Ghostx Server...
cd /d %~dp0
call venv\Scripts\activate
python run.py 