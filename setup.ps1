# BidSense one-shot setup + launch (Windows).
# Installs backend + frontend deps, creates .env from the example if missing,
# starts the API in a new window, then runs the frontend in this one.
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

Write-Host "[1/4] Backend dependencies..." -ForegroundColor Cyan
Push-Location "$root\backend"
python -m pip install -r requirements.txt --quiet
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "  Created backend/.env from example (no keys needed for the cached demo)." -ForegroundColor Yellow
}
Pop-Location

Write-Host "[2/4] Frontend dependencies..." -ForegroundColor Cyan
Push-Location "$root\frontend"
npm install --silent
Pop-Location

Write-Host "[3/4] Starting backend on http://localhost:8000 (new window)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command",
    "cd '$root\backend'; python -m uvicorn main:app --port 8000"

Write-Host "[4/4] Starting frontend on http://localhost:3000 ..." -ForegroundColor Cyan
Write-Host "  Demo documents are in demo-assets\ - drag one onto the dropzone." -ForegroundColor Green
Set-Location "$root\frontend"
npm run dev
