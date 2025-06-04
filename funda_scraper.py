import time
import logging
import random
import re
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

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
            
            # Initialize the driver
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            
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
            raise

    def get_page(self, page_num=1):
        """Get the HTML content of a page using Selenium"""
        url = f"{self.base_url}/agrarische-grond/{self.city}/+{self.radius}/"
        if page_num > 1:
            url += f"?page={page_num}"
            
        logger.info(f"Searching URL: {url}")
        
        try:
            # Add random delay before request
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

    def parse_listing(self, element):
        """Parse a single listing element"""
        try:
            # Find the content inner div
            content_inner = element.find("div", class_="search-result-content-inner")
            if not content_inner:
                return None

            # Extract title and location
            header_title = content_inner.find("h2", class_="search-result__header-title")
            header_subtitle = content_inner.find("h4", class_="search-result__header-subtitle")
            
            # Extract price
            price_div = content_inner.find("div", class_="search-result-info-price")
            price = price_div.find("span", class_="search-result-price") if price_div else None
            
            # Extract area
            area = None
            kenmerken = content_inner.find("ul", class_="search-result-kenmerken")
            if kenmerken:
                area_span = kenmerken.find("span", title="Oppervlakte")
                if area_span:
                    area = area_span.text.strip()
            
            # Extract realtor
            realtor = content_inner.find("a", class_="search-result-makelaar")
            realtor_name = realtor.find("span", class_="search-result-makelaar-name") if realtor else None
            
            # Extract URL
            url = None
            title_link = content_inner.find("a", attrs={"data-object-url-tracking": "resultlist"})
            if title_link:
                url = title_link.get("href")
            
            return {
                "title": header_title.text.strip() if header_title else "N/A",
                "type": header_subtitle.text.strip() if header_subtitle else "N/A",
                "price": price.text.strip() if price else "N/A",
                "area": area,
                "realtor": realtor_name.text.strip() if realtor_name else "N/A",
                "url": url
            }
        except Exception as e:
            logger.error(f"Error parsing listing: {str(e)}")
            return None

    def scrape(self, n_pages=1):
        """Scrape listings from Funda in Business"""
        all_listings = []
        
        logger.info("Starting scraper for Funda Business agricultural land listings")
        logger.info(f"Search criteria: City={self.city}, Radius={self.radius}")
        
        try:
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
                
                # Add random delay between pages
                if page < n_pages:
                    time.sleep(random.uniform(3, 6))
            
            # Convert to DataFrame
            if all_listings:
                df = pd.DataFrame(all_listings)
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
        radius="50km"
    )
    df = scraper.scrape(n_pages=1)
    print("\nFirst few listings:")
    print(df.head()) 