from funda_scraper import FundaBusinessScraper

# Initialize the scraper
scraper = FundaBusinessScraper(headless=True)

try:
    # Scrape listings (default: 5 pages)
    listings = scraper.get_listings(max_pages=3)
    
    # Save to CSV
    scraper.save_to_csv(listings, "my_listings.csv")
finally:
    # Always close the browser
    scraper.close()