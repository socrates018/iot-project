# filepath: c:\Users\socra\Downloads\esp32v2.ps1
# Auto-elevate to admin
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Start-Process -FilePath "powershell" -ArgumentList "-NoProfile", "-ExecutionPolicy Bypass", "-File `"$PSCommandPath`"" -Verb RunAs
    return
}

param(
    [string]$PythonPath,
    [string]$FirmwareURL
)

# Start transcript to log all output (overwrite each run)
$logPath = Join-Path $PSScriptRoot "esp32-flash-log.txt"
Start-Transcript -Path $logPath

# Improved Python path detection for Windows
function Find-Python {
    $possiblePaths = @(
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python39\python.exe",
        "$env:ProgramFiles\Python311\python.exe",
        "$env:ProgramFiles\Python310\python.exe",
        "$env:ProgramFiles\Python39\python.exe"
    )
    foreach ($p in $possiblePaths) {
        if (Test-Path $p) { return $p }
    }
    # Try from PATH
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    $pythonFromPath = if ($pythonCommand) { $pythonCommand.Source } else { $null }
    if ($pythonFromPath -and (Test-Path $pythonFromPath)) {
        return $pythonFromPath
    }
    return $null
}

if (-not $PythonPath -or -not (Test-Path $PythonPath)) {
    $PythonPath = Find-Python
    if (-not $PythonPath) {
        Write-Host "Python not found in common locations or PATH." -ForegroundColor Red
        $PythonPath = Read-Host "Please enter the full path to your python.exe"
        if (-not (Test-Path $PythonPath)) {
            Write-Host "Python still not found. Exiting script." -ForegroundColor Red
            Stop-Transcript
            return
        }
    }
}

if (-not $FirmwareURL) {
    $FirmwareURL = "https://micropython.org/download/ESP32_GENERIC_C3/esp32c3-20240105-v1.22.1.bin"
}

# Configuration
$firmwareUrl = "https://micropython.org/resources/firmware/esp32-20240222-v1.22.2.bin"
$driverUrl = "https://www.silabs.com/documents/public/software/CP210x_Windows_Drivers.zip"
$pythonUrl = "https://www.python.org/ftp/python/3.11.4/python-3.11.4-amd64.exe"

# Initialize firmware file path
$firmwareFile = Join-Path $PSScriptRoot "esp32-micropython.bin"

# Clear screen and show header
Clear-Host
Write-Host "`n=== ESP32 Programming Setup ===" -ForegroundColor Cyan
Write-Host "=== Version 2.0 - Real-Time Output ===`n" -ForegroundColor Cyan

$tempDir = "$env:TEMP\Drivers_$(Get-Date -Format 'yyyyMMddHHmmss')"
New-Item -Path $tempDir -ItemType Directory -Force | Out-Null

# Download CP210x Universal Windows Driver
$cp210xZip = "$tempDir\CP210x_Universal_Windows_Driver.zip"
try {
    Write-Host "=== Stage: Downloading CP210x Universal Driver ===" -ForegroundColor Cyan
    Invoke-WebRequest -Uri "https://www.silabs.com/documents/public/software/CP210x_Universal_Windows_Driver.zip" `
        -OutFile $cp210xZip -UseBasicParsing
    Expand-Archive -Path $cp210xZip -DestinationPath "$tempDir\CP210x" -Force
}
catch {
    Write-Warning "CP210x download failed: $_"
    return
}

# Download CH341SER Driver
$ch341Exe = "$tempDir\CH341SER.EXE"
try {
    Write-Host "=== Stage: Downloading CH341SER Driver ===" -ForegroundColor Cyan
    Invoke-WebRequest -Uri "https://www.wch.cn/download/file?id=65" `
        -OutFile $ch341Exe -UseBasicParsing
}
catch {
    Write-Warning "CH341SER download failed: $_"
    return
}

# Install CP210x Driver using INF file
$cp210xInf = Get-ChildItem -Path "$tempDir\CP210x" -Filter "*.inf" -Recurse | Select-Object -First 1
if ($cp210xInf) {
    Write-Host "=== Stage: Installing CP210x drivers ===" -ForegroundColor Green
    pnputil /add-driver "$($cp210xInf.FullName)" /install | Out-Null
}
else {
    Write-Warning "No INF file found in CP210x package"
}

# Install CH341SER Driver
if (Test-Path $ch341Exe) {
    Write-Host "=== Stage: Installing CH341SER driver ===" -ForegroundColor Green
    # Use /silent for a fully automatic, quiet install
    Start-Process -FilePath $ch341Exe -ArgumentList "/silent" -Wait -WindowStyle Hidden
}

# Verify installations
Write-Host "=== Stage: Installation Verification ==="
$cp210xDevices = Get-PnpDevice | Where-Object { $_.HardwareID -like "USB\VID_10C4&PID_EA*" }
$ch341Devices = Get-PnpDevice | Where-Object { $_.HardwareID -like "USB\VID_1A86&PID_7523*" }

Write-Host "CP210x Devices:"
$cp210xDevices | Format-Table FriendlyName, Status -AutoSize

Write-Host "`nCH341 Devices:"
$ch341Devices | Format-Table FriendlyName, Status -AutoSize

# Cleanup
Write-Host "=== Stage: Cleaning up temporary files ==="
Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue

# Install dependencies
function Install-Dependencies {
    Write-Host "=== Stage: Installing esptool ===" -ForegroundColor Gray
    & $PythonPath -m pip install esptool --disable-pip-version-check
}

# Detect ESP32-C3 COM port
function Get-ESPPort {
    Write-Host "=== Stage: Detecting ESP32-C3 COM port ===" -ForegroundColor Cyan
    $ports = Get-PnpDevice -Class Ports -PresentOnly | 
        Where-Object { $_.FriendlyName -match 'CP210|CH340|USB Serial Device' }
    
    if ($ports.Count -eq 0) {
        Write-Host "No ESP32-related COM ports detected. Please enter manually." -ForegroundColor Yellow
        return (Read-Host "Enter COM port (e.g., COM3)")
    }
    # Always use the first detected port automatically
    $deviceId = $ports[0].DeviceID
    if ($deviceId -match "(COM\d+)") {
        Write-Host "Auto-selected port: $($matches[1])" -ForegroundColor Green
        return $matches[1]
    }
    Write-Host "Could not auto-detect COM port. Please enter manually." -ForegroundColor Yellow
    return (Read-Host "Enter COM port (e.g., COM3)")
}

# Flash firmware
$global:comPort = $null
function Update-ESP32C3 {
    Write-Host "=== Stage: Downloading latest ESP32-C3 firmware ===" -ForegroundColor Cyan

    # Use a direct link to a valid .bin file (replace with your preferred firmware if needed)
    $firmwareUrl = "https://micropython.org/resources/firmware/ESP32_GENERIC_C3-20250415-v1.25.0.bin"
    $firmwareBin = Join-Path $env:TEMP "esp32c3_firmware.bin"

    # Download the firmware .bin file
    Invoke-WebRequest -Uri $firmwareUrl -OutFile $firmwareBin

    if (-not (Test-Path $firmwareBin)) {
        Write-Host "Firmware .bin file was not downloaded successfully." -ForegroundColor Red
        return
    }

    # Use Get-ESPPort to detect/select COM port
    $global:comPort = Get-ESPPort

    if (-not $global:comPort) {
        Write-Host "No COM port selected. Exiting." -ForegroundColor Red
        return
    }

    # Flash the firmware
    & $PythonPath -m esptool --chip esp32c3 --port $global:comPort erase_flash
    & $PythonPath -m esptool --chip esp32c3 --port $global:comPort --baud 460800 write_flash -z 0x0 $firmwareBin

    Write-Host "Firmware flashing complete." -ForegroundColor Green
}

# Main execution
Write-Host "=== Stage: Installing dependencies ===" -ForegroundColor Cyan
Install-Dependencies
Write-Host "=== Stage: Flashing ESP32-C3 ===" -ForegroundColor Cyan
Update-ESP32C3

Write-Host "`nFlash successful! Connect with:" -ForegroundColor Green
Write-Host "1. Serial terminal: python -m serial.tools.miniterm $global:comPort 115200"
Write-Host "`nFirst connection tip: Wait 5 seconds after plugging in before sending commands!"

# Stop transcript and notify user
Stop-Transcript
Write-Host "`nAll output has been saved to $logPath" -ForegroundColor Cyan

Start-Sleep -Seconds 10