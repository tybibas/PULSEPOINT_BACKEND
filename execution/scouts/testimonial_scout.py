import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from apify_client import ApifyClient
import re

def find_testimonials_url(company_name, domain, apify_client):
    """
    Uses Google Search to find the Testimonials/Reviews URL.
    """
    print(f"      📡 [TestimonialScout] Searching for testimonials URL via Apify: {company_name}")
    query = f'site:{domain} ("testimonials" OR "reviews" OR "what clients say" OR "results")'
    
    try:
        run_input = {
            "queries": query,
            "maxPagesPerQuery": 1,
            "resultsPerPage": 3
        }
        run = apify_client.actor("apify/google-search-scraper").call(run_input=run_input)
        
        for item in apify_client.dataset(run["defaultDatasetId"]).iterate_items():
            for res in item.get("organicResults", []):
                url = res.get("url", "").lower()
                # Heuristic: Check if it looks like a testimonials page
                if any(kw in url for kw in ['testimonial', 'review', 'results', 'stories', 'clients']):
                    return res.get("url")
        return None
    except Exception as e:
        print(f"      ⚠️ [TestimonialScout] Apify discovery failed: {e}")
        return None

def scout_testimonials(company_name, company_website, apify_client):
    """
    Crawl the company's testimonials section and extract Key Outcomes.
    """
    print(f"      🔍 [TestimonialScout] Scouting {company_name} ({company_website})...")
    
    domain = company_website.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
    
    target_url = find_testimonials_url(company_name, domain, apify_client)
    
    if not target_url:
        # Fallback guesses
        for path in ["/testimonials", "/reviews", "/results", "/clients"]:
             target_url = f"https://{domain}{path}"
             break 
             
    print(f"      📡 [TestimonialScout] Targeting page: {target_url}")
    
    try:
        # Use Apify to scrape the page
        run_input = {
            "startUrls": [{"url": target_url}],
            "maxDepth": 0, 
            "maxPagesPerCrawl": 1 
        }
        run = apify_client.actor("apify/website-content-crawler").call(run_input=run_input)
        
        items = list(apify_client.dataset(run["defaultDatasetId"]).iterate_items())
        if not items:
            return []
            
        page_text = items[0].get("text", "")
        
        found_triggers = []
        
        # We return the whole page context for the AI to analyze.
        # The AI (in monitor_companies_job.py) will apply the "Significance Filter".
        
        if len(page_text) > 500: # Ensure we actually got content
            found_triggers.append({
                'url': target_url,
                'title': f"Testimonials Page: {target_url}",
                'text': page_text[:8000], # Truncate 
                'source': 'testimonial_scout',
                'is_testimonial': True
            })
        
        return found_triggers

    except Exception as e:
        print(f"      ⚠️ [TestimonialScout] Error scouting testimonials: {e}")
        return []
