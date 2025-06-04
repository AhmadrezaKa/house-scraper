# Funda Business Agricultural Land Scraper

A simple web scraper for extracting agricultural land listings from Funda in Business (https://www.fundainbusiness.nl/agrarische-grond/).

## Features

- Scrapes agricultural land listings from Funda in Business
- Extracts title, price, location, and detailed information
- Supports pagination
- Returns data in a pandas DataFrame format

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd house-scraper
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

The scraper can be used in two ways:

1. Run directly from command line:
```bash
python funda_scraper.py
```

2. Import and use in your Python code:
```python
from funda_scraper import FundaScraper

# Initialize the scraper
scraper = FundaScraper()

# Scrape listings (default: 1 page)
df = scraper.scrape(n_pages=1)

# Print the results
print(df.head())
```

## Output

The scraper returns a pandas DataFrame with the following columns:
- title: The title of the listing
- price: The price of the property
- location: The location of the property
- details: A dictionary containing additional property details
- url: The URL of the listing

## Notes

- The scraper includes a 2-second delay between page requests to avoid overwhelming the server
- Make sure to respect the website's terms of service and robots.txt
- The scraper uses a standard User-Agent header to identify itself

## License

This project is licensed under the MIT License - see the LICENSE file for details.