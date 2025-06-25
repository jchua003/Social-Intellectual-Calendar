from typing import List, Dict, Any
from bs4 import BeautifulSoup
from .base import BaseScraper
import re

class NYUScraper(BaseScraper):
    def __init__(self, session):
        super().__init__(session)
        self.museum_id = "nyu"
        self.museum_name = "NYU Institute of Fine Arts"
        self.museum_location = "NYU Institute of Fine Arts, 1 East 78th Street, New York, NY"
        
    def get_urls(self) -> List[str]:
        return [
            "https://ifa.nyu.edu/events/upcoming.htm",
            "https://ifa.nyu.edu/events/lectures.htm",
            "https://ifa.nyu.edu/events/symposia.htm"
        ]
        
    async def parse_events(self, html: str, url: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, 'html.parser')
        events = []
        
        # NYU IFA typically uses a simple list structure
        # Look for event listings
        event_containers = soup.find_all('div', class_='event-item') or \
                          soup.find_all('div', class_='content-item') or \
                          soup.find_all('article')
        
        # If no structured containers, look for date patterns in text
        if not event_containers:
            # Find all paragraphs or divs that might contain events
            text_blocks = soup.find_all(['p', 'div', 'li'])
            
            for block in text_blocks:
                text = block.get_text(strip=True)
                
                # Look for date patterns
                date_match = re.search(r'(\w+\s+\d{1,2},?\s+\d{4})', text)
                if date_match:
                    date = self.parse_date(date_match.group(1))
                    if date:
                        # Extract title - usually before the date
                        title_match = re.search(r'^([^,]+?)(?:\s*,?\s*' + re.escape(date_match.group(1)) + ')', text)
                        if title_match:
                            title = title_match.group(1).strip()
                        else:
                            # Or after the date
                            title_match = re.search(date_match.group(1) + r'\s*[,:]\s*(.+?)(?:\.|$)', text)
                            if title_match:
                                title = title_match.group(1).strip()
                            else:
                                continue
                        
                        # Extract time if present
                        time_match = re.search(r'(\d{1,2}:\d{2}\s*(?:am|pm|AM|PM))', text, re.IGNORECASE)
                        time = self.parse_time(time_match.group(1)) if time_match else None
                        
                        # Determine event type
                        event_type = 'Lecture'  # Default for academic institution
                        if 'symposium' in text.lower() or 'symposia' in url:
                            event_type = 'Symposium'
                        elif 'workshop' in text.lower():
                            event_type = 'Workshop'
                        elif 'colloquium' in text.lower():
                            event_type = 'Symposium'
                        
                        events.append(self.create_event(
                            title=title,
                            date=date,
                            time=time,
                            description=text[:200],
                            event_type=event_type,
                            url=url
                        ))
        else:
            # Parse structured event containers
            for container in event_containers[:20]:
                # Extract title
                title_elem = container.find(['h2', 'h3', 'h4', 'strong']) or \
                            container.find('a', class_='event-title')
                
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                
                # Extract date
                text = container.get_text()
                date_match = re.search(r'(\w+\s+\d{1,2},?\s+\d{4})', text)
                if not date_match:
                    continue
                    
                date = self.parse_date(date_match.group(1))
                if not date:
                    continue
                
                # Extract time
                time_match = re.search(r'(\d{1,2}:\d{2}\s*(?:am|pm|AM|PM))', text, re.IGNORECASE)
                time = self.parse_time(time_match.group(1)) if time_match else None
                
                # Extract description
                desc_elem = container.find('p')
                description = desc_elem.get_text(strip=True)[:200] if desc_elem else ""
                
                # Determine event type
                event_type = None
                if 'lecture' in url or 'lecture' in title.lower():
                    event_type = 'Lecture'
                elif 'symposia' in url or 'symposium' in title.lower():
                    event_type = 'Symposium'
                
                events.append(self.create_event(
                    title=title,
                    date=date,
                    time=time,
                    description=description,
                    event_type=event_type,
                    url=url
                ))
                
        return events
