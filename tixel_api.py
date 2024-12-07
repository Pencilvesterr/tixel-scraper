import time
import random
import requests
from typing import Dict, Any, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from enum import Enum
from logger_config import setup_logger

logger = setup_logger('tixel_api')

class Category(Enum):
    MUSIC = "music"
    FESTIVAL = "festival"
    SPORTS = "sports"
    THEATRE = "theatre"
    COMEDY = "comedy"
    FOOD_AND_DRINK = "food-and-drink"

    def __str__(self):
        return self.value + "-tickets"

class TixelAPI:
    # Common User-Agent strings
    USER_AGENTS = [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    ]
    
    def __init__(self, base_delay: float = 2.0, max_retries: int = 3):
        self.session = requests.Session()
        self.base_delay = base_delay
        self.logger = logger.getChild('TixelAPI')
        
        self.logger.info(f"Initializing TixelAPI (base_delay={base_delay}s, max_retries={max_retries})")
        
        # Configure retry strategy with exponential backoff
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1.5,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.logger.debug("Session configured with retry strategy")
    
    def _get_headers(self) -> Dict[str, str]:
        """Generate headers that look like a real browser"""
        user_agent = random.choice(self.USER_AGENTS)
        self.logger.debug(f"Selected User-Agent: {user_agent}")
        
        return {
            'User-Agent': user_agent,
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://tixel.com/au/discover/Sydney',
            'Origin': 'https://tixel.com',
            'DNT': '1',
            'Connection': 'keep-alive',
        }
    
    def _make_request(self, url: str) -> Optional[Dict[str, Any]]:
        """Make a request with proper delays and error handling"""
        # Add jitter to the base delay to make it look more natural
        delay = self.base_delay + random.uniform(0.5, 1.5)
        self.logger.debug(f"Waiting {delay:.2f}s before making request")
        time.sleep(delay)
        
        try:
            self.logger.debug(f"Making request to: {url}")
            response = self.session.get(url, headers=self._get_headers())
            response.raise_for_status()
            self.logger.debug(f"Request successful: {response.status_code}")
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error making request to {url}: {str(e)}")
            if hasattr(e.response, 'status_code'):
                self.logger.error(f"Status code: {e.response.status_code}")
            if hasattr(e.response, 'text'):
                self.logger.debug(f"Response text: {e.response.text[:500]}")
            return None

    def get_events_for_category(self, city: str, category: Category, page: int = 1, limit: int = 1000) -> dict:
        """Request events for a specific category and page"""
        self.logger.info(f"Requesting events for {city} in category {category} (page {page})")
        endpoint = f"https://tixel.com/nuxt-api/events-by-city/au/{city}?category={category}&dates=%7B%22named%22:%22this-month%22%7D&genres=&limit={limit}&availableOnly=false&page={page}&sortBy=date&sortOrder=asc"
        
        data = self._make_request(endpoint)
        if not data:
            self.logger.error(f"Failed to fetch data for {category} page {page}")
            return {}
        
        events_count = len(data.get('events', []))
        has_more = data.get('hasMore', False)
        total = data.get('total', 0)
        self.logger.info(f"Retrieved {events_count} events (hasMore={has_more}, total={total})")
        
        return data

    def get_all_events_for_category(self, city: str, category: Category) -> list:
        """Fetch all events for a category, handling pagination"""
        self.logger.info(f"Starting collection of all events for {category} in {city}")
        all_events = []
        page = 1
        
        while True:
            data = self.get_events_for_category(city, category, page)
            events = data.get('events', [])
            if not events:
                self.logger.info(f"No events found for {category} on page {page}")
                break
                
            all_events.extend(events)
            self.logger.debug(f"Added {len(events)} events from page {page}")
            
            # Check if there are more pages
            if not data.get('hasMore', False):
                self.logger.debug(f"No more pages available for {category}")
                break
                
            page += 1
            
        self.logger.info(f"Completed collection for {category}. Total events: {len(all_events)}")
        return all_events
