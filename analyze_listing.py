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
            
            # Analyze page structure
            logger.info("\n=== PAGE STRUCTURE ANALYSIS ===")
            
            # 1. Basic Information
            logger.info("\n1. Basic Information:")
            title = soup.find("h1", class_="object-header__title")
            if title:
                logger.info(f"Title: {title.text.strip()}")
            
            # 2. Price Information
            logger.info("\n2. Price Information:")
            price = soup.find("div", class_="object-primary__price")
            if price:
                logger.info(f"Price: {price.text.strip()}")
            
            # 3. Location Information
            logger.info("\n3. Location Information:")
            location = soup.find("div", class_="object-buurt")
            if location:
                logger.info(f"Location: {location.text.strip()}")
            
            # 4. Property Characteristics
            logger.info("\n4. Property Characteristics:")
            kenmerken = soup.find_all("div", class_="object-kenmerken-group")
            for group in kenmerken:
                group_title = group.find("h3")
                if group_title:
                    logger.info(f"\nGroup: {group_title.text.strip()}")
                    items = group.find_all("li")
                    for item in items:
                        label = item.find("span", class_="object-kenmerken-label")
                        value = item.find("span", class_="object-kenmerken-value")
                        if label and value:
                            logger.info(f"  {label.text.strip()}: {value.text.strip()}")
            
            # 5. Description
            logger.info("\n5. Description:")
            description = soup.find("div", class_="object-description")
            if description:
                logger.info(f"Description: {description.text.strip()}")
            
            # 6. Features
            logger.info("\n6. Features:")
            features = soup.find_all("div", class_="object-features")
            for feature_group in features:
                items = feature_group.find_all("li")
                for item in items:
                    logger.info(f"  {item.text.strip()}")
            
            # 7. Images
            logger.info("\n7. Images:")
            images = soup.find_all("div", class_="object-media-fotos")
            for img_group in images:
                img_tags = img_group.find_all("img")
                for img in img_tags:
                    src = img.get("src")
                    if src:
                        logger.info(f"  Image URL: {src}")
            
            # 8. Documents
            logger.info("\n8. Documents:")
            documents = soup.find_all("div", class_="object-documenten")
            for doc_group in documents:
                links = doc_group.find_all("a")
                for link in links:
                    logger.info(f"  Document: {link.text.strip()} - {link.get('href')}")
            
            # 9. Broker Information
            logger.info("\n9. Broker Information:")
            broker = soup.find("div", class_="object-verkoop")
            if broker:
                broker_name = broker.find("h3")
                if broker_name:
                    logger.info(f"Broker: {broker_name.text.strip()}")
                details = broker.find_all("li")
                for detail in details:
                    label = detail.find("span", class_="object-kenmerken-label")
                    value = detail.find("span", class_="object-kenmerken-value")
                    if label and value:
                        logger.info(f"  {label.text.strip()}: {value.text.strip()}")
            
            # 10. Map Information
            logger.info("\n10. Map Information:")
            map_div = soup.find("div", class_="object-kaart")
            if map_div:
                logger.info("Map data available")
                # You might want to extract coordinates or other map-related data here
            
            # 11. All Available Classes
            logger.info("\n11. All Available Classes:")
            all_classes = set()
            for tag in soup.find_all(class_=True):
                all_classes.update(tag['class'])
            for class_name in sorted(all_classes):
                logger.info(f"  {class_name}")
            
        finally:
            driver.quit()
            
    except Exception as e:
        logger.error(f"Error analyzing page: {str(e)}")
        if 'driver' in locals():
            driver.quit()

if __name__ == "__main__":
    # Test URL
    test_url = "https://www.fundainbusiness.nl/agrarische-grond/neer/object-89395886-schooldijk/"
    analyze_listing_page(test_url) 