import time
import logging
import random
import re
import pandas as pd
import sqlite3
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import os
import sys
import platform
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FundaScraper:
    def __init__(self, city="den-bosch", radius="50km", db_path="F:/Databases/Funda/Funda.db"):
        """Initialize the Funda Scraper for agricultural land
        
        Args:
            city (str): City to search in (e.g., "den-bosch", "amsterdam")
            radius (str): Search radius (e.g., "50km")
            db_path (str): Path to SQLite database
        """
        self.base_url = "https://www.fundainbusiness.nl"
        self.city = city.lower().replace(" ", "-")
        self.radius = radius
        self.db_path = db_path
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
            
            try:
                # Try to use Chrome directly
                self.driver = webdriver.Chrome(options=options)
                
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

    def get_page(self, page_num=1):
        """Get the HTML content of a page using Selenium"""
        url = f"{self.base_url}/alle-bedrijfsaanbod/{self.city}/+{self.radius}/"
        if page_num > 1:
            url += f"p{page_num}/"
            
        logger.info(f"Searching URL: {url}")
        
        try:
            # Add random delay before request
            time.sleep(random.uniform(2, 4))
            
            # Load the page
            self.driver.get(url)
            
            # Wait for the content to load
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "search-result-main"))
                )
            except TimeoutException:
                # If the main class isn't found, try to find any content
                logger.info("Main search results not found, checking page content...")
                page_source = self.driver.page_source
                logger.info(f"Page title: {self.driver.title}")
                
                # Log some page content for debugging
                logger.info("First 500 characters of page content:")
                logger.info(page_source[:500])
                
                # Check for common elements
                if "search-result" in page_source:
                    logger.info("Found 'search-result' in page source")
                if "object-search" in page_source:
                    logger.info("Found 'object-search' in page source")
                if "search-results" in page_source:
                    logger.info("Found 'search-results' in page source")
                
                return page_source
            
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

    def get_listing_details(self, url):
        """Get detailed information from a listing's page"""
        try:
            logger.info(f"Getting details for listing: {url}")
            
            # Add random delay before request
            time.sleep(random.uniform(2, 4))
            
            # Load the page
            self.driver.get(url)
            
            # Wait for the content to load
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "object-primary"))
                )
            except TimeoutException:
                logger.warning(f"Timeout waiting for listing page to load: {url}")
                return {}
            
            # Get page content
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Initialize details dictionary
            details = {}
            
            # 1. Basic Information
            header = soup.find("div", class_="object-header__content")
            if header:
                # Title and Location
                title_div = header.find("h1")
                if title_div:
                    title = title_div.find("span", class_="object-header__title")
                    subtitle = title_div.find("span", class_="object-header__subtitle")
                    if title:
                        details['title'] = title.text.strip()
                    if subtitle:
                        details['location'] = subtitle.text.strip()
                
                # Price
                price_div = header.find("div", class_="object-header__pricing")
                if price_div:
                    price = price_div.find("strong", class_="object-header__price")
                    if price:
                        details['price'] = price.text.strip()
            
            # 2. Description
            description_section = soup.find("section", class_="object-description")
            if description_section:
                description_body = description_section.find("div", class_="object-description-body")
                if description_body:
                    details['description'] = description_body.text.strip()
            
            # 3. Property Characteristics
            kenmerken_body = soup.find("div", class_="object-kenmerken-body")
            if kenmerken_body:
                current_section = None
                kadastrale_codes = []
                eigendomssituaties = []
                
                for element in kenmerken_body.children:
                    if element.name == 'h3':
                        current_section = element.text.strip()
                    elif element.name == 'dl':
                        # Special handling for kadastrale gegevens
                        if current_section == "Kadastrale gegevens":
                            # Find all kadastrale group headers
                            group_headers = element.find_all("dt", class_="object-kenmerken-group-header")
                            for header in group_headers:
                                # Get kadastrale code
                                kadaster_title = header.find("div", class_="kadaster-title")
                                if not kadaster_title:
                                    kadaster_title = header.find("div", class_="")
                                if kadaster_title:
                                    kadastrale_code = kadaster_title.text.strip()
                                    if kadastrale_code:
                                        kadastrale_codes.append(kadastrale_code)
                                        
                                        # Find corresponding eigendomssituatie
                                        next_dd = header.find_next_sibling("dd", class_="object-kenmerken-group-list")
                                        if next_dd:
                                            eigendom_dt = next_dd.find("dt", string="Eigendomssituatie")
                                            if eigendom_dt:
                                                eigendom_dd = eigendom_dt.find_next_sibling("dd")
                                                if eigendom_dd:
                                                    eigendom_span = eigendom_dd.find("span")
                                                    if eigendom_span:
                                                        eigendomssituaties.append(eigendom_span.text.strip())
                        else:
                            # Process other sections normally
                            for dt, dd in zip(element.find_all('dt'), element.find_all('dd')):
                                label = dt.text.strip()
                                value = dd.text.strip()
                                
                                # Clean up the value (remove extra whitespace and newlines)
                                value = ' '.join(value.split())
                                
                                # Store in details with section prefix
                                if current_section:
                                    key = f"{current_section}_{label}"
                                else:
                                    key = label
                                details[key] = value
                
                # After processing all elements, store aggregated kadastrale data
                if kadastrale_codes:
                    details['kadastrale_code'] = '-'.join(kadastrale_codes)
                if eigendomssituaties:
                    details['eigendomssituatie'] = '-'.join(eigendomssituaties)
            
            # Log the details we found
            logger.info(f"Found {len(details)} details for listing")
            for key, value in details.items():
                logger.debug(f"{key}: {value}")
            
            return details
            
        except Exception as e:
            logger.error(f"Error getting listing details: {str(e)}")
            return {}

    def parse_listing(self, element):
        """Parse a single listing element"""
        try:
            # Find the content div
            content = element.find("div", class_="search-result-content")
            if not content:
                logger.debug("No content div found")
                return None

            # Find the inner content
            content_inner = content.find("div", class_="search-result-content-inner")
            if not content_inner:
                logger.debug("No content inner div found")
                return None

            # Extract title and location
            header_title_col = content_inner.find("div", class_="search-result__header-title-col")
            header_title = header_title_col.find("h2") if header_title_col else None
            
            # Extract category
            category = None
            category_h4 = content_inner.find("h4", class_="search-result__header-subtitle")
            if category_h4:
                category = category_h4.text.strip()
            
            # Extract price
            price_div = content_inner.find("div", class_="search-result-info-price")
            price = price_div.find("span") if price_div else None
            
            # Extract location
            location = None
            info_div = content_inner.find("div", class_="search-result-info")
            if info_div:
                location_span = info_div.find("span", title="Locatie")
                if location_span:
                    location = location_span.text.strip()
            
            # Extract URL
            url = None
            title_link = header_title_col.find("a") if header_title_col else None
            if title_link:
                url = title_link.get("href")
                if url and not url.startswith("http"):
                    url = f"{self.base_url}{url}"
            
            # Extract listing ID from URL using the pattern object-XXXXX-
            listing_id = None
            if url:
                match = re.search(r'object-(\d+)-', url)
                if match:
                    listing_id = match.group(1)
            
            # Get detailed information from the listing page
            details = self.get_listing_details(url) if url else {}
            
            # Combine basic and detailed information
            listing_data = {
                "listing_id": listing_id,
                "title": header_title.text.strip() if header_title else "N/A",
                "category": category if category else "N/A",
                "price": price.text.strip() if price else "N/A",
                "location": location,
                "url": url,
                "initial_scraped_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Add all details from the listing page
            listing_data.update(details)
            
            logger.info(f"Successfully scraped listing: {listing_data['title']}")
            return listing_data
            
        except Exception as e:
            logger.error(f"Error parsing listing: {str(e)}")
            return None

    def get_total_pages(self):
        """Get the total number of pages from pagination"""
        try:
            # Wait for pagination to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "pagination-pages"))
            )
            
            # Find all page links
            page_links = self.driver.find_elements(By.CSS_SELECTOR, ".pagination-pages a")
            
            if not page_links:
                logger.info("No pagination found, assuming single page")
                return 1
            
            # Get the highest page number
            max_page = 1
            for link in page_links:
                try:
                    page_num = int(link.get_attribute("data-pagination-page"))
                    max_page = max(max_page, page_num)
                except (ValueError, TypeError):
                    continue
            
            logger.info(f"Found {max_page} total pages")
            return max_page
            
        except Exception as e:
            logger.error(f"Error getting total pages: {str(e)}")
            return 1

    def append_to_database(self, df):
        """Append the scraped data to SQLite database with scraping history"""
        try:
            # Connect to SQLite database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Enable foreign key support
            cursor.execute('PRAGMA foreign_keys = ON')
            
            # Clean column names to match database columns
            df.columns = [col.replace(' ', '_') for col in df.columns]
            
            # Drop existing tables if they exist (to recreate with proper constraints)
            cursor.execute('DROP TABLE IF EXISTS ScrapingHistory')
            cursor.execute('DROP TABLE IF EXISTS Listings')
            
            # Create main listings table with proper primary key
            cursor.execute('''
                CREATE TABLE Listings (
                    listing_id TEXT NOT NULL PRIMARY KEY,
                    title TEXT,
                    category TEXT,
                    price TEXT,
                    location TEXT,
                    url TEXT
                )
            ''')
            
            # Create scraping history table with proper foreign key
            cursor.execute('''
                CREATE TABLE ScrapingHistory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    listing_id TEXT NOT NULL,
                    scrape_date TEXT NOT NULL,
                    FOREIGN KEY (listing_id) REFERENCES Listings(listing_id) ON DELETE CASCADE
                )
            ''')
            
            # Get current timestamp for new scrapes
            current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Process each row
            for _, row in df.iterrows():
                # Check if listing already exists
                cursor.execute('SELECT listing_id FROM Listings WHERE listing_id = ?', 
                             (row['listing_id'],))
                existing = cursor.fetchone()
                
                if existing:
                    # Add new scrape date to history
                    cursor.execute('''
                        INSERT INTO ScrapingHistory (listing_id, scrape_date)
                        VALUES (?, ?)
                    ''', (row['listing_id'], current_timestamp))
                else:
                    # Insert new listing with basic information
                    cursor.execute('''
                        INSERT INTO Listings (listing_id, title, category, price, location, url)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        row['listing_id'],
                        row.get('title', 'N/A'),
                        row.get('category', 'N/A'),
                        row.get('price', 'N/A'),
                        row.get('location', 'N/A'),
                        row.get('url', 'N/A')
                    ))
                    
                    # Add initial scrape date to history
                    cursor.execute('''
                        INSERT INTO ScrapingHistory (listing_id, scrape_date)
                        VALUES (?, ?)
                    ''', (row['listing_id'], current_timestamp))
            
            conn.commit()
            logger.info(f"Successfully updated database with {len(df)} records")
            
        except Exception as e:
            logger.error(f"Error updating database: {str(e)}")
            if 'conn' in locals():
                conn.rollback()
        finally:
            if 'conn' in locals():
                conn.close()

    def get_existing_listings(self):
        """Get all existing listing IDs and URLs from the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT listing_id, url FROM Listings')
            existing_listings = {row[0]: row[1] for row in cursor.fetchall()}
            
            return existing_listings
        except Exception as e:
            logger.error(f"Error getting existing listings: {str(e)}")
            return {}
        finally:
            if 'conn' in locals():
                conn.close()

    def scrape(self, n_pages=None):
        """Scrape listings from Funda in Business"""
        all_listings = []
        
        logger.info("Starting scraper for Funda Business agricultural land listings")
        logger.info(f"Search criteria: City={self.city}, Radius={self.radius}")
        
        try:
            # Get existing listings from database
            existing_listings = self.get_existing_listings()
            logger.info(f"Found {len(existing_listings)} existing listings in database")
            
            # Get first page to determine total pages
            html_content = self.get_page(1)
            if not html_content:
                return pd.DataFrame()
            
            # Get total number of pages
            total_pages = self.get_total_pages()
            if n_pages is not None:
                total_pages = min(total_pages, n_pages)
            
            logger.info(f"Will scrape {total_pages} pages")
            
            # Process first page
            soup = BeautifulSoup(html_content, 'html.parser')
            listings = soup.find_all("div", class_="search-result-main")
            
            if listings:
                for listing in listings:
                    # Extract URL first to check if it exists
                    content = listing.find("div", class_="search-result-content")
                    if not content:
                        continue
                        
                    content_inner = content.find("div", class_="search-result-content-inner")
                    if not content_inner:
                        continue
                        
                    header_title_col = content_inner.find("div", class_="search-result__header-title-col")
                    title_link = header_title_col.find("a") if header_title_col else None
                    
                    if not title_link:
                        continue
                        
                    url = title_link.get("href")
                    if url and not url.startswith("http"):
                        url = f"{self.base_url}{url}"
                    
                    # Extract listing ID
                    listing_id = None
                    if url:
                        match = re.search(r'object-(\d+)-', url)
                        if match:
                            listing_id = match.group(1)
                    
                    if not listing_id:
                        continue
                    
                    # Check if listing exists in database
                    if listing_id in existing_listings:
                        # Just add to the list with minimal info for updating scrapelog
                        listing_data = {
                            "listing_id": listing_id,
                            "url": url,
                            "title": title_link.text.strip() if title_link else "N/A"
                        }
                        all_listings.append(listing_data)
                    else:
                        # For new listings, get all details
                        logger.info(f"Found new listing: {url}")
                        # Get detailed information from the listing page
                        details = self.get_listing_details(url)
                        
                        # Get basic information from the listing element
                        category = None
                        category_h4 = content_inner.find("h4", class_="search-result__header-subtitle")
                        if category_h4:
                            category = category_h4.text.strip()
                        
                        price = None
                        price_div = content_inner.find("div", class_="search-result-info-price")
                        if price_div:
                            price_span = price_div.find("span")
                            if price_span:
                                price = price_span.text.strip()
                        
                        location = None
                        info_div = content_inner.find("div", class_="search-result-info")
                        if info_div:
                            location_span = info_div.find("span", title="Locatie")
                            if location_span:
                                location = location_span.text.strip()
                        
                        # Combine all information
                        listing_data = {
                            "listing_id": listing_id,
                            "title": title_link.text.strip() if title_link else "N/A",
                            "category": category if category else "N/A",
                            "price": price if price else "N/A",
                            "location": location if location else "N/A",
                            "url": url,
                            "initial_scraped_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        # Add all details from the listing page
                        listing_data.update(details)
                        all_listings.append(listing_data)
            
            # Process remaining pages
            for page in range(2, total_pages + 1):
                logger.info(f"Scraping page {page} of {total_pages}")
                
                # Get page content
                html_content = self.get_page(page)
                if not html_content:
                    continue
                    
                # Parse the page
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Find all listing elements
                listings = soup.find_all("div", class_="search-result-main")
                
                if not listings:
                    logger.info(f"No listings found on page {page}")
                    break
                    
                # Parse each listing
                for listing in listings:
                    # Extract URL first to check if it exists
                    content = listing.find("div", class_="search-result-content")
                    if not content:
                        continue
                        
                    content_inner = content.find("div", class_="search-result-content-inner")
                    if not content_inner:
                        continue
                        
                    header_title_col = content_inner.find("div", class_="search-result__header-title-col")
                    title_link = header_title_col.find("a") if header_title_col else None
                    
                    if not title_link:
                        continue
                        
                    url = title_link.get("href")
                    if url and not url.startswith("http"):
                        url = f"{self.base_url}{url}"
                    
                    # Extract listing ID
                    listing_id = None
                    if url:
                        match = re.search(r'object-(\d+)-', url)
                        if match:
                            listing_id = match.group(1)
                    
                    if not listing_id:
                        continue
                    
                    # Check if listing exists in database
                    if listing_id in existing_listings:
                        # Just add to the list with minimal info for updating scrapelog
                        listing_data = {
                            "listing_id": listing_id,
                            "url": url,
                            "title": title_link.text.strip() if title_link else "N/A"
                        }
                        all_listings.append(listing_data)
                    else:
                        # For new listings, get all details
                        logger.info(f"Found new listing: {url}")
                        # Get detailed information from the listing page
                        details = self.get_listing_details(url)
                        
                        # Get basic information from the listing element
                        category = None
                        category_h4 = content_inner.find("h4", class_="search-result__header-subtitle")
                        if category_h4:
                            category = category_h4.text.strip()
                        
                        price = None
                        price_div = content_inner.find("div", class_="search-result-info-price")
                        if price_div:
                            price_span = price_div.find("span")
                            if price_span:
                                price = price_span.text.strip()
                        
                        location = None
                        info_div = content_inner.find("div", class_="search-result-info")
                        if info_div:
                            location_span = info_div.find("span", title="Locatie")
                            if location_span:
                                location = location_span.text.strip()
                        
                        # Combine all information
                        listing_data = {
                            "listing_id": listing_id,
                            "title": title_link.text.strip() if title_link else "N/A",
                            "category": category if category else "N/A",
                            "price": price if price else "N/A",
                            "location": location if location else "N/A",
                            "url": url,
                            "initial_scraped_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        # Add all details from the listing page
                        listing_data.update(details)
                        all_listings.append(listing_data)
                
                logger.info(f"Found {len(listings)} listings on page {page}")
                
                # Add random delay between pages
                if page < total_pages:
                    time.sleep(random.uniform(3, 6))
            
            # Convert to DataFrame
            if all_listings:
                df = pd.DataFrame(all_listings)
                
                # Clean column names by replacing spaces with underscores
                df.columns = [col.replace(' ', '_') for col in df.columns]
                
                logger.info(f"Total listings found: {len(df)}")
                
                # Save to CSV with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"funda_listings_{self.city}_{timestamp}.csv"
                df.to_csv(filename, index=False, encoding='utf-8')
                logger.info(f"Saved {len(df)} listings to {filename}")
                
                # Append to database
                self.append_to_database(df)
                
                return df
            return pd.DataFrame()
            
        finally:
            # Always close the driver
            self.driver.quit()

if __name__ == "__main__":
    # Example usage
    scraper = FundaScraper(
        city="nuland",
        radius="3km",
        db_path="C:/Ahmadreza_Files/TEMP/Test_DB/funda_test_DB.db"
    )
    # Scrape all pages
    df = scraper.scrape()
    print("\nFirst few listings:")
    print(df.head()) 
    