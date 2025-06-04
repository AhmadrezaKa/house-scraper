import time
import logging
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def analyze_listing_page(url):
    """Analyze the structure of a Funda listing page"""
    try:
        # Setup Chrome options
        options = Options()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        # Add user agent
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
        
        # Initialize driver
        driver = webdriver.Chrome(options=options)
        
        try:
            # Load the page
            logger.info(f"Loading page: {url}")
            driver.get(url)
            
            # Wait for content to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "object-primary"))
            )
            
            # Get page content
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Initialize data dictionary
            listing_data = {}
            
            # 1. Basic Information
            logger.info("\n=== BASIC INFORMATION ===")
            header = soup.find("div", class_="object-header__content")
            if header:
                # Title and Location
                title_div = header.find("h1")
                if title_div:
                    title = title_div.find("span", class_="object-header__title")
                    subtitle = title_div.find("span", class_="object-header__subtitle")
                    if title:
                        listing_data['title'] = title.text.strip()
                        logger.info(f"Title: {title.text.strip()}")
                    if subtitle:
                        listing_data['location'] = subtitle.text.strip()
                        logger.info(f"Location: {subtitle.text.strip()}")
                
                # Price
                price_div = header.find("div", class_="object-header__pricing")
                if price_div:
                    price = price_div.find("strong", class_="object-header__price")
                    if price:
                        listing_data['price'] = price.text.strip()
                        logger.info(f"Price: {price.text.strip()}")
            
            # 2. Description
            logger.info("\n=== DESCRIPTION ===")
            description_section = soup.find("section", class_="object-description")
            if description_section:
                description_body = description_section.find("div", class_="object-description-body")
                if description_body:
                    listing_data['description'] = description_body.text.strip()
                    logger.info(f"Description: {description_body.text.strip()}")
            
            # 3. Property Characteristics
            logger.info("\n=== PROPERTY CHARACTERISTICS ===")
            kenmerken_body = soup.find("div", class_="object-kenmerken-body")
            if kenmerken_body:
                current_section = None
                for element in kenmerken_body.children:
                    if element.name == 'h3':
                        current_section = element.text.strip()
                        logger.info(f"\n--- {current_section} ---")
                    elif element.name == 'dl':
                        # Process the definition list
                        for dt, dd in zip(element.find_all('dt'), element.find_all('dd')):
                            label = dt.text.strip()
                            value = dd.text.strip()
                            
                            # Clean up the value (remove extra whitespace and newlines)
                            value = ' '.join(value.split())
                            
                            # Store in listing_data with section prefix
                            if current_section:
                                key = f"{current_section}_{label}"
                            else:
                                key = label
                            listing_data[key] = value
                            
                            logger.info(f"{label}: {value}")
                            
                            # Special handling for kadastrale gegevens
                            if current_section == "Kadastrale gegevens":
                                kadaster_title = dt.find("div", class_="kadaster-title")
                                if kadaster_title:
                                    listing_data['kadaster_title'] = kadaster_title.text.strip()
                                    logger.info(f"Kadaster Title: {kadaster_title.text.strip()}")
            
            # Print all collected data
            logger.info("\n=== COLLECTED DATA ===")
            for key, value in listing_data.items():
                logger.info(f"{key}: {value}")
            
            return listing_data
            
        finally:
            driver.quit()
            
    except Exception as e:
        logger.error(f"Error analyzing page: {str(e)}")
        if 'driver' in locals():
            driver.quit()
        return None

if __name__ == "__main__":
    # Test URL
    test_url = "https://www.fundainbusiness.nl/agrarische-grond/heythuysen/object-89102295-arenbos/"
    analyze_listing_page(test_url) 