import time
import logging
import re
import random
import pandas as pd
import sys
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

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
        self.setup_driver()
        
    def setup_driver(self):
        """Setup Chrome driver with anti-detection measures"""
        try:
            options = Options()
            
            # Add arguments to make browser less detectable
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-gpu')
            
            # Add random window size
            window_sizes = [(1920, 1080), (1366, 768), (1440, 900)]
            width, height = random.choice(window_sizes)
            options.add_argument(f'--window-size={width},{height}')
            
            # Add random user agent
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            ]
            options.add_argument(f'user-agent={random.choice(user_agents)}')
            
            # Add experimental options
            options.add_experimental_option('excludeSwitches', ['enable-automation'])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Try to initialize the driver with ChromeDriverManager
            try:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
            except Exception as e:
                logger.error("Failed to initialize Chrome driver. Please ensure Chrome is installed.")
                logger.error("Installation instructions:")
                logger.error("Windows: Download and install Chrome from https://www.google.com/chrome/")
                logger.error("Linux: Run 'sudo apt-get install google-chrome-stable'")
                logger.error("macOS: Run 'brew install --cask google-chrome'")
                raise Exception("Chrome installation not found. Please install Chrome browser first.") from e
            
            # Set page load timeout
            self.driver.set_page_load_timeout(30)
            
            # Execute CDP commands to prevent detection
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": random.choice(user_agents)
            })
            
            # Remove webdriver flags
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
        except Exception as e:
            logger.error(f"Error setting up Chrome driver: {str(e)}")
            logger.error("Please ensure Chrome is installed and try again.")
            raise
        
    def _get_page(self, page_num):
        """Get the HTML content of a page using Selenium"""
        url = f"{self.base_url}/agrarische-grond/{self.city}/+{self.radius}/"
        if page_num > 1:
            url += f"?page={page_num}"
            
        logger.info(f"Searching URL: {url}")
        logger.info(f"Search criteria: City={self.city}, Radius={self.radius}, Page={page_num}")
        
        try:
            # Add random delay between requests
            time.sleep(random.uniform(2, 4))
            
            # Load the page
            self.driver.get(url)
            
            # Wait for the content to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "search-result"))
            )
            
            # Add random scrolling behavior
            self._simulate_human_scrolling()
            
            # Check if we hit the verification page
            if "Je bent bijna op de pagina die je zoekt" in self.driver.page_source:
                logger.warning("Hit verification page. The website is blocking automated access.")
                logger.warning("Possible solutions:")
                logger.warning("1. Wait a few minutes before trying again")
                logger.warning("2. Use a different IP address")
                logger.warning("3. Try using a proxy service")
                return None
            
            return self.driver.page_source
            
        except TimeoutException:
            logger.error("Timeout waiting for page to load")
            return None
        except Exception as e:
            logger.error(f"Error fetching page {page_num}: {str(e)}")
            return None
            
    def _simulate_human_scrolling(self):
        """Simulate human-like scrolling behavior"""
        try:
            # Get page height
            page_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Scroll in random steps
            current_position = 0
            while current_position < page_height:
                # Random scroll amount
                scroll_amount = random.randint(100, 300)
                current_position += scroll_amount
                
                # Scroll
                self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                
                # Random pause
                time.sleep(random.uniform(0.1, 0.3))
                
        except Exception as e:
            logger.warning(f"Error during scrolling simulation: {str(e)}")

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
        
        try:
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
                
                # Add random delay between pages
                if page < self.n_pages:
                    time.sleep(random.uniform(3, 6))
            
            # Convert to DataFrame
            if all_listings:
                df = pd.DataFrame(all_listings)
                # Clean up price column if it exists
                if 'price' in df.columns:
                    df['price'] = df['price'].str.replace('€', '').str.replace('.', '').str.replace(',', '.').str.strip()
                logger.info(f"Total listings found: {len(df)}")
                return df
            return pd.DataFrame()
            
        finally:
            # Always close the driver
            self.driver.quit()

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