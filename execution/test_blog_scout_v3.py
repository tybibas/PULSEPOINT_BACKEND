import os
import sys
from dotenv import load_dotenv
from apify_client import ApifyClient
from execution.scouts.blog_scout import scout_latest_blog_posts

load_dotenv()

def test_blog_scout_refined():
    apify_key = os.environ.get("APIFY_API_KEY")
    if not apify_key:
        print("Error: APIFY_API_KEY not found in .env")
        return
        
    client = ApifyClient(apify_key)
    
    test_companies = [
        {"name": "10Fold", "url": "https://10fold.com"}, # Fallback verification
        {"name": "Boostability", "url": "https://www.boostability.com"} # Widening test
    ]
    
    for comp in test_companies:
        print(f"\n--- Testing {comp['name']} ({comp['url']}) ---")
        try:
            posts = scout_latest_blog_posts(comp['name'], comp['url'], client)
            print(f"Result: Found {len(posts)} items.")
            for p in posts[:5]:
                date_str = p.get('publish_date') or "UNDATED"
                print(f" - [{date_str}] [{p['source']}] {p['title']}")
                # print(f"   Snippet: {p['text'][:100]}...")
        except Exception as e:
            print(f"      ❌ Test Failed for {comp['name']}: {e}")

if __name__ == "__main__":
    test_blog_scout_refined()
