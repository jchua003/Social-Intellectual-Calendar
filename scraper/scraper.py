import asyncio
import aiohttp
import json
from datetime import datetime
import os
from museums import moma, met, nyu, arts_club, explorers, womens_history, asia_society

class MuseumEventsScraper:
    def __init__(self):
        self.scrapers = []
        self.all_events = []
        
    async def initialize(self):
        """Initialize all museum scrapers with a shared session."""
        # Create session with headers to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        
        # Initialize all scrapers
        self.scrapers = [
            moma.MoMAScraper(self.session),
            met.MetScraper(self.session),
            nyu.NYUScraper(self.session),
            arts_club.ArtsClubScraper(self.session),
            explorers.ExplorersScraper(self.session),
            womens_history.WomensHistoryScraper(self.session),
            asia_society.AsiaSocietyScraper(self.session)
        ]
        
    async def scrape_all(self):
        """Run all scrapers concurrently."""
        tasks = []
        for scraper in self.scrapers:
            print(f"Starting scraper for {scraper.museum_name}...")
            tasks.append(scraper.scrape())
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect all events, handling any errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Error with {self.scrapers[i].museum_name}: {result}")
            elif result:
                print(f"Found {len(result)} events from {self.scrapers[i].museum_name}")
                self.all_events.extend(result)
            else:
                print(f"No events found from {self.scrapers[i].museum_name}")
                
    async def close(self):
        """Close the session."""
        await self.session.close()
        
    def save_events(self, filename='../data/events.json'):
        """Save all events to a JSON file."""
        # Ensure the data directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        data = {
            'last_updated': datetime.now().isoformat(),
            'events': self.all_events
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        print(f"Saved {len(self.all_events)} events to {filename}")

async def main():
    scraper = MuseumEventsScraper()
    try:
        await scraper.initialize()
        await scraper.scrape_all()
        scraper.save_events()
    finally:
        await scraper.close()

if __name__ == "__main__":
    print("Starting museum events scraper...")
    asyncio.run(main())
    print("Scraping complete!")
