#!/usr/bin/env python3
"""
Advanced Web Scraper using Selenium with Stealth Mode
Bypasses anti-bot measures and handles JavaScript-rendered content
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium_stealth import stealth
import undetected_chromedriver as uc
import time
import random
import json
from datetime import datetime
import re
from bs4 import BeautifulSoup

class StealthMuseumScraper:
    def __init__(self):
        self.events = []
        self.setup_driver()
        
    def setup_driver(self):
        """Setup Chrome driver with stealth settings"""
        # Option 1: Using undetected-chromedriver (most effective)
        try:
            self.driver = uc.Chrome(
                options=self.get_chrome_options(),
                version_main=None  # Auto-detect Chrome version
            )
            print("Using undetected-chromedriver")
        except:
            # Option 2: Regular Chrome with stealth
            chrome_options = self.get_chrome_options()
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # Apply stealth settings
            stealth(self.driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
            )
            print("Using regular Chrome with stealth")
    
    def get_chrome_options(self):
        """Get Chrome options with anti-detection settings"""
        chrome_options = Options()
        
        # Essential anti-detection arguments
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Additional stealth options
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")
        
        # Randomize user agent
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        ]
        chrome_options.add_argument(f'user-agent={random.choice(user_agents)}')
        
        # For GitHub Actions (headless mode)
        if self.is_github_actions():
            chrome_options.add_argument("--headless")
            
        return chrome_options
    
    def is_github_actions(self):
        """Check if running in GitHub Actions"""
        import os
        return os.environ.get('GITHUB_ACTIONS') == 'true'
    
    def random_delay(self, min_seconds=1, max_seconds=3):
        """Add random delay to mimic human behavior"""
        time.sleep(random.uniform(min_seconds, max_seconds))
    
    def scroll_page(self, pause_time=2):
        """Scroll page to load dynamic content"""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        while True:
            # Scroll down
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self.random_delay(pause_time, pause_time + 1)
            
            # Check if new content loaded
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
    
    def scrape_moma(self):
        """Scrape MoMA using Selenium"""
        print("Scraping MoMA...")
        
        try:
            # Try the main calendar page
            self.driver.get("https://www.moma.org/calendar/")
            self.random_delay(3, 5)
            
            # Wait for content to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "calendar-tile"))
            )
            
            # Scroll to load all events
            self.scroll_page()
            
            # Get page source and parse with BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Find event tiles
            events = soup.find_all('div', class_='calendar-tile') or \
                    soup.find_all('article', class_='event-listing')
            
            for event in events[:20]:  # Limit to 20 events
                try:
                    # Extract title
                    title_elem = event.find('h3') or event.find('h2') or \
                                event.find(class_='event-title')
                    if not title_elem:
                        continue
                    title = title_elem.get_text(strip=True)
                    
                    # Extract date
                    date_elem = event.find(class_='event-date') or \
                               event.find('time')
                    if date_elem:
                        date_text = date_elem.get('datetime', '') or \
                                   date_elem.get_text(strip=True)
                        date = self.parse_date(date_text)
                        
                        if date:
                            # Extract other details
                            desc_elem = event.find('p') or event.find(class_='description')
                            description = desc_elem.get_text(strip=True)[:200] if desc_elem else ""
                            
                            self.events.append({
                                'id': f"moma-{len(self.events)+1}",
                                'museum': 'moma',
                                'museumName': 'MoMA',
                                'title': title,
                                'type': 'Special Event',
                                'date': date,
                                'time': 'See website for time',
                                'description': description,
                                'location': 'MoMA, 11 West 53rd Street, New York, NY',
                                'url': 'https://www.moma.org/calendar/'
                            })
                except Exception as e:
                    print(f"Error parsing MoMA event: {e}")
                    
            print(f"Found {len(self.events)} MoMA events")
            
        except Exception as e:
            print(f"Error scraping MoMA: {e}")
    
    def scrape_met_api(self):
        """Use Met Museum API if available"""
        print("Checking Met Museum API...")
        
        # The Met has a public API for collections, but events might be in a different endpoint
        # This is an example of checking for API endpoints
        
        import requests
        
        # Try potential API endpoints
        api_endpoints = [
            "https://www.metmuseum.org/api/events",
            "https://www.metmuseum.org/api/calendar",
            "https://www.metmuseum.org/events/api/load-more"
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': 'https://www.metmuseum.org/events/whats-on'
        }
        
        for endpoint in api_endpoints:
            try:
                response = requests.get(endpoint, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    print(f"Found API endpoint: {endpoint}")
                    # Process the JSON data
                    # This would depend on the actual API structure
            except:
                continue
    
    def parse_date(self, date_string):
        """Parse date string to YYYY-MM-DD format"""
        # Implementation from previous examples
        try:
            # Try various date formats
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%B %d, %Y', '%b %d, %Y']:
                try:
                    dt = datetime.strptime(date_string, fmt)
                    return dt.strftime('%Y-%m-%d')
                except:
                    continue
        except:
            pass
        return None
    
    def save_events(self):
        """Save scraped events"""
        data = {
            'last_updated': datetime.now().isoformat(),
            'events': self.events
        }
        
        with open('../data/events.json', 'w') as f:
            json.dump(data, f, indent=2)
            
        print(f"Saved {len(self.events)} events")
    
    def close(self):
        """Close the browser"""
        if hasattr(self, 'driver'):
            self.driver.quit()

# For GitHub Actions compatibility
def setup_chrome_for_actions():
    """Setup Chrome for GitHub Actions environment"""
    import os
    import subprocess
    
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        # Install Chrome
        subprocess.run(['sudo', 'apt-get', 'update'])
        subprocess.run(['sudo', 'apt-get', 'install', '-y', 'google-chrome-stable'])

if __name__ == "__main__":
    setup_chrome_for_actions()
    
    scraper = StealthMuseumScraper()
    try:
        scraper.scrape_moma()
        # Add more museum scrapers here
        scraper.save_events()
    finally:
        scraper.close()
