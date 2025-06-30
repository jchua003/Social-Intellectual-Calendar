#!/usr/bin/env python3
"""
Hybrid Museum Events Scraper
Combines CSV data with automated web scraping
"""

import json
import os
from datetime import datetime
import subprocess
import sys

class HybridEventsScraper:
    def __init__(self):
        self.csv_events = []
        self.scraped_events = []
        self.all_events = []
        
    def load_csv_events(self):
        """Load events from CSV processor"""
        print("Loading CSV events...")
        
        # Run the CSV processor
        result = subprocess.run([sys.executable, 'csv_to_events.py'], 
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"CSV processor failed: {result.stderr}")
            return False
            
        # Load the generated events
        if os.path.exists('../data/events.json'):
            with open('../data/events.json', 'r') as f:
                data = json.load(f)
                self.csv_events = data.get('events', [])
                print(f"Loaded {len(self.csv_events)} events from CSV")
                return True
        return False
    
    def run_web_scrapers(self):
        """Run automated web scrapers for museums that allow it"""
        print("\nRunning web scrapers...")
        
        # Import scrapers only if they're available
        scrapers_to_try = []
        
        # Try simple API-based scrapers first
        try:
            from simple_scrapers import SimpleAPIScrapers
            scrapers_to_try.append(('API Scrapers', SimpleAPIScrapers))
        except ImportError:
            print("Simple scrapers not available")
        
        # Try Selenium scrapers if available
        try:
            from selenium_scraper import SeleniumMuseumScraper
            scrapers_to_try.append(('Selenium Scrapers', SeleniumMuseumScraper))
        except ImportError:
            print("Selenium scrapers not available")
        
        # Run available scrapers
        for scraper_name, scraper_class in scrapers_to_try:
            print(f"\nTrying {scraper_name}...")
            try:
                scraper = scraper_class()
                events = scraper.scrape_all()
                self.scraped_events.extend(events)
                print(f"Got {len(events)} events from {scraper_name}")
            except Exception as e:
                print(f"{scraper_name} failed: {str(e)}")
                
    def merge_events(self):
        """Merge CSV and scraped events, removing duplicates"""
        print("\nMerging events...")
        
        # Create a set of event signatures from CSV events
        csv_signatures = set()
        for event in self.csv_events:
            # Create signature from title, date, and museum
            sig = f"{event['museum']}|{event['date']}|{event['title'][:50]}"
            csv_signatures.add(sig)
            self.all_events.append(event)
        
        # Add scraped events that don't duplicate CSV events
        added_from_scraping = 0
        for event in self.scraped_events:
            sig = f"{event['museum']}|{event['date']}|{event['title'][:50]}"
            if sig not in csv_signatures:
                self.all_events.append(event)
                added_from_scraping += 1
        
        print(f"Total events: {len(self.all_events)}")
        print(f"  - From CSV: {len(self.csv_events)}")
        print(f"  - From scraping: {added_from_scraping}")
        
    def save_events(self):
        """Save all events to JSON"""
        # Sort by date
        self.all_events.sort(key=lambda x: x['date'])
        
        # Create output
        output = {
            'last_updated': datetime.now().isoformat(),
            'events': self.all_events,
            'sources': {
                'csv_count': len(self.csv_events),
                'scraped_count': len(self.scraped_events),
                'total_count': len(self.all_events)
            }
        }
        
        # Save to file
        os.makedirs('../data', exist_ok=True)
        with open('../data/events.json', 'w') as f:
            json.dump(output, f, indent=2)
            
        print(f"\nSaved {len(self.all_events)} events to data/events.json")
        
def main():
    scraper = HybridEventsScraper()
    
    # Always load CSV events first (reliable source)
    if not scraper.load_csv_events():
        print("Warning: No CSV events loaded")
    
    # Try to add web scraped events
    scraper.run_web_scrapers()
    
    # Merge and save
    scraper.merge_events()
    scraper.save_events()
    
if __name__ == "__main__":
    main()
