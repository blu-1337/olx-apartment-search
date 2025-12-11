"""
Telegram Setup Helper
Helps you get your Telegram bot token and chat ID
"""

import requests
import json
import os


def create_bot():
    """
    Instructions for creating a Telegram bot
    """
    print("=" * 60)
    print("TELEGRAM BOT SETUP INSTRUCTIONS")
    print("=" * 60)
    print("\n1. Open Telegram and search for @BotFather")
    print("2. Send /newbot command to BotFather")
    print("3. Follow the instructions to name your bot")
    print("4. Copy the bot token you receive (looks like: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz)")
    print("\n5. Start a chat with your new bot (search for it by name)")
    print("6. Send any message to your bot (e.g., 'Hello')")
    print("7. Run this script again with your bot token to get your chat ID")
    print("\n" + "=" * 60)


def get_chat_id(bot_token):
    """
    Get chat ID from Telegram bot
    
    Args:
        bot_token: Telegram bot token
    """
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data.get('ok'):
            print(f"Error: {data.get('description', 'Unknown error')}")
            return None
        
        updates = data.get('result', [])
        if not updates:
            print("\n⚠ No messages found. Please:")
            print("  1. Start a chat with your bot")
            print("  2. Send a message to your bot")
            print("  3. Run this script again")
            return None
        
        # Get chat ID from the last message
        last_update = updates[-1]
        message = last_update.get('message', {})
        chat = message.get('chat', {})
        chat_id = chat.get('id')
        
        if chat_id:
            print(f"\n✓ Your Chat ID: {chat_id}")
            return str(chat_id)
        else:
            print("Could not find chat ID in updates")
            return None
            
    except requests.RequestException as e:
        print(f"Error connecting to Telegram API: {e}")
        return None


def create_config_file(bot_token, chat_id):
    """
    Create config.json file with Telegram credentials
    
    Args:
        bot_token: Telegram bot token
        chat_id: Telegram chat ID
    """
    config = {
        "telegram_bot_token": bot_token,
        "telegram_chat_id": chat_id
    }
    
    config_file = "config.json"
    
    # Check if config.json already exists
    if os.path.exists(config_file):
        response = input(f"\n{config_file} already exists. Overwrite? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled.")
            return False
    
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        print(f"\n✓ Configuration saved to {config_file}")
        print("⚠ Keep this file secure and don't share it!")
        return True
    except Exception as e:
        print(f"Error creating config file: {e}")
        return False


if __name__ == "__main__":
    print("\nTelegram Setup Helper\n")
    
    # Check if config already exists
    if os.path.exists("config.json"):
        print("⚠ config.json already exists.")
        response = input("Do you want to set up a new configuration? (y/n): ")
        if response.lower() != 'y':
            print("Exiting.")
            exit(0)
    
    # Show instructions
    create_bot()
    
    # Get bot token
    bot_token = input("\nEnter your bot token (or press Enter to skip): ").strip()
    
    if not bot_token:
        print("Skipping setup.")
        exit(0)
    
    # Get chat ID
    print("\nFetching your chat ID...")
    chat_id = get_chat_id(bot_token)
    
    if chat_id:
        # Create config file
        create_config_file(bot_token, chat_id)
        print("\n✓ Setup complete! You can now run scraper.py")
    else:
        print("\n✗ Setup incomplete. Please try again.")

