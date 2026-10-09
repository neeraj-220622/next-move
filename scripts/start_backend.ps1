#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Start the NextMove FastAPI backend in development mode.
.DESCRIPTION
    Activates the Python virtual environment and starts uvicorn with --reload.
    Copy .env.example to .env and adjust values before running.
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

    Write-Host "Starting NextMove backend..." -ForegroundColor Cyan
    uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
} finally {
    Pop-Location
}
