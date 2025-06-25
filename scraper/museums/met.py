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
