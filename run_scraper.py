from funda_scraper import FundaScraper

def main():
    # Create scraper instance
    scraper = FundaScraper(
        area="amsterdam",  # Change this to your desired area
        want_to="rent",    # Options: "rent" or "buy"
        n_pages=1         # Number of pages to scrape
    )
    
    # Run the scraper
    print("Starting to scrape...")
    df = scraper.run()
    
    # Display results
    print("\nFirst few listings:")
    print(df.head())
    
    # Save to CSV
    if not df.empty:
        df.to_csv("funda_listings.csv", index=False)
        print("\nResults saved to 'funda_listings.csv'")
    else:
        print("\nNo listings found!")

if __name__ == "__main__":
    main() 