import json
import os
from datetime import datetime
from museum_specific_scrapers import MuseumSpecificScrapers
from csv_to_events import CSVToEvents

class IntegratedScraper:
    def __init__(self):
        self.events = []
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.root_dir = os.path.dirname(self.script_dir)
        self.data_dir = os.path.join(self.root_dir, 'data')
        
    def load_csv_events(self):
        """Load events from CSV processing"""
        csv_events_path = os.path.join(self.data_dir, 'events.json')
        if os.path.exists(csv_events_path):
            try:
                with open(csv_events_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.events.extend(data.get('events', []))
                    print(f"✅ Loaded {len(data.get('events', []))} events from CSV")
            except Exception as e:
                print(f"❌ Error loading CSV events: {str(e)}")
    
    def load_museum_events(self):
        """Load events from museum-specific scrapers"""
        museums = ['moma', 'met', 'nyu-ifa', 'national-arts-club', 
                   'explorers-club', 'womens-history', 'asia-society']
        
        for museum in museums:
            filename = f"{museum.replace('-', '_')}_events.json"
            filepath = os.path.join(self.data_dir, filename)
            
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        events = data.get('events', [])
                        self.events.extend(events)
                        print(f"✅ Loaded {len(events)} events from {museum}")
                except Exception as e:
                    print(f"❌ Error loading {museum} events: {str(e)}")
    
    def generate_event_id(self, event):
        """Generate unique ID for event"""
        import re
        components = [
            event.get('title', ''),
            event.get('date', ''),
            event.get('museum', '')
        ]
        id_string = '-'.join(components).lower()
        id_string = re.sub(r'[^a-z0-9-]', '', id_string)
        return id_string[:100]
    
    def merge_all_events(self):
        """Merge all events from different sources"""
        print("\n🔄 Starting event merge process...")
        
        # Load events from all sources
        self.load_csv_events()
        self.load_museum_events()
        
        # Ensure all events have IDs
        for event in self.events:
            if not event.get('id'):
                event['id'] = self.generate_event_id(event)
        
        print(f"\n📊 Total events collected: {len(self.events)}")
    
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
                'museums_scraped': list(set(e.get('museum', '') for e in unique_events if e.get('museum')))
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

def main():
    """Main function"""
    print("🚀 Starting Integrated Event Scraper...")
    print(f"Working directory: {os.getcwd()}")
    
    scraper = IntegratedScraper()
    scraper.merge_all_events()
    scraper.save_events()
    
    print("\n✨ Integration complete!")

if __name__ == "__main__":
    main()
