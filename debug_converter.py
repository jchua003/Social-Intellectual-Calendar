import csv
import json
import os
from datetime import datetime
import glob

def debug_csv_directory():
    """Debug function to check CSV files"""
    csv_directory = "data/csv"
    
    print("=== DEBUGGING CSV DIRECTORY ===")
    print(f"Current working directory: {os.getcwd()}")
    print(f"CSV directory path: {os.path.abspath(csv_directory)}")
    print(f"CSV directory exists: {os.path.exists(csv_directory)}")
    
    if os.path.exists(csv_directory):
        print(f"\nContents of {csv_directory}:")
        files = os.listdir(csv_directory)
        for file in files:
            filepath = os.path.join(csv_directory, file)
            size = os.path.getsize(filepath)
            print(f"  - {file} ({size} bytes)")
        
        # Check CSV files specifically
        csv_files = glob.glob(os.path.join(csv_directory, "*.csv"))
        print(f"\nFound {len(csv_files)} CSV files:")
        for csv_file in csv_files:
            print(f"  - {csv_file}")
            
            # Try to read first few lines
            try:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    print(f"    First line: {f.readline().strip()}")
            except Exception as e:
                print(f"    Error reading: {e}")
    else:
        print(f"\nERROR: Directory {csv_directory} does not exist!")
        print("Checking parent directory:")
        if os.path.exists("data"):
            print("  data/ exists with contents:", os.listdir("data"))
        else:
            print("  data/ directory doesn't exist either!")

def convert_csv_to_json_with_debug():
    # Directory containing CSV files
    csv_directory = "data/csv"
    output_file = "data/events.json"
    
    print("\n=== STARTING CONVERSION ===")
    
    all_events = []
    event_id = 1
    museums_scraped = []
    
    # Museum mapping (based on your HTML)
    museum_mapping = {
        "Asia Society": {"code": "asia", "name": "Asia Society"},
        "MoMA": {"code": "moma", "name": "MoMA"},
        "The Met": {"code": "met", "name": "The Met"},
        "NYU Institute": {"code": "nyu", "name": "NYU Institute"},
        "National Arts Club": {"code": "arts", "name": "National Arts Club"},
        "Explorers Club": {"code": "explorers", "name": "Explorers Club"},
        "Women's History": {"code": "womens", "name": "Women's History"},
        "Womens History": {"code": "womens", "name": "Women's History"},  # Alternative spelling
    }
    
    # Get all CSV files
    csv_pattern = os.path.join(csv_directory, "*.csv")
    csv_files = glob.glob(csv_pattern)
    
    print(f"\nSearching for CSV files with pattern: {csv_pattern}")
    print(f"Found {len(csv_files)} CSV files")
    
    if len(csv_files) == 0:
        print("\nNo CSV files found! Checking alternative locations...")
        # Try alternative patterns
        alt_patterns = [
            "*.csv",
            "data/*.csv",
            "scraper/*.csv",
            "scraper/data/csv/*.csv"
        ]
        for pattern in alt_patterns:
            alt_files = glob.glob(pattern)
            if alt_files:
                print(f"Found files with pattern '{pattern}': {alt_files}")
    
    for csv_file in csv_files:
        print(f"\n--- Processing: {csv_file} ---")
        
        # Extract museum name from filename
        filename = os.path.basename(csv_file)
        print(f"Filename: {filename}")
        
        # Try different matching strategies
        museum_info = None
        museum_name_from_file = filename.replace("_events.csv", "").replace(".csv", "").replace("_", " ")
        print(f"Extracted museum name: '{museum_name_from_file}'")
        
        # Try exact match first
        if museum_name_from_file in museum_mapping:
            museum_info = museum_mapping[museum_name_from_file]
            print(f"Exact match found: {museum_info}")
        else:
            # Try partial match
            for key, value in museum_mapping.items():
                if key.lower() in museum_name_from_file.lower() or museum_name_from_file.lower() in key.lower():
                    museum_info = value
                    print(f"Partial match found: {key} -> {museum_info}")
                    break
        
        if not museum_info:
            print(f"WARNING: Could not match museum for {filename}")
            # Use a default
            museum_info = {"code": "unknown", "name": museum_name_from_file}
            print(f"Using default: {museum_info}")
        
        museums_scraped.append(museum_info['name'])
        
        # Read CSV file
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                # Read first line to check headers
                first_line = file.readline()
                print(f"Headers: {first_line.strip()}")
                file.seek(0)  # Reset to beginning
                
                csv_reader = csv.DictReader(file)
                row_count = 0
                
                for row in csv_reader:
                    row_count += 1
                    if row_count <= 2:  # Print first 2 rows for debugging
                        print(f"Row {row_count}: {dict(row)}")
                    
                    # Parse date
                    date_str = row.get('Date', '').strip()
                    formatted_date = parse_date(date_str)
                    
                    if not formatted_date:
                        print(f"Skipping event with invalid date: '{date_str}'")
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
                        "url": row.get('More Info:', row.get('More Info', '')).strip()
                    }
                    
                    # Clean up the URL field
                    if event['url'] and event['url'].startswith(':'):
                        event['url'] = event['url'][1:].strip()
                    
                    all_events.append(event)
                    event_id += 1
                
                print(f"Processed {row_count} rows, created {event_id - 1} events")
                    
        except Exception as e:
            print(f"ERROR processing {csv_file}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Sort events by date
    all_events.sort(key=lambda x: x['date'])
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Write JSON file
    output_data = {
        "last_updated": datetime.now().isoformat(),
        "events": all_events,
        "metadata": {
            "total_events": len(all_events),
            "scraping_method": "integrated",
            "museums_scraped": museums_scraped
        }
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n=== CONVERSION COMPLETE ===")
    print(f"Total events converted: {len(all_events)}")
    print(f"Output file: {output_file}")
    
    return output_file

def parse_date(date_str):
    """Parse various date formats to YYYY-MM-DD"""
    if not date_str:
        return None
    
    # Clean the date string
    date_str = date_str.strip()
    
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
        "%B %d",              # July 15 (assume current year)
        "%b %d",              # Jul 15 (assume current year)
    ]
    
    for fmt in date_formats:
        try:
            if "%Y" not in fmt:  # If year not in format, add current year
                date_obj = datetime.strptime(f"{date_str} 2025", f"{fmt} %Y")
            else:
                date_obj = datetime.strptime(date_str, fmt)
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    print(f"  Could not parse date: '{date_str}'")
    return None

if __name__ == "__main__":
    # First debug to see what's in the directory
    debug_csv_directory()
    
    # Then run the conversion with debug output
    output_file = convert_csv_to_json_with_debug()
