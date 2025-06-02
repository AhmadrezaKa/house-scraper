from funda_scraper import FundaScraper

# Initialize the scraper with your desired parameters
scraper = FundaScraper(
    area="amsterdam",  # Change this to your desired area
    want_to="rent",    # Options: "rent" or "buy"
    find_past=False,   # Set to True if you want to see past listings
    n_pages=1         # Number of pages to scrape
)

# Run the scraper and get results
df = scraper.run()

# Display the first few results
print("\nFirst few listings:")
print(df.head())

# Save results to CSV
df.to_csv("funda_listings.csv", index=False)
print("\nResults saved to 'funda_listings.csv'") 