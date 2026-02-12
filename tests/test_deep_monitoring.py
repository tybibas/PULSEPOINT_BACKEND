
import os
import sys
from dotenv import load_dotenv
sys.path.append(os.path.join(os.getcwd(), 'execution'))
from scouts.blog_scout import scout_latest_blog_posts
from scouts.social_scout import scout_executive_social_activity
from apify_client import ApifyClient

load_dotenv()

def test_blog_scout():
    print("--- Testing BlogScout ---")
    client = ApifyClient(os.environ.get("APIFY_API_KEY"))
    results = scout_latest_blog_posts("York IE", "york.ie", client)
    print(f"Found {len(results)} blog posts:")
    for r in results:
        print(f"- {r['title']} ({r['url']}) [Date: {r.get('publish_date')}]")

def test_social_scout():
    print("\n--- Testing SocialScout ---")
    client = ApifyClient(os.environ.get("APIFY_API_KEY"))
    results = scout_executive_social_activity("Kyle York", "York IE", client)
    print(f"Found {len(results)} social signals:")
    for r in results:
        print(f"- {r['title']} ({r['url']})")

if __name__ == "__main__":
    test_blog_scout()
    # test_social_scout() # Uncomment if you want to test social (costs credits)
