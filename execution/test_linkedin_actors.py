import os
import sys
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()
client = ApifyClient(os.environ.get("APIFY_API_KEY"))

def test_company_scraper():
    print("\n🏢 TESTING COMPANY SCRAPER...")
    potential_slugs = [
        "curious_coder/linkedin-company-posts-scraper", # Trying original guess again just in case
        "curious_coder/linkedin-company-posts",
        "apimaestro/linkedin-company-posts",
        "harvest_api/linkedin-company-posts-scraper"
    ]

    for actor_id in potential_slugs:
        print(f"Trying {actor_id}...")
        run_input = {
            "companyUrl": "https://www.linkedin.com/company/microsoft",
            "limit": 5
        }
        try:
            run = client.actor(actor_id).call(run_input=run_input, timeout_secs=30)
            if run:
                print(f"✅ SUCCESS: {actor_id} worked!")
                print(f"Run {run['id']} finished. Status: {run['status']}")
                return # Found it
            else:
                print(f"❌ {actor_id} returned no run.")
        except Exception as e:
            print(f"❌ {actor_id} failed: {e}")

def test_profile_scraper():
    print("\n👤 TESTING PROFILE SCRAPER...")
    actor_id = "apimaestro/linkedin-profile-posts"
    
    # Using 'username' as discovered from logs
    username = "reidhoffman" 
    run_input = {
        "username": username,
        "resultsCount": 5
    }
    
    print(f"Calling {actor_id} with {run_input}")
    try:
        run = client.actor(actor_id).call(run_input=run_input, timeout_secs=60)
        if run:
            print(f"Run {run['id']} finished. Status: {run['status']}")
            dataset = client.dataset(run["defaultDatasetId"])
            items = list(dataset.list_items(limit=3).items)
            print(f"Got {len(items)} items.")
            if items:
                # Check author
                auth = items[0].get("author", {})
                name = auth.get("name") if isinstance(auth, dict) else auth
                print(f"Author: {name}") 
                print(f"Sample Text: {items[0].get('text', '')[:50]}...")
        else:
            print("Run failed to start.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_company_scraper()
    test_profile_scraper()
