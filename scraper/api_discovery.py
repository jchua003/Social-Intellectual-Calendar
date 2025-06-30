import requests
import json
from urllib.parse import urljoin, urlparse
import re

class APIDiscovery:
    """Discover and use hidden APIs that museums use for their own websites"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.moma.org/',
            'Origin': 'https://www.moma.org'
        })
        
    def discover_api_endpoints(self, base_url):
        """Discover API endpoints by analyzing network traffic patterns"""
        
        # Common API patterns
        api_patterns = [
            '/api/', '/v1/', '/v2/', '/v3/',
            '/rest/', '/data/', '/json/',
            '/events.json', '/calendar.json',
            '/wp-json/',  # WordPress REST API
            '/graphql',   # GraphQL endpoint
            '/_api/',     # Some custom APIs
            '/ajax/',     # AJAX endpoints
        ]
        
        # Common endpoint names
        endpoint_names = [
            'events', 'calendar', 'programs', 'exhibitions',
            'load-more', 'fetch', 'list', 'search',
            'filter', 'upcoming', 'schedule'
        ]
        
        discovered = []
        
        for pattern in api_patterns:
            for endpoint in endpoint_names:
                urls_to_try = [
                    urljoin(base_url, f"{pattern}{endpoint}"),
                    urljoin(base_url, f"{pattern}{endpoint}.json"),
                    urljoin(base_url, f"{pattern}{endpoint}/upcoming"),
                    urljoin(base_url, f"{pattern}{endpoint}/list"),
                ]
                
                for url in urls_to_try:
                    try:
                        response = self.session.get(url, timeout=5)
                        if response.status_code == 200:
                            # Check if it's JSON
                            try:
                                data = response.json()
                                discovered.append({
                                    'url': url,
                                    'type': 'json',
                                    'sample': str(data)[:200]
                                })
                                print(f"Found API: {url}")
                            except:
                                pass
                    except:
                        pass
                        
        return discovered
    
    def analyze_javascript_files(self, base_url):
        """Analyze JavaScript files to find API endpoints"""
        
        # First, get the main page
        response = self.session.get(base_url)
        
        # Find all JavaScript files
        js_pattern = re.compile(r'<script[^>]+src=["\']([^"\']+\.js)["\']', re.IGNORECASE)
        js_files = js_pattern.findall(response.text)
        
        api_endpoints = []
        
        for js_file in js_files:
            js_url = urljoin(base_url, js_file)
            try:
                js_response = self.session.get(js_url)
                js_content = js_response.text
                
                # Look for API calls in JavaScript
                # Common patterns in JS code
                api_patterns = [
                    r'fetch\(["\']([^"\']+)["\']',  # fetch() calls
                    r'\.get\(["\']([^"\']+)["\']',   # jQuery/axios .get()
                    r'\.post\(["\']([^"\']+)["\']',  # .post() calls
                    r'url:\s*["\']([^"\']+)["\']',   # AJAX url parameter
                    r'endpoint:\s*["\']([^"\']+)["\']',  # endpoint variables
                    r'apiUrl.*?["\']([^"\']+)["\']',  # API URL variables
                    r'/api/[^"\'\\s]+',  # Direct API paths
                ]
                
                for pattern in api_patterns:
                    matches = re.findall(pattern, js_content)
                    for match in matches:
                        if match.startswith('/') or match.startswith('http'):
                            full_url = urljoin(base_url, match)
                            if full_url not in api_endpoints:
                                api_endpoints.append(full_url)
                                
            except:
                pass
                
        return api_endpoints
    
    def check_common_museum_apis(self):
        """Check known museum API endpoints"""
        
        known_apis = {
            'brooklyn': {
                'base': 'https://www.brooklynmuseum.org',
                'endpoints': [
                    '/api/v2/events',
                    '/api/v2/exhibitions',
                    '/api/v2/calendar/events'
                ]
            },
            'cooper_hewitt': {
                'base': 'https://api.collection.cooperhewitt.org/rest/',
                'endpoints': [
                    '?method=cooperhewitt.events.getList',
                    '?method=cooperhewitt.exhibitions.getList'
                ]
            },
            'met': {
                'base': 'https://collectionapi.metmuseum.org',
                'endpoints': [
                    '/public/collection/v1/objects',
                    # The Met's event API is not public, but we can try
                ]
            }
        }
        
        working_apis = []
        
        for museum, config in known_apis.items():
            for endpoint in config['endpoints']:
                url = config['base'] + endpoint
                try:
                    response = self.session.get(url, timeout=10)
                    if response.status_code == 200:
                        working_apis.append({
                            'museum': museum,
                            'url': url,
                            'data': response.json()
                        })
                except:
                    pass
                    
        return working_apis
    
    def intercept_ajax_calls(self, url):
        """
        Use browser developer tools approach to intercept AJAX calls
        This is what you would do manually:
        1. Open Chrome DevTools
        2. Go to Network tab
        3. Filter by XHR/Fetch
        4. Look for API calls when page loads or when clicking "Load More"
        """
        
        # Example findings from manual inspection:
        ajax_endpoints = {
            'moma': [
                'https://www.moma.org/calendar/load-more',
                'https://www.moma.org/api/calendar/events',
                'https://www.moma.org/wp-json/wp/v2/events'
            ],
            'whitney': [
                'https://whitney.org/api/events',
                'https://whitney.org/calendar/api/load'
            ]
        }
        
        return ajax_endpoints

# Example: How to find hidden APIs manually
"""
1. Open Chrome DevTools (F12)
2. Go to Network tab
3. Visit the museum calendar page
4. Look for XHR/Fetch requests
5. Check request headers and parameters
6. Test the endpoints directly

Common things to look for:
- Requests that return JSON data
- Requests with parameters like ?page=1 or ?offset=0
- POST requests with form data
- GraphQL queries
"""
