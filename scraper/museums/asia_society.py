# museums/asia_society.py
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from .base import BaseScraper
import re

class AsiaSocietyScraper(BaseScraper):
    def __init__(self, session):
        super().__init__(session)
        self.museum_id = "asia"
        self.museum_name = "Asia Society"
        self.museum_location = "Asia Society Museum, 725 Park Avenue, New York, NY"
        
    def get_urls(self) -> List[str]:
        return [
            "https://asiasociety.org/new-york/events",
            "https://asiasociety.org/new-york/exhibitions",
            "https://asiasociety.org/new-york/performances"
        ]
        
    async def parse_events(self, html: str, url: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, 'html.parser')
        events = []
        
        # Asia Society event structure
        event_items = soup.find_all('div', class_='event-item') or \
                     soup.find_all('article', class_='node-event') or \
                     soup.find_all('div', class_='views-row')
        
        for item in event_items[:20]:
            # Title
            title_elem = item.find(['h2', 'h3', 'h4']) or \
                        item.find('a', class_='event-title')
            if not title_elem:
                continue
                
            title = title_elem.get_text(strip=True)
            
            # Date
            date_elem = item.find('time') or \
                       item.find('div', class_='event-date') or \
                       item.find('span', class_='date-display-single')
            
            if date_elem:
                date_text = date_elem.get('datetime', '') or date_elem.get_text(strip=True)
                date = self.parse_date(date_text)
                if date:
                    # Time
                    time_elem = item.find('div', class_='event-time') or \
                               item.find('span', class_='date-display-start')
                    time = self.parse_time(time_elem.get_text(strip=True)) if time_elem else None
                    
                    # Description
                    desc_elem = item.find('div', class_='field-content') or \
                               item.find('p')
                    description = desc_elem.get_text(strip=True)[:200] if desc_elem else ""
                    
                    # Event type
                    event_type = None
                    if 'performance' in url:
                        event_type = 'Performance'
                    elif 'exhibition' in url:
                        event_type = 'Exhibition'
                    elif 'film' in title.lower():
                        event_type = 'Film'
                    elif 'workshop' in title.lower():
                        event_type = 'Workshop'
                    
                    events.append(self.create_event(
                        title=title,
                        date=date,
                        time=time,
                        description=description,
                        event_type=event_type,
                        url=url
                    ))
                    
        return events
