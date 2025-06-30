import aiohttp
import asyncio
from fake_useragent import UserAgent
import random
from aiohttp_proxy import ProxyConnector
import json
from datetime import datetime

class ProxyRotationScraper:
    def __init__(self):
        self.ua = UserAgent()
        self.events = []
        
        # Free proxy services (for testing - paid proxies are more reliable)
        self.proxy_sources = [
            'https://www.proxy-list.download/api/v1/get?type=http',
            'https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=us',
        ]
        
        # Headers pool
        self.headers_pool = [
            {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0',
            },
            {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Pragma': 'no-cache',
                'Cache-Control': 'no-cache',
            }
        ]
    
    async def get_proxies(self):
        """Fetch list of working proxies"""
        proxies = []
        
        # For production, use a paid proxy service like:
        # - Bright Data (formerly Luminati)
        # - Oxylabs
        # - SmartProxy
        # - Residential proxies work best for avoiding detection
        
        # Example with paid proxy service:
        # proxies = [
        #     'http://username:password@proxy1.service.com:8000',
        #     'http://username:password@proxy2.service.com:8000',
        # ]
        
        return proxies
    
    def get_random_headers(self):
        """Get randomized headers"""
        headers = random.choice(self.headers_pool).copy()
        headers['User-Agent'] = self.ua.random
        
        # Add random variations
        if random.random() > 0.5:
            headers['X-Forwarded-For'] = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
        
        return headers
    
    async def fetch_with_retry(self, session, url, max_retries=3):
        """Fetch URL with retry logic"""
        for attempt in range(max_retries):
            try:
                # Random delay between requests
                await asyncio.sleep(random.uniform(1, 3))
                
                headers = self.get_random_headers()
                
                async with session.get(url, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        return await response.text()
                    elif response.status == 403:
                        print(f"Access denied for {url}, trying different approach...")
                        # Try with different headers or proxy
                        continue
                    
            except Exception as e:
                print(f"Attempt {attempt + 1} failed for {url}: {e}")
                
        return None
    
    async def scrape_with_playwright(self):
        """Alternative: Use Playwright for better JavaScript handling"""
        # Playwright is Microsoft's alternative to Puppeteer/Selenium
        # Better for modern web scraping
        
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            # Launch browser with stealth settings
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-web-security',
                ]
            )
            
            # Create context with random viewport
            context = await browser.new_context(
                viewport={'width': random.randint(1200, 1920), 
                         'height': random.randint(800, 1080)},
                user_agent=self.ua.random,
                locale='en-US',
                timezone_id='America/New_York',
            )
            
            # Add stealth scripts
            await context.add_init_script("""
                // Override navigator properties
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Override chrome property
                window.chrome = {
                    runtime: {},
                };
                
                // Override permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            """)
            
            page = await context.new_page()
            
            # Example: Scrape MoMA
            await page.goto('https://www.moma.org/calendar/', wait_until='networkidle')
            
            # Wait for content and interact like a human
            await page.wait_for_timeout(random.randint(2000, 4000))
            
            # Scroll to trigger lazy loading
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
            await page.wait_for_timeout(random.randint(1000, 2000))
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            
            # Extract content
            content = await page.content()
            
            await browser.close()
            
            return content

# Requirements for advanced scraping:
# pip install aiohttp aiohttp-proxy fake-useragent playwright
# playwright install chromium
