# museums/womens_history.py
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from .base import BaseScraper
import re

class WomensHistoryScraper(BaseScraper):
    def __init__(self, session):
        super().__init__(session)
        self.museum_id = "womens"
        self.museum_name = "Center for Women's History"
        self.museum_location = "New-York Historical Society, 170 Central Park West, New York, NY"
        
    def get_urls(self) -> List[str]:
        return [
            "https://www.nyhistory.org/programs",
            "https://www.nyhistory.org/exhibitions",
            "https://www.nyhistory.org/center-womens-history"
        ]
        
    async def parse_events(self, html: str, url: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, 'html.parser')
        events = []
        
        # NY Historical Society structure
        event_items = soup.find_all('div', class_='program-item') or \
                     soup.find_all('article', class_='event') or \
                     soup.find_all('div', class_='views-row')
        
        for item in event_items[:20]:
            # Title
            title_elem = item.find(['h2', 'h3', 'h4']) or \
                        item.find('a', class_='program-title')
            if not title_elem:
                continue
                
            title = title_elem.get_text(strip=True)
            
            # Only include women's history related events
            if not any(word in title.lower() for word in ['women', 'female', 'gender', 'feminist']):
                # Check description
                desc_elem = item.find('p') or item.find('div', class_='field-content')
                if desc_elem:
                    desc_text = desc_elem.get_text(strip=True)
                    if not any(word in desc_text.lower() for word in ['women', 'female', 'gender']):
                        continue
            
            # Date
            date_elem = item.find('time') or \
                       item.find('span', class_='date-display-single')
            
            if date_elem:
                date_text = date_elem.get('datetime', '') or date_elem.get_text(strip=True)
                date = self.parse_date(date_text)
                if date:
                    # Time
                    time_elem = item.find('span', class_='date-display-start')
                    time = self.parse_time(time_elem.get_text(strip=True)) if time_elem else None
                    
                    # Description
                    desc_elem = item.find('p') or item.find('div', class_='field-content')
                    description = desc_elem.get_text(strip=True)[:200] if desc_elem else ""
                    
                    # Event type
                    event_type = None
                    if 'panel' in title.lower():
                        event_type = 'Panel Discussion'
                    elif 'exhibition' in url:
                        event_type = 'Exhibition'
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
