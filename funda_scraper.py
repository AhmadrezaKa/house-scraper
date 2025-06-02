import time
import json
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FundaScraper:
    def __init__(self, area="amsterdam", want_to="rent", find_past=False, n_pages=1, headless=True):
        """
        Initialize the Funda Scraper
        
        Args:
            area (str): Area to search in (e.g., "amsterdam", "rotterdam")
            want_to (str): Type of listing ("rent" or "buy")
            find_past (bool): Whether to search for past listings
            n_pages (int): Number of pages to scrape
            headless (bool): Whether to run browser in headless mode
        """
        self.base_url = "https://www.fundainbusiness.nl"
        self.area = area.lower()
        self.want_to = want_to.lower()
        self.find_past = find_past
        self.n_pages = n_pages
        self.headless = headless
        
        # Construct the URL based on parameters
        self.search_url = self._construct_search_url()
        self.setup_driver()
        
    def _construct_search_url(self):
        """Construct the search URL based on parameters"""
        base = f"{self.base_url}/agrarische-grond/"
        params = []
        
        if self.area:
            params.append(f"area={self.area}")
        if self.want_to:
            params.append(f"type={self.want_to}")
        if self.find_past:
            params.append("status=sold")
            
        return f"{base}?{'&'.join(params)}"
        
    def setup_driver(self):
        """Setup Selenium WebDriver with appropriate options"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        
        # Add random user agent
        ua = UserAgent()
        chrome_options.add_argument(f'user-agent={ua.random}')
        
        # Add other options to avoid detection
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
    def run(self, raw_data=False):
        """
        Run the scraper and return the results
        
        Args:
            raw_data (bool): If True, return raw data without processing
            
        Returns:
            pandas.DataFrame: DataFrame containing the scraped data
        """
        listings = []
        current_page = 1
        
        try:
            while current_page <= self.n_pages:
                url = f"{self.search_url}&page={current_page}"
                logger.info(f"Scraping page {current_page}")
                
                self.driver.get(url)
                time.sleep(2)  # Wait for page to load
                
                # Wait for listings to be present
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "search-result"))
                )
                
                # Parse the page
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                listing_elements = soup.find_all("div", class_="search-result")
                
                if not listing_elements:
                    logger.info("No more listings found")
                    break
                
                for element in listing_elements:
                    listing_data = self._extract_listing_data(element)
                    if listing_data:
                        listings.append(listing_data)
                
                current_page += 1
                
        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")
        finally:
            self.close()
        
        if raw_data:
            return listings
        
        # Convert to DataFrame and process
        df = pd.DataFrame(listings)
        if not df.empty:
            # Clean up price column
            df['price'] = df['price'].str.replace('€', '').str.replace('.', '').str.replace(',', '.').astype(float)
            
            # Extract details into separate columns
            details_df = pd.json_normalize(df['details'])
            df = pd.concat([df.drop('details', axis=1), details_df], axis=1)
            
        return df
    
    def _extract_listing_data(self, element):
        """Extract data from a single listing element"""
        try:
            # Extract basic information
            title = element.find("h2", class_="search-result__header-title").text.strip()
            price = element.find("span", class_="search-result-price").text.strip()
            location = element.find("h4", class_="search-result__header-subtitle").text.strip()
            
            # Extract details
            details = {}
            detail_elements = element.find_all("li", class_="search-result-kenmerken-item")
            for detail in detail_elements:
                label = detail.find("span", class_="search-result-kenmerken-label").text.strip()
                value = detail.find("span", class_="search-result-kenmerken-value").text.strip()
                details[label] = value
            
            return {
                "title": title,
                "price": price,
                "location": location,
                "details": details,
                "url": element.find("a")["href"] if element.find("a") else None
            }
            
        except Exception as e:
            logger.error(f"Error extracting listing data: {str(e)}")
            return None
    
    def close(self):
        """Close the browser"""
        if hasattr(self, 'driver'):
            self.driver.quit()

if __name__ == "__main__":
    # Example usage
    scraper = FundaScraper(
        area="amsterdam",
        want_to="rent",
        find_past=False,
        n_pages=1
    )
    df = scraper.run()
    print(df.head()) 