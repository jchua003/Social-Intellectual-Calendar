#!/usr/bin/env python3
"""
CSV to Events Processor - Customized for NYC Museums Format
Converts museum CSV files into the events.json format
"""

import csv
import json
import os
from datetime import datetime
import re
from typing import List, Dict, Any

# Museum configurations
MUSEUMS = {
    'met': {
        'id': 'met',
        'name': 'The Met',
        'location': 'The Met Fifth Avenue, 1000 Fifth Avenue, New York, NY'
    },
    'moma': {
        'id': 'moma',
        'name': 'MoMA',
        'location': 'MoMA, 11 West 53rd Street, New York, NY'
    },
    'nyu': {
        'id': 'nyu',
        'name': 'NYU Institute',
        'location': 'NYU Institute of Fine Arts, 1 East 78th Street, New York, NY'
    },
    'arts': {
        'id': 'arts',
        'name': 'National Arts Club',
        'location': 'National Arts Club, 15 Gramercy Park South, New York, NY'
    },
    'explorers': {
        'id': 'explorers',
        'name': 'Explorers Club',
        'location': 'The Explorers Club, 46 East 70th Street, New York, NY'
    },
    'womens': {
        'id': 'womens',
        'name': "Women's History",
        'location': 'New-York Historical Society, 170 Central Park West, New York, NY'
    },
    'asia': {
        'id': 'asia',
        'name': 'Asia Society',
        'location': 'Asia Society, 725 Park Avenue, New York, NY'
    }
}

class CSVEventProcessor:
    def __init__(self):
        self.events = []
        self.event_counter = 0
        
    def parse_date(self, date_string: str) -> str:
        """Parse various date formats to YYYY-MM-DD"""
        if not date_string:
            return None
            
        date_string = date_string.strip()
        
        # Already in correct format
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_string):
            return date_string
            
        # Try different date formats
        date_formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%m/%d/%y',
            '%d/%m/%Y',
            '%B %d, %Y',
            '%b %d, %Y',
            '%m-%d-%Y',
            '%d-%m-%Y',
            '%Y/%m/%d',
            '%B %d %Y',
            '%b %d %Y',
            '%m.%d.%Y',
            '%d.%m.%Y',
            '%m-%d-%y',  # Added for 2-digit year
            '%m/%d/%y'   # Added for 2-digit year
        ]
        
        for fmt in date_formats:
            try:
                dt = datetime.strptime(date_string, fmt)
                # Handle 2-digit years
                if dt.year < 100:
                    dt = dt.replace(year=dt.year + 2000)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue
                
        # Try to extract date components
        # Match patterns like "July 15, 2025" or "15 July 2025"
        month_names = '(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)'
        
        # Pattern 1: Month DD, YYYY
        pattern1 = rf'({month_names})\s+(\d{{1,2}}),?\s+(\d{{4}})'
        match = re.search(pattern1, date_string, re.IGNORECASE)
        if match:
            try:
                month_str, day, year = match.groups()
                dt = datetime.strptime(f"{month_str} {day} {year}", "%B %d %Y")
                return dt.strftime('%Y-%m-%d')
            except:
                try:
                    dt = datetime.strptime(f"{month_str} {day} {year}", "%b %d %Y")
                    return dt.strftime('%Y-%m-%d')
                except:
                    pass
                    
        print(f"Warning: Could not parse date '{date_string}'")
        return None
        
    def process_csv_file(self, filename: str, museum_id: str) -> List[Dict[str, Any]]:
        """Process a single CSV file with the NYC Museums format"""
        
        if museum_id not in MUSEUMS:
            print(f"Error: Unknown museum ID '{museum_id}'")
            return []
            
        museum = MUSEUMS[museum_id]
        events = []
        
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                # Read the CSV
                reader = csv.DictReader(file)
                
                for row_num, row in enumerate(reader, 1):
                    # Skip empty rows
                    if not any(row.values()):
                        continue
                    
                    # Extract fields based on your CSV format
                    event_name = row.get('Name', '').strip()
                    if not event_name:
                        print(f"Warning: Skipping row {row_num} without event name")
                        continue
                    
                    date_str = row.get('Date', '').strip()
                    date = self.parse_date(date_str)
                    if not date:
                        print(f"Warning: Skipping event '{event_name}' - could not parse date '{date_str}'")
                        continue
                    
                    # Check if date is in the future (after June 2025)
                    event_date = datetime.strptime(date, '%Y-%m-%d')
                    if event_date < datetime(2025, 6, 1):
                        continue  # Skip past events
                    
                    # Time
                    time = row.get('Time', '').strip()
                    if not time:
                        time = "See website for time"
                    
                    # Event Type
                    event_type = row.get('Event Type', '').strip()
                    if not event_type:
                        event_type = 'Special Event'
                    
                    # Description - prefer Short Description if available
                    description = row.get('Short Description', '').strip()
                    if not description:
                        description = row.get('Description', '').strip()
                    if len(description) > 200:
                        description = description[:197] + "..."
                    
                    # Location from CSV (might be more specific than museum default)
                    location = row.get('Location', '').strip()
                    if not location or location.lower() == 'moma' or location.lower() == museum['name'].lower():
                        location = museum['location']
                    
                    # Create event
                    self.event_counter += 1
                    event = {
                        'id': f"{museum_id}-{self.event_counter}-{date.replace('-', '')}",
                        'museum': museum_id,
                        'museumName': museum['name'],
                        'title': event_name,
                        'type': event_type,
                        'date': date,
                        'time': time,
                        'description': description,
                        'location': location
                    }
                    
                    events.append(event)
                
                print(f"Processed {len(events)} future events from {filename}")
                
        except FileNotFoundError:
            print(f"Error: File '{filename}' not found")
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
            import traceback
            traceback.print_exc()
            
        return events
        
    def process_all_csvs(self, csv_directory: str = 'csv_data'):
        """Process all CSV files in a directory"""
        if not os.path.exists(csv_directory):
            print(f"Creating directory '{csv_directory}'...")
            os.makedirs(csv_directory)
            print(f"Please add your CSV files to the '{csv_directory}' directory")
            return
            
        # Look for CSV files
        csv_files = []
        for file in os.listdir(csv_directory):
            if file.endswith('.csv'):
                # Try to determine museum from filename
                file_lower = file.lower()
                if 'moma' in file_lower:
                    csv_files.append((file, 'moma'))
                elif 'met' in file_lower:
                    csv_files.append((file, 'met'))
                elif 'nyu' in file_lower:
                    csv_files.append((file, 'nyu'))
                elif 'arts' in file_lower or 'club' in file_lower:
                    csv_files.append((file, 'arts'))
                elif 'explorer' in file_lower:
                    csv_files.append((file, 'explorers'))
                elif 'women' in file_lower or 'history' in file_lower:
                    csv_files.append((file, 'womens'))
                elif 'asia' in file_lower:
                    csv_files.append((file, 'asia'))
                else:
                    print(f"Warning: Could not determine museum for {file}")
        
        if not csv_files:
            print(f"No CSV files found in {csv_directory}")
            return
            
        for filename, museum_id in csv_files:
            filepath = os.path.join(csv_directory, filename)
            print(f"\nProcessing {filename} for {MUSEUMS[museum_id]['name']}...")
            events = self.process_csv_file(filepath, museum_id)
            self.events.extend(events)
                
    def save_events(self, output_file: str = '../data/events.json'):
        """Save all events to JSON file"""
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Sort events by date
        self.events.sort(key=lambda x: x['date'])
        
        # Filter to only include future events
        future_events = [e for e in self.events if datetime.strptime(e['date'], '%Y-%m-%d') >= datetime(2025, 6, 1)]
        
        # Create output data
        data = {
            'last_updated': datetime.now().isoformat(),
            'events': future_events
        }
        
        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        print(f"\nSuccessfully saved {len(future_events)} future events to {output_file}")
        
def main():
    """Main function"""
    processor = CSVEventProcessor()
    
    print("=== CSV to Events Processor ===\n")
    print("Processing CSV files for NYC Museums Calendar\n")
    
    # Process all CSVs
    processor.process_all_csvs()
    
    if processor.events:
        processor.save_events()
        print("\nDone! Events have been saved to data/events.json")
    else:
        print("\nNo events found to process.")
        print("\nMake sure your CSV files are in the 'csv_data' directory")
        print("and named with the museum name (e.g., 'MoMA.csv', 'Met.csv')")

if __name__ == "__main__":
    main()
