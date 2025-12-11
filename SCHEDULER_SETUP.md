# Windows Task Scheduler Setup Guide

This guide will help you set up the OLX scraper to run automatically every 10 minutes on Windows.

## Method 1: Automated Setup (Recommended)

1. **Open PowerShell as Administrator**:
   - Press `Win + X`
   - Select "Windows PowerShell (Admin)" or "Terminal (Admin)"
   - Click "Yes" when prompted by UAC

2. **Navigate to the project directory**:
   ```powershell
   cd G:\work\olx-apartment-search
   ```

3. **Run the setup script**:
   ```powershell
   .\setup_scheduler.ps1
   ```

   To customize the interval (default is 10 minutes):
   ```powershell
   .\setup_scheduler.ps1 -IntervalMinutes 15
   ```

4. **Verify the task was created**:
   - Open Task Scheduler (`Win + R`, type `taskschd.msc`)
   - Look for "OLX Apartment Scraper" in the task list
   - Right-click and select "Run" to test it immediately

## Method 2: Manual Setup via Task Scheduler GUI

1. **Open Task Scheduler**:
   - Press `Win + R`
   - Type `taskschd.msc` and press Enter

2. **Create Basic Task**:
   - Click "Create Basic Task" in the right panel
   - Name: `OLX Apartment Scraper`
   - Description: `Runs OLX apartment scraper every 10 minutes`

3. **Set Trigger**:
   - Select "When the computer starts" (or "When I log on")
   - Click Next
   - Check "Repeat task every: 10 minutes"
   - Duration: "Indefinitely" or set an end date
   - Click Next

4. **Set Action**:
   - Select "Start a program"
   - Program/script: Browse and find `python.exe` (usually in `C:\Users\YourName\AppData\Local\Programs\Python\Python3XX\python.exe` or `C:\Python3XX\python.exe`)
   - Add arguments: `scraper.py`
   - Start in: `G:\work\olx-apartment-search`
   - Click Next

5. **Finish**:
   - Review settings
   - Check "Open the Properties dialog for this task when I click Finish"
   - Click Finish

6. **Configure Advanced Settings**:
   - In Properties dialog:
     - **General tab**: Check "Run whether user is logged on or not" and "Run with highest privileges"
     - **Conditions tab**: 
       - Uncheck "Start the task only if the computer is on AC power"
       - Check "Start the task only if the following network connection is available"
     - **Settings tab**:
       - Check "Allow task to be run on demand"
       - Check "Run task as soon as possible after a scheduled start is missed"
   - Click OK

## Method 3: Using Command Line (schtasks)

Open Command Prompt or PowerShell as Administrator and run:

```cmd
schtasks /create /tn "OLX Apartment Scraper" /tr "python G:\work\olx-apartment-search\scraper.py" /sc minute /mo 10 /ru SYSTEM /rl HIGHEST /f
```

Note: This runs as SYSTEM user. To run as your user, use:
```cmd
schtasks /create /tn "OLX Apartment Scraper" /tr "python G:\work\olx-apartment-search\scraper.py" /sc minute /mo 10 /ru "%USERNAME%" /rl HIGHEST /f
```

## Verifying the Task

1. **Check Task Status**:
   - Open Task Scheduler
   - Find "OLX Apartment Scraper"
   - Check the "Status" column (should show "Ready")

2. **Test Run**:
   - Right-click the task
   - Select "Run"
   - Check "Last Run Result" - should show "(0x0)" for success

3. **View History**:
   - Right-click the task → "History"
   - Check for any errors

## Troubleshooting

### Task doesn't run
- **Check Python path**: Make sure Python is in your system PATH, or use full path in the task
- **Check working directory**: Ensure "Start in" is set to the project directory
- **Check permissions**: Task should run with highest privileges
- **Check logs**: View Task Scheduler History tab for error messages

### Python not found
- Use full path to python.exe in the task action
- Example: `C:\Users\YourName\AppData\Local\Programs\Python\Python314\python.exe`

### Script errors
- Test the script manually first: `python scraper.py`
- Check that `config.json` exists and is properly configured
- Ensure all dependencies are installed: `pip install -r requirements.txt`

### Task runs but no notifications
- Check that Telegram bot token and chat ID are correct in `config.json`
- Verify internet connection
- Check Task Scheduler History for script errors
- Run the script manually to see output

## Disabling/Removing the Task

### To Disable:
- Open Task Scheduler
- Find "OLX Apartment Scraper"
- Right-click → "Disable"

### To Delete:
- Open Task Scheduler
- Find "OLX Apartment Scraper"
- Right-click → "Delete"

Or use PowerShell:
```powershell
Unregister-ScheduledTask -TaskName "OLX Apartment Scraper" -Confirm:$false
```

## Changing the Interval

1. Open Task Scheduler
2. Find "OLX Apartment Scraper"
3. Right-click → "Properties"
4. Go to "Triggers" tab
5. Select the trigger → "Edit"
6. Change "Repeat task every" to desired interval
7. Click OK

Or use the setup script again with a different interval:
```powershell
.\setup_scheduler.ps1 -IntervalMinutes 15
```

