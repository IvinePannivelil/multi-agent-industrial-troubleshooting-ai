# Set location to script's directory
$rootDir = $PSScriptRoot
Set-Location -Path $rootDir

# Forward to the core service launcher
& "$rootDir\start.ps1"
