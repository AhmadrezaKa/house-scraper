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

class FundaBusinessScraper:
    def __init__(self, headless=True):
        """
        Initialize the Funda Business Scraper
        
        Args:
            headless (bool): Whether to run browser in headless mode
        """
        self.base_url = "https://www.fundainbusiness.nl"
        self.agrarische_url = f"{self.base_url}/agrarische-grond/"
        self.setup_driver(headless)
        
    def setup_driver(self, headless):
        """Setup Selenium WebDriver with appropriate options"""
        chrome_options = Options()
        if headless:
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
        
    def get_listings(self, max_pages=5):
        """
        Scrape agricultural land listings from Funda Business
        
        Args:
            max_pages (int): Maximum number of pages to scrape
            
        Returns:
            list: List of dictionaries containing listing data
        """
        listings = []
        current_page = 1
        
        try:
            while current_page <= max_pages:
                url = f"{self.agrarische_url}?page={current_page}"
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
        
        return listings
    
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
    
    def save_to_csv(self, listings, filename="funda_business_listings.csv"):
        """Save scraped listings to CSV file"""
        df = pd.DataFrame(listings)
        df.to_csv(filename, index=False)
        logger.info(f"Saved {len(listings)} listings to {filename}")
    
    def close(self):
        """Close the browser"""
        self.driver.quit()

if __name__ == "__main__":
    # Example usage
    scraper = FundaBusinessScraper(headless=True)
    try:
        listings = scraper.get_listings(max_pages=3)
        scraper.save_to_csv(listings)
    finally:
        scraper.close() 