from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
import re

class BaseScraper(ABC):
    """Base class for all museum scrapers"""
    
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        self.museum_id = ""
        self.museum_name = ""
        self.museum_location = ""
        
    @abstractmethod
    def get_urls(self) -> List[str]:
        """Return list of URLs to scrape"""
        pass
        
    @abstractmethod
    async def parse_events(self, html: str, url: str) -> List[Dict[str, Any]]:
        """Parse events from HTML content"""
        pass
        
    async def fetch_page(self, url: str) -> Optional[str]:
        """Fetch HTML content from URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            async with self.session.get(url, headers=headers, timeout=30) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    print(f"Error fetching {url}: Status {response.status}")
                    return None
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
            
    async def scrape(self) -> List[Dict[str, Any]]:
        """Main scraping method"""
        all_events = []
        urls = self.get_urls()
        
        for url in urls:
            html = await self.fetch_page(url)
            if html:
                events = await self.parse_events(html, url)
                all_events.extend(events)
                
        return all_events
        
    def parse_date(self, date_str: str) -> Optional[str]:
        """Parse various date formats to YYYY-MM-DD"""
        # Clean the date string
        date_str = re.sub(r'\s+', ' ', date_str.strip())
        
        # Try different date formats
        formats = [
            '%B %d, %Y',  # January 15, 2025
            '%b %d, %Y',  # Jan 15, 2025
            '%m/%d/%Y',   # 01/15/2025
            '%Y-%m-%d',   # 2025-01-15
            '%d %B %Y',   # 15 January 2025
            '%d %b %Y',   # 15 Jan 2025
        ]
        
        for fmt in formats:
            try:
                date = datetime.strptime(date_str, fmt)
                return date.strftime('%Y-%m-%d')
            except ValueError:
                continue
                
        # Try to extract date components with regex
        patterns = [
            r'(\w+)\s+(\d{1,2}),?\s+(\d{4})',  # Month Day, Year
            r'(\d{1,2})/(\d{1,2})/(\d{4})',     # MM/DD/YYYY
        ]
        
        for pattern in patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    if '/' in pattern:
                        month, day, year = match.groups()
                        date = datetime(int(year), int(month), int(day))
                    else:
                        month_str, day, year = match.groups()
                        # Convert month name to number
                        date = datetime.strptime(f"{month_str} {day} {year}", '%B %d %Y')
                    return date.strftime('%Y-%m-%d')
                except:
                    pass
                    
        print(f"Could not parse date: {date_str}")
        return None
        
    def parse_time(self, time_str: str) -> str:
        """Parse time string to standardized format"""
        # Clean the time string
        time_str = re.sub(r'\s+', ' ', time_str.strip())
        
        # Extract time range if present
        time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm|AM|PM)?\s*[-–]\s*(\d{1,2}):?(\d{2})?\s*(am|pm|AM|PM)?', time_str, re.IGNORECASE)
        
        if time_match:
            start_hour, start_min, start_ampm, end_hour, end_min, end_ampm = time_match.groups()
            
            # Format start time
            start_min = start_min or '00'
            start_ampm = (start_ampm or end_ampm or 'PM').upper()
            start_time = f"{start_hour}:{start_min} {start_ampm}"
            
            # Format end time
            end_min = end_min or '00'
            end_ampm = (end_ampm or start_ampm).upper()
            end_time = f"{end_hour}:{end_min} {end_ampm}"
            
            return f"{start_time} - {end_time}"
        
        # Single time
        single_time = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm|AM|PM)?', time_str, re.IGNORECASE)
        if single_time:
            hour, minute, ampm = single_time.groups()
            minute = minute or '00'
            ampm = (ampm or 'PM').upper()
            return f"{hour}:{minute} {ampm}"
            
        # Default time if parsing fails
        return "See website for time"
        
    def classify_event_type(self, title: str, description: str = "") -> str:
        """Classify event based on title and description"""
        text = (title + " " + description).lower()
        
        type_keywords = {
            'Exhibition': ['exhibition', 'exhibit', 'display', 'showcase', 'collection'],
            'Workshop': ['workshop', 'hands-on', 'make', 'create', 'craft'],
            'Lecture': ['lecture', 'talk', 'presentation', 'speaker'],
            'Performance': ['performance', 'concert', 'dance', 'music', 'theater'],
            'Film': ['film', 'screening', 'movie', 'cinema', 'video'],
            'Family Program': ['family', 'kids', 'children', 'youth'],
            'Tour': ['tour', 'guided', 'walk'],
            'Symposium': ['symposium', 'conference', 'colloquium'],
            'Opening': ['opening', 'reception', 'preview'],
            'Panel Discussion': ['panel', 'discussion', 'conversation'],
            'Artist Talk': ['artist talk', 'artist lecture'],
            'Gallery Talk': ['gallery talk', 'curator talk'],
        }
        
        for event_type, keywords in type_keywords.items():
            if any(keyword in text for keyword in keywords):
                return event_type
                
        return 'Special Event'
        
    def create_event(self, title: str, date: str, time: str = None, 
                    description: str = "", event_type: str = None,
                    url: str = None) -> Dict[str, Any]:
        """Create standardized event object"""
        if not event_type:
            event_type = self.classify_event_type(title, description)
            
        if not time:
            time = self.get_default_time(event_type)
            
        return {
            'museum': self.museum_id,
            'museumName': self.museum_name,
            'title': title.strip(),
            'type': event_type,
            'date': date,
            'time': time,
            'description': description.strip() or f"Join us for this {event_type.lower()} at {self.museum_name}.",
            'location': self.museum_location,
            'url': url
        }
        
    def get_default_time(self, event_type: str) -> str:
        """Get default time based on event type"""
        default_times = {
            'Exhibition': '10:00 AM - 5:00 PM',
            'Workshop': '2:00 PM - 4:00 PM',
            'Lecture': '6:00 PM - 7:30 PM',
            'Performance': '7:00 PM - 9:00 PM',
            'Film': '7:00 PM - 9:00 PM',
            'Family Program': '11:00 AM - 1:00 PM',
            'Tour': '2:00 PM - 3:00 PM',
            'Symposium': '9:00 AM - 5:00 PM',
            'Opening': '6:00 PM - 8:00 PM',
            'Panel Discussion': '6:00 PM - 7:30 PM',
            'Artist Talk': '6:00 PM - 7:30 PM',
            'Gallery Talk': '3:00 PM - 4:00 PM',
            'Special Event': '6:00 PM - 8:00 PM'
        }
        return default_times.get(event_type, '6:00 PM - 8:00 PM')
