from funda_scraper import FundaScraper

def main():
    # Create scraper instance
    scraper = FundaScraper(
        city="den-bosch",    # Change this to your desired city
        radius="50km",       # Change this to your desired radius
        n_pages=1           # Number of pages to scrape
    )
    
    # Run the scraper
    print("Starting to scrape agricultural land listings...")
    df = scraper.run()
    
    # Display results
    print("\nFirst few listings:")
    print(df.head())
    
    # Save to CSV
    if not df.empty:
        filename = f"funda_agrarische_{scraper.city}_{scraper.radius}.csv"
        df.to_csv(filename, index=False)
        print(f"\nResults saved to '{filename}'")
    else:
        print("\nNo listings found!")

if __name__ == "__main__":
    main() 