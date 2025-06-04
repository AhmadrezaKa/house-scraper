import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import logging
import random
import re

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FundaScraper:
    def __init__(self, city="den-bosch", radius="50km"):
        """Initialize the Funda Scraper for agricultural land
        
        Args:
            city (str): City to search in (e.g., "den-bosch", "amsterdam")
            radius (str): Search radius (e.g., "50km")
        """
        self.base_url = "https://www.fundainbusiness.nl"
        self.city = city.lower().replace(" ", "-")
        self.radius = radius
        
        # List of common user agents
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'
        ]
        
        # Initialize session for persistent cookies
        self.session = requests.Session()
        
    def _get_random_headers(self):
        """Generate random headers for each request"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1'
        }

    def get_page(self, page_num=1):
        """Get the HTML content of a page"""
        url = f"{self.base_url}/agrarische-grond/{self.city}/+{self.radius}/"
        if page_num > 1:
            url += f"?page={page_num}"
            
        logger.info(f"Searching URL: {url}")
        
        try:
            # Add random delay before request (between 2 and 5 seconds)
            time.sleep(random.uniform(2, 5))
            
            # Get headers for this request
            headers = self._get_random_headers()
            
            # Make the request using the session
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            
            # Add random delay after request (between 1 and 3 seconds)
            time.sleep(random.uniform(1, 3))
            
            # Check if we hit the verification page
            if "Je bent bijna op de pagina die je zoekt" in response.text:
                logger.warning("Hit verification page. The website is blocking automated access.")
                return None
                
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching page {page_num}: {str(e)}")
            return None

    def parse_listing(self, element):
        """Parse a single listing element"""
        try:
            # Extract basic information
            title = element.find("h2", class_="search-result__header-title")
            price = element.find("span", class_="search-result-price")
            location = element.find("h4", class_="search-result__header-subtitle")
            
            # Extract details
            details = {}
            detail_elements = element.find_all("li", class_="search-result-kenmerken-item")
            for detail in detail_elements:
                label = detail.find("span", class_="search-result-kenmerken-label")
                value = detail.find("span", class_="search-result-kenmerken-value")
                if label and value:
                    details[label.text.strip()] = value.text.strip()
            
            # Extract area if available
            area = None
            if "details" in details:
                area_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:ha|m²)', details["details"])
                if area_match:
                    area = area_match.group(1)
            
            return {
                "title": title.text.strip() if title else "N/A",
                "price": price.text.strip() if price else "N/A",
                "location": location.text.strip() if location else "N/A",
                "area": area,
                "details": details,
                "url": element.find("a")["href"] if element.find("a") else None
            }
        except Exception as e:
            logger.error(f"Error parsing listing: {str(e)}")
            return None

    def scrape(self, n_pages=1):
        """Scrape listings from Funda in Business"""
        all_listings = []
        
        logger.info("Starting scraper for Funda Business agricultural land listings")
        logger.info(f"Search criteria: City={self.city}, Radius={self.radius}")
        
        for page in range(1, n_pages + 1):
            logger.info(f"Scraping page {page}")
            
            # Get page content
            html_content = self.get_page(page)
            if not html_content:
                continue
                
            # Parse the page
            soup = BeautifulSoup(html_content, 'html.parser')
            listings = soup.find_all("div", class_="search-result")
            
            if not listings:
                logger.info("No more listings found")
                break
                
            # Parse each listing
            for listing in listings:
                listing_data = self.parse_listing(listing)
                if listing_data:
                    all_listings.append(listing_data)
            
            logger.info(f"Found {len(listings)} listings on page {page}")
            
            # Add longer random delay between pages (between 5 and 10 seconds)
            if page < n_pages:
                time.sleep(random.uniform(5, 10))
        
        # Convert to DataFrame
        if all_listings:
            df = pd.DataFrame(all_listings)
            # Clean up price column if it exists
            if 'price' in df.columns:
                df['price'] = df['price'].str.replace('€', '').str.replace('.', '').str.replace(',', '.').str.strip()
            logger.info(f"Total listings found: {len(df)}")
            return df
        return pd.DataFrame()

if __name__ == "__main__":
    # Example usage
    scraper = FundaScraper(
        city="den-bosch",
        radius="50km"
    )
    df = scraper.scrape(n_pages=1)
    print("\nFirst few listings:")
    print(df.head()) 