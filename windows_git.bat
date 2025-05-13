@echo off
setlocal

set "gitPath=C:\Program Files\Git\bin"
set "found="
for %%G in ("%PATH:;=" "%") do (
    if /I "%%~G"=="%gitPath%" set found=1
)
if not defined found (
    setx PATH "%PATH%;%gitPath%" >nul
    echo Git path added. Restart terminal to apply changes.
) else (
    echo Git path is already in PATH.
)

echo Installing GitVersion using winget...
winget install --id GitTools.GitVersion --silent --accept-package-agreements --accept-source-agreements
echo GitVersion installation completed.

endlocal
timeout /t 10