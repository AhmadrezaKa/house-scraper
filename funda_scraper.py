import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FundaScraper:
    def __init__(self, area="amsterdam", want_to="rent", n_pages=1):
        """
        Initialize the Funda Scraper
        
        Args:
            area (str): Area to search in (e.g., "amsterdam", "rotterdam")
            want_to (str): Type of listing ("rent" or "buy")
            n_pages (int): Number of pages to scrape
        """
        self.base_url = "https://www.fundainbusiness.nl"
        self.area = area.lower()
        self.want_to = want_to.lower()
        self.n_pages = n_pages
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def _get_page(self, page_num):
        """Get the HTML content of a page"""
        url = f"{self.base_url}/agrarische-grond/?area={self.area}&type={self.want_to}&page={page_num}"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
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

    def run(self):
        """Run the scraper and return results as a DataFrame"""
        all_listings = []
        
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
            
            # Be nice to the server
            time.sleep(2)
        
        # Convert to DataFrame
        if all_listings:
            df = pd.DataFrame(all_listings)
            # Clean up price column if it exists
            if 'price' in df.columns:
                df['price'] = df['price'].str.replace('€', '').str.replace('.', '').str.replace(',', '.').str.strip()
            return df
        return pd.DataFrame()

if __name__ == "__main__":
    # Example usage
    scraper = FundaScraper(
        area="amsterdam",
        want_to="rent",
        n_pages=1
    )
    df = scraper.run()
    print("\nFirst few listings:")
    print(df.head()) 