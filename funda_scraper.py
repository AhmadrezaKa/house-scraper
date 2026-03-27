import time
import logging
import random
import re
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class FundaScraper:
    def __init__(
        self,
        city="den-bosch",
        radius="50km",
        categories=None
    ):
        """Initialize the Funda scraper for agrarian listings only."""
        self.base_url = "https://www.fundainbusiness.nl"
        self.city = city.lower().replace(" ", "-")
        self.radius = radius
        self.categories = categories or ["agrarisch-bedrijf", "agrarische-grond"]
        self.setup_driver()

    def setup_driver(self):
        """Setup Chrome driver with anti-detection measures."""
        try:
            options = Options()

            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-gpu")

            window_sizes = [(1920, 1080), (1366, 768), (1440, 900)]
            width, height = random.choice(window_sizes)
            options.add_argument(f"--window-size={width},{height}")

            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ]
            chosen_user_agent = random.choice(user_agents)
            options.add_argument(f"user-agent={chosen_user_agent}")

            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)

            self.driver = webdriver.Chrome(options=options)
            self.driver.set_page_load_timeout(30)

            self.driver.execute_cdp_cmd(
                "Network.setUserAgentOverride",
                {"userAgent": chosen_user_agent}
            )

            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

        except Exception as e:
            logger.error(f"Error setting up Chrome driver: {str(e)}")
            raise

    def get_page(self, category, page_num=1):
        """Get HTML content of a search result page."""
        url = f"{self.base_url}/{category}/{self.city}/+{self.radius}/"
        if page_num > 1:
            url += f"p{page_num}/"

        logger.info(f"Searching category={category}, URL: {url}")

        try:
            time.sleep(random.uniform(2, 4))
            self.driver.get(url)

            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "search-result-main"))
                )
            except TimeoutException:
                logger.info("Search results not immediately found, checking page content...")
                page_source = self.driver.page_source

                if "Je bent bijna op de pagina die je zoekt" in page_source:
                    logger.warning("Verification page detected.")
                    return None

                return page_source

            self._simulate_human_scrolling()

            if "Je bent bijna op de pagina die je zoekt" in self.driver.page_source:
                logger.warning("Verification page detected.")
                return None

            return self.driver.page_source

        except TimeoutException:
            logger.error("Timeout waiting for page to load")
            return None
        except Exception as e:
            logger.error(f"Error fetching page {page_num} for category {category}: {str(e)}")
            return None

    def _simulate_human_scrolling(self):
        """Simulate human-like scrolling behavior."""
        try:
            page_height = self.driver.execute_script("return document.body.scrollHeight")
            current_position = 0

            while current_position < page_height:
                scroll_amount = random.randint(100, 300)
                current_position += scroll_amount
                self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                time.sleep(random.uniform(0.1, 0.3))

        except Exception as e:
            logger.warning(f"Error during scrolling simulation: {str(e)}")

    def get_total_pages(self):
        """Get total number of pages from pagination."""
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "pagination-pages"))
            )

            page_links = self.driver.find_elements(By.CSS_SELECTOR, ".pagination-pages a")

            if not page_links:
                logger.info("No pagination found, assuming single page")
                return 1

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
            logger.info(f"Could not determine pagination exactly, assuming 1 page. Reason: {str(e)}")
            return 1

    def _normalize_text(self, value):
        if value is None:
            return None
        value = value.get_text(" ", strip=True) if hasattr(value, "get_text") else str(value)
        value = " ".join(value.split())
        return value if value else None

    def _extract_location_from_header(self, soup, title_text=None):
        """
        Try detail-page location first.
        If not found, fall back to the part after the comma in the title.
        """
        header = soup.find("div", class_="object-header__content")
        if header:
            h1 = header.find("h1")
            if h1:
                subtitle = h1.find("span", class_="object-header__subtitle")
                subtitle_text = self._normalize_text(subtitle)
                if subtitle_text:
                    return subtitle_text

        if title_text and "," in title_text:
            return title_text.split(",", 1)[1].strip()

        return None

    def _extract_price_from_header(self, soup):
        header = soup.find("div", class_="object-header__content")
        if header:
            price_div = header.find("div", class_="object-header__pricing")
            if price_div:
                price = price_div.find("strong", class_="object-header__price")
                price_text = self._normalize_text(price)
                if price_text:
                    return price_text
        return None

    def _extract_description(self, soup):
        description_section = soup.find("section", class_="object-description")
        if description_section:
            description_body = description_section.find("div", class_="object-description-body")
            if description_body:
                return self._normalize_text(description_body)
        return None

    def _extract_standard_kenmerken(self, soup):
        """
        Extract a fixed set of standardized kenmerken fields.
        """
        details = {
            "description": self._extract_description(soup),
            "kadastrale_code": None,
            "kadastrale_oppervlakte": None,
            "eigendomssituatie": None,
            "oppervlakte": None,
            "perceeloppervlakte": None,
            "bestemming": None,
            "vraagprijs_per_m2": None
        }

        kenmerken_body = soup.find("div", class_="object-kenmerken-body")
        if not kenmerken_body:
            return details

        current_section = None
        kadastrale_codes = []
        kadastrale_oppervlaktes = []
        eigendomssituaties = []

        for element in kenmerken_body.children:
            if getattr(element, "name", None) == "h3":
                current_section = self._normalize_text(element)

            elif getattr(element, "name", None) == "dl":
                if current_section == "Kadastrale gegevens":
                    current_code = None

                    for child in element.children:
                        if getattr(child, "name", None) == "dt":
                            classes = child.get("class", [])

                            if "object-kenmerken-group-header" in classes:
                                kadaster_title = child.find("div", class_="kadaster-title")
                                current_code = self._normalize_text(kadaster_title or child)
                                if current_code:
                                    kadastrale_codes.append(current_code)

                            else:
                                label = self._normalize_text(child)
                                dd = child.find_next_sibling("dd")
                                value = self._normalize_text(dd)

                                if not label or not value:
                                    continue

                                label_lower = label.lower()

                                if "eigendomssituatie" in label_lower:
                                    eigendomssituaties.append(value)
                                elif "oppervlakte" in label_lower:
                                    kadastrale_oppervlaktes.append(value)

                # General dt/dd parsing for the rest of the page
                dts = element.find_all("dt", recursive=False)
                dds = element.find_all("dd", recursive=False)

                for dt, dd in zip(dts, dds):
                    label = self._normalize_text(dt)
                    value = self._normalize_text(dd)

                    if not label or not value:
                        continue

                    label_lower = label.lower()

                    if label_lower == "oppervlakte":
                        details["oppervlakte"] = value
                    elif label_lower == "perceeloppervlakte":
                        details["perceeloppervlakte"] = value
                    elif label_lower == "bestemming":
                        details["bestemming"] = value
                    elif label_lower in ["vraagprijs per m²", "vraagprijs per m2"]:
                        details["vraagprijs_per_m2"] = value

        if kadastrale_codes:
            details["kadastrale_code"] = " | ".join(dict.fromkeys(kadastrale_codes))

        if kadastrale_oppervlaktes:
            details["kadastrale_oppervlakte"] = " | ".join(dict.fromkeys(kadastrale_oppervlaktes))

        if eigendomssituaties:
            details["eigendomssituatie"] = " | ".join(dict.fromkeys(eigendomssituaties))

        return details

    def get_listing_details(self, url):
        """Get fixed, clean details from a listing page."""
        try:
            logger.info(f"Getting details for listing: {url}")

            time.sleep(random.uniform(2, 4))
            self.driver.get(url)

            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "object-primary"))
                )
            except TimeoutException:
                logger.warning(f"Timeout waiting for listing page to load: {url}")
                return {}

            soup = BeautifulSoup(self.driver.page_source, "html.parser")

            header = soup.find("div", class_="object-header__content")
            title_text = None
            if header:
                h1 = header.find("h1")
                if h1:
                    title_span = h1.find("span", class_="object-header__title")
                    title_text = self._normalize_text(title_span)

            details = self._extract_standard_kenmerken(soup)
            details["location"] = self._extract_location_from_header(soup, title_text=title_text)
            details["price"] = self._extract_price_from_header(soup)

            return details

        except Exception as e:
            logger.error(f"Error getting listing details: {str(e)}")
            return {}

    def scrape(self, n_pages=None):
        """Scrape agrarian listings and export them to CSV only."""
        all_listings = []
        seen_listing_ids = set()

        logger.info("Starting scraper for Funda Business agrarian listings only")
        logger.info(f"Search criteria: City={self.city}, Radius={self.radius}")
        logger.info(f"Categories: {self.categories}")

        try:
            for category in self.categories:
                logger.info(f"--- Processing category: {category} ---")

                first_page_html = self.get_page(category, 1)
                if not first_page_html:
                    logger.warning(f"Skipping category {category} because first page could not be loaded.")
                    continue

                total_pages = self.get_total_pages()
                if n_pages is not None:
                    total_pages = min(total_pages, n_pages)

                logger.info(f"Will scrape {total_pages} pages for category {category}")

                for page in range(1, total_pages + 1):
                    logger.info(f"Scraping page {page} of {total_pages} for {category}")

                    if page == 1:
                        html_content = first_page_html
                    else:
                        html_content = self.get_page(category, page)

                    if not html_content:
                        continue

                    soup = BeautifulSoup(html_content, "html.parser")
                    listings = soup.find_all("div", class_="search-result-main")

                    if not listings:
                        logger.info(f"No listings found on page {page} for category {category}")
                        break

                    for listing in listings:
                        try:
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

                            listing_id = None
                            if url:
                                match = re.search(r"object-(\d+)-", url)
                                if match:
                                    listing_id = match.group(1)

                            if not listing_id:
                                continue

                            if listing_id in seen_listing_ids:
                                continue

                            seen_listing_ids.add(listing_id)

                            category_text = None
                            category_h4 = content_inner.find("h4", class_="search-result__header-subtitle")
                            if category_h4:
                                category_text = self._normalize_text(category_h4)

                            price = None
                            price_div = content_inner.find("div", class_="search-result-info-price")
                            if price_div:
                                price_span = price_div.find("span")
                                if price_span:
                                    price = self._normalize_text(price_span)

                            # fallback location from title
                            title_text = self._normalize_text(title_link)
                            location_from_title = None
                            if title_text and "," in title_text:
                                location_from_title = title_text.split(",", 1)[1].strip()

                            details = self.get_listing_details(url) if url else {}

                            listing_data = {
                                "listing_id": listing_id,
                                "source_category": category,
                                "title": title_text,
                                "category": category_text,
                                "price": details.get("price") or price,
                                "location": details.get("location") or location_from_title,
                                "url": url,
                                "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "description": details.get("description"),
                                "kadastrale_code": details.get("kadastrale_code"),
                                "kadastrale_oppervlakte": details.get("kadastrale_oppervlakte"),
                                "eigendomssituatie": details.get("eigendomssituatie"),
                                "oppervlakte": details.get("oppervlakte"),
                                "perceeloppervlakte": details.get("perceeloppervlakte"),
                                "bestemming": details.get("bestemming"),
                                "vraagprijs_per_m2": details.get("vraagprijs_per_m2"),
                            }

                            all_listings.append(listing_data)
                            logger.info(f"Successfully scraped listing: {listing_data['title']}")

                        except Exception as e:
                            logger.error(f"Error parsing one listing: {str(e)}")
                            continue

                    if page < total_pages:
                        time.sleep(random.uniform(3, 6))

            if all_listings:
                df = pd.DataFrame(all_listings)

                fixed_columns = [
                    "listing_id",
                    "source_category",
                    "title",
                    "category",
                    "price",
                    "location",
                    "url",
                    "scraped_at",
                    "description",
                    "kadastrale_code",
                    "kadastrale_oppervlakte",
                    "eigendomssituatie",
                    "oppervlakte",
                    "perceeloppervlakte",
                    "bestemming",
                    "vraagprijs_per_m2",
                ]

                for col in fixed_columns:
                    if col not in df.columns:
                        df[col] = None

                df = df[fixed_columns]

                logger.info(f"Total unique listings found: {len(df)}")

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"funda_agrarisch_{self.city}_{timestamp}.csv"
                df.to_csv(filename, index=False, encoding="utf-8-sig")

                logger.info(f"Saved {len(df)} listings to {filename}")
                return df

            return pd.DataFrame()

        finally:
            try:
                self.driver.quit()
            except Exception as e:
                logger.error(f"Error while closing the driver: {e}")


if __name__ == "__main__":
    scraper = FundaScraper(
        city="nuland",
        radius="3km",
        categories=["agrarisch-bedrijf", "agrarische-grond"]
    )

    df = scraper.scrape()

    print("\nFirst few listings:")
    print(df.head())
