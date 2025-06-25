# museums/explorers.py
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from .base import BaseScraper
import re

class ExplorersScraper(BaseScraper):
    def __init__(self, session):
        super().__init__(session)
        self.museum_id = "explorers"
        self.museum_name = "The Explorers Club"
        self.museum_location = "The Explorers Club, 46 East 70th Street, New York, NY"
        
    def get_urls(self) -> List[str]:
        return [
            "https://explorers.org/events/",
            "https://explorers.org/public_lectures/"
        ]
        
    async def parse_events(self, html: str, url: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, 'html.parser')
        events = []
        
        # Explorers Club event structure
        event_blocks = soup.find_all('div', class_='event-block') or \
                      soup.find_all('div', class_='event-listing') or \
                      soup.find_all('article')
        
        for block in event_blocks[:20]:
            # Extract title
            title_elem = block.find(['h2', 'h3', 'h4', 'a'])
            if not title_elem:
                continue
                
            title = title_elem.get_text(strip=True)
            
            # Extract date
            text = block.get_text()
            date_match = re.search(r'(\w+\s+\d{1,2},?\s+\d{4})', text)
            if date_match:
                date = self.parse_date(date_match.group(1))
                if date:
                    # Time
                    time_match = re.search(r'(\d{1,2}:\d{2}\s*(?:am|pm|AM|PM))', text, re.IGNORECASE)
                    time = self.parse_time(time_match.group(1)) if time_match else None
                    
                    # Description
                    desc_elem = block.find('p')
                    description = desc_elem.get_text(strip=True)[:200] if desc_elem else ""
                    
                    # Event type
                    event_type = 'Lecture'  # Default
                    if 'film' in title.lower():
                        event_type = 'Film'
                    elif 'expedition' in title.lower():
                        event_type = 'Special Event'
                    elif 'dinner' in title.lower() or 'gala' in title.lower():
                        event_type = 'Social Event'
                    
                    events.append(self.create_event(
                        title=title,
                        date=date,
                        time=time,
                        description=description,
                        event_type=event_type,
                        url=url
                    ))
                    
        return events
