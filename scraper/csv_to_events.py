#!/usr/bin/env python3
"""
CSV to Events Processor - Complete Version
Handles all CSV formats including unnamed columns and "More Info:" columns
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
        """Process a single CSV file with support for various URL column formats"""
        
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
                
                # Print column names for debugging
                print(f"\nColumns in {os.path.basename(filename)}: {reader.fieldnames}")
                
                for row_num, row in enumerate(reader, 1):
                    row_count += 1
                    
                    # Skip empty rows
                    if not any(row.values()):
                        continue
                    
                    # Extract event name
                    event_name = row.get('Name', '').strip()
                    if not event_name:
                        continue
                    
                    # Extract date
                    date_str = row.get('Date', '').strip()
                    date = self.parse_date(date_str)
                    if not date:
                        print(f"Warning: Event '{event_name}' has unparseable date '{date_str}' - including anyway")
                        date = "2025-12-31"  # Placeholder for events with bad dates
                    
                    # Check if date is in the future (after June 2025)
                    try:
                        event_date = datetime.strptime(date, '%Y-%m-%d')
                        if event_date < datetime(2025, 6, 1):
                            continue  # Skip past events
                    except:
                        pass  # Include events with placeholder dates
                    
                    # Extract time
                    time = row.get('Time', '').strip()
                    if not time:
                        time = "See website for time"
                    
                    # Extract event type
                    event_type = row.get('Event Type', '').strip()
                    if not event_type:
                        event_type = 'Special Event'
                    
                    # Extract description - prefer Short Description
                    description = row.get('Short Description', '').strip()
                    if not description:
                        description = row.get('Description', '').strip()
                    if len(description) > 200:
                        description = description[:197] + "..."
                    
                    # Extract location
                    location = row.get('Location', '').strip()
                    if not location or location.lower() in [museum['name'].lower(), museum_id]:
                        location = museum['location']
                    
                    # EXTRACT URL - Check all possible columns
                    url = None
                    
                    # 1. First priority: Check "More Info:" column (with colon)
                    if 'More Info:' in row:
                        url = row.get('More Info:', '').strip()
                        if url:
                            print(f"  Found URL in 'More Info:' column for event: {event_name[:30]}...")
                    
                    # 2. Check unnamed column (empty string key)
                    if not url and '' in row:
                        url = row.get('', '').strip()
                        if url:
                            print(f"  Found URL in unnamed column for event: {event_name[:30]}...")
                    
                    # 3. Check other common URL column names
                    if not url:
                        url_columns = [
                            'More Info', 'more info', 'MoreInfo',  # Without colon
                            'URL', 'url', 'Url',
                            'Link', 'link', 'LINK',
                            'Website', 'website', 'WEBSITE',
                            'Event URL', 'event_url', 'EventURL',
                            'Event Link', 'event_link', 'EventLink',
                            'Registration', 'registration', 'Register',
                            'Info Link', 'info_link', 'InfoLink',
                            'Details', 'More Details', 'Learn More'
                        ]
                        
                        for col in url_columns:
                            if col in row and row[col].strip():
                                url = row[col].strip()
                                print(f"  Found URL in '{col}' column for event: {event_name[:30]}...")
                                break
                    
                    # 4. If still no URL, scan all columns for URL patterns
                    if not url:
                        for key, value in row.items():
                            if value and isinstance(value, str):
                                # Check if value contains URL patterns
                                if any(pattern in value for pattern in ['http://', 'https://', 'www.']):
                                    # Make sure it's likely a URL and not just text mentioning a website
                                    if len(value.strip()) < 200 and ' ' not in value.strip()[:50]:
                                        url = value.strip()
                                        print(f"  Found URL in '{key}' column for event: {event_name[:30]}...")
                                        break
                    
                    # Clean up URL if found
                    if url:
                        # Remove quotes if present
                        url = url.strip('"\'')
                        
                        # Remove trailing punctuation
                        url = url.rstrip('.,;:')
                        
                        # Add https:// if missing
                        if url.startswith('www.'):
                            url = 'https://' + url
                        elif not url.startswith(('http://', 'https://')):
                            # Check if it looks like a URL
                            if '.' in url and ' ' not in url:
                                url = 'https://' + url
                            else:
                                url = None  # Not a valid URL
                    
                    # If no URL found, use museum base URL
                    if not url:
                        url = museum.get('base_url', '')
                    
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
                        'location': location,
                        'url': url
                    }
                    
                    events.append(event)
                
                print(f"Processed {len(events)} future events from {filename}")
                
                # Count events with non-default URLs
                specific_urls = sum(1 for e in events if e['url'] and not e['url'].endswith(('.org', '.com', '.edu')) or '/calendar/' in e['url'] or '/events/' in e['url'])
                if specific_urls > 0:
                    print(f"  ✓ {specific_urls} events have specific event URLs")
                
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
            print(f"Error: Directory '{csv_directory}' not found")
            print("Please ensure your CSV files are in 'scraper/csv_data/' directory")
            return
            
        # Look for CSV files
        csv_files = []
        for file in os.listdir(csv_directory):
            if file.endswith('.csv'):
                # Try to determine museum from filename
                file_lower = file.lower()
                museum_id = None
                
                if 'moma' in file_lower:
                    museum_id = 'moma'
                elif 'met' in file_lower:
                    museum_id = 'met'
                elif 'nyu' in file_lower:
                    museum_id = 'nyu'
                elif 'arts' in file_lower or 'national' in file_lower:
                    museum_id = 'arts'
                elif 'explorer' in file_lower:
                    museum_id = 'explorers'
                elif 'women' in file_lower or 'history' in file_lower:
                    museum_id = 'womens'
                elif 'asia' in file_lower:
                    museum_id = 'asia'
                
                if museum_id:
                    csv_files.append((file, museum_id))
                else:
                    print(f"Warning: Could not determine museum for {file}")
                    print("  Filename should contain: moma, met, nyu, arts, explorer, women, or asia")
        
        if not csv_files:
            print(f"No CSV files found in {csv_directory}")
            return
            
        print(f"\nFound {len(csv_files)} CSV files to process")
        
        # Process each CSV file
        for filename, museum_id in csv_files:
            filepath = os.path.join(csv_directory, filename)
            print(f"\n{'='*60}")
            print(f"Processing: {filename}")
            print(f"Museum: {MUSEUMS[museum_id]['name']}")
            print(f"{'='*60}")
            
            events = self.process_csv_file(filepath, museum_id)
            self.events.extend(events)
                
    def save_events(self, output_file: str = '../data/events.json'):
        """Save all events to JSON file"""
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Sort events by date
        self.events.sort(key=lambda x: x['date'])
        
        # Filter to only include future events (after June 2025)
        future_events = []
        for event in self.events:
            try:
                event_date = datetime.strptime(event['date'], '%Y-%m-%d')
                if event_date >= datetime(2025, 6, 1):
                    future_events.append(event)
            except:
                # Include events with placeholder dates
                future_events.append(event)
        
        # Create output data
        data = {
            'last_updated': datetime.now().isoformat(),
            'events': future_events
        }
        
        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        print(f"\n{'='*60}")
        print(f"PROCESSING COMPLETE")
        print(f"{'='*60}")
        print(f"Total events saved: {len(future_events)}")
        
        # Summary by museum
        museum_counts = {}
        url_counts = {}
        
        for event in future_events:
            museum = event['museumName']
            if museum not in museum_counts:
                museum_counts[museum] = 0
                url_counts[museum] = 0
            
            museum_counts[museum] += 1
            
            # Count events with specific URLs (not just the museum homepage)
            if event.get('url') and (
                '/calendar/' in event['url'] or 
                '/events/' in event['url'] or 
                '/exhibitions/' in event['url'] or
                not event['url'].endswith(('.org', '.com', '.edu'))
            ):
                url_counts[museum] += 1
        
        print("\nEvents by museum:")
        for museum in sorted(museum_counts.keys()):
            total = museum_counts[museum]
            with_urls = url_counts[museum]
            print(f"  {museum}: {total} events ({with_urls} with specific URLs)")
        
        print(f"\nEvents saved to: {output_file}")
        print("\nNext steps:")
        print("1. Check your GitHub Actions to see if the workflow completed")
        print("2. Refresh your website to see events with clickable links")
        print("3. If URLs are missing, check that your CSV has a 'More Info:' column")

def main():
    """Main function"""
    print("CSV to Events Processor")
    print("=" * 60)
    
    processor = CSVEventProcessor()
    
    # Process all CSVs
    processor.process_all_csvs()
    
    if processor.events:
        processor.save_events()
    else:
        print("\nNo events found to process.")
        print("Please check:")
        print("1. CSV files exist in 'csv_data' directory")
        print("2. CSV files have the correct column names")
        print("3. Events have dates after June 2025")

if __name__ == "__main__":
    main()
