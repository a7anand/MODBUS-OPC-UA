#Requires -RunAsAdministrator
<#
.SYNOPSIS
  Install Modbus OPC UA Gateway to start in the background at Windows startup.

.DESCRIPTION
  Prefers NSSM (true Windows service) if nssm.exe is on PATH or in the install folder.
  Otherwise registers a Scheduled Task at system startup (runs as SYSTEM).

.PARAMETER InstallDir
  Folder containing ModbusOPCUAGateway.exe (default: parent of this script if EXE present).
#>
param(
    [string]$InstallDir = "",
    [string]$TaskName = "ModbusOPCUAGateway",
    [string]$ServiceName = "ModbusOPCUAGateway",
    [string]$NssmPath = ""
)

$ErrorActionPreference = "Stop"

if (-not $InstallDir) {
    $candidate = Split-Path -Parent $PSScriptRoot
    if (Test-Path (Join-Path $candidate "ModbusOPCUAGateway.exe")) {
        $InstallDir = $candidate
    } else {
        $InstallDir = Get-Location
    }
}
$InstallDir = (Resolve-Path $InstallDir).Path
$Exe = Join-Path $InstallDir "ModbusOPCUAGateway.exe"
if (-not (Test-Path $Exe)) {
    Write-Error "ModbusOPCUAGateway.exe not found in $InstallDir"
}

$Args = "--run --portable --config config\gateway.yaml"
$LogDir = Join-Path $InstallDir "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Find-Nssm {
    if ($NssmPath -and (Test-Path $NssmPath)) { return (Resolve-Path $NssmPath).Path }
    $local = Join-Path $InstallDir "nssm.exe"
    if (Test-Path $local) { return $local }
    $cmd = Get-Command nssm -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

# Remove previous task if present
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

$nssm = Find-Nssm
if ($nssm) {
    Write-Host "Installing Windows service via NSSM: $ServiceName"
    & $nssm stop $ServiceName 2>$null
    & $nssm remove $ServiceName confirm 2>$null
    & $nssm install $ServiceName $Exe $Args
    & $nssm set $ServiceName AppDirectory $InstallDir
    & $nssm set $ServiceName DisplayName "Modbus OPC UA Gateway"
    & $nssm set $ServiceName Description "Industrial Modbus to OPC UA gateway with embedded web UI on port 8080"
    & $nssm set $ServiceName Start SERVICE_AUTO_START
    & $nssm set $ServiceName AppStdout (Join-Path $LogDir "service-stdout.log")
    & $nssm set $ServiceName AppStderr (Join-Path $LogDir "service-stderr.log")
    & $nssm set $ServiceName AppRotateFiles 1
    & $nssm set $ServiceName AppRotateBytes 10485760
    & $nssm start $ServiceName
    Write-Host "Service started. Web UI: http://127.0.0.1:8080 (see config\gateway.yaml)"
    exit 0
}

Write-Host "NSSM not found — using Scheduled Task at startup (SYSTEM)."
$action = New-ScheduledTaskAction -Execute $Exe -Argument $Args -WorkingDirectory $InstallDir
$trigger = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
Start-ScheduledTask -TaskName $TaskName
Write-Host "Scheduled task '$TaskName' registered and started."
Write-Host "Web UI: http://127.0.0.1:8080"
Write-Host "To use a Windows Service instead, place nssm.exe in $InstallDir and run this script again."
