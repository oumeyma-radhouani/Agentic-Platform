param(
    [switch]$SkipFrontendBuild
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = $PSScriptRoot
$BackendDirectory = Join-Path $ProjectRoot "backend"
$FrontendDirectory = Join-Path $ProjectRoot "frontend"
$PythonExecutable = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Failures = [System.Collections.Generic.List[string]]::new()

function Invoke-ProjectCheck {
    param(
        [Parameter(Mandatory)]
        [string]$Name,

        [Parameter(Mandatory)]
        [scriptblock]$Action
    )

    Write-Host ""
    Write-Host "==> $Name" -ForegroundColor Cyan

    try {
        & $Action
        if ($LASTEXITCODE -ne 0) {
            throw "$Name exited with code $LASTEXITCODE."
        }

        Write-Host "PASS: $Name" -ForegroundColor Green
    }
    catch {
        $Failures.Add($Name)
        Write-Host "FAIL: $Name" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
    }
}

if (-not (Test-Path -LiteralPath $PythonExecutable)) {
    Write-Host "Missing Python environment: $PythonExecutable" -ForegroundColor Red
    Write-Host "Create it with: python -m venv .venv" -ForegroundColor Yellow
    exit 2
}

if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
    Write-Host "npm.cmd was not found. Install Node.js before running this script." -ForegroundColor Red
    exit 2
}

if (-not (Test-Path -LiteralPath (Join-Path $FrontendDirectory "node_modules"))) {
    Write-Host "Frontend dependencies are missing." -ForegroundColor Red
    Write-Host "Install them with: Set-Location frontend; npm.cmd ci" -ForegroundColor Yellow
    exit 2
}

Invoke-ProjectCheck "Backend unit and API tests" {
    Push-Location $BackendDirectory
    try {
        & $PythonExecutable -m unittest discover -s ..\tests -v
    }
    finally {
        Pop-Location
    }
}

Invoke-ProjectCheck "Frontend lint" {
    Push-Location $FrontendDirectory
    try {
        & npm.cmd exec -- eslint app next.config.ts
    }
    finally {
        Pop-Location
    }
}

if (-not $SkipFrontendBuild) {
    Invoke-ProjectCheck "Frontend production build" {
        Push-Location $FrontendDirectory
        try {
            & npm.cmd run build
        }
        finally {
            Pop-Location
        }
    }
}

if (Get-Command git -ErrorAction SilentlyContinue) {
    Invoke-ProjectCheck "Git whitespace validation" {
        Push-Location $ProjectRoot
        try {
            & git diff --check
        }
        finally {
            Pop-Location
        }
    }
}

Write-Host ""
if ($Failures.Count -gt 0) {
    Write-Host "Project verification failed:" -ForegroundColor Red
    foreach ($Failure in $Failures) {
        Write-Host "  - $Failure" -ForegroundColor Red
    }
    exit 1
}

Write-Host "All project checks passed." -ForegroundColor Green
exit 0
