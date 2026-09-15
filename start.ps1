# Launcher for Multi-Agent Industrial Troubleshooting AI Core Services
$rootDir = $PSScriptRoot
Set-Location -Path $rootDir

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Starting Multi-Agent Industrial Troubleshooting AI       " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Start Python Backend (apps/sense-api on port 8001)
Write-Host "Starting AI Coordination API on http://localhost:8001 ..." -ForegroundColor Green
Start-Process powershell -WorkingDirectory "$rootDir\apps\sense-api" -ArgumentList "-NoExit", "-Command", ".\venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload" -WindowStyle Minimized

# 2. Start Next.js Frontend (apps/portal on port 3004)
Write-Host "Starting Diagnostic Web Portal on http://localhost:3004 ..." -ForegroundColor Green
Start-Process powershell -WorkingDirectory "$rootDir\apps\portal" -ArgumentList "-NoExit", "-Command", "npm run dev -- -p 3004" -WindowStyle Minimized

Write-Host "Waiting 5 seconds for services to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host "Opening Diagnostic Portal: http://localhost:3004" -ForegroundColor Cyan
Start-Process "http://localhost:3004"
Write-Host "Core system running! API docs available at http://localhost:8001/docs" -ForegroundColor Green
