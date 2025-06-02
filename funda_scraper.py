import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import logging
import re
import random

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FundaScraper:
    def __init__(self, city="den-bosch", radius="50km", n_pages=1):
        """
        Initialize the Funda Scraper for agricultural land
        
        Args:
            city (str): City to search in (e.g., "den-bosch", "amsterdam")
            radius (str): Search radius (e.g., "50km")
            n_pages (int): Number of pages to scrape
        """
        self.base_url = "https://www.fundainbusiness.nl"
        self.city = city.lower().replace(" ", "-")
        self.radius = radius
        self.n_pages = n_pages
        
        # List of common user agents
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59'
        ]
        
        # Initialize session
        self.session = requests.Session()
        
    def _get_headers(self):
        """Get random headers for the request"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'TE': 'Trailers',
        }
        
    def _get_page(self, page_num):
        """Get the HTML content of a page"""
        url = f"{self.base_url}/agrarische-grond/{self.city}/+{self.radius}/"
        if page_num > 1:
            url += f"?page={page_num}"
            
        logger.info(f"Searching URL: {url}")
        logger.info(f"Search criteria: City={self.city}, Radius={self.radius}, Page={page_num}")
        
        try:
            # Add random delay between requests
            time.sleep(random.uniform(2, 5))
            
            response = self.session.get(url, headers=self._get_headers())
            response.raise_for_status()
            
            # Check if we hit the verification page
            if "Je bent bijna op de pagina die je zoekt" in response.text:
                logger.warning("Hit verification page. The website is blocking automated access.")
                logger.warning("Possible solutions:")
                logger.warning("1. Wait a few minutes before trying again")
                logger.warning("2. Use a different IP address")
                logger.warning("3. Try using a proxy service")
                return None
                
            # Log the response status and size
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response size: {len(response.text)} bytes")
            
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching page {page_num}: {str(e)}")
            return None

    def _parse_listing(self, element):
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

    def run(self):
        """Run the scraper and return results as a DataFrame"""
        all_listings = []
        
        logger.info("Starting scraper for Funda Business agricultural land listings")
        logger.info(f"Website: {self.base_url}")
        logger.info(f"Search parameters: City={self.city}, Radius={self.radius}")
        
        for page in range(1, self.n_pages + 1):
            logger.info(f"Scraping page {page}")
            
            # Get page content
            html_content = self._get_page(page)
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
                listing_data = self._parse_listing(listing)
                if listing_data:
                    all_listings.append(listing_data)
            
            logger.info(f"Found {len(listings)} listings on page {page}")
        
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
        radius="50km",
        n_pages=1
    )
    df = scraper.run()
    print("\nFirst few listings:")
    print(df.head()) 