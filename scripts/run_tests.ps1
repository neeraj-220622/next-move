#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Run the NextMove backend test suite.
.DESCRIPTION
    Activates the venv and runs pytest with verbose output.
    No live Hindsight server or Qwen model is required — all external calls are mocked.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$BackendDir = Join-Path $PSScriptRoot ".." "backend"
Push-Location $BackendDir

try {
    $VenvActivate = Join-Path $BackendDir ".venv" "Scripts" "Activate.ps1"
    if (-not (Test-Path $VenvActivate)) {
        Write-Error "Virtual environment not found. Run: python -m venv .venv"
    }

    . $VenvActivate

    Write-Host "Running NextMove backend tests..." -ForegroundColor Cyan
    pytest tests/ -v
} finally {
    Pop-Location
}
