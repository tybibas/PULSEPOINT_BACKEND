from apify_client import ApifyClient
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    api_key = os.getenv("APIFY_API_KEY")
    client = ApifyClient(api_key)
    query = "Bouygues SA investor relations"
    print(f"Testing Apify search for: '{query}' ({type(query)})")
    
    run_input = {
        "queries": query,
        "maxPagesPerQuery": 1,
        "resultsPerPage": 1,
        "countryCode": "gb",
    }
    print(f"Input: {run_input}")
    
    try:
        run = client.actor("apify/google-search-scraper").call(run_input=run_input)
        print("Run finished successfully!")
        
        dataset_items = client.dataset(run["defaultDatasetId"]).list_items().items
        if dataset_items:
            print(f"Found {len(dataset_items)} items.")
            print(dataset_items[0].get('organicResults', [])[0].get('url'))
        else:
            print("No items found.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
