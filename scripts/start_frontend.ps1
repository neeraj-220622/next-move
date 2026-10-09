#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Start the NextMove React frontend in development mode.
.DESCRIPTION
    Installs npm dependencies if node_modules is absent, then runs Vite.
    Copy .env.example to .env.local and adjust values before running.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$FrontendDir = Join-Path $PSScriptRoot ".." "frontend"
Push-Location $FrontendDir

try {
    if (-not (Test-Path "node_modules")) {
        Write-Host "node_modules not found — running npm install..." -ForegroundColor Yellow
        npm install
    }

    Write-Host "Starting NextMove frontend..." -ForegroundColor Cyan
    npm run dev
} finally {
    Pop-Location
}
