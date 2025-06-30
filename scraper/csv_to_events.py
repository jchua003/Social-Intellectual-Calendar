#!/usr/bin/env python3
"""
CSV to Events Processor - Updated to handle all URL column variations
Including "More Info:" with colon
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
        'location': 'The Met Fifth Avenue, 1000 Fifth Avenue, New York, NY',
        'base_url': 'https://www.metmuseum.org'
    },
    'moma': {
        'id': 'moma',
        'name': 'MoMA',
        'location': 'MoMA, 11 West 53rd Street, New York, NY',
        'base_url': 'https://www.moma.org'
    },
    'nyu': {
        'id': 'nyu',
        'name': 'NYU Institute',
        'location': 'NYU Institute of Fine Arts, 1 East 78th Street, New York, NY',
        'base_url': 'https://ifa.nyu.edu'
    },
    'arts': {
        'id': 'arts',
        'name': 'National Arts Club',
        'location': 'National Arts Club, 15 Gramercy Park South, New York, NY',
        'base_url': 'https://www.nationalartsclub.org'
    },
    'explorers': {
        'id': 'explorers',
        'name': 'Explorers Club',
        'location': 'The Explorers Club, 46 East 70th Street, New York, NY',
        'base_url': 'https://explorers.org'
    },
    'womens': {
        'id': 'womens',
        'name': "Women's History",
        'location': 'New-York Historical Society, 170 Central Park West, New York, NY',
        'base_url': 'https://www.nyhistory.org'
    },
    'asia': {
        'id': 'asia',
        'name': 'Asia Society',
        'location': 'Asia Society, 725 Park Avenue, New York, NY',
        'base_url': 'https://asiasociety.org'
    }
}

class CSVEventProcessor:
    def __init__(self):
        self.events = []
        self.event_counter = 0
        self.debug_mode = True  # Set to True to see column details
        
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
            '%m-%d-%y',
            '%m/%d/%y'
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
                
        # Try to extract date components with regex
        patterns = [
            r'(\w+)\s+(\d{1,2}),?\s+(\d{2,4})',  # July 15, 2025
            r'(\d{1,2})\s+(\w+)\s+(\d{2,4})',     # 15 July 2025
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',  # 7/15/25 or 7-15-25
        ]
        
        for pattern in patterns:
            match = re.search(pattern, date_string)
            if match:
                try:
                    if pattern.startswith(r'(\w+)'):  # Month name first
                        month_str, day, year = match.groups()
                        # Try full month name
                        try:
                            dt = datetime.strptime(f"{month_str} {day} {year}", "%B %d %Y")
                        except:
                            # Try abbreviated month name
                            dt = datetime.strptime(f"{month_str} {day} {year}", "%b %d %Y")
                    elif pattern.startswith(r'(\d{1,2})\s+(\w+)'):  # Day month year
                        day, month_str, year = match.groups()
                        try:
                            dt = datetime.strptime(f"{month_str} {day} {year}", "%B %d %Y")
                        except:
                            dt = datetime.strptime(f"{month_str} {day} {year}", "%b %d %Y")
                    else:  # Numeric format
                        month, day, year = match.groups()
                        year = int(year)
                        if year < 100:
                            year += 2000
                        dt = datetime(year, int(month), int(day))
                    
                    return dt.strftime('%Y-%m-%d')
                except:
                    continue
                    
        print(f"Warning: Could not parse date '{date_string}'")
        return None
        
    def process_csv_file(self, filename: str, museum_id: str) -> List[Dict[str, Any]]:
        """Process a single CSV file with various URL column formats"""
        
        if museum_id not in MUSEUMS:
            print(f"Error: Unknown museum ID '{museum_id}'")
            return []
            
        museum = MUSEUMS[museum_id]
        events = []
        row_count = 0
        
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                # Read the CSV
                reader = csv.DictReader(file)
                
                # Debug: Print column names
                if self.debug_mode and row_count == 0:
                    print(f"\nCSV Columns found: {reader.fieldnames}")
                    if 'More Info:' in reader.fieldnames:
                        print("✓ Found 'More Info:' column for URLs")
                    if '' in reader.fieldnames:
                        print("✓ Found unnamed column")
                    print()
                
                for row_num, row in enumerate(reader, 1):
                    row_count += 1
                    
                    # Skip empty rows
                    if not any(row.values()):
                        continue
                    
                    # Extract fields based on CSV format
                    event_name = row.get('Name', '').strip()
                    if not event_name:
                        continue
                    
                    date_str = row.get('Date', '').strip()
                    date = self.parse_date(date_str)
                    if not date:
                        print(f"Warning: Event '{event_name}' has unparseable date '{date_str}' - including anyway")
                        date = "2025-12-31"  # Placeholder date
                    
                    # Check if date is in the future (after June 2025)
                    event_date = datetime.strptime(date, '%Y-%m-%d')
                    if event_date < datetime(2025, 6, 1):
                        continue  # Skip past events
                    
                    # Extract other fields
                    time = row.get('Time', '').strip()
                    if not time:
                        time = "See website for time"
                    
                    event_type = row.get('Event Type', '').strip()
                    if not event_type:
                        event_type = 'Special Event'
                    
                    # Description - prefer Short Description
                    description = row.get('Short Description', '').strip()
                    if not description:
                        description = row.get('Description', '').strip()
                    if len(description) > 200:
                        description = description[:197] + "..."
                    
                    location = row.get('Location', '').strip()
                    if not location or location.lower() in ['explorers club', 'explorers', museum['name'].lower()]:
                        location = museum['location']
                    
                    # EXTRACT URL - Check multiple possible columns
                    url = None
                    
                    # 1. Check "More Info:" column (with colon) - for Explorers Club
                    url = row.get('More Info:', '').strip()
                    
                    # 2. If no URL, check unnamed column (for MoMA)
                    if not url:
                        url = row.get('', '').strip()
                    
                    # 3. If still no URL, check other common field names
                    if not url:
                        url_fields = [
                            'More Info', 'more info', 'MoreInfo',  # Without colon
                            'url', 'URL', 'Url',
                            'link', 'Link', 'LINK',
                            'website', 'Website', 'WEBSITE',
                            'event_url', 'Event URL', 'EventURL',
                            'event_link', 'Event Link', 'EventLink',
                            'registration', 'Registration', 'Register',
                            'info_link', 'Info Link', 'InfoLink',
                            'details', 'Details', 'More Details'
                        ]
                        
                        for field in url_fields:
                            if field in row and row[field].strip():
                                url = row[field].strip()
                                break
                    
                    # 4. If still no URL, scan ALL fields for anything that looks like a URL
                    if not url:
                        for key, value in row.items():
                            if value and any(pattern in str(value) for pattern in ['http://', 'https://', 'www.', '.org', '.com', '.edu']):
                                # Make sure it's not the description or other text field with URL mention
                                if len(value) < 200 and not ' ' in value.strip():  # URLs typically don't have spaces
                                    url = value.strip()
                                    if self.debug_mode:
                                        print(f"Found URL in field '{key}': {url}")
                                    break
                    
                    # Clean up URL if found
                    if url:
                        # Remove any trailing punctuation
                        url = url.rstrip('.,;:')
                        
                        # Add https:// if missing
                        if url.startswith('www.'):
                            url = 'https://' + url
                        elif not url.startswith(('http://', 'https://')):
                            # Check if it looks like a URL
                            if ('.' in url and ' ' not in url and 
                                any(domain in url for domain in ['.org', '.com', '.edu', '.gov', '.net'])):
                                url = 'https://' + url
                    
                    # If still no URL, use museum base URL
                    if not url:
                        url = museum.get('base_url', '')
                        if self.debug_mode and row_num <= 3:
                            print(f"No URL found for '{event_name}', using museum base URL")
                    
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
                    
                    # Always add URL
                    if url:
                        event['url'] = url
                    
                    events.append(event)
                    
                    # Debug: Show first event with URL info
                    if self.debug_mode and row_num == 1:
                        print(f"First event processed:")
                        print(f"  Title: {event['title']}")
                        print(f"  URL: {event.get('url', 'No URL')}")
                        print()
                
                print(f"\nProcessed {len(events)} future events from {filename}")
                
                # Report URL statistics
                events_with_urls = sum(1 for e in events if e.get('url') and not e['url'].endswith(('.org', '.com', '.edu')))
                print(f"Events with specific URLs: {events_with_urls} out of {len(events)}")
                
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
            
        # Process each CSV file
        for filename, museum_id in csv_files:
            filepath = os.path.join(csv_directory, filename)
            print(f"\n{'='*50}")
            print(f"Processing {filename} for {MUSEUMS[museum_id]['name']}")
            print(f"{'='*50}")
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
            
        print(f"\n{'='*50}")
        print(f"FINAL SUMMARY")
        print(f"{'='*50}")
        print(f"Total events saved: {len(future_events)}")
        
        # Count events with URLs by museum
        museum_url_counts = {}
        for event in future_events:
            museum = event['museumName']
            has_url = bool(event.get('url') and not event['url'].endswith(('.org', '.com', '.edu')))
            
            if museum not in museum_url_counts:
                museum_url_counts[museum] = {'total': 0, 'with_urls': 0}
            
            museum_url_counts[museum]['total'] += 1
            if has_url:
                museum_url_counts[museum]['with_urls'] += 1
        
        print("\nEvents by museum:")
        for museum, counts in museum_url_counts.items():
            print(f"  {museum}: {counts['total']} events ({counts['with_urls']} with specific URLs)")

def main():
    """Main function"""
    processor = CSVEventProcessor()
    
    print("=== CSV to Events Processor ===")
    print("Processing museum event CSV files")
    print("Debug mode: ON\n")
    
    # Process all CSVs
    processor.process_all_csvs()
    
    if processor.events:
        processor.save_events()
        print("\nDone! Events have been saved to data/events.json")
    else:
        print("\nNo events found to process.")

if __name__ == "__main__":
    main()
