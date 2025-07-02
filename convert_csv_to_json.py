import csv
import json
import os
from datetime import datetime
import glob

def convert_csv_to_json():
    # Directory containing CSV files
    csv_directory = "data/csv"
    output_file = "data/events.json"
    
    all_events = []
    event_id = 1
    
    # Museum mapping (based on your HTML)
    museum_mapping = {
        "Asia Society": {"code": "asia", "name": "Asia Society"},
        "MoMA": {"code": "moma", "name": "MoMA"},
        "The Met": {"code": "met", "name": "The Met"},
        "NYU Institute": {"code": "nyu", "name": "NYU Institute"},
        "National Arts Club": {"code": "arts", "name": "National Arts Club"},
        "Explorers Club": {"code": "explorers", "name": "Explorers Club"},
        "Women's History": {"code": "womens-history", "name": "Women's History"}
    }
    
    # Get all CSV files
    csv_files = glob.glob(os.path.join(csv_directory, "*.csv"))
    
    for csv_file in csv_files:
        print(f"Processing: {csv_file}")
        
        # Extract museum name from filename
        filename = os.path.basename(csv_file)
        museum_name_from_file = filename.replace("_events.csv", "").replace("_", " ")
        
        # Find matching museum
        museum_info = None
        for key, value in museum_mapping.items():
            if key.lower() in museum_name_from_file.lower():
                museum_info = value
                break
        
        if not museum_info:
            print(f"Warning: Could not match museum for {filename}")
            continue
        
        # Read CSV file
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                
                for row in csv_reader:
                    # Parse date (assuming format like "July 15, 2025" or "2025-07-15")
                    date_str = row.get('Date', '').strip()
                    formatted_date = parse_date(date_str)
                    
                    if not formatted_date:
                        print(f"Skipping event with invalid date: {date_str}")
                        continue
                    
                    # Create event object
                    event = {
                        "id": f"{museum_info['code']}-{event_id}",
                        "museum": museum_info['code'],
                        "museumName": museum_info['name'],
                        "title": row.get('Name', 'Untitled Event').strip(),
                        "type": row.get('Event Type', 'Special Event').strip(),
                        "date": formatted_date,
                        "time": row.get('Time', '10:00 AM - 5:00 PM').strip(),
                        "description": row.get('Short Description', row.get('Description', '')).strip(),
                        "location": row.get('Location', f"{museum_info['name']}, New York, NY").strip(),
                        "url": row.get('More Info:', '').strip()
                    }
                    
                    # Clean up the URL field (remove double colons if present)
                    if event['url'] and event['url'].startswith(':'):
                        event['url'] = event['url'][1:].strip()
                    
                    all_events.append(event)
                    event_id += 1
                    
        except Exception as e:
            print(f"Error processing {csv_file}: {str(e)}")
    
    # Sort events by date
    all_events.sort(key=lambda x: x['date'])
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Write JSON file
    output_data = {
        "last_updated": datetime.now().isoformat(),
        "events": all_events
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nConverted {len(all_events)} events to {output_file}")
    return output_file

def parse_date(date_str):
    """Parse various date formats to YYYY-MM-DD"""
    if not date_str:
        return None
    
    # Try different date formats
    date_formats = [
        "%Y-%m-%d",           # 2025-07-15
        "%B %d, %Y",          # July 15, 2025
        "%b %d, %Y",          # Jul 15, 2025
        "%m/%d/%Y",           # 07/15/2025
        "%d/%m/%Y",           # 15/07/2025
        "%Y/%m/%d",           # 2025/07/15
        "%d-%m-%Y",           # 15-07-2025
        "%d %B %Y",           # 15 July 2025
        "%d %b %Y",           # 15 Jul 2025
    ]
    
    for fmt in date_formats:
        try:
            date_obj = datetime.strptime(date_str.strip(), fmt)
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    return None

if __name__ == "__main__":
    output_file = convert_csv_to_json()
    print(f"\nJSON file created: {output_file}")
    print("\nNext steps:")
    print("1. Commit and push this file to your GitHub repository")
    print("2. Make sure it's in the path: data/events.json")
    print("3. Your website should now load the events!")
