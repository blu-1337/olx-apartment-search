# PowerShell script to set up Windows Task Scheduler for OLX scraper
# Run this script as Administrator to create the scheduled task

param(
    [string]$TaskName = "OLX Apartment Scraper",
    [int]$IntervalMinutes = 10
)

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator', then run this script again." -ForegroundColor Yellow
    exit 1
}

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonPath = (Get-Command python).Source
$scraperScript = Join-Path $scriptPath "scraper.py"
$workingDir = $scriptPath

Write-Host "Setting up scheduled task..." -ForegroundColor Green
Write-Host "Task Name: $TaskName" -ForegroundColor Cyan
Write-Host "Interval: Every $IntervalMinutes minutes" -ForegroundColor Cyan
Write-Host "Python: $pythonPath" -ForegroundColor Cyan
Write-Host "Script: $scraperScript" -ForegroundColor Cyan
Write-Host "Working Directory: $workingDir" -ForegroundColor Cyan
Write-Host ""

# Check if task already exists
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "Task '$TaskName' already exists. Removing it..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Create the action (what to run)
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument "`"$scraperScript`"" -WorkingDirectory $workingDir

# Create the trigger (when to run - every 10 minutes)
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) -RepetitionDuration (New-TimeSpan -Days 365)

# Create settings
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable

# Create the principal (run as current user)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest

# Register the task
try {
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "Runs OLX apartment scraper every $IntervalMinutes minutes to check for new listings and send Telegram notifications" | Out-Null
    Write-Host "✓ Scheduled task created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Task Details:" -ForegroundColor Cyan
    Write-Host "  Name: $TaskName" -ForegroundColor White
    Write-Host "  Runs: Every $IntervalMinutes minutes" -ForegroundColor White
    Write-Host "  Status: Enabled" -ForegroundColor White
    Write-Host ""
    Write-Host "To manage the task:" -ForegroundColor Yellow
    Write-Host "  1. Open Task Scheduler (taskschd.msc)" -ForegroundColor White
    Write-Host "  2. Look for '$TaskName' in the task list" -ForegroundColor White
    Write-Host "  3. Right-click to Enable/Disable/Run/Delete" -ForegroundColor White
    Write-Host ""
    Write-Host "To test the task, right-click it in Task Scheduler and select 'Run'" -ForegroundColor Yellow
} catch {
    Write-Host "Error creating scheduled task: $_" -ForegroundColor Red
    exit 1
}

