# Funda Business Scraper

A Python-based web scraper for extracting agricultural land listings from Funda Business (fundainbusiness.nl).

## Features

- Scrapes agricultural land listings from Funda Business
- Extracts detailed information including price, location, and property details
- Saves data to CSV format
- Uses Selenium with anti-detection measures
- Configurable number of pages to scrape

## Requirements

- Python 3.8+
- Chrome browser installed
- Required Python packages (install using `pip install -r requirements.txt`):
  - requests
  - beautifulsoup4
  - pandas
  - python-dotenv
  - selenium
  - webdriver-manager
  - fake-useragent

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd house-scraper
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

Basic usage example:

```python
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
```

## Output

The scraper saves the following information for each listing:
- Title
- Price
- Location
- Property details (size, type, etc.)
- URL

## Notes

- The scraper includes anti-detection measures to avoid being blocked
- Use responsibly and respect the website's terms of service
- Consider adding delays between requests if scraping large amounts of data
- The website structure might change, requiring updates to the scraper

## License

MIT License