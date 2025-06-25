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
