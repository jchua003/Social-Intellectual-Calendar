
import json
import os
import sys
import argparse
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import re

class MuseumSpecificScrapers:
    def __init__(self):
        self.events = []
        # Get the correct paths
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.root_dir = os.path.dirname(self.script_dir)
        self.data_dir = os.path.join(self.root_dir, 'data')
        self.setup_driver()
        
    def setup_driver(self):
        """Setup Chrome driver with options"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)
    
    def clean_text(self, text):
        """Clean and normalize text"""
        if not text:
            return ""
        return ' '.join(text.split()).strip()
    
    def generate_event_id(self, event):
        """Generate unique ID for event"""
        components = [
            event.get('title', ''),
            event.get('date', ''),
            event.get('museum', '')
        ]
        id_string = '-'.join(components).lower()
        id_string = re.sub(r'[^a-z0-9-]', '', id_string)
        return id_string[:100]
    
    def scrape_moma(self):
        """Scrape MoMA events"""
        print("Scraping MoMA...")
        try:
            self.driver.get("https://www.moma.org/calendar/")
            time.sleep(3)
            
            # Wait for events to load
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "calendar-tile")))
            
            events = self.driver.find_elements(By.CLASS_NAME, "calendar-tile")
            
            for event in events[:20]:  # Limit to 20 events
                try:
                    title = event.find_element(By.CLASS_NAME, "calendar-tile__title").text
                    date = event.find_element(By.CLASS_NAME, "calendar-tile__date").text
                    
                    event_data = {
                        'title': self.clean_text(title),
                        'date': date,
                        'museum': 'MoMA',
                        'location': 'Museum of Modern Art, New York',
                        'data_source': 'web_scraper'
                    }
                    
                    event_data['id'] = self.generate_event_id(event_data)
                    self.events.append(event_data)
                    
                except Exception as e:
                    continue
                    
            print(f"✅ Scraped {len(self.events)} events from MoMA")
            
        except Exception as e:
            print(f"❌ Error scraping MoMA: {str(e)}")
    
    def scrape_met(self):
        """Scrape The Met events"""
        print("Scraping The Met...")
        try:
            self.driver.get("https://www.metmuseum.org/events/whats-on")
            time.sleep(3)
            
            # Add Met-specific scraping logic here
            # This is a placeholder - you'll need to inspect their actual page structure
            
            print("✅ Completed Met scraping")
            
        except Exception as e:
            print(f"❌ Error scraping The Met: {str(e)}")
    
    def scrape_nyu_ifa(self):
        """Scrape NYU Institute of Fine Arts events"""
        print("Scraping NYU IFA...")
        try:
            self.driver.get("https://ifa.nyu.edu/events/")
            time.sleep(3)
            
            # Add NYU IFA-specific scraping logic here
            
            print("✅ Completed NYU IFA scraping")
            
        except Exception as e:
            print(f"❌ Error scraping NYU IFA: {str(e)}")
    
    def scrape_national_arts_club(self):
        """Scrape National Arts Club events"""
        print("Scraping National Arts Club...")
        try:
            self.driver.get("https://www.nationalartsclub.org/events")
            time.sleep(3)
            
            # Add National Arts Club-specific scraping logic here
            
            print("✅ Completed National Arts Club scraping")
            
        except Exception as e:
            print(f"❌ Error scraping National Arts Club: {str(e)}")
    
    def scrape_explorers_club(self):
        """Scrape The Explorers Club events"""
        print("Scraping The Explorers Club...")
        try:
            self.driver.get("https://www.explorers.org/events/")
            time.sleep(3)
            
            # Add Explorers Club-specific scraping logic here
            
            print("✅ Completed Explorers Club scraping")
            
        except Exception as e:
            print(f"❌ Error scraping Explorers Club: {str(e)}")
    
    def scrape_womens_history(self):
        """Scrape Center for Women's History events"""
        print("Scraping Center for Women's History...")
        try:
            self.driver.get("https://www.nyhistory.org/womens-history")
            time.sleep(3)
            
            # Add Women's History-specific scraping logic here
            
            print("✅ Completed Women's History scraping")
            
        except Exception as e:
            print(f"❌ Error scraping Women's History: {str(e)}")
    
    def scrape_asia_society(self):
        """Scrape Asia Society events"""
        print("Scraping Asia Society...")
        try:
            self.driver.get("https://asiasociety.org/new-york/events")
            time.sleep(3)
            
            # Add Asia Society-specific scraping logic here
            
            print("✅ Completed Asia Society scraping")
            
        except Exception as e:
            print(f"❌ Error scraping Asia Society: {str(e)}")
    
    def save_events(self, museum_name):
        """Save events for specific museum"""
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Create filename for this museum
        filename = f"{museum_name.lower().replace(' ', '_')}_events.json"
        filepath = os.path.join(self.data_dir, filename)
        
        output = {
            'last_updated': datetime.now().isoformat(),
            'museum': museum_name,
            'events': self.events,
            'metadata': {
                'total_events': len(self.events),
                'data_source': 'web_scraper',
                'scraping_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved {len(self.events)} events to {filepath}")
        
        # Also append to main events.json if it exists
        events_path = os.path.join(self.data_dir, 'events.json')
        if os.path.exists(events_path):
            with open(events_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Append new events
            existing_events = data.get('events', [])
            existing_events.extend(self.events)
            
            # Remove duplicates
            unique_events = []
            seen_ids = set()
            for event in existing_events:
                event_id = event.get('id')
                if event_id and event_id not in seen_ids:
                    seen_ids.add(event_id)
                    unique_events.append(event)
            
            data['events'] = unique_events
            data['last_updated'] = datetime.now().isoformat()
            
            with open(events_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
    
    def close(self):
        """Close the driver"""
        if hasattr(self, 'driver'):
            self.driver.quit()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Scrape museum events')
    parser.add_argument('--museum', type=str, required=True, 
                       help='Museum to scrape (moma, met, nyu-ifa, etc.)')
    
    args = parser.parse_args()
    museum = args.museum.lower()
    
    print(f"Starting scraper for {museum}...")
    print(f"Working directory: {os.getcwd()}")
    
    scraper = MuseumSpecificScrapers()
    
    try:
        # Map museum names to scraper methods
        scrapers = {
            'moma': scraper.scrape_moma,
            'met': scraper.scrape_met,
            'nyu-ifa': scraper.scrape_nyu_ifa,
            'national-arts-club': scraper.scrape_national_arts_club,
            'explorers-club': scraper.scrape_explorers_club,
            'womens-history': scraper.scrape_womens_history,
            'asia-society': scraper.scrape_asia_society
        }
        
        if museum in scrapers:
            scrapers[museum]()
            scraper.save_events(museum)
        else:
            print(f"❌ Unknown museum: {museum}")
            sys.exit(1)
            
    finally:
        scraper.close()
    
    print(f"\nScraping complete for {museum}!")

if __name__ == "__main__":
    main()
