import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FundaScraper:
    def __init__(self):
        """Initialize the Funda Scraper for agricultural land"""
        self.base_url = "https://www.fundainbusiness.nl/agrarische-grond/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def get_page(self, page_num=1):
        """Get the HTML content of a page"""
        url = f"{self.base_url}?page={page_num}" if page_num > 1 else self.base_url
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
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
            
            return {
                "title": title.text.strip() if title else "N/A",
                "price": price.text.strip() if price else "N/A",
                "location": location.text.strip() if location else "N/A",
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
            
            # Add delay between pages
            if page < n_pages:
                time.sleep(2)
        
        # Convert to DataFrame
        if all_listings:
            df = pd.DataFrame(all_listings)
            logger.info(f"Total listings found: {len(df)}")
            return df
        return pd.DataFrame()

if __name__ == "__main__":
    # Example usage
    scraper = FundaScraper()
    df = scraper.scrape(n_pages=1)
    print("\nFirst few listings:")
    print(df.head()) 