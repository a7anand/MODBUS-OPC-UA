#Requires -RunAsAdministrator
param(
    [string]$InstallDir = "",
    [string]$TaskName = "ModbusOPCUAGateway",
    [string]$ServiceName = "ModbusOPCUAGateway",
    [string]$NssmPath = ""
)

$ErrorActionPreference = "SilentlyContinue"

if (-not $InstallDir) {
    $InstallDir = Split-Path -Parent $PSScriptRoot
}
$nssm = $NssmPath
if (-not $nssm -or -not (Test-Path $nssm)) {
    $local = Join-Path $InstallDir "nssm.exe"
    if (Test-Path $local) { $nssm = $local }
    else {
        $cmd = Get-Command nssm -ErrorAction SilentlyContinue
        if ($cmd) { $nssm = $cmd.Source }
    }
}

if ($nssm -and (Test-Path $nssm)) {
    & $nssm stop $ServiceName
    & $nssm remove $ServiceName confirm
    Write-Host "Removed NSSM service $ServiceName"
}

Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
Write-Host "Removed scheduled task $TaskName (if it existed)."
