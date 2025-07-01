#!/usr/bin/env python3
"""
Integrated Museum Event Scraper
Combines multiple scraping strategies with fallbacks
"""

import json
import os
from datetime import datetime
import asyncio
import aiohttp
from museum_specific_scrapers import MuseumSpecificScrapers, MUSEUM_CONFIGS
from monitoring import ScraperMonitor, MonitoredScraper
from csv_to_events import CSVEventProcessor

class IntegratedMuseumScraper:
    def __init__(self):
        self.events = []
        self.monitor = ScraperMonitor()
        self.specific_scrapers = MuseumSpecificScrapers()
        self.csv_processor = CSVEventProcessor()
        self.strategies = {
            'api': self.try_api_scraping,
            'selenium': self.try_selenium_scraping,
            'csv': self.try_csv_import
        }
        
    async def scrape_all_museums(self):
        """Main method to scrape all museums"""
        print("=" * 50)
        print(f"Starting Integrated Museum Scraper")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
        # Try to scrape each museum
        for museum_id, config in MUSEUM_CONFIGS.items():
            print(f"\n🎯 Processing {config['name']}...")
            
            # Try different strategies in order
            success = False
            events = []
            
            # Strategy 1: Try specific API/scraper
            try:
                scraper_method = getattr(self.specific_scrapers, config['scraper'])
                monitored_scraper = MonitoredScraper(scraper_method, museum_id)
                events = monitored_scraper.scrape()
                
                if events:
                    success = True
                    print(f"✅ API scraping successful: {len(events)} events")
                    
            except Exception as e:
                print(f"❌ API scraping failed: {str(e)}")
            
            # Strategy 2: Try Selenium if API fails
            if not success:
                try:
                    events = await self.try_selenium_scraping(config)
                    if events:
                        success = True
                        print(f"✅ Selenium scraping successful: {len(events)} events")
                        self.monitor.log_scrape_attempt(museum_id, True, len(events))
                except Exception as e:
                    print(f"❌ Selenium scraping failed: {str(e)}")
            
            # Strategy 3: Try CSV import as last resort
            if not success:
                try:
                    events = self.try_csv_import(museum_id)
                    if events:
                        success = True
                        print(f"✅ CSV import successful: {len(events)} events")
                        self.monitor.log_scrape_attempt(museum_id, True, len(events))
                except Exception as e:
                    print(f"❌ CSV import failed: {str(e)}")
                    self.monitor.log_scrape_attempt(museum_id, False, 0, e)
            
            # Add events to collection
            if events:
                self.events.extend(events)
            else:
                print(f"⚠️  No events found for {config['name']}")
        
        # Generate summary
        self.generate_summary()
        
        # Save results
        self.save_events()
        
        # Check if we need manual intervention
        self.check_manual_intervention_needed()
    
    async def try_api_scraping(self, config):
        """Try API-based scraping"""
        # This is handled by museum_specific_scrapers.py
        pass
    
    async def try_selenium_scraping(self, config):
        """Try Selenium-based scraping"""
        from selenium_scraper import StealthMuseumScraper
        
        scraper = StealthMuseumScraper()
        try:
            # Implement museum-specific Selenium scraping
            return scraper.scrape_with_selenium_stealth(config)
        finally:
            scraper.close()
    
    def try_csv_import(self, museum_id):
        """Try importing from CSV files"""
        csv_file = f"csv_data/{museum_id}_events.csv"
        
        if os.path.exists(csv_file):
            return self.csv_processor.process_csv_file(csv_file, museum_id)
        
        # Try alternative naming
        alt_names = {
            'moma': ['MoMA.csv', 'moma_events.csv', 'MOMA_events.csv'],
            'met': ['Met.csv', 'met_events.csv', 'The_Met_events.csv'],
            'nyu': ['NYU.csv', 'nyu_events.csv', 'NYU_IFA_events.csv'],
            'asia': ['Asia_Society.csv', 'asia_society_events.csv'],
            'arts': ['Arts_Club.csv', 'national_arts_club_events.csv'],
            'explorers': ['Explorers.csv', 'explorers_club_events.csv'],
            'womens': ['Womens_History.csv', 'womens_history_events.csv']
        }
        
        if museum_id in alt_names:
            for alt_name in alt_names[museum_id]:
                alt_path = f"csv_data/{alt_name}"
                if os.path.exists(alt_path):
                    return self.csv_processor.process_csv_file(alt_path, museum_id)
        
        return []
    
    def generate_summary(self):
        """Generate scraping summary"""
        print("\n" + "=" * 50)
        print("SCRAPING SUMMARY")
        print("=" * 50)
        
        # Count events by museum
        museum_counts = {}
        for event in self.events:
            museum = event.get('museumName', 'Unknown')
            museum_counts[museum] = museum_counts.get(museum, 0) + 1
        
        print(f"Total events scraped: {len(self.events)}")
        print("\nEvents by museum:")
        for museum, count in sorted(museum_counts.items()):
            print(f"  - {museum}: {count} events")
        
        # Get health status
        health = self.monitor.check_scraper_health()
        print(f"\nScraper health:")
        print(f"  ✅ Healthy: {len(health['healthy'])} museums")
        print(f"  ⚠️  Warning: {len(health['warning'])} museums")
        print(f"  ❌ Critical: {len(health['critical'])} museums")
        
        if health['critical']:
            print(f"\nCritical issues with: {', '.join(health['critical'])}")
    
    def save_events(self):
    """Save all events to JSON file"""
    # Get the correct path to data directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)
    data_dir = os.path.join(root_dir, 'data')
    
    # Ensure data directory exists
    os.makedirs(data_dir, exist_ok=True)
    
    # Remove duplicates
    unique_events = []
    seen_ids = set()
    
    for event in self.events:
        event_id = event.get('id')
        if event_id and event_id not in seen_ids:
            seen_ids.add(event_id)
            unique_events.append(event)
    
    # Sort by date
    unique_events.sort(key=lambda x: x.get('date', ''))
    
    # Save to file
    output = {
        'last_updated': datetime.now().isoformat(),
        'events': unique_events,
        'metadata': {
            'total_events': len(unique_events),
            'scraping_method': 'integrated',
            'museums_scraped': list(set(e.get('museum', '') for e in unique_events))
        }
    }
    
    # Use absolute path
    events_path = os.path.join(data_dir, 'events.json')
    with open(events_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Saved {len(unique_events)} unique events to {events_path}")
    
    # Also print file size for debugging
    file_size = os.path.getsize(events_path)
    print(f"📁 File size: {file_size:,} bytes")

# ========== MAIN EXECUTION ==========
async def main():
    """Main execution function"""
    scraper = IntegratedMuseumScraper()
    
    try:
        await scraper.scrape_all_museums()
        
        # Generate monitoring report
        print("\n" + "=" * 50)
        print("MONITORING REPORT")
        print("=" * 50)
        print(scraper.monitor.generate_report())
        
    except Exception as e:
        print(f"\n❌ Critical error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Log critical failure
        scraper.monitor.send_alert(
            "Critical Scraper Failure",
            f"The integrated scraper failed completely.\nError: {str(e)}"
        )

if __name__ == "__main__":
    # Check if running in GitHub Actions
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        print("Running in GitHub Actions environment")
        
        # Install Chrome for Selenium
        os.system('sudo apt-get update')
        os.system('sudo apt-get install -y google-chrome-stable')
    
    # Run the scraper
    asyncio.run(main())
merge-and-deploy:
    runs-on: ubuntu-latest
    needs: scrape-museum-events
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          ref: main
          
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          
      - name: Merge all events
        run: |
          cd scraper
          python integrated_scraper.py
          
      # ADD THE DEBUGGING STEP HERE ↓↓↓
      - name: Debug file locations
        run: |
          echo "Current directory:"
          pwd
          echo -e "\nLooking for events.json files:"
          find . -name "events.json" -type f -ls
          echo -e "\nDirectory structure:"
          ls -la
          ls -la data/ || echo "No data directory in root"
          ls -la scraper/ || echo "No scraper directory"
          echo -e "\nChecking data directory contents:"
          ls -la data/ || echo "No data directory"
          if [ -f data/events.json ]; then
            echo -e "\nFirst 500 characters of data/events.json:"
            head -c 500 data/events.json
          fi
          
      - name: Ensure events.json is in data directory
        run: |
          # Create data directory if it doesn't exist
          mkdir -p data
          
          # Find and copy events.json to data directory
          if [ -f scraper/events.json ]; then
            cp scraper/events.json data/events.json
            echo "Copied events.json from scraper to data directory"
          elif [ -f events.json ]; then
            cp events.json data/events.json
            echo "Copied events.json from root to data directory"
          fi
          
          # Verify the file exists
          if [ -f data/events.json ]; then
            echo "Success: data/events.json exists"
            echo "File size: $(ls -lh data/events.json)"
            echo "First 100 characters:"
            head -c 100 data/events.json
          else
            echo "ERROR: data/events.json not found!"
            exit 1
          fi
        
      - name: Update events.json
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add -A
          git diff --staged --quiet || git commit -m "Update events from all sources"
          
      - name: Push changes
        uses: ad-m/github-push-action@master
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          branch: main
