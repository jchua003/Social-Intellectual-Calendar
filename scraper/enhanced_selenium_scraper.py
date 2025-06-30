#!/usr/bin/env python3
"""
Enhanced Selenium scraper using undetected-chromedriver
For museums that heavily block automation
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
from datetime import datetime
import os

class EnhancedSeleniumScraper:
    def __init__(self):
        self.events = []
        self.driver = None
        
    def setup_driver(self):
        """Setup undetected Chrome driver"""
        options = uc.ChromeOptions()
        
        # For GitHub Actions
        if os.environ.get('GITHUB_ACTIONS'):
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
        
        # Stealth options
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--window-size=1920,1080')
        
        # Initialize undetected driver
        self.driver = uc.Chrome(options=options, version_main=None)
        
        # Additional stealth
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def human_like_behavior(self):
        """Simulate human-like behavior"""
        # Random mouse movements
        self.driver.execute_script("""
            var event = new MouseEvent('mousemove', {
                view: window,
                bubbles: true,
                cancelable: true,
                clientX: Math.random() * window.innerWidth,
                clientY: Math.random() * window.innerHeight
            });
            document.dispatchEvent(event);
        """)
        
        # Random scroll
        scroll_amount = random.randint(100, 300)
        self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        
        # Random delay
        time.sleep(random.uniform(0.5, 2))
        
    def scrape_moma_selenium(self):
        """Scrape MoMA with Selenium"""
        url = "https://www.moma.org/calendar/"
        
        try:
            self.driver.get(url)
            self.human_like_behavior()
            
            # Wait for initial load
            time.sleep(3)
            
            # Try to click "Load More" button if it exists
            try:
                load_more = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Load More')]"))
                )
                self.driver.execute_script("arguments[0].click();", load_more)
                time.sleep(2)
            except:
                pass
            
            # Get page source and parse
            page_source = self.driver.page_source
            # Parse with BeautifulSoup or extract directly
            
            # Example: Extract using Selenium
            events = self.driver.find_elements(By.CSS_SELECTOR, ".calendar-tile, .event-item")
            
            for event in events[:20]:
                try:
                    title = event.find_element(By.CSS_SELECTOR, "h3, h4, .title").text
                    date_elem = event.find_element(By.CSS_SELECTOR, "time, .date")
                    
                    event_data = {
                        'id': f"moma-selenium-{len(self.events)}",
                        'museum': 'moma',
                        'museumName': 'MoMA',
                        'title': title,
                        'date': self.parse_date(date_elem.text),
                        'time': 'See website for time',
                        'description': '',
                        'type': 'Special Event',
                        'location': 'MoMA, 11 West 53rd Street, New York, NY',
                        'url': url
                    }
                    
                    if event_data['date']:
                        self.events.append(event_data)
                        
                except:
                    continue
                    
        except Exception as e:
            print(f"MoMA Selenium error: {e}")
            
    def scrape_all_museums(self):
        """Scrape all museums that might work with Selenium"""
        self.setup_driver()
        
        try:
            # Museums that might work better with Selenium
            museums_to_try = [
                ('MoMA', self.scrape_moma_selenium),
                # Add more museums as needed
            ]
            
            for museum_name, scraper_func in museums_to_try:
                print(f"Selenium scraping {museum_name}...")
                try:
                    scraper_func()
                    print(f"✓ Got {len(self.events)} events from {museum_name}")
                except Exception as e:
                    print(f"✗ {museum_name} failed: {e}")
                    
                # Delay between museums
                time.sleep(random.uniform(5, 10))
                
        finally:
            if self.driver:
                self.driver.quit()
                
        return self.events
    
    def parse_date(self, date_string):
        """Parse date to YYYY-MM-DD format"""
        # Implementation from previous scrapers
        return None
