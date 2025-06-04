import time
import logging
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException

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
            
            # Initialize data dictionary
            listing_data = {}
            
            # 1. Basic Information
            logger.info("\n=== BASIC INFORMATION ===")
            header = driver.find_element(By.CLASS_NAME, "object-header__content")
            if header:
                # Title and Location
                title_div = header.find_element(By.TAG_NAME, "h1")
                title = title_div.find_element(By.CLASS_NAME, "object-header__title")
                subtitle = title_div.find_element(By.CLASS_NAME, "object-header__subtitle")
                
                listing_data['title'] = title.text.strip()
                listing_data['location'] = subtitle.text.strip()
                logger.info(f"Title: {title.text.strip()}")
                logger.info(f"Location: {subtitle.text.strip()}")
                
                # Price
                try:
                    price_div = header.find_element(By.CLASS_NAME, "object-header__pricing")
                    price = price_div.find_element(By.CLASS_NAME, "object-header__price")
                    listing_data['price'] = price.text.strip()
                    logger.info(f"Price: {price.text.strip()}")
                except:
                    logger.info("No price information found")
            
            # 2. Description
            logger.info("\n=== DESCRIPTION ===")
            try:
                # Find and click the expand button
                expand_button = driver.find_element(By.CLASS_NAME, "object-description-open-button")
                logger.info("Found expand button, clicking to show full description...")
                
                # Scroll to the button
                driver.execute_script("arguments[0].scrollIntoView(true);", expand_button)
                time.sleep(1)  # Wait for scroll to complete
                
                # Click the button
                expand_button.click()
                
                # Wait for the description to expand
                time.sleep(2)  # Wait for animation
                
                # Get the updated page content
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                description_section = soup.find("section", class_="object-description")
                if description_section:
                    description_body = description_section.find("div", class_="object-description-body")
                    if description_body:
                        listing_data['description'] = description_body.text.strip()
                        logger.info(f"Full Description: {description_body.text.strip()}")
            except Exception as e:
                logger.error(f"Error getting full description: {str(e)}")
                # Try to get the truncated description as fallback
                try:
                    description_section = soup.find("section", class_="object-description")
                    if description_section:
                        description_body = description_section.find("div", class_="object-description-body")
                        if description_body:
                            listing_data['description'] = description_body.text.strip()
                            logger.info(f"Truncated Description: {description_body.text.strip()}")
                except:
                    logger.error("Could not get description at all")
            
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
    test_url = "https://www.fundainbusiness.nl/agrarische-grond/neer/object-89395886-schooldijk/"
    analyze_listing_page(test_url) 