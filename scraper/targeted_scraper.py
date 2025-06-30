#!/usr/bin/env python3
"""
Targeted scraper for the 7 specific NYC museums
Uses multiple strategies to maximize success
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc

class TargetedMuseumScraper:
    def __init__(self):
        self.events = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
    def scrape_all_museums(self):
        """Try to scrape all 7 museums using various techniques"""
        museums = [
            {
                'name': 'MoMA',
                'scraper': self.scrape_moma,
                'id': 'moma'
            },
            {
                'name': 'The Met',
                'scraper': self.scrape_met,
                'id': 'met'
            },
            {
                'name': 'NYU Institute',
                'scraper': self.scrape_nyu,
                'id': 'nyu'
            },
            {
                'name': 'National Arts Club',
                'scraper': self.scrape_arts_club,
                'id': 'arts'
            },
            {
                'name': 'Explorers Club',
                'scraper': self.scrape_explorers,
                'id': 'explorers'
            },
            {
                'name': "Women's History",
                'scraper': self.scrape_womens_history,
                'id': 'womens'
            },
            {
                'name': 'Asia Society',
                'scraper': self.scrape_asia_society,
                'id': 'asia'
            }
        ]
        
        for museum in museums:
            print(f"\nAttempting to scrape {museum['name']}...")
            try:
                count_before = len(self.events)
                museum['scraper']()
                count_after = len(self.events)
                added = count_after - count_before
                print(f"✓ {museum['name']}: Added {added} events")
            except Exception as e:
                print(f"✗ {museum['name']}: Failed - {str(e)}")
                
        return self.events
    
    # ========== MoMA ==========
    def scrape_moma(self):
        """Scrape MoMA - they use WordPress"""
        strategies = [
            # Strategy 1: Try WordPress REST API
            ('https://www.moma.org/wp-json/wp/v2/events', self.parse_wordpress_json),
            ('https://www.moma.org/wp-json/tribe/events/v1/events', self.parse_tribe_events),
            
            # Strategy 2: Try calendar page with different user agents
            ('https://www.moma.org/calendar/', self.parse_moma_html),
            
            # Strategy 3: Try their API endpoints
            ('https://www.moma.org/calendar/events.json', self.parse_json_endpoint),
        ]
        
        for url, parser in strategies:
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    parser(response, 'moma', 'MoMA')
                    if self.events:  # If we got events, stop trying
                        break
            except:
                continue
                
    def parse_moma_html(self, response, museum_id, museum_name):
        """Parse MoMA HTML page"""
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for event containers
        selectors = [
            'div.calendar-tile',
            'article.event-listing',
            'div.program-item',
            'div[class*="event"]'
        ]
        
        for selector in selectors:
            events = soup.select(selector)
            if events:
                for event in events[:20]:
                    self.extract_event_from_html(event, museum_id, museum_name)
                break
    
    # ========== Met Museum ==========
    def scrape_met(self):
        """Scrape Met Museum"""
        # The Met often has JSON data embedded in their pages
        url = 'https://www.metmuseum.org/events/whats-on'
        
        try:
            response = self.session.get(url)
            if response.status_code == 200:
                # Look for JSON-LD structured data
                soup = BeautifulSoup(response.text, 'html.parser')
                scripts = soup.find_all('script', type='application/ld+json')
                
                for script in scripts:
                    try:
                        data = json.loads(script.string)
                        if isinstance(data, list):
                            for item in data:
                                if item.get('@type') == 'Event':
                                    self.parse_structured_data(item, 'met', 'The Met')
                        elif data.get('@type') == 'Event':
                            self.parse_structured_data(data, 'met', 'The Met')
                    except:
                        continue
                        
                # Also try regular HTML parsing
                self.parse_met_html(soup, 'met', 'The Met')
                
        except Exception as e:
            print(f"Met scraping error: {e}")
            
    def parse_met_html(self, soup, museum_id, museum_name):
        """Parse Met HTML"""
        # Met-specific selectors
        events = soup.select('div.event-info, article.program-item')
        
        for event in events[:20]:
            self.extract_event_from_html(event, museum_id, museum_name,
                                        location='The Met Fifth Avenue, 1000 Fifth Avenue, New York, NY')
    
    # ========== NYU IFA ==========
    def scrape_nyu(self):
        """Scrape NYU Institute of Fine Arts"""
        urls = [
            'https://ifa.nyu.edu/events/upcoming.htm',
            'https://ifa.nyu.edu/events/lectures.htm',
            'https://ifa.nyu.edu/events/calendar.htm'
        ]
        
        for url in urls:
            try:
                response = self.session.get(url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    # NYU often uses simple HTML structure
                    self.parse_academic_events(soup, 'nyu', 'NYU Institute')
            except:
                continue
    
    # ========== National Arts Club ==========
    def scrape_arts_club(self):
        """Scrape National Arts Club"""
        url = 'https://www.nationalartsclub.org/events'
        
        try:
            # Many clubs use event management systems
            response = self.session.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Check for common event management systems
                if 'tribe-events' in response.text:
                    self.parse_tribe_events_html(soup, 'arts', 'National Arts Club')
                else:
                    self.parse_generic_events(soup, 'arts', 'National Arts Club')
        except:
            pass
    
    # ========== Explorers Club ==========
    def scrape_explorers(self):
        """Scrape Explorers Club"""
        # Explorers Club might require special handling
        urls = [
            'https://explorers.org/events/',
            'https://explorers.org/calendar/',
            'https://explorers.org/public_lectures/'
        ]
        
        for url in urls:
            try:
                # Add referrer to appear more legitimate
                headers = self.session.headers.copy()
                headers['Referer'] = 'https://explorers.org/'
                
                response = self.session.get(url, headers=headers)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    self.parse_generic_events(soup, 'explorers', 'Explorers Club')
            except:
                continue
    
    # ========== Women's History ==========
    def scrape_womens_history(self):
        """Scrape Center for Women's History"""
        url = 'https://www.nyhistory.org/programs'
        
        try:
            response = self.session.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Filter for women's history events
                self.parse_filtered_events(soup, 'womens', "Women's History",
                                         filter_terms=['women', 'female', 'gender', 'feminist'])
        except:
            pass
    
    # ========== Asia Society ==========
    def scrape_asia_society(self):
        """Scrape Asia Society"""
        url = 'https://asiasociety.org/new-york/events'
        
        try:
            response = self.session.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                self.parse_generic_events(soup, 'asia', 'Asia Society')
        except:
            pass
    
    # ========== Parsing Helpers ==========
    def extract_event_from_html(self, element, museum_id, museum_name, location=None):
        """Extract event data from HTML element"""
        try:
            # Find title
            title_elem = element.find(['h2', 'h3', 'h4', 'a'])
            if not title_elem:
                return
            title = title_elem.get_text(strip=True)
            
            # Find date
            date_elem = element.find(['time', '.date', '.event-date'])
            if date_elem:
                date_text = date_elem.get('datetime', '') or date_elem.get_text(strip=True)
                date = self.parse_date(date_text)
                
                if date:
                    # Create event
                    event = {
                        'id': f"{museum_id}-web-{len(self.events)}",
                        'museum': museum_id,
                        'museumName': museum_name,
                        'title': title,
                        'date': date,
                        'time': 'See website for time',
                        'description': '',
                        'type': 'Special Event',
                        'location': location or f'{museum_name}, New York, NY',
                        'url': f'https://{museum_id}.org/events'
                    }
                    
                    # Try to extract description
                    desc_elem = element.find(['p', '.description'])
                    if desc_elem:
                        event['description'] = desc_elem.get_text(strip=True)[:200]
                    
                    self.events.append(event)
                    
        except Exception as e:
            pass
    
    def parse_structured_data(self, data, museum_id, museum_name):
        """Parse schema.org structured data"""
        try:
            date = self.parse_date(data.get('startDate', ''))
            if date:
                event = {
                    'id': f"{museum_id}-web-{len(self.events)}",
                    'museum': museum_id,
                    'museumName': museum_name,
                    'title': data.get('name', ''),
                    'date': date,
                    'time': 'See website for time',
                    'description': data.get('description', '')[:200],
                    'type': 'Special Event',
                    'location': data.get('location', {}).get('name', f'{museum_name}, New York, NY'),
                    'url': data.get('url', '')
                }
                self.events.append(event)
        except:
            pass
    
    def parse_date(self, date_string):
        """Parse date to YYYY-MM-DD format"""
        if not date_string:
            return None
            
        # Try ISO format
        try:
            dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d')
        except:
            pass
            
        # Try common formats
        formats = ['%Y-%m-%d', '%m/%d/%Y', '%B %d, %Y', '%b %d, %Y']
        for fmt in formats:
            try:
                dt = datetime.strptime(date_string.strip(), fmt)
                return dt.strftime('%Y-%m-%d')
            except:
                continue
                
        return None
    
    def parse_wordpress_json(self, response, museum_id, museum_name):
        """Parse WordPress REST API response"""
        try:
            data = response.json()
            for item in data[:20]:
                # WordPress event structure
                date = self.parse_date(item.get('date', ''))
                if date:
                    event = {
                        'id': f"{museum_id}-web-{len(self.events)}",
                        'museum': museum_id,
                        'museumName': museum_name,
                        'title': item.get('title', {}).get('rendered', ''),
                        'date': date,
                        'time': 'See website for time',
                        'description': '',
                        'type': 'Special Event',
                        'location': f'{museum_name}, New York, NY',
                        'url': item.get('link', '')
                    }
                    self.events.append(event)
        except:
            pass
    
    def parse_tribe_events(self, response, museum_id, museum_name):
        """Parse Tribe Events (WordPress plugin) response"""
        try:
            data = response.json()
            events = data.get('events', [])
            
            for item in events[:20]:
                date = self.parse_date(item.get('start_date', ''))
                if date:
                    event = {
                        'id': f"{museum_id}-web-{len(self.events)}",
                        'museum': museum_id,
                        'museumName': museum_name,
                        'title': item.get('title', ''),
                        'date': date,
                        'time': item.get('start_time', 'See website for time'),
                        'description': item.get('description', '')[:200],
                        'type': 'Special Event',
                        'location': item.get('venue', {}).get('venue', f'{museum_name}, New York, NY'),
                        'url': item.get('url', '')
                    }
                    self.events.append(event)
        except:
            pass
    
    def parse_json_endpoint(self, response, museum_id, museum_name):
        """Parse generic JSON endpoint"""
        try:
            data = response.json()
            # Handle different JSON structures
            if isinstance(data, list):
                events = data
            elif 'events' in data:
                events = data['events']
            elif 'data' in data:
                events = data['data']
            else:
                events = []
                
            for item in events[:20]:
                # Generic event parsing
                date = None
                for date_field in ['date', 'start_date', 'event_date', 'startDate']:
                    if date_field in item:
                        date = self.parse_date(item[date_field])
                        break
                        
                if date:
                    title = item.get('title') or item.get('name') or item.get('event_name', '')
                    
                    event = {
                        'id': f"{museum_id}-web-{len(self.events)}",
                        'museum': museum_id,
                        'museumName': museum_name,
                        'title': title,
                        'date': date,
                        'time': 'See website for time',
                        'description': item.get('description', '')[:200],
                        'type': 'Special Event',
                        'location': f'{museum_name}, New York, NY',
                        'url': item.get('url', '') or item.get('link', '')
                    }
                    self.events.append(event)
        except:
            pass
    
    def parse_generic_events(self, soup, museum_id, museum_name):
        """Parse generic event listings"""
        # Common event selectors
        selectors = [
            '.event-item',
            '.calendar-event', 
            'article.event',
            'div[class*="event-"]',
            '.program-item',
            '.listing-item'
        ]
        
        for selector in selectors:
            events = soup.select(selector)
            if events:
                for event in events[:20]:
                    self.extract_event_from_html(event, museum_id, museum_name)
                break
    
    def parse_academic_events(self, soup, museum_id, museum_name):
        """Parse academic institution event format"""
        # Academic sites often use simple paragraph or list structures
        # Look for date patterns in text
        text_blocks = soup.find_all(['p', 'li', 'div'])
        
        for block in text_blocks:
            text = block.get_text()
            # Look for date pattern
            date_match = re.search(r'(\w+\s+\d{1,2},?\s+\d{4})', text)
            if date_match:
                date = self.parse_date(date_match.group(1))
                if date:
                    # Extract title (usually before the date)
                    title = text[:date_match.start()].strip()
                    if len(title) > 10 and len(title) < 200:
                        event = {
                            'id': f"{museum_id}-web-{len(self.events)}",
                            'museum': museum_id,
                            'museumName': museum_name,
                            'title': title,
                            'date': date,
                            'time': 'See website for time',
                            'description': text[:200],
                            'type': 'Lecture',
                            'location': 'NYU Institute of Fine Arts, 1 East 78th Street, New York, NY',
                            'url': 'https://ifa.nyu.edu/events/'
                        }
                        self.events.append(event)
    
    def parse_filtered_events(self, soup, museum_id, museum_name, filter_terms):
        """Parse events and filter by terms"""
        self.parse_generic_events(soup, museum_id, museum_name)
        
        # Filter events
        filtered = []
        for event in self.events:
            text = (event['title'] + ' ' + event['description']).lower()
            if any(term in text for term in filter_terms):
                filtered.append(event)
                
        self.events = filtered
    
    def parse_tribe_events_html(self, soup, museum_id, museum_name):
        """Parse Tribe Events calendar HTML"""
        events = soup.select('.tribe-events-calendar-list__event')
        
        for event in events[:20]:
            title_elem = event.select_one('.tribe-events-calendar-list__event-title')
            date_elem = event.select_one('.tribe-events-calendar-list__event-datetime')
            
            if title_elem and date_elem:
                date = self.parse_date(date_elem.get_text(strip=True))
                if date:
                    event_data = {
                        'id': f"{museum_id}-web-{len(self.events)}",
                        'museum': museum_id,
                        'museumName': museum_name,
                        'title': title_elem.get_text(strip=True),
                        'date': date,
                        'time': 'See website for time',
                        'description': '',
                        'type': 'Special Event',
                        'location': f'{museum_name}, New York, NY',
                        'url': ''
                    }
                    self.events.append(event_data)
