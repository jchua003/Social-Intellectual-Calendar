from typing import List, Dict, Any
from bs4 import BeautifulSoup
from .base import BaseScraper
import re

class MoMAScraper(BaseScraper):
    def __init__(self, session):
        super().__init__(session)
        self.museum_id = "moma"
        self.museum_name = "MoMA"
        self.museum_location = "MoMA, 11 West 53rd Street, New York, NY"
        
    def get_urls(self) -> List[str]:
        return [
            "https://www.moma.org/calendar/",
            "https://www.moma.org/calendar/exhibitions",
            "https://www.moma.org/calendar/programs"
        ]
        
    async def parse_events(self, html: str, url: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, 'html.parser')
        events = []
        
        # MoMA uses different structures for different pages
        if 'exhibitions' in url:
            # Parse exhibitions
            exhibitions = soup.find_all('div', class_='exhibition-item') or \
                         soup.find_all('article', class_='exhibition') or \
                         soup.find_all('div', {'data-testid': 'exhibition-card'})
            
            for exhibit in exhibitions[:20]:  # Limit to prevent too many
                title_elem = exhibit.find(['h2', 'h3', 'h4']) or \
                            exhibit.find('a', class_='exhibition-title')
                
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                
                # Extract dates
                date_elem = exhibit.find('div', class_='dates') or \
                           exhibit.find('span', class_='exhibition-dates') or \
                           exhibit.find(text=re.compile(r'\w+\s+\d+,?\s+\d{4}'))
                
                if date_elem:
                    date_text = date_elem.get_text() if hasattr(date_elem, 'get_text') else str(date_elem)
                    # For exhibitions, use the opening date
                    date_match = re.search(r'(\w+\s+\d+,?\s+\d{4})', date_text)
                    if date_match:
                        date = self.parse_date(date_match.group(1))
                        if date:
                            description = ""
                            desc_elem = exhibit.find('div', class_='description') or \
                                       exhibit.find('p')
                            if desc_elem:
                                description = desc_elem.get_text(strip=True)[:200]
                                
                            events.append(self.create_event(
                                title=title,
                                date=date,
                                description=description,
                                event_type='Exhibition',
                                url=url
                            ))
                            
        else:
            # Parse regular events/programs
            event_items = soup.find_all('div', class_='event-item') or \
                         soup.find_all('article', class_='program') or \
                         soup.find_all('div', class_='calendar-event')
            
            for event in event_items[:30]:  # Limit results
                title_elem = event.find(['h2', 'h3', 'h4', 'a'])
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                
                # Extract date
                date_elem = event.find('time') or \
                           event.find('div', class_='event-date') or \
                           event.find('span', class_='date')
                           
                if not date_elem:
                    # Try to find date in text
                    date_text = event.get_text()
                    date_match = re.search(r'(\w+\s+\d+,?\s+\d{4})', date_text)
                    if date_match:
                        date = self.parse_date(date_match.group(1))
                    else:
                        continue
                else:
                    date_text = date_elem.get('datetime', '') or date_elem.get_text(strip=True)
                    date = self.parse_date(date_text)
                    
                if not date:
                    continue
                    
                # Extract time
                time_elem = event.find('div', class_='event-time') or \
                           event.find('span', class_='time')
                time = self.parse_time(time_elem.get_text(strip=True)) if time_elem else None
                
                # Extract description
                desc_elem = event.find('div', class_='description') or \
                           event.find('p', class_='event-description')
                description = desc_elem.get_text(strip=True)[:200] if desc_elem else ""
                
                # Determine event type
                type_elem = event.find('span', class_='event-type') or \
                           event.find('div', class_='category')
                event_type = None
                if type_elem:
                    type_text = type_elem.get_text(strip=True)
                    event_type = self.classify_event_type(type_text, title + " " + description)
                
                events.append(self.create_event(
                    title=title,
                    date=date,
                    time=time,
                    description=description,
                    event_type=event_type,
                    url=url
                ))
                
        return events
