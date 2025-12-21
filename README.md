# OLX Apartment Search Scraper

A Python application that automatically monitors OLX.ro for apartment rentals in Craiova, filters listings by price and description, and sends Telegram notifications for new listings.

## Features

- 🔍 Scrapes three OLX search pages for apartments and houses in Craiova
- 💰 Filters listings by maximum price (500€)
- 🚫 Excludes short-term rentals (detects keywords like "regim hotelier", "pe noapte", etc.)
- 📱 Sends Telegram notifications for new listings
- 💾 Tracks sent listings in a JSON database to avoid duplicates
- 🇷🇴 Supports Romanian language keywords

## Requirements

- Python 3.7+
- Internet connection
- Telegram bot token and chat ID

## Installation

1. Install required packages:
```bash
pip install -r requirements.txt
```

2. Set up Telegram bot:
   - Run the setup helper:
   ```bash
   python setup_telegram.py
   ```
   - Follow the instructions to create a bot and get your chat ID
   - Or manually create `config.json` based on `config.json.example`

## Configuration

Create a `config.json` file with your Telegram credentials:

```json
{
  "telegram_bot_token": "YOUR_BOT_TOKEN_HERE",
  "telegram_chat_id": "YOUR_CHAT_ID_HERE"
}
```

### Getting Telegram Bot Token

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow instructions to name your bot
4. Copy the bot token you receive

### Getting Chat ID

1. Start a chat with your bot (search for it by name)
2. Send any message to your bot
3. Run `python setup_telegram.py` - it will automatically detect your chat ID
4. Or visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates` and find the chat ID in the response

## Usage

Run the scraper:

```bash
python scraper.py
```

The script will:
1. Fetch listings from all three OLX URLs
2. Filter by price (≤ 500€)
3. Check descriptions for short-term rental keywords
4. Compare with existing database
5. Send Telegram notifications for new listings
6. Update the database

## Monitored URLs

The scraper monitors these three OLX search pages:
- 4-room apartments in Craiova (sorted by price ascending)
- 3-room apartments in Craiova (sorted by price ascending)
- Houses for rent in Craiova (sorted by price ascending)

## Database

Listings are stored in `listings_db.json` to prevent duplicate notifications. Each listing includes:
- Title
- Price
- Link
- Description
- Timestamp when first found

## Short-term Rental Keywords

The following Romanian keywords are detected to filter out short-term rentals:
- "regim hotelier"
- "pe noapte"
- "pe zi"
- "pe săptămână"
- "pe weekend"
- "temporar"
- "scurtă perioadă"
- "cazare"
- "hotel"
- "airbnb"

## Automation

To run automatically, you can set up a cron job (Linux/Mac) or Task Scheduler (Windows):

### Windows Task Scheduler
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., daily at 9 AM)
4. Action: Start a program
5. Program: `python`
6. Arguments: `G:\work\olx-apartment-search\scraper.py`
7. Start in: `G:\work\olx-apartment-search`

### Linux/Mac Cron
```bash
# Run every day at 9 AM
0 9 * * * cd /path/to/olx-apartment-search && python scraper.py
```

## Files

- `scraper.py` - Main scraping script
- `telegram_notifier.py` - Telegram notification handler
- `setup_telegram.py` - Helper script for Telegram setup
- `config.json` - Configuration file (create from config.json.example)
- `listings_db.json` - Database of processed listings (auto-created)
- `requirements.txt` - Python dependencies

## Notes

- The scraper only checks the first page of results (as requested)
- Listings are already sorted by price (ascending) on OLX
- The script includes error handling and will continue even if some listings fail
- Telegram notifications include formatted HTML messages with listing details

## Troubleshooting

**No notifications received:**
- Check that `config.json` exists and contains valid credentials
- Verify bot token and chat ID are correct
- Make sure you've sent at least one message to your bot

**Scraping errors:**
- Check your internet connection
- OLX website structure may have changed - check the HTML selectors
- Some listings may fail silently - check console output

**Database issues:**
- If `listings_db.json` becomes corrupted, you can delete it and start fresh
- The file is automatically created on first run

