@echo off
setlocal enabledelayedexpansion

:: Configuration
set USER=pi
set HOST=10.24.4.12
set PASSWORD=1234
set PLINK_URL=https://the.earth.li/~sgtatham/putty/latest/w64/plink.exe
set PLINK_FILE=plink.exe

:: Check if plink.exe is present
if not exist "%PLINK_FILE%" (
    echo plink.exe not found. Downloading from PuTTY website...
    powershell -Command "Invoke-WebRequest -Uri '%PLINK_URL%' -OutFile '%PLINK_FILE%'"
    if not exist "%PLINK_FILE%" (
        echo Failed to download plink.exe. Exiting.
        pause
        exit /b
    )
    echo Successfully downloaded plink.exe.
)

:: Prompt for venv setup
set /p SETUP_VENV=Do you want to enable Python venv and install requirements? (y/n): 

:: Generate temporary remote shell script
> remote_script.sh echo echo %PASSWORD% ^| sudo -S true

if /I "%SETUP_VENV%"=="y" (
    >> remote_script.sh echo python3 -m venv venv
    >> remote_script.sh echo source venv/bin/activate
    >> remote_script.sh echo pip install -r requirements.txt
)

>> remote_script.sh echo dpkg -s mosquitto-clients ^> /dev/null 2^>^&1 ^|^| ^(echo %PASSWORD% ^| sudo -S apt update ^&^& echo %PASSWORD% ^| sudo -S apt install -y mosquitto-clients^)

:: Run script over SSH with plink
echo Starting SSH session with remote script...
%PLINK_FILE% -ssh %USER%@%HOST% -pw %PASSWORD% -t "bash -l" < remote_script.sh

:: Clean up
del remote_script.sh

endlocal