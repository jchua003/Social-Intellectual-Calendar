import csv
import json
import os
from datetime import datetime
import re

class CSVToEvents:
    def __init__(self):
        self.events = []
        # Get the correct paths
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.root_dir = os.path.dirname(self.script_dir)
        self.data_dir = os.path.join(self.root_dir, 'data')
        # Look for CSV files in scraper/csv_data
        self.csv_dir = os.path.join(self.script_dir, 'csv_data')
        
    def clean_text(self, text):
        """Clean and normalize text"""
        if not text:
            return ""
        # Remove extra whitespace and normalize
        text = ' '.join(text.split())
        return text.strip()
    
    def parse_date(self, date_str):
        """Parse various date formats"""
        if not date_str:
            return None
            
        # Try different date formats
        date_formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%B %d, %Y',
            '%b %d, %Y',
            '%Y-%m-%d %H:%M:%S'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        # If no format matches, return the original string
        return date_str
    
    def generate_event_id(self, event):
        """Generate unique ID for event"""
        # Create ID from title, date, and museum
        components = [
            event.get('title', ''),
            event.get('date', ''),
            event.get('museum', '')
        ]
        id_string = '-'.join(components).lower()
        # Remove special characters and spaces
        id_string = re.sub(r'[^a-z0-9-]', '', id_string)
        return id_string[:100]  # Limit length
    
    def process_csv_file(self, filepath, museum_name, museum_id):
        """Process a single CSV file"""
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as file:
                # Try to detect delimiter
                sample = file.read(1024)
                file.seek(0)
                delimiter = ',' if ',' in sample else '\t'
                
                reader = csv.DictReader(file, delimiter=delimiter)
                event_count = 0
                
                for row in reader:
                    # Map CSV columns to event structure
                    event = {
                         'title': self.clean_text(
                            row.get('title',
                                    row.get('Title',
                                            row.get('Name',
                                                    row.get('event_name', ''))))),
                        'description': self.clean_text(
                            row.get('Short Description') or
                            row.get('short_description') or
                            row.get('Short_Description') or
                            row.get('description') or
                            row.get('Description') or
                            row.get('event_description') or
                            ''),
                        'date': self.parse_date(row.get('date', row.get('Date', row.get('event_date', '')))),
                        'time': self.clean_text(row.get('time', row.get('Time', row.get('event_time', '')))),
                        'location': self.clean_text(row.get('location', row.get('Location', row.get('venue', '')))),
                        'museum': museum_id,
                        'museumName': museum_name,
                        'url': self.clean_text(
                            row.get('url') or
                            row.get('URL') or
                            row.get('link') or
                            row.get('More Info:') or
                            row.get('More Info') or
                            ''),
                        'image_url': self.clean_text(row.get('image_url', row.get('image', row.get('Image', '')))),
                        'price': self.clean_text(row.get('price', row.get('Price', row.get('cost', 'Free')))),
                        'registration_url': self.clean_text(row.get('registration_url', row.get('registration', row.get('Registration', '')))),
                        'type': self.clean_text(row.get('type', row.get('Type', row.get('event_type', 'Exhibition')))),
                        'data_source': 'csv'
                    }
                    
                    # Only add if we have at least a title and date
                    if event['title'] and event['date']:
                        event['id'] = self.generate_event_id(event)
                        self.events.append(event)
                        event_count += 1
                        
            print(f"✅ Processed {filepath}: {event_count} events")
            
        except Exception as e:
            print(f"❌ Error processing {filepath}: {str(e)}")
    
    def process_all_csv_files(self):
        """Process all CSV files in the scraper/csv_data directory"""
        # Ensure output directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        print(f"📁 Looking for CSV files in: {self.csv_dir}")
        
        # Look for CSV files
        csv_files = []
        
        # Check in scraper/csv_data directory
        if os.path.exists(self.csv_dir):
            csv_data_files = [f for f in os.listdir(self.csv_dir) if f.endswith('.csv')]
            print(f"Found {len(csv_data_files)} CSV files: {csv_data_files}")
            for file in csv_data_files:
                csv_files.append(os.path.join(self.csv_dir, file))
        else:
            print(f"❌ Directory not found: {self.csv_dir}")
            # Try alternative locations
            alt_csv_dir = os.path.join(self.root_dir, 'data', 'csv_data')
            if os.path.exists(alt_csv_dir):
                print(f"📁 Found alternative CSV directory: {alt_csv_dir}")
                csv_data_files = [f for f in os.listdir(alt_csv_dir) if f.endswith('.csv')]
                print(f"Found {len(csv_data_files)} CSV files: {csv_data_files}")
                for file in csv_data_files:
                    csv_files.append(os.path.join(alt_csv_dir, file))
        
        if len(csv_files) == 0:
            print("❌ No CSV files found! Please add CSV files to scraper/csv_data/ directory")
            # Create empty events.json anyway
            self.save_events()
            return
        
        print(f"📊 Total CSV files to process: {len(csv_files)}")
        
        # Process each CSV file
        for csv_file in csv_files:
            # Extract museum name from filename
            filename = os.path.basename(csv_file)
            museum_name = filename.replace('.csv', '').replace('_', ' ').title()

            # Generate a clean museum_id without trailing '-events' or '_events'
            museum_id = filename.replace('.csv', '').lower()
            museum_id = re.sub(r'[_-]events$', '', museum_id)
            museum_id = museum_id.replace(' ', '-')

            print(f"\n📄 Processing: {csv_file}")
            self.process_csv_file(csv_file, museum_name, museum_id)
    
    def save_events(self):
        """Save all events to JSON file"""
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
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
                'data_source': 'csv',
                'processing_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }
        
        # Save to data/events.json
        events_path = os.path.join(self.data_dir, 'events.json')
        with open(events_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Saved {len(unique_events)} unique events to {events_path}")
        
        # Print file size for debugging
        file_size = os.path.getsize(events_path)
        print(f"📁 File size: {file_size:,} bytes")

def main():
    """Main function"""
    print("Starting CSV to Events conversion...")
    print(f"Working directory: {os.getcwd()}")
    
    converter = CSVToEvents()
    converter.process_all_csv_files()
    converter.save_events()
    
    print("\nCSV processing complete!")

if __name__ == "__main__":
    main()
