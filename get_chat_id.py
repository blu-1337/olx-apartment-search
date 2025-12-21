"""
Quick script to get your Telegram Chat ID using your bot token
"""

import requests
import json
import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Your bot token
BOT_TOKEN = "8252139378:AAHWUJHNe8K8eEkL5zOMse7TBA93aD3J3HE"

def get_chat_id():
    """Get chat ID from Telegram bot"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    
    print("Fetching your chat ID...")
    print("\n⚠ Make sure you've:")
    print("  1. Started a chat with your bot")
    print("  2. Sent at least one message to your bot")
    print()
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data.get('ok'):
            print(f"❌ Error: {data.get('description', 'Unknown error')}")
            return None
        
        updates = data.get('result', [])
        if not updates:
            print("❌ No messages found!")
            print("\nPlease:")
            print("  1. Open Telegram")
            print("  2. Search for your bot")
            print("  3. Start a chat and send a message (e.g., 'Hello')")
            print("  4. Run this script again")
            return None
        
        # Get chat ID from the last message
        last_update = updates[-1]
        message = last_update.get('message', {})
        chat = message.get('chat', {})
        chat_id = chat.get('id')
        chat_username = chat.get('username', 'N/A')
        chat_first_name = chat.get('first_name', 'N/A')
        
        if chat_id:
            print(f"✓ Found your chat!")
            print(f"  Name: {chat_first_name}")
            print(f"  Username: @{chat_username}")
            print(f"  Chat ID: {chat_id}")
            print()
            
            # Create config.json
            config = {
                "telegram_bot_token": BOT_TOKEN,
                "telegram_chat_id": str(chat_id)
            }
            
            try:
                with open("config.json", 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2)
                print("✓ Created config.json successfully!")
                print("✓ Setup complete! You can now run: python scraper.py")
                return str(chat_id)
            except Exception as e:
                print(f"❌ Error creating config.json: {e}")
                print(f"\nManually create config.json with:")
                print(f'  "telegram_bot_token": "{BOT_TOKEN}"')
                print(f'  "telegram_chat_id": "{chat_id}"')
                return str(chat_id)
        else:
            print("❌ Could not find chat ID in updates")
            return None
            
    except requests.RequestException as e:
        print(f"❌ Error connecting to Telegram API: {e}")
        print("\nCheck your internet connection and try again.")
        return None

if __name__ == "__main__":
    get_chat_id()

