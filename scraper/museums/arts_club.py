# museums/arts_club.py
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from .base import BaseScraper
import re

class ArtsClubScraper(BaseScraper):
    def __init__(self, session):
        super().__init__(session)
        self.museum_id = "arts"
        self.museum_name = "National Arts Club"
        self.museum_location = "National Arts Club, 15 Gramercy Park South, New York, NY"
        
    def get_urls(self) -> List[str]:
        return [
            "https://nationalartsclub.org/events/",
            "https://nationalartsclub.org/exhibitions/"
        ]
        
    async def parse_events(self, html: str, url: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, 'html.parser')
        events = []
        
        # National Arts Club event structure
        event_items = soup.find_all('div', class_='event-item') or \
                     soup.find_all('article', class_='event') or \
                     soup.find_all('div', class_='tribe-events-list-event')
        
        for item in event_items[:20]:
            # Title
            title_elem = item.find(['h2', 'h3', 'h4']) or \
                        item.find('a', class_='tribe-event-url')
            if not title_elem:
                continue
                
            title = title_elem.get_text(strip=True)
            
            # Date
            date_elem = item.find('time') or \
                       item.find('span', class_='tribe-event-date-start')
            
            if date_elem:
                date_text = date_elem.get('datetime', '') or date_elem.get_text(strip=True)
                date = self.parse_date(date_text)
                if date:
                    # Time
                    time_elem = item.find('span', class_='tribe-event-time')
                    time = self.parse_time(time_elem.get_text(strip=True)) if time_elem else None
                    
                    # Description
                    desc_elem = item.find('div', class_='tribe-events-list-event-description') or \
                               item.find('p')
                    description = desc_elem.get_text(strip=True)[:200] if desc_elem else ""
                    
                    # Event type
                    event_type = None
                    if 'exhibition' in url or 'exhibition' in title.lower():
                        event_type = 'Exhibition'
                    elif 'opening' in title.lower():
                        event_type = 'Opening'
                    elif 'reception' in title.lower():
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
