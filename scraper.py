"""
Apartment Search Scraper
Fetches apartment listings from OLX.ro and Publi24.ro, filters by price and description,
and sends notifications via Telegram for new listings.
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import re
from typing import List, Dict, Optional
from datetime import datetime


class OLXScraper:
    """Main scraper class for OLX apartment listings"""
    
    # URLs to scrape
    URLS = [
        "https://www.olx.ro/imobiliare/apartamente-garsoniere-de-inchiriat/4-camere/craiova/?currency=EUR&search%5Border%5D=filter_float_price:asc",
        "https://www.olx.ro/imobiliare/apartamente-garsoniere-de-inchiriat/3-camere/craiova/?currency=EUR&search%5Border%5D=filter_float_price%3Aasc",
        "https://www.olx.ro/imobiliare/case-de-inchiriat/craiova/?currency=EUR&search%5Border%5D=filter_float_price%3Aasc"
    ]
    
    # Keywords that indicate short-term rental (Romanian)
    SHORT_TERM_KEYWORDS = [
        "regim hotelier",
        "pe noapte",
        "pe zi",
        "pe săptămână",
        "pe săptămâna",
        "pe weekend",
        "temporar",
        "scurtă perioadă",
        "scurta perioada",
        "cazare",
        "hotel",
        "airbnb",
        "targ de craciun",
        "târg crăciun",
        "targ craciun",
        "târgul de crăciun",
        "targul de craciun",
        "perioada targului",
        "perioada târgului",
        "perioada targului de craciun",
        "perioada târgului de crăciun",
        "perioada targului de crăciun",
        "perioada târgului de craciun",
        "pentru targ",
        "pentru târg",
        "pentru targ de craciun",
        "pentru târg de crăciun",
        "in perioada targului",
        "în perioada târgului",
        "în perioada targului",
        "durata targului",
        "durata târgului",
        "timpul targului",
        "spațiu comercial",
        "spatiu comercial",
        "timpul târgului"
    ]
    
    # Minimum price threshold in EUR
    MIN_PRICE = 100
    
    # Maximum price threshold in EUR
    MAX_PRICE = 500
    
    # Database file path
    DB_FILE = "listings_db.json"
    
    # Global debug flag - set to True to enable debug output
    DEBUG_ENABLED = False
    
    def __init__(self):
        """Initialize the scraper"""
        self.session = requests.Session()
        # Set user agent to avoid blocking
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.listings = []
    
    @classmethod
    def enable_debug(cls, enabled: bool = True):
        """
        Enable or disable debug output
        
        Args:
            enabled: True to enable debug output, False to disable
        """
        cls.DEBUG_ENABLED = enabled
        status = "enabled" if enabled else "disabled"
        print(f"Debug mode {status}")
    
    def _debug(self, message: str):
        """
        Print debug message if debug is enabled
        
        Args:
            message: Debug message to print
        """
        if self.DEBUG_ENABLED:
            print(message)
    
    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch a webpage and return BeautifulSoup object
        
        Args:
            url: URL to fetch
            
        Returns:
            BeautifulSoup object or None if request fails
        """
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def extract_price(self, price_element) -> Optional[float]:
        """
        Extract price from price element and convert to float
        
        Args:
            price_element: BeautifulSoup element containing price
            
        Returns:
            Price as float or None if extraction fails
        """
        if not price_element:
            return None
        
        # Get text and extract numbers
        price_text = price_element.get_text(strip=True)
        
        # Remove currency symbols (€, EUR, lei, etc.) and other non-numeric characters except digits, spaces, dots, and commas
        # Keep spaces, dots, and commas for number parsing
        price_text = re.sub(r'[^\d\s.,]', '', price_text)
        
        # Remove all spaces (handles "1 400" -> "1400")
        price_text = price_text.replace(' ', '')
        
        # Handle European number format (1.400,50) vs US format (1,400.50)
        # If there's a comma followed by 2 digits at the end, it's likely decimal separator
        # Otherwise, dots/commas are thousands separators
        if re.search(r',\d{2}$', price_text):
            # European format: 1.400,50 -> 1400.50
            price_text = price_text.replace('.', '').replace(',', '.')
        else:
            # Remove dots and commas (they're thousands separators)
            # Handle both 1.400 and 1,400 formats
            price_text = price_text.replace('.', '').replace(',', '')
        
        # Extract the number
        price_match = re.search(r'(\d+(?:\.\d+)?)', price_text)
        
        if price_match:
            try:
                return float(price_match.group(1))
            except ValueError:
                return None
        return None
    
    def extract_listings_from_page(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Extract listings from a single page
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            List of dictionaries containing listing data
        """
        listings = []
        
        # Find all listing cards
        listing_cards = soup.find_all('div', {'data-cy': 'l-card'})
        
        for card in listing_cards:
            try:
                # Extract title from h4 element
                title_element = card.find('h4')
                if not title_element:
                    continue
                title = title_element.get_text(strip=True)
                
                # Extract price from p element with data-testid="ad-price"
                price_element = card.find('p', {'data-testid': 'ad-price'})
                price = self.extract_price(price_element)
                
                if price is None:
                    continue
                
                # Extract link from a element
                link_element = card.find('a', href=True)
                if not link_element:
                    continue
                
                # Make sure link is absolute
                link = link_element['href']
                if link.startswith('/'):
                    link = f"https://www.olx.ro{link}"
                
                listings.append({
                    'title': title,
                    'price': price,
                    'link': link,
                    'description': None  # Will be filled later
                })
            except Exception as e:
                print(f"Error extracting listing: {e}")
                continue
        
        return listings
    
    def filter_by_price(self, listings: List[Dict]) -> List[Dict]:
        """
        Filter listings by price range (MIN_PRICE <= price <= MAX_PRICE)
        
        Args:
            listings: List of listing dictionaries
            
        Returns:
            Filtered list with prices between MIN_PRICE and MAX_PRICE
        """
        return [
            listing for listing in listings 
            if self.MIN_PRICE <= listing['price'] <= self.MAX_PRICE
        ]
    
    def fetch_description(self, link: str) -> Optional[str]:
        """
        Fetch description from listing detail page
        
        Args:
            link: URL of the listing detail page
            
        Returns:
            Description text or None if extraction fails
        """
        self._debug(f"  [DEBUG] Fetching description from: {link}")
        soup = self.fetch_page(link)
        if not soup:
            self._debug(f"  [DEBUG] Failed to fetch page")
            return None
        
        self._debug(f"  [DEBUG] Page fetched successfully")
        
        try:
            # Method 1: Look for the full description div (data-cy="adPageAdDescription")
            # This contains the complete description even if it's hidden behind "Mai mult" button
            desc_div = soup.find('div', {'data-cy': 'adPageAdDescription'})
            self._debug(f"  [DEBUG] Method 1: Found div[data-cy='adPageAdDescription']: {desc_div is not None}")
            if desc_div:
                # Try to get text from span inside the div first
                desc_span = desc_div.find('span')
                self._debug(f"  [DEBUG] Method 1: Found span inside div: {desc_span is not None}")
                if desc_span:
                    # Get all text, preserving paragraph structure
                    desc_text = desc_span.get_text(separator='\n', strip=True)
                    self._debug(f"  [DEBUG] Method 1: Text from span (\\n): '{desc_text[:100] if desc_text else 'None'}...' (length: {len(desc_text) if desc_text else 0})")
                    # If that doesn't work, try with space separator
                    if not desc_text or len(desc_text.strip()) < 10:
                        desc_text = desc_span.get_text(separator=' ', strip=True)
                        self._debug(f"  [DEBUG] Method 1: Text from span (space): '{desc_text[:100] if desc_text else 'None'}...' (length: {len(desc_text) if desc_text else 0})")
                else:
                    # If no span, get text directly from div
                    desc_text = desc_div.get_text(separator='\n', strip=True)
                    self._debug(f"  [DEBUG] Method 1: Text from div (\\n): '{desc_text[:100] if desc_text else 'None'}...' (length: {len(desc_text) if desc_text else 0})")
                    if not desc_text or len(desc_text.strip()) < 10:
                        desc_text = desc_div.get_text(separator=' ', strip=True)
                        self._debug(f"  [DEBUG] Method 1: Text from div (space): '{desc_text[:100] if desc_text else 'None'}...' (length: {len(desc_text) if desc_text else 0})")
                
                if desc_text:
                    # Clean HTML tags and normalize whitespace
                    desc_text = self._clean_description(desc_text)
                    self._debug(f"  [DEBUG] Method 1: After cleaning: '{desc_text[:100] if desc_text else 'None'}...' (length: {len(desc_text) if desc_text else 0})")
                    # Filter out button text and other non-description content
                    if desc_text and len(desc_text.strip()) > 10:
                        desc_lower = desc_text.lower()
                        if desc_lower not in ['mai mult', 'mai mult...', 'show more', 'vezi mai mult', 'raportează', 'raporteaza']:
                            # Remove any remaining button text
                            desc_text = re.sub(r'(?i)\s*mai\s*mult\s*\.?\.?\.?\s*$', '', desc_text).strip()
                            desc_text = re.sub(r'(?i)^mai\s*mult\s*\.?\.?\.?\s*', '', desc_text).strip()
                            if desc_text and len(desc_text.strip()) > 10:
                                self._debug(f"  [DEBUG] Method 1: SUCCESS - Returning description")
                                return desc_text
                        else:
                            self._debug(f"  [DEBUG] Method 1: Filtered out (button text detected)")
                    else:
                        self._debug(f"  [DEBUG] Method 1: Text too short after cleaning")
                else:
                    self._debug(f"  [DEBUG] Method 1: No text extracted")
            
            # Method 2: Find the Descriere heading and look for description nearby
            desc_heading = soup.find('h2', {'data-sentry-source-file': 'AdDescription.tsx'}, string=re.compile('Descriere'))
            self._debug(f"  [DEBUG] Method 2: Found h2[data-sentry-source-file='AdDescription.tsx']: {desc_heading is not None}")
            
            if not desc_heading:
                # Try alternative search
                desc_heading = soup.find('h2', string=re.compile('Descriere', re.I))
                self._debug(f"  [DEBUG] Method 2: Found h2 with 'Descriere' text: {desc_heading is not None}")
            
            if desc_heading:
                # Find the parent container
                parent = desc_heading.parent
                if parent:
                    # Look for div with data-cy="adPageAdDescription" in the same section
                    desc_div = parent.find('div', {'data-cy': 'adPageAdDescription'})
                    if desc_div:
                        desc_span = desc_div.find('span')
                        if desc_span:
                            desc_text = desc_span.get_text(separator='\n', strip=True)
                            if not desc_text or len(desc_text.strip()) < 10:
                                desc_text = desc_span.get_text(separator=' ', strip=True)
                        else:
                            desc_text = desc_div.get_text(separator='\n', strip=True)
                            if not desc_text or len(desc_text.strip()) < 10:
                                desc_text = desc_div.get_text(separator=' ', strip=True)
                        
                        if desc_text:
                            desc_text = self._clean_description(desc_text)
                            if desc_text and len(desc_text.strip()) > 10:
                                desc_lower = desc_text.lower()
                                if desc_lower not in ['mai mult', 'mai mult...', 'show more', 'vezi mai mult', 'raportează', 'raporteaza']:
                                    desc_text = re.sub(r'(?i)\s*mai\s*mult\s*\.?\.?\.?\s*$', '', desc_text).strip()
                                    desc_text = re.sub(r'(?i)^mai\s*mult\s*\.?\.?\.?\s*', '', desc_text).strip()
                                    if desc_text and len(desc_text.strip()) > 10:
                                        return desc_text
                    
                    # Fallback: Look for div with data-cy="ad_description"
                    desc_div = parent.find('div', {'data-cy': 'ad_description'})
                    if desc_div:
                        desc_text = desc_div.get_text(strip=True)
                        # Check if it's just "Mai Mult" button text
                        if desc_text.lower() not in ['mai mult', 'mai mult...', 'show more', 'vezi mai mult']:
                            desc_text = self._clean_description(desc_text)
                            return desc_text if desc_text else None
            
            # Method 3: Fallback - search for description in common locations
            desc_div = soup.find('div', {'data-cy': 'ad_description'})
            self._debug(f"  [DEBUG] Method 3: Found div[data-cy='ad_description']: {desc_div is not None}")
            if desc_div:
                desc_text = desc_div.get_text(strip=True)
                self._debug(f"  [DEBUG] Method 3: Text extracted: '{desc_text[:100] if desc_text else 'None'}...'")
                # Check if it's just "Mai Mult"
                if desc_text.lower() not in ['mai mult', 'mai mult...', 'show more', 'vezi mai mult']:
                    desc_text = self._clean_description(desc_text)
                    self._debug(f"  [DEBUG] Method 3: After cleaning: '{desc_text[:100] if desc_text else 'None'}...'")
                    if desc_text:
                        self._debug(f"  [DEBUG] Method 3: SUCCESS - Returning description")
                        return desc_text
            
        except Exception as e:
            self._debug(f"  [DEBUG] ERROR extracting description from {link}: {e}")
            if self.DEBUG_ENABLED:
                import traceback
                traceback.print_exc()
        
        print(f"  -> Warning: Could not extract description from {link}")
        return None
    
    def _clean_description(self, description: str) -> str:
        """
        Clean description text by removing unwanted prefixes and fixing formatting
        Also handles HTML tags like <br> by converting them to newlines
        
        Args:
            description: Raw description text (may contain HTML)
            
        Returns:
            Cleaned description text
        """
        if not description:
            return ""
        
        # Convert HTML line breaks to newlines
        description = re.sub(r'<br\s*/?>', '\n', description, flags=re.IGNORECASE)
        description = re.sub(r'<br\s+[^>]*>', '\n', description, flags=re.IGNORECASE)
        
        # Remove other HTML tags (but keep the text content)
        description = re.sub(r'<[^>]+>', '', description)
        
        # Remove "Descriere" prefix (case-insensitive, with or without space)
        description = re.sub(r'(?i)^descriere\s+', '', description)
        
        # Remove "Descriere" if it appears at the start without proper spacing
        # Handle cases like "DescriereApartament" -> "Apartament"
        description = re.sub(r'(?i)^descriere(?=[A-ZĂÂÎȘȚăâîșț])', '', description)
        
        # Clean up multiple spaces and normalize whitespace
        description = re.sub(r'[ \t]+', ' ', description)  # Multiple spaces/tabs to single space
        description = re.sub(r'\n\s*\n', '\n\n', description)  # Multiple newlines to double newline
        description = description.strip()
        
        return description
    
    def is_short_term_rental(self, text: str) -> bool:
        """
        Check if text contains short-term rental keywords
        
        Args:
            text: Text to check (can be title or description)
            
        Returns:
            True if short-term rental keywords found, False otherwise
        """
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Check for any short-term keywords
        for keyword in self.SHORT_TERM_KEYWORDS:
            if keyword.lower() in text_lower:
                return True
        
        return False
    
    def extract_floor_info(self, title: str, description: str = "") -> Optional[str]:
        """
        Extract floor information from title and description
        Looks for patterns like "et 4/4", "etaj 1/4", "et.2/4", "etajul 7", etc.
        
        Args:
            title: Listing title
            description: Listing description (optional)
            
        Returns:
            Floor information string (e.g., "4/4", "7/?") or None if not found
        """
        text = f"{title} {description}".lower()
        
        # Patterns to match floor information (ordered by specificity)
        patterns = [
            # Full patterns with both floor and total: "et 4/4", "etaj 1/4", "etajul 3/5"
            r'et(?:aj)?(?:ul)?\s*(\d+)\s*/\s*(\d+)',  # "et 4/4", "etaj 1/4", "etajul 3/5"
            r'et\.\s*(\d+)\s*/\s*(\d+)',  # "et. 2/4"
            r'etaj\s*(\d+)\s*din\s*(\d+)',  # "etaj 1 din 4"
            r'et\.\s*(\d+)\s*din\s*(\d+)',  # "et. 2 din 4"
            r'(\d+)\s*/\s*(\d+)\s*etaj',  # "4/4 etaj"
            # Pattern: "etajul X al unui bloc cu Y etaje"
            r'etajul\s*(\d+)\s*al\s*unui\s*bloc\s*cu\s*(\d+)\s*etaje',
            # Standalone X/Y pattern - only match reasonable floor numbers (1-20)
            r'(?:^|[\s,.-])([1-9]|1[0-9]|20)\s*/\s*([1-9]|1[0-9]|20)(?:\s|$|,|\.|mp)',  # "5/6" standalone
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                floor = match.group(1)
                total_floors = match.group(2)
                return f"{floor}/{total_floors}"
        
        # Try to find single floor numbers: "etaj 1", "etajul 7", "et 2", "et.2"
        single_floor_patterns = [
            r'etajul\s+(\d+)',  # "etajul 7"
            r'etaj\s+(\d+)',  # "etaj 1"
            r'\bet\s+(\d+)',  # "et 2"
            r'\bet\.\s*(\d+)',  # "et.2"
            r'la\s+etajul\s+(\d+)',  # "la etajul 1"
            r'etajul\s+(\d+)\s+al',  # "etajul 2 al"
        ]
        
        for pattern in single_floor_patterns:
            match = re.search(pattern, text)
            if match:
                floor = match.group(1)
                # Try to find total floors in the same text
                total_match = re.search(r'(?:bloc|imobil|cladire).*?(?:cu\s+)?(\d+)\s+etaje?', text)
                if total_match:
                    total_floors = total_match.group(1)
                    return f"{floor}/{total_floors}"
                else:
                    # Return just the floor number if total not found
                    return f"{floor}/?"
        
        # Special case: "etaj intermediar" (middle floor)
        if 'etaj intermediar' in text:
            # Try to find total floors
            total_match = re.search(r'(?:bloc|imobil|cladire).*?(?:cu\s+)?(\d+)\s+etaje?', text)
            if total_match:
                total_floors = int(total_match.group(1))
                # Approximate middle floor
                middle_floor = str(max(1, total_floors // 2))
                return f"{middle_floor}/{total_floors} (intermediar)"
            return "intermediar"
        
        return None
    
    def extract_lift_info(self, title: str, description: str = "") -> Optional[str]:
        """
        Extract lift/elevator information from title and description
        Looks for keywords like "lift", "ascensor", "elevator", etc.
        
        Args:
            title: Listing title
            description: Listing description (optional)
            
        Returns:
            "Yes" if lift found, "No" if explicitly mentioned as absent, None if not mentioned
        """
        text = f"{title} {description}".lower()
        
        # Keywords indicating presence of lift (more comprehensive)
        lift_keywords = [
            'lift',
            'ascensor',
            'elevator',
            'ascensoare',
            'cu lift',
            'bloc cu lift',
            'are lift',
            'lift nou',
            'cu ascensor',
            'bloc cu ascensor',
            'are ascensor',
            'ascensor nou',
            'dotat cu lift',
            'dotat cu ascensor',
            'prevazut cu lift',
            'prevazut cu ascensor',
            'dispunand de lift',
            'dispunand de ascensor'
        ]
        
        # Keywords indicating absence of lift
        no_lift_keywords = [
            'fara lift',
            'fără lift',
            'nu are lift',
            'fara ascensor',
            'fără ascensor',
            'nu are ascensor',
            'fara ascensoare',
            'fără ascensoare',
            'bloc fara lift',
            'bloc fără lift'
        ]
        
        # Check for absence first
        for keyword in no_lift_keywords:
            if keyword in text:
                return "No"
        
        # Check for presence
        for keyword in lift_keywords:
            if keyword in text:
                return "Yes"
        
        return None
    
    def process_listings(self) -> List[Dict]:
        """
        Main method to process all listings from all URLs
        
        Returns:
            List of processed listing dictionaries
        """
        all_listings = []
        
        # Fetch listings from all URLs
        for url in self.URLS:
            print(f"Fetching listings from: {url}")
            soup = self.fetch_page(url)
            
            if soup:
                listings = self.extract_listings_from_page(soup)
                print(f"Found {len(listings)} listings")
                all_listings.extend(listings)
        
        # Filter by price
        filtered_listings = self.filter_by_price(all_listings)
        print(f"After price filter ({self.MIN_PRICE}€ - {self.MAX_PRICE}€): {len(filtered_listings)} listings")
        
        # Process each listing: check title first, then fetch description and check it too
        final_listings = []
        for listing in filtered_listings:
            print(f"Processing: {listing['title']} - {listing['price']}€")
            
            # Check title first for short-term rental keywords
            if self.is_short_term_rental(listing['title']):
                print(f"  -> Skipped (short-term rental detected in title)")
                continue
            
            # Skip description fetching for storia.ro links
            if 'storia.ro' in listing['link']:
                print(f"  -> Skipping description fetch for storia.ro link")
                description = None
                listing['description'] = None
            else:
                # Fetch description for non-storia.ro links
                description = self.fetch_description(listing['link'])
                
                if description:
                    # Check description for short-term rental keywords
                    if self.is_short_term_rental(description):
                        print(f"  -> Skipped (short-term rental detected in description)")
                        continue
                    
                    listing['description'] = description
                else:
                    print(f"  -> Warning: Could not fetch description")
                    description = ""
                    listing['description'] = None
            
            # Extract floor and lift information from title and description
            # Use empty string if description is None to avoid errors
            description_text = description if description else ""
            floor_info = self.extract_floor_info(listing['title'], description_text)
            lift_info = self.extract_lift_info(listing['title'], description_text)
            
            listing['floor'] = floor_info
            listing['lift'] = lift_info
            
            final_listings.append(listing)
        
        return final_listings
    
    def load_database(self) -> List[Dict]:
        """
        Load existing listings from database file
        
        Returns:
            List of existing listings
        """
        if not os.path.exists(self.DB_FILE):
            return []
        
        try:
            with open(self.DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading database: {e}")
            return []
    
    def save_database(self, listings: List[Dict]):
        """
        Save listings to database file
        
        Args:
            listings: List of listings to save
        """
        try:
            with open(self.DB_FILE, 'w', encoding='utf-8') as f:
                json.dump(listings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving database: {e}")
    
    def find_new_listings(self, current_listings: List[Dict]) -> List[Dict]:
        """
        Compare current listings with database and find new ones
        
        Args:
            current_listings: List of current listings
            
        Returns:
            List of new listings not in database
        """
        existing_listings = self.load_database()
        
        # Create a set of existing listing links for quick lookup
        existing_links = {listing['link'] for listing in existing_listings}
        
        # Find new listings
        new_listings = [
            listing for listing in current_listings
            if listing['link'] not in existing_links
        ]
        
        return new_listings
    
    def update_database(self, new_listings: List[Dict]):
        """
        Add new listings to database
        
        Args:
            new_listings: List of new listings to add
        """
        existing_listings = self.load_database()
        
        # Add timestamp to new listings
        timestamp = datetime.now().isoformat()
        for listing in new_listings:
            listing['found_at'] = timestamp
        
        # Combine and save
        all_listings = existing_listings + new_listings
        self.save_database(all_listings)


class Publi24Scraper:
    """Main scraper class for Publi24 apartment listings"""
    
    # URLs to scrape
    URLS = [
        # 3-camere apartments (pages 1-3)
        "https://www.publi24.ro/anunturi/imobiliare/de-inchiriat/apartamente/apartamente-3-camere/dolj/craiova/?pag=1&ordered=asc&orderby=price",
        "https://www.publi24.ro/anunturi/imobiliare/de-inchiriat/apartamente/apartamente-3-camere/dolj/craiova/?pag=2&ordered=asc&orderby=price",
        "https://www.publi24.ro/anunturi/imobiliare/de-inchiriat/apartamente/apartamente-3-camere/dolj/craiova/?pag=3&ordered=asc&orderby=price",
        # 4-camere apartments (pages 1-3)
        "https://www.publi24.ro/anunturi/imobiliare/de-inchiriat/apartamente/apartamente-4-camere/dolj/craiova/?pag=1&ordered=asc&orderby=price",
        "https://www.publi24.ro/anunturi/imobiliare/de-inchiriat/apartamente/apartamente-4-camere/dolj/craiova/?pag=2&ordered=asc&orderby=price",
        "https://www.publi24.ro/anunturi/imobiliare/de-inchiriat/apartamente/apartamente-4-camere/dolj/craiova/?pag=3&ordered=asc&orderby=price",
        # Case-vile (pages 1-3)
        "https://www.publi24.ro/anunturi/imobiliare/de-inchiriat/case-vile/dolj/craiova/?pag=1&ordered=asc&orderby=price",
        "https://www.publi24.ro/anunturi/imobiliare/de-inchiriat/case-vile/dolj/craiova/?pag=2&ordered=asc&orderby=price",
        "https://www.publi24.ro/anunturi/imobiliare/de-inchiriat/case-vile/dolj/craiova/?pag=3&ordered=asc&orderby=price",
    ]
    
    # Keywords that indicate short-term rental (Romanian) - same as OLX
    SHORT_TERM_KEYWORDS = [
        "regim hotelier",
        "pe noapte",
        "pe zi",
        "pe săptămână",
        "pe săptămâna",
        "pe weekend",
        "temporar",
        "scurtă perioadă",
        "scurta perioada",
        "cazare",
        "hotel",
        "airbnb",
        "targ de craciun",
        "târg crăciun",
        "targ craciun",
        "târgul de crăciun",
        "targul de craciun",
        "perioada targului",
        "perioada târgului",
        "perioada targului de craciun",
        "perioada târgului de crăciun",
        "perioada targului de crăciun",
        "perioada târgului de craciun",
        "pentru targ",
        "pentru târg",
        "pentru targ de craciun",
        "pentru târg de crăciun",
        "in perioada targului",
        "în perioada târgului",
        "în perioada targului",
        "durata targului",
        "durata târgului",
        "timpul targului",
        "spațiu comercial",
        "spatiu comercial",
        "timpul târgului"
    ]
    
    # Minimum price threshold in EUR
    MIN_PRICE = 100
    
    # Maximum price threshold in EUR
    MAX_PRICE = 500
    
    # Database file path
    DB_FILE = "listings_db.json"
    
    # Global debug flag - set to True to enable debug output
    DEBUG_ENABLED = False
    
    def __init__(self):
        """Initialize the scraper"""
        self.session = requests.Session()
        # Set user agent to avoid blocking
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.listings = []
    
    @classmethod
    def enable_debug(cls, enabled: bool = True):
        """
        Enable or disable debug output
        
        Args:
            enabled: True to enable debug output, False to disable
        """
        cls.DEBUG_ENABLED = enabled
        status = "enabled" if enabled else "disabled"
        print(f"Debug mode {status}")
    
    def _debug(self, message: str):
        """
        Print debug message if debug is enabled
        
        Args:
            message: Debug message to print
        """
        if self.DEBUG_ENABLED:
            print(message)
    
    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch a webpage and return BeautifulSoup object
        
        Args:
            url: URL to fetch
            
        Returns:
            BeautifulSoup object or None if request fails
        """
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def extract_price(self, price_element) -> Optional[float]:
        """
        Extract price from price element and convert to float
        
        Args:
            price_element: BeautifulSoup element containing price
            
        Returns:
            Price as float or None if extraction fails
        """
        if not price_element:
            return None
        
        # Get text and extract numbers
        price_text = price_element.get_text(strip=True)
        
        # Remove currency symbols (€, EUR, lei, etc.) and other non-numeric characters except digits, spaces, dots, and commas
        # Keep spaces, dots, and commas for number parsing
        price_text = re.sub(r'[^\d\s.,]', '', price_text)
        
        # Remove all spaces (handles "1 400" -> "1400")
        price_text = price_text.replace(' ', '')
        
        # Handle European number format (1.400,50) vs US format (1,400.50)
        # If there's a comma followed by 2 digits at the end, it's likely decimal separator
        # Otherwise, dots/commas are thousands separators
        if re.search(r',\d{2}$', price_text):
            # European format: 1.400,50 -> 1400.50
            price_text = price_text.replace('.', '').replace(',', '.')
        else:
            # Remove dots and commas (they're thousands separators)
            # Handle both 1.400 and 1,400 formats
            price_text = price_text.replace('.', '').replace(',', '')
        
        # Extract the number
        price_match = re.search(r'(\d+(?:\.\d+)?)', price_text)
        
        if price_match:
            try:
                return float(price_match.group(1))
            except ValueError:
                return None
        return None
    
    def extract_listings_from_page(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Extract listings from a single page
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            List of dictionaries containing listing data
        """
        listings = []
        
        # Find the article-list container
        article_list = soup.find('div', class_='article-list')
        if not article_list:
            self._debug("  [DEBUG] No article-list container found")
            return listings
        
        # Find all article-content divs - each represents a listing
        # The structure is: article-list > (article or div) > art-img + article-content
        article_content_divs = article_list.find_all('div', class_='article-content')
        
        if not article_content_divs:
            # Try alternative: look for article tags
            article_tags = article_list.find_all('article')
            for article in article_tags:
                content_div = article.find('div', class_='article-content')
                if content_div:
                    article_content_divs.append(content_div)
        
        self._debug(f"  [DEBUG] Found {len(article_content_divs)} article-content divs")
        
        for content_div in article_content_divs:
            try:
                # Extract title from h2 with class "article-title" inside article-content
                title_element = content_div.find('h2', class_='article-title')
                
                if not title_element:
                    self._debug("  [DEBUG] No title element found, skipping")
                    continue
                
                title = title_element.get_text(strip=True)
                
                # Extract price from div with class "article-info" inside article-content
                price_element = content_div.find('div', class_='article-info')
                
                if not price_element:
                    self._debug(f"  [DEBUG] No price element found for: {title}")
                    continue
                
                price = self.extract_price(price_element)
                
                if price is None:
                    self._debug(f"  [DEBUG] Could not extract price for: {title}")
                    continue
                
                # Extract link - usually in the title's parent <a> tag
                link_element = title_element.find_parent('a', href=True)
                if not link_element:
                    # Try to find <a> tag in the article-content div
                    link_element = content_div.find('a', href=True)
                if not link_element:
                    # Try to find <a> tag in the parent container
                    parent = content_div.find_parent(['article', 'div'])
                    if parent:
                        link_element = parent.find('a', href=True)
                
                if not link_element:
                    self._debug(f"  [DEBUG] No link element found for: {title}")
                    continue
                
                # Make sure link is absolute
                link = link_element['href']
                if link.startswith('/'):
                    link = f"https://www.publi24.ro{link}"
                elif not link.startswith('http'):
                    link = f"https://www.publi24.ro/{link}"
                
                listings.append({
                    'title': title,
                    'price': price,
                    'link': link,
                    'description': None  # Will be filled later
                })
            except Exception as e:
                self._debug(f"  [DEBUG] Error extracting listing: {e}")
                print(f"Error extracting listing: {e}")
                continue
        
        return listings
    
    def filter_by_price(self, listings: List[Dict]) -> List[Dict]:
        """
        Filter listings by price range (MIN_PRICE <= price <= MAX_PRICE)
        
        Args:
            listings: List of listing dictionaries
            
        Returns:
            Filtered list with prices between MIN_PRICE and MAX_PRICE
        """
        return [
            listing for listing in listings 
            if self.MIN_PRICE <= listing['price'] <= self.MAX_PRICE
        ]
    
    def fetch_description(self, link: str) -> Optional[str]:
        """
        Fetch description from listing detail page
        
        Args:
            link: URL of the listing detail page
            
        Returns:
            Description text or None if extraction fails
        """
        self._debug(f"  [DEBUG] Fetching description from: {link}")
        soup = self.fetch_page(link)
        if not soup:
            self._debug(f"  [DEBUG] Failed to fetch page")
            return None
        
        self._debug(f"  [DEBUG] Page fetched successfully")
        
        try:
            # Look for description in common locations on publi24
            # Try multiple selectors that might contain the description
            desc_selectors = [
                ('div', {'class': 'article-description'}),
                ('div', {'class': 'description'}),
                ('div', {'id': 'description'}),
                ('div', {'class': 'ad-description'}),
                ('p', {'class': 'article-description'}),
            ]
            
            for tag, attrs in desc_selectors:
                desc_element = soup.find(tag, attrs)
                if desc_element:
                    desc_text = desc_element.get_text(separator='\n', strip=True)
                    if desc_text and len(desc_text.strip()) > 10:
                        desc_text = self._clean_description(desc_text)
                        if desc_text and len(desc_text.strip()) > 10:
                            self._debug(f"  [DEBUG] Found description using {tag} with {attrs}")
                            return desc_text
            
            # Fallback: look for any div containing "descriere" in class or id
            desc_elements = soup.find_all(['div', 'p'], class_=lambda x: x and 'descriere' in x.lower())
            desc_elements.extend(soup.find_all(['div', 'p'], id=lambda x: x and 'descriere' in x.lower()))
            
            for desc_element in desc_elements:
                desc_text = desc_element.get_text(separator='\n', strip=True)
                if desc_text and len(desc_text.strip()) > 10:
                    desc_text = self._clean_description(desc_text)
                    if desc_text and len(desc_text.strip()) > 10:
                        self._debug(f"  [DEBUG] Found description using fallback method")
                        return desc_text
            
        except Exception as e:
            self._debug(f"  [DEBUG] ERROR extracting description from {link}: {e}")
            if self.DEBUG_ENABLED:
                import traceback
                traceback.print_exc()
        
        print(f"  -> Warning: Could not extract description from {link}")
        return None
    
    def _clean_description(self, description: str) -> str:
        """
        Clean description text by removing unwanted prefixes and fixing formatting
        Also handles HTML tags like <br> by converting them to newlines
        
        Args:
            description: Raw description text (may contain HTML)
            
        Returns:
            Cleaned description text
        """
        if not description:
            return ""
        
        # Convert HTML line breaks to newlines
        description = re.sub(r'<br\s*/?>', '\n', description, flags=re.IGNORECASE)
        description = re.sub(r'<br\s+[^>]*>', '\n', description, flags=re.IGNORECASE)
        
        # Remove other HTML tags (but keep the text content)
        description = re.sub(r'<[^>]+>', '', description)
        
        # Remove "Descriere" prefix (case-insensitive, with or without space)
        description = re.sub(r'(?i)^descriere\s+', '', description)
        
        # Remove "Descriere" if it appears at the start without proper spacing
        # Handle cases like "DescriereApartament" -> "Apartament"
        description = re.sub(r'(?i)^descriere(?=[A-ZĂÂÎȘȚăâîșț])', '', description)
        
        # Clean up multiple spaces and normalize whitespace
        description = re.sub(r'[ \t]+', ' ', description)  # Multiple spaces/tabs to single space
        description = re.sub(r'\n\s*\n', '\n\n', description)  # Multiple newlines to double newline
        description = description.strip()
        
        return description
    
    def is_short_term_rental(self, text: str) -> bool:
        """
        Check if text contains short-term rental keywords
        
        Args:
            text: Text to check (can be title or description)
            
        Returns:
            True if short-term rental keywords found, False otherwise
        """
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Check for any short-term keywords
        for keyword in self.SHORT_TERM_KEYWORDS:
            if keyword.lower() in text_lower:
                return True
        
        return False
    
    def extract_floor_info(self, title: str, description: str = "") -> Optional[str]:
        """
        Extract floor information from title and description
        Looks for patterns like "et 4/4", "etaj 1/4", "et.2/4", "etajul 7", etc.
        
        Args:
            title: Listing title
            description: Listing description (optional)
            
        Returns:
            Floor information string (e.g., "4/4", "7/?") or None if not found
        """
        text = f"{title} {description}".lower()
        
        # Patterns to match floor information (ordered by specificity)
        patterns = [
            # Full patterns with both floor and total: "et 4/4", "etaj 1/4", "etajul 3/5"
            r'et(?:aj)?(?:ul)?\s*(\d+)\s*/\s*(\d+)',  # "et 4/4", "etaj 1/4", "etajul 3/5"
            r'et\.\s*(\d+)\s*/\s*(\d+)',  # "et. 2/4"
            r'etaj\s*(\d+)\s*din\s*(\d+)',  # "etaj 1 din 4"
            r'et\.\s*(\d+)\s*din\s*(\d+)',  # "et. 2 din 4"
            r'(\d+)\s*/\s*(\d+)\s*etaj',  # "4/4 etaj"
            # Pattern: "etajul X al unui bloc cu Y etaje"
            r'etajul\s*(\d+)\s*al\s*unui\s*bloc\s*cu\s*(\d+)\s*etaje',
            # Standalone X/Y pattern - only match reasonable floor numbers (1-20)
            r'(?:^|[\s,.-])([1-9]|1[0-9]|20)\s*/\s*([1-9]|1[0-9]|20)(?:\s|$|,|\.|mp)',  # "5/6" standalone
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                floor = match.group(1)
                total_floors = match.group(2)
                return f"{floor}/{total_floors}"
        
        # Try to find single floor numbers: "etaj 1", "etajul 7", "et 2", "et.2"
        single_floor_patterns = [
            r'etajul\s+(\d+)',  # "etajul 7"
            r'etaj\s+(\d+)',  # "etaj 1"
            r'\bet\s+(\d+)',  # "et 2"
            r'\bet\.\s*(\d+)',  # "et.2"
            r'la\s+etajul\s+(\d+)',  # "la etajul 1"
            r'etajul\s+(\d+)\s+al',  # "etajul 2 al"
        ]
        
        for pattern in single_floor_patterns:
            match = re.search(pattern, text)
            if match:
                floor = match.group(1)
                # Try to find total floors in the same text
                total_match = re.search(r'(?:bloc|imobil|cladire).*?(?:cu\s+)?(\d+)\s+etaje?', text)
                if total_match:
                    total_floors = total_match.group(1)
                    return f"{floor}/{total_floors}"
                else:
                    # Return just the floor number if total not found
                    return f"{floor}/?"
        
        # Special case: "etaj intermediar" (middle floor)
        if 'etaj intermediar' in text:
            # Try to find total floors
            total_match = re.search(r'(?:bloc|imobil|cladire).*?(?:cu\s+)?(\d+)\s+etaje?', text)
            if total_match:
                total_floors = int(total_match.group(1))
                # Approximate middle floor
                middle_floor = str(max(1, total_floors // 2))
                return f"{middle_floor}/{total_floors} (intermediar)"
            return "intermediar"
        
        return None
    
    def extract_lift_info(self, title: str, description: str = "") -> Optional[str]:
        """
        Extract lift/elevator information from title and description
        Looks for keywords like "lift", "ascensor", "elevator", etc.
        
        Args:
            title: Listing title
            description: Listing description (optional)
            
        Returns:
            "Yes" if lift found, "No" if explicitly mentioned as absent, None if not mentioned
        """
        text = f"{title} {description}".lower()
        
        # Keywords indicating presence of lift (more comprehensive)
        lift_keywords = [
            'lift',
            'ascensor',
            'elevator',
            'ascensoare',
            'cu lift',
            'bloc cu lift',
            'are lift',
            'lift nou',
            'cu ascensor',
            'bloc cu ascensor',
            'are ascensor',
            'ascensor nou',
            'dotat cu lift',
            'dotat cu ascensor',
            'prevazut cu lift',
            'prevazut cu ascensor',
            'dispunand de lift',
            'dispunand de ascensor'
        ]
        
        # Keywords indicating absence of lift
        no_lift_keywords = [
            'fara lift',
            'fără lift',
            'nu are lift',
            'fara ascensor',
            'fără ascensor',
            'nu are ascensor',
            'fara ascensoare',
            'fără ascensoare',
            'bloc fara lift',
            'bloc fără lift'
        ]
        
        # Check for absence first
        for keyword in no_lift_keywords:
            if keyword in text:
                return "No"
        
        # Check for presence
        for keyword in lift_keywords:
            if keyword in text:
                return "Yes"
        
        return None
    
    def process_listings(self) -> List[Dict]:
        """
        Main method to process all listings from all URLs
        
        Returns:
            List of processed listing dictionaries
        """
        all_listings = []
        
        # Fetch listings from all URLs
        for url in self.URLS:
            print(f"Fetching listings from: {url}")
            soup = self.fetch_page(url)
            
            if soup:
                listings = self.extract_listings_from_page(soup)
                print(f"Found {len(listings)} listings")
                all_listings.extend(listings)
        
        # Filter by price
        filtered_listings = self.filter_by_price(all_listings)
        print(f"After price filter ({self.MIN_PRICE}€ - {self.MAX_PRICE}€): {len(filtered_listings)} listings")
        
        # Process each listing: check title first, then fetch description and check it too
        final_listings = []
        for listing in filtered_listings:
            print(f"Processing: {listing['title']} - {listing['price']}€")
            
            # Check title first for short-term rental keywords
            if self.is_short_term_rental(listing['title']):
                print(f"  -> Skipped (short-term rental detected in title)")
                continue
            
            # Fetch description
            description = self.fetch_description(listing['link'])
            
            if description:
                # Check description for short-term rental keywords
                if self.is_short_term_rental(description):
                    print(f"  -> Skipped (short-term rental detected in description)")
                    continue
                
                listing['description'] = description
            else:
                print(f"  -> Warning: Could not fetch description")
                description = ""
                listing['description'] = None
            
            # Extract floor and lift information from title and description
            # Use empty string if description is None to avoid errors
            description_text = description if description else ""
            floor_info = self.extract_floor_info(listing['title'], description_text)
            lift_info = self.extract_lift_info(listing['title'], description_text)
            
            listing['floor'] = floor_info
            listing['lift'] = lift_info
            
            final_listings.append(listing)
        
        return final_listings
    
    def load_database(self) -> List[Dict]:
        """
        Load existing listings from database file
        
        Returns:
            List of existing listings
        """
        if not os.path.exists(self.DB_FILE):
            return []
        
        try:
            with open(self.DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading database: {e}")
            return []
    
    def save_database(self, listings: List[Dict]):
        """
        Save listings to database file
        
        Args:
            listings: List of listings to save
        """
        try:
            with open(self.DB_FILE, 'w', encoding='utf-8') as f:
                json.dump(listings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving database: {e}")
    
    def find_new_listings(self, current_listings: List[Dict]) -> List[Dict]:
        """
        Compare current listings with database and find new ones
        
        Args:
            current_listings: List of current listings
            
        Returns:
            List of new listings not in database
        """
        existing_listings = self.load_database()
        
        # Create a set of existing listing links for quick lookup
        existing_links = {listing['link'] for listing in existing_listings}
        
        # Find new listings
        new_listings = [
            listing for listing in current_listings
            if listing['link'] not in existing_links
        ]
        
        return new_listings
    
    def update_database(self, new_listings: List[Dict]):
        """
        Add new listings to database
        
        Args:
            new_listings: List of new listings to add
        """
        existing_listings = self.load_database()
        
        # Add timestamp to new listings
        timestamp = datetime.now().isoformat()
        for listing in new_listings:
            listing['found_at'] = timestamp
        
        # Combine and save
        all_listings = existing_listings + new_listings
        self.save_database(all_listings)


if __name__ == "__main__":
    import sys
    from telegram_notifier import TelegramNotifier
    
    # Enable/disable debug mode (set to True to see debug output)
    # OLXScraper.enable_debug(True)  # Uncomment to enable debug mode
    # Publi24Scraper.enable_debug(True)  # Uncomment to enable debug mode
    # OLXScraper.enable_debug(False)  # Uncomment to disable debug mode
    # Publi24Scraper.enable_debug(False)  # Uncomment to disable debug mode
    
    all_new_listings = []
    
    # Run OLX scraper
    print("=" * 60)
    print("Starting OLX scraper...")
    print("=" * 60)
    olx_scraper = OLXScraper()
    olx_listings = olx_scraper.process_listings()
    print(f"\nTotal valid OLX listings found: {len(olx_listings)}")
    
    olx_new_listings = olx_scraper.find_new_listings(olx_listings)
    print(f"New OLX listings: {len(olx_new_listings)}")
    
    if olx_new_listings:
        olx_scraper.update_database(olx_new_listings)
        print(f"Database updated with {len(olx_new_listings)} new OLX listings")
        all_new_listings.extend(olx_new_listings)
    
    # Run Publi24 scraper
    print("\n" + "=" * 60)
    print("Starting Publi24 scraper...")
    print("=" * 60)
    publi24_scraper = Publi24Scraper()
    publi24_listings = publi24_scraper.process_listings()
    print(f"\nTotal valid Publi24 listings found: {len(publi24_listings)}")
    
    publi24_new_listings = publi24_scraper.find_new_listings(publi24_listings)
    print(f"New Publi24 listings: {len(publi24_new_listings)}")
    
    if publi24_new_listings:
        publi24_scraper.update_database(publi24_new_listings)
        print(f"Database updated with {len(publi24_new_listings)} new Publi24 listings")
        all_new_listings.extend(publi24_new_listings)
    
    # Send notifications for all new listings
    if all_new_listings:
        # Sort listings by price (ascending) before sending
        all_new_listings_sorted = sorted(all_new_listings, key=lambda x: x.get('price', 0))
        print(f"\nTotal new listings from all sources: {len(all_new_listings_sorted)}")
        print(f"Listings sorted by price (ascending)")
        
        # Send Telegram notification
        # Load Telegram configuration
        config_file = "config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    bot_token = config.get('telegram_bot_token')
                    chat_id = config.get('telegram_chat_id')
                    
                    if bot_token and chat_id:
                        notifier = TelegramNotifier(bot_token, chat_id)
                        print("\nSending Telegram notifications...")
                        try:
                            if notifier.send_listings(all_new_listings_sorted):
                                print("✓ Notifications sent successfully!")
                            else:
                                print("✗ Some notifications failed to send")
                        except Exception as send_error:
                            print(f"\n✗ Error sending Telegram notifications: {send_error}")
                            import traceback
                            traceback.print_exc()
                            print("\nNew listings found:")
                            for listing in all_new_listings:
                                print(f"  - {listing['title']} - {listing['price']}€")
                    else:
                        print("\n⚠ Telegram configuration incomplete. Skipping notifications.")
                        print("New listings found:")
                        for listing in all_new_listings:
                            print(f"  - {listing['title']} - {listing['price']}€")
            except Exception as e:
                print(f"\nError loading Telegram config: {e}")
                import traceback
                traceback.print_exc()
                print("\nNew listings found:")
                for listing in all_new_listings:
                    print(f"  - {listing['title']} - {listing['price']}€")
        else:
            print("\n⚠ config.json not found. Skipping Telegram notifications.")
            print("Please create config.json with telegram_bot_token and telegram_chat_id")
            print("\nNew listings found:")
            for listing in all_new_listings:
                print(f"  - {listing['title']} - {listing['price']}€")
    else:
        print("\nNo new listings found from any source.")

