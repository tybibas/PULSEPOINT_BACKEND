import os
import sys
from dotenv import load_dotenv
from apify_client import ApifyClient
from execution.scouts.blog_scout import scout_latest_blog_posts

load_dotenv()

def test_blog_scout():
    apify_key = os.environ.get("APIFY_API_KEY")
    if not apify_key:
        print("Error: APIFY_API_KEY not found in .env")
        return
        
    client = ApifyClient(apify_key)
    
    test_companies = [
        {"name": "BrandExtract", "url": "https://www.brandextract.com"},
        {"name": "York IE", "url": "https://york.ie"}
    ]
    
    for comp in test_companies:
        print(f"\n--- Testing {comp['name']} ---")
        posts = scout_latest_blog_posts(comp['name'], comp['url'], client)
        print(f"Result: Found {len(posts)} posts.")
        for p in posts[:3]:
            print(f" - [{p.get('publish_date')}] {p['title']}")

if __name__ == "__main__":
    test_blog_scout()
