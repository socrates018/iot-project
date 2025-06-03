@echo off
setlocal enabledelayedexpansion

:: =============================================
:: User Configuration - Modify these as needed
:: =============================================
:: Repository URL to clone (hardcoded)
set "REPO_URL=https://github.com/socrates018/iot-project"

:: Base directory where clones will be created (current directory by default)
set "BASE_DIR=%CD%"

:: Suffix for mirror clone folder
set "MIRROR_SUFFIX=.mirror"

:: Pause on completion (true/false)
set "PAUSE_ON_COMPLETION=true"

:: =============================================
:: Git Clone Script - Normal and Mirror
:: =============================================

:: Get current date in YYYYMMDD format
for /f "tokens=2 delims==." %%i in ('"wmic os get localdatetime /value"') do set "CURR_DATE=%%i"
set "CURR_DATE=!CURR_DATE:~0,8!"

:: Extract repository name from URL (get last path segment, remove .git if present)
for %%a in ("%REPO_URL%") do (
    set "repo_path=%%~nxa"
)
set "repo_name=!repo_path:.git=!"

:: Append date to repo name
set "clone_name=!repo_name!_!CURR_DATE!"
set "mirror_name=!repo_name!_!CURR_DATE!!MIRROR_SUFFIX!"

:: Create base directory if it doesn't exist
if not "%BASE_DIR%"=="." (
    if not exist "%BASE_DIR%" mkdir "%BASE_DIR%"
)

:: Remove existing folders if they exist
if exist "%BASE_DIR%\!clone_name!" (
    echo Removing existing folder: "%BASE_DIR%\!clone_name!"
    rmdir /s /q "%BASE_DIR%\!clone_name!"
)
if exist "%BASE_DIR%\!mirror_name!" (
    echo Removing existing folder: "%BASE_DIR%\!mirror_name!"
    rmdir /s /q "%BASE_DIR%\!mirror_name!"
)

echo Cloning repository: !repo_name!
echo.

:: Normal clone
echo Creating normal clone...
git clone "%REPO_URL%" "%BASE_DIR%\!clone_name!"
if errorlevel 1 (
    echo Error cloning repository normally
    if "%PAUSE_ON_COMPLETION%"=="true" pause
    exit /b 1
)

:: Mirror clone
echo.
echo Creating mirror clone...
git clone --mirror "%REPO_URL%" "%BASE_DIR%\!mirror_name!"
if errorlevel 1 (
    echo Error creating mirror clone
    if "%PAUSE_ON_COMPLETION%"=="true" pause
    exit /b 1
)

echo.
echo Successfully created both clones:
echo - Normal clone:  "%BASE_DIR%\!clone_name!"
echo - Mirror clone:  "%BASE_DIR%\!mirror_name!"

if "%PAUSE_ON_COMPLETION%"=="true" pause