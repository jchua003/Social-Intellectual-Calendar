from typing import List, Dict, Any
from bs4 import BeautifulSoup
from .base import BaseScraper
import re
import json

class MetScraper(BaseScraper):
    def __init__(self, session):
        super().__init__(session)
        self.museum_id = "met"
        self.museum_name = "The Met"
        self.museum_location = "The Met Fifth Avenue, 1000 Fifth Avenue, New York, NY"
        
    def get_urls(self) -> List[str]:
        return [
            "https://www.metmuseum.org/events/whats-on",
            "https://www.metmuseum.org/exhibitions",
            "https://www.metmuseum.org/events/programs/met-creates",
            "https://www.metmuseum.org/events/programs/lectures-and-panels",
            "https://www.metmuseum.org/events/programs/met-live-arts"
        ]
        
    async def parse_events(self, html: str, url: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, 'html.parser')
        events = []
        
        # The Met has different structures for different sections
        if 'exhibitions' in url:
            # Parse exhibitions
            exhibitions = soup.find_all('div', class_='exhibition-object__content-wrapper') or \
                         soup.find_all('article', {'data-testid': 'exhibition-card'})
            
            for exhibit in exhibitions[:15]:
                title_elem = exhibit.find('h2') or exhibit.find('h3') or \
                            exhibit.find('div', class_='exhibition-object__title')
                
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                
                # Extract dates - Met often shows date ranges
                date_elem = exhibit.find('div', class_='exhibition-object__date') or \
                           exhibit.find('p', class_='exhibition-date')
                
                if date_elem:
                    date_text = date_elem.get_text(strip=True)
                    # Extract opening date from range
                    date_match = re.search(r'(\w+\s+\d+,?\s+\d{4})', date_text)
                    if date_match:
                        date = self.parse_date(date_match.group(1))
                        if date:
                            # Get description
                            desc_elem = exhibit.find('div', class_='exhibition-object__short-description') or \
                                       exhibit.find('p')
                            description = desc_elem.get_text(strip=True)[:200] if desc_elem else ""
                            
                            events.append(self.create_event(
                                title=title,
                                date=date,
                                description=description,
                                event_type='Exhibition',
                                url=url
                            ))
                            
        else:
            # Parse regular events
            # Look for event cards in various possible containers
            event_cards = soup.find_all('div', class_='event-card') or \
                         soup.find_all('article', class_='program-card') or \
                         soup.find_all('div', class_='card-event')
            
            # Also check for JSON-LD structured data
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, list):
                        for item in data:
                            if item.get('@type') == 'Event':
                                title = item.get('name', '')
                                start_date = item.get('startDate', '')
                                if title and start_date:
                                    date = self.parse_date(start_date)
                                    if date:
                                        events.append(self.create_event(
                                            title=title,
                                            date=date,
                                            description=item.get('description', '')[:200],
                                            event_type=self.classify_event_type(title, item.get('description', '')),
                                            url=item.get('url', url)
                                        ))
                except:
                    pass
            
            # Parse event cards
            for card in event_cards[:20]:
                title_elem = card.find(['h2', 'h3', 'h4']) or \
                            card.find('a', class_='event-title')
                
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                
                # Extract date
                date_elem = card.find('time') or \
                           card.find('div', class_='event-date') or \
                           card.find('span', class_='date')
                
                if not date_elem:
                    continue
                    
                date_text = date_elem.get('datetime', '') or date_elem.get_text(strip=True)
                date = self.parse_date(date_text)
                
                if not date:
                    continue
                
                # Extract time
                time_elem = card.find('span', class_='event-time') or \
                           card.find('div', class_='time')
                time = self.parse_time(time_elem.get_text(strip=True)) if time_elem else None
                
                # Extract description
                desc_elem = card.find('p') or card.find('div', class_='description')
                description = desc_elem.get_text(strip=True)[:200] if desc_elem else ""
                
                # Try to determine event type from card classes or text
                event_type = None
                card_classes = ' '.join(card.get('class', []))
                if 'lecture' in card_classes:
                    event_type = 'Lecture'
                elif 'performance' in card_classes:
                    event_type = 'Performance'
                elif 'family' in card_classes:
                    event_type = 'Family Program'
                elif 'tour' in card_classes:
                    event_type = 'Tour'
                
                events.append(self.create_event(
                    title=title,
                    date=date,
                    time=time,
                    description=description,
                    event_type=event_type,
                    url=url
                ))
                
        return events
