# GitHub Actions Setup Guide

This guide explains how to set up the GitHub Actions workflow to run the OLX scraper automatically every 10 minutes.

## Prerequisites

- A GitHub repository with this project
- Telegram bot token and chat ID (see main README.md for instructions)

## Setup Steps

### 1. Add GitHub Secrets

You need to add two secrets to your GitHub repository:

1. Go to your repository on GitHub
2. Click on **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** and add:

   **Secret 1: `TELEGRAM_BOT_TOKEN`**
   - Name: `TELEGRAM_BOT_TOKEN`
   - Value: Your Telegram bot token (from BotFather)

   **Secret 2: `TELEGRAM_CHAT_ID`**
   - Name: `TELEGRAM_CHAT_ID`
   - Value: Your Telegram chat ID

### 2. Enable Workflow

The workflow is already configured in `.github/workflows/scraper.yml`. It will:
- Run automatically every 10 minutes
- Can be manually triggered from the **Actions** tab

### 3. Verify Setup

1. Go to the **Actions** tab in your GitHub repository
2. You should see the "OLX Apartment Scraper" workflow
3. You can manually trigger it by clicking **Run workflow**
4. Check the logs to ensure it runs successfully

## How It Works

1. **Schedule**: The workflow runs every 10 minutes using cron: `*/10 * * * *`
2. **Environment**: Runs on Ubuntu latest with Python 3.11
3. **Dependencies**: Automatically installs packages from `requirements.txt`
4. **Configuration**: Creates `config.json` from GitHub secrets at runtime
5. **Database**: The `listings_db.json` file is committed back to the repository after each run to persist data between runs
6. **Notifications**: Sends Telegram notifications for new listings found

## Manual Trigger

You can manually trigger the workflow at any time:
1. Go to **Actions** tab
2. Select **OLX Apartment Scraper** workflow
3. Click **Run workflow** button
4. Select the branch and click **Run workflow**

## Troubleshooting

### Workflow not running
- Check that the schedule is enabled (GitHub Actions schedules are disabled for inactive repositories)
- Make sure the repository is not archived
- Verify secrets are correctly set

### Authentication errors
- Ensure `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` secrets are set correctly
- Verify your bot token is valid
- Make sure you've sent at least one message to your bot

### Database not updating
- Check workflow logs for errors
- Verify the workflow has write permissions (configured in workflow file)
- Check that `listings_db.json` is not in `.gitignore`

## Notes

- The workflow commits `listings_db.json` back to the repository after each run
- Commit messages include `[skip ci]` to prevent triggering workflows on database updates
- The workflow uses Python 3.11 - ensure your code is compatible
- GitHub Actions provides 2,000 free minutes per month for private repos (unlimited for public repos)

