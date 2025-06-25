import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
import aiohttp
from bs4 import BeautifulSoup
import re
from museums import moma, met, nyu, arts_club, explorers, womens_history, asia_society

class MuseumEventsScraper:
    def __init__(self):
        self.session = None
        self.events = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
        
    async def scrape_all_museums(self) -> List[Dict[str, Any]]:
        """Scrape events from all museums concurrently"""
        scrapers = [
            moma.MoMAScraper(self.session),
            met.MetScraper(self.session),
            nyu.NYUScraper(self.session),
            arts_club.ArtsClubScraper(self.session),
            explorers.ExplorersScraper(self.session),
            womens_history.WomensHistoryScraper(self.session),
            asia_society.AsiaSocietyScraper(self.session)
        ]
        
        # Run all scrapers concurrently
        tasks = [scraper.scrape() for scraper in scrapers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine all events
        all_events = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Error scraping {scrapers[i].__class__.__name__}: {result}")
            else:
                all_events.extend(result)
                
        # Sort events by date
        all_events.sort(key=lambda x: x['date'])
        
        # Add unique IDs
        for i, event in enumerate(all_events):
            event['id'] = f"{event['museum']}-{i+1}"
            
        return all_events
        
    def save_events(self, events: List[Dict[str, Any]], filename: str = 'data/events.json'):
        """Save events to JSON file"""
        output = {
            'last_updated': datetime.now().isoformat(),
            'events': events
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
            
        print(f"Saved {len(events)} events to {filename}")

async def main():
    async with MuseumEventsScraper() as scraper:
        events = await scraper.scrape_all_museums()
        scraper.save_events(events)

if __name__ == "__main__":
    asyncio.run(main())
