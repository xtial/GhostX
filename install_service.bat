@echo off
echo Installing Ghostx Service...

REM Set paths
set SERVICE_NAME=Ghostx
set PYTHON_PATH=%~dp0venv\Scripts\python.exe
set APP_PATH=%~dp0run.py
set NSSM_PATH=%~dp0nssm.exe

REM Install service
%NSSM_PATH% install %SERVICE_NAME% %PYTHON_PATH%
%NSSM_PATH% set %SERVICE_NAME% AppParameters %APP_PATH%
%NSSM_PATH% set %SERVICE_NAME% AppDirectory %~dp0
%NSSM_PATH% set %SERVICE_NAME% DisplayName "Ghostx Web Service"
%NSSM_PATH% set %SERVICE_NAME% Description "Ghostx Web Application Service"
%NSSM_PATH% set %SERVICE_NAME% Start SERVICE_AUTO_START
%NSSM_PATH% set %SERVICE_NAME% ObjectName LocalSystem
%NSSM_PATH% set %SERVICE_NAME% AppStdout %~dp0logs\service.log
%NSSM_PATH% set %SERVICE_NAME% AppStderr %~dp0logs\service.log

echo Service installed successfully!
echo Starting service...
net start %SERVICE_NAME%

pause 