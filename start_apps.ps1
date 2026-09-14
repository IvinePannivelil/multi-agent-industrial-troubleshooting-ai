# Set location to script's directory
$rootDir = $PSScriptRoot
Set-Location -Path $rootDir

$apps = @(
    @{ name="apps/goose-mart"; port=3000 },
    @{ name="apps/goose-digital"; port=3001 },
    @{ name="apps/goose-elevate"; port=3002 },
    @{ name="apps/hire-my-engineer"; port=3003 },
    @{ name="apps/portal"; port=3004 }
)

foreach ($app in $apps) {
    $name = $app.name
    $port = $app.port
    Write-Host "Starting $name on port $port..."
    Start-Process powershell -WorkingDirectory $rootDir -ArgumentList "-NoExit", "-Command", "`$env:PORT=$port; npm run dev --workspace=$name" -WindowStyle Minimized
}

# Start the Python Coordination Layer (Goose Sense API)
Write-Host "Starting Goose Sense API on port 8001..."
Start-Process powershell -WorkingDirectory $rootDir -ArgumentList "-NoExit", "-Command", "cd apps/sense-api; .\venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload" -WindowStyle Minimized

Write-Host "Waiting 15 seconds for servers to start..."
Start-Sleep -Seconds 15

Write-Host "Opening Chrome..."
Start-Process "chrome" -ArgumentList "http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003", "http://localhost:3004"
Write-Host "Done!"
