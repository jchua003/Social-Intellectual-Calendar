"""
Museum-Specific Scraping Solutions
Each museum requires a different approach based on their technology stack
"""

import requests
import json
from datetime import datetime
from bs4 import BeautifulSoup
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc

class MuseumSpecificScrapers:
    def __init__(self):
        self.events = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json, text/html, */*',
            'Accept-Language': 'en-US,en;q=0.9',
        })
    
    # ========== MOMA ==========
    def scrape_moma_api(self):
        """MoMA uses a WordPress backend with REST API"""
        print("Scraping MoMA via API...")
        
        # MoMA potential endpoints (discovered via DevTools)
        endpoints = [
            # WordPress REST API endpoints
            'https://www.moma.org/wp-json/wp/v2/events',
            'https://www.moma.org/wp-json/tribe/events/v1/events',
            
            # Custom endpoints
            'https://www.moma.org/calendar/api/events',
            'https://www.moma.org/api/v1/calendar/events',
            
            # AJAX endpoints
            'https://www.moma.org/wp-admin/admin-ajax.php'
        ]
        
        # Try WordPress Events Calendar API
        params = {
            'per_page': 50,
            'start_date': datetime.now().strftime('%Y-%m-%d'),
            'orderby': 'date',
            'order': 'asc',
            'status': 'publish'
        }
        
        for endpoint in endpoints:
            try:
                if 'admin-ajax' in endpoint:
                    # WordPress AJAX approach
                    data = {
                        'action': 'tribe_events_list',
                        'page': 1,
                        'event_display': 'list'
                    }
                    response = self.session.post(endpoint, data=data)
                else:
                    response = self.session.get(endpoint, params=params)
                
                if response.status_code == 200:
                    print(f"Success with endpoint: {endpoint}")
                    return self.parse_moma_response(response.json())
            except Exception as e:
                continue
        
        # Fallback to GraphQL if REST fails
        return self.scrape_moma_graphql()
    
    def scrape_moma_graphql(self):
        """Some museums use GraphQL for their data"""
        graphql_endpoint = 'https://www.moma.org/graphql'
        
        query = """
        query GetEvents($first: Int!, $after: String) {
            events(first: $first, after: $after, where: {status: "publish"}) {
                nodes {
                    id
                    title
                    date
                    excerpt
                    eventDetails {
                        startDate
                        endDate
                        time
                        location
                    }
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
        """
        
        variables = {
            'first': 50,
            'after': None
        }
        
        try:
            response = self.session.post(
                graphql_endpoint,
                json={'query': query, 'variables': variables}
            )
            if response.status_code == 200:
                return self.parse_graphql_events(response.json())
        except:
            pass
    
    # ========== MET MUSEUM ==========
    def scrape_met_calendar(self):
        """Met Museum uses a custom calendar system"""
        print("Scraping Met Museum...")
        
        # The Met loads events dynamically
        # First, get the main calendar page to find API endpoints
        calendar_url = 'https://www.metmuseum.org/events/whats-on'
        
        response = self.session.get(calendar_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for data attributes or inline JSON
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and 'window.__INITIAL_STATE__' in script.string:
                # Extract the JSON data
                match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', script.string, re.DOTALL)
                if match:
                    try:
                        data = json.loads(match.group(1))
                        return self.parse_met_initial_state(data)
                    except:
                        pass
        
        # Try API endpoints
        api_endpoints = [
            'https://www.metmuseum.org/api/events/upcoming',
            'https://www.metmuseum.org/events/api/list',
            f'https://www.metmuseum.org/events/api/calendar/{datetime.now().year}/{datetime.now().month}'
        ]
        
        for endpoint in api_endpoints:
            try:
                response = self.session.get(endpoint)
                if response.status_code == 200:
                    return self.parse_met_api_response(response.json())
            except:
                continue
    
    # ========== ASIA SOCIETY ==========
    def scrape_asia_society(self):
        """Asia Society often uses Eventbrite or similar platforms"""
        print("Scraping Asia Society...")
        
        # Check if they use Eventbrite API
        eventbrite_org_id = 'asiasociety'  # Their Eventbrite organization ID
        eventbrite_url = f'https://www.eventbriteapi.com/v3/organizations/{eventbrite_org_id}/events/'
        
        # You would need an Eventbrite API key for this
        # headers = {'Authorization': 'Bearer YOUR_EVENTBRITE_API_KEY'}
        
        # Alternative: Scrape their calendar directly
        calendar_url = 'https://asiasociety.org/new-york/events'
        
        response = self.session.get(calendar_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for structured data
        json_ld = soup.find_all('script', type='application/ld+json')
        for script in json_ld:
            try:
                data = json.loads(script.string)
                if '@type' in data and data['@type'] == 'Event':
                    self.events.append(self.parse_structured_data(data))
            except:
                pass
    
    # ========== NYU IFA ==========
    def scrape_nyu_ifa(self):
        """NYU Institute of Fine Arts - Academic institution approach"""
        print("Scraping NYU IFA...")
        
        # Academic institutions often have simpler structures
        urls = [
            'https://ifa.nyu.edu/events/upcoming.json',  # Try JSON endpoint
            'https://ifa.nyu.edu/events/feed.xml',       # Try RSS feed
            'https://ifa.nyu.edu/apis/events/upcoming'   # Try API
        ]
        
        # Also check for calendar exports
        ical_url = 'https://ifa.nyu.edu/events/calendar.ics'
        
        for url in urls:
            try:
                response = self.session.get(url)
                if response.status_code == 200:
                    if url.endswith('.json'):
                        return self.parse_json_feed(response.json())
                    elif url.endswith('.xml'):
                        return self.parse_rss_feed(response.text)
            except:
                continue
    
    # ========== BROWSER AUTOMATION FALLBACK ==========
    def scrape_with_selenium_stealth(self, museum_config):
        """Ultimate fallback using undetected Chrome"""
        print(f"Using Selenium for {museum_config['name']}...")
        
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Add stealth options
        prefs = {
            'profile.default_content_setting_values.notifications': 2,
            'profile.default_content_settings.popups': 0,
        }
        options.add_experimental_option('prefs', prefs)
        
        # Use undetected chromedriver
        driver = uc.Chrome(options=options, version_main=None)
        
        try:
            # Visit the page
            driver.get(museum_config['url'])
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Simulate human behavior
            driver.execute_script("window.scrollTo(0, 500);")
            import time
            time.sleep(2)
            
            # Look for "Load More" buttons and click them
            try:
                load_more = driver.find_element(By.XPATH, "//button[contains(text(), 'Load More')]")
                driver.execute_script("arguments[0].click();", load_more)
                time.sleep(2)
            except:
                pass
            
            # Get the page source
            page_source = driver.page_source
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Extract events based on common patterns
            events = self.extract_events_from_soup(soup, museum_config)
            
            return events
            
        finally:
            driver.quit()
    
    # ========== PARSING HELPERS ==========
    def parse_structured_data(self, data):
        """Parse Schema.org Event structured data"""
        event = {
            'id': f"{data.get('name', '').replace(' ', '-')}-{datetime.now().timestamp()}",
            'title': data.get('name', ''),
            'date': self.parse_date(data.get('startDate', '')),
            'time': self.extract_time(data.get('startDate', '')),
            'description': data.get('description', '')[:200],
            'location': data.get('location', {}).get('name', ''),
            'url': data.get('url', '')
        }
        return event
    
    def extract_events_from_soup(self, soup, museum_config):
        """Generic event extraction from HTML"""
        events = []
        
        # Common event selectors
        selectors = [
            '.event-item', '.calendar-event', '.event-listing',
            'article.event', 'div.event-card', '.program-item',
            '[class*="event"]', '[class*="calendar"]'
        ]
        
        for selector in selectors:
            event_elements = soup.select(selector)
            if event_elements:
                for elem in event_elements[:20]:  # Limit to 20 events
                    event = self.parse_event_element(elem, museum_config)
                    if event:
                        events.append(event)
                break
        
        return events
    
    def parse_event_element(self, elem, museum_config):
        """Parse individual event element"""
        # Extract title
        title_selectors = ['h2', 'h3', 'h4', '.title', '.event-title']
        title = None
        for selector in title_selectors:
            title_elem = elem.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                break
        
        if not title:
            return None
        
        # Extract date
        date_selectors = ['time', '.date', '.event-date', '[datetime]']
        date = None
        for selector in date_selectors:
            date_elem = elem.select_one(selector)
            if date_elem:
                date_text = date_elem.get('datetime', '') or date_elem.get_text(strip=True)
                date = self.parse_date(date_text)
                if date:
                    break
        
        if not date:
            return None
        
        # Extract other details
        desc_elem = elem.select_one('p, .description, .excerpt')
        description = desc_elem.get_text(strip=True)[:200] if desc_elem else ""
        
        return {
            'id': f"{museum_config['id']}-{hash(title)}-{date.replace('-', '')}",
            'museum': museum_config['id'],
            'museumName': museum_config['name'],
            'title': title,
            'type': 'Special Event',
            'date': date,
            'time': 'See website for time',
            'description': description,
            'location': museum_config['location'],
            'url': museum_config['url']
        }
    
    def parse_date(self, date_string):
        """Parse various date formats"""
        if not date_string:
            return None
            
        # ISO format
        if 'T' in date_string:
            try:
                dt = datetime.fromisoformat(date_string.split('T')[0])
                return dt.strftime('%Y-%m-%d')
            except:
                pass
        
        # Try various formats
        formats = [
            '%Y-%m-%d', '%m/%d/%Y', '%B %d, %Y',
            '%b %d, %Y', '%d %B %Y', '%d %b %Y'
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_string.strip(), fmt)
                return dt.strftime('%Y-%m-%d')
            except:
                continue
        
        return None

# Museum configurations
MUSEUM_CONFIGS = {
    'moma': {
        'id': 'moma',
        'name': 'MoMA',
        'url': 'https://www.moma.org/calendar/',
        'location': 'MoMA, 11 West 53rd Street, New York, NY',
        'scraper': 'scrape_moma_api'
    },
    'met': {
        'id': 'met',
        'name': 'The Met',
        'url': 'https://www.metmuseum.org/events/whats-on',
        'location': 'The Met Fifth Avenue, 1000 Fifth Avenue, New York, NY',
        'scraper': 'scrape_met_calendar'
    },
    'asia': {
        'id': 'asia',
        'name': 'Asia Society',
        'url': 'https://asiasociety.org/new-york/events',
        'location': 'Asia Society, 725 Park Avenue, New York, NY',
        'scraper': 'scrape_asia_society'
    },
    'nyu': {
        'id': 'nyu',
        'name': 'NYU Institute',
        'url': 'https://ifa.nyu.edu/events/upcoming.htm',
        'location': 'NYU Institute of Fine Arts, 1 East 78th Street, New York, NY',
        'scraper': 'scrape_nyu_ifa'
    }
}
