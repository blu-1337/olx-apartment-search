"""
Telegram Bot Notifier
Sends notifications to Telegram about new apartment listings
"""

import requests
from typing import List, Dict, Optional
import os
import time


class TelegramNotifier:
    """Handles sending notifications via Telegram Bot API"""
    
    def __init__(self, bot_token: str, chat_id: str):
        """
        Initialize Telegram notifier
        
        Args:
            bot_token: Telegram bot token from BotFather
            chat_id: Telegram chat ID to send messages to
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send_message(self, text: str, parse_mode: str = "HTML", retries: int = 3) -> bool:
        """
        Send a text message to Telegram with retry logic
        
        Args:
            text: Message text to send
            parse_mode: Parse mode (HTML or Markdown)
            retries: Number of retry attempts
            
        Returns:
            True if successful, False otherwise
        """
        url = f"{self.api_url}/sendMessage"
        payload = {
            'chat_id': self.chat_id,
            'text': text,
            'parse_mode': parse_mode
        }
        
        for attempt in range(retries):
            try:
                response = requests.post(url, json=payload, timeout=10)
                
                # Check for rate limiting (429 Too Many Requests)
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    print(f"Rate limited. Waiting {retry_after} seconds before retry...")
                    time.sleep(retry_after)
                    continue
                
                response.raise_for_status()
                return True
            except requests.RequestException as e:
                if attempt < retries - 1:
                    wait_time = (attempt + 1) * 2  # Exponential backoff: 2s, 4s, 6s
                    print(f"Error sending Telegram message (attempt {attempt + 1}/{retries}): {e}")
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"Error sending Telegram message after {retries} attempts: {e}")
                    return False
        
        return False
    
    def format_listing_message(self, listing: Dict) -> str:
        """
        Format a single listing as HTML message
        
        Args:
            listing: Dictionary containing listing data
            
        Returns:
            Formatted HTML message string
        """
        title = listing.get('title', 'N/A')
        price = listing.get('price', 0)
        link = listing.get('link', '#')
        description = listing.get('description') or 'No description available'
        floor = listing.get('floor')
        lift = listing.get('lift')
        
        # Truncate description if too long (handle None case)
        if description and len(description) > 500:
            description = description[:500] + "..."
        
        # Build floor and lift info lines
        info_lines = []
        if floor:
            info_lines.append(f"🏢 <b>Floor:</b> {floor}")
        if lift:
            lift_emoji = "✅" if lift == "Yes" else "❌"
            info_lines.append(f"{lift_emoji} <b>Lift:</b> {lift}")
        
        info_section = "\n".join(info_lines)
        if info_section:
            info_section = info_section + "\n"
        
        message = f"""
<b>🏠 {title}</b>

💰 <b>Price:</b> {price}€
{info_section}🔗 <a href="{link}">View Listing</a>

📝 <b>Description:</b>
{description}
"""
        return message.strip()
    
    def send_listings(self, listings: List[Dict]) -> bool:
        """
        Send multiple listings as separate messages
        
        Args:
            listings: List of listing dictionaries
            
        Returns:
            True if all messages sent successfully, False otherwise
        """
        if not listings:
            return True
        
        success = True
        
        # Send summary first
        summary = f"🔔 <b>Found {len(listings)} new listing(s)!</b>\n"
        if not self.send_message(summary):
            success = False
        
        # Send each listing with delays to avoid rate limiting
        for idx, listing in enumerate(listings):
            message = self.format_listing_message(listing)
            
            print(f"Sending listing {idx + 1}/{len(listings)}: {listing.get('title', 'N/A')[:50]}...")
            
            # Send text message
            if not self.send_message(message):
                print(f"  ✗ Failed to send listing {idx + 1}")
                success = False
            else:
                print(f"  ✓ Sent successfully")
            
            # Add delay between listings to avoid rate limiting (Telegram limit: ~20 messages/minute)
            # Wait 3 seconds between listings to stay well under the limit
            if idx < len(listings) - 1:  # Don't wait after the last listing
                time.sleep(3)
        
        return success
    
    @staticmethod
    def get_chat_id(bot_token: str) -> Optional[str]:
        """
        Helper method to get chat ID by sending a message to the bot first
        This is a one-time setup step
        
        Args:
            bot_token: Telegram bot token
            
        Returns:
            Chat ID if found, None otherwise
        """
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('ok') and data.get('result'):
                # Get the last update
                updates = data['result']
                if updates:
                    last_update = updates[-1]
                    chat_id = last_update.get('message', {}).get('chat', {}).get('id')
                    return str(chat_id) if chat_id else None
        except Exception as e:
            print(f"Error getting chat ID: {e}")
        
        return None

