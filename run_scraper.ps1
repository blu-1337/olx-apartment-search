# PowerShell script to run OLX scraper
# This script changes to the script directory and runs the scraper

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Run the scraper
python scraper.py

# Check exit code
if ($LASTEXITCODE -ne 0) {
    Write-Host "Scraper encountered an error. Exit code: $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

exit 0

