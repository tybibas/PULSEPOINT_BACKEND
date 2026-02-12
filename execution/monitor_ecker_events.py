import os
import json
import time
from apify_client import ApifyClient
from openai import OpenAI
from datetime import datetime, timedelta

# CONFIGURATION
APIFY_TOKEN = os.environ.get("APIFY_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
DAYS_BACK = 2  # Monitor last 48 hours

# LEAD LIST (Extracted from target_lead_list.md)
LEADS = [
    {"name": "Longfellow Real Estate Partners", "domain": "lfrep.com"},
    {"name": "Trammell Crow Company", "domain": "trammellcrow.com"},
    {"name": "Sudberry Properties", "domain": "sudprop.com"},
    {"name": "Kilroy Realty Corporation", "domain": "kilroyrealty.com"},
    {"name": "Alexandria Real Estate Equities", "domain": "are.com"},
    {"name": "Carrier Johnson + Culture", "domain": "carrierjohnson.com"},
    {"name": "Gensler", "domain": "gensler.com"},
    {"name": "RNT Architects", "domain": "rfrench.com"},
    {"name": "Joseph Wong Design Associates", "domain": "jwdainc.com"},
    {"name": "Studio E Architects", "domain": "studioe.com"},
    {"name": "McCarthy Building Companies", "domain": "mccarthy.com"},
    {"name": "Gafcon", "domain": "gafcon.com"},
    {"name": "Oltmans Construction Co.", "domain": "oltmans.com"},
    {"name": "Turner Construction Company", "domain": "turnerconstruction.com"},
    {"name": "DPR Construction", "domain": "dpr.com"}
]

# TARGET KEYWORDS (Construction & Design Triggers)
KEYWORDS = '("groundbreaking" OR "construction" OR "new project" OR "development" OR "renovation" OR "contract won" OR "appointed")'

def analyze_event_relevance(news_item, company_name):
    """
    Uses OpenAI to filter news for relevance to Mural/Signage opportunities.
    """
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    prompt = f"""
    You are a Lead Generation Analyst for 'Ecker Design Co', a firm that creates custom murals and environmental graphics for commercial buildings.
    
    Analyze this news item for {company_name}:
    Title: {news_item.get('title')}
    Description: {news_item.get('description')}
    Source: {news_item.get('source')}
    
    Determine if this represents a VALID OPPORTUNITY for us to pitch custom art/signage.
    Valid Triggers:
    1. New Groundbreaking or Construction start.
    2. Major Renovation or "Repositioning" of a property.
    3. Won a major contract (if Architect/GC).
    4. New Office Opening.
    
    Return JSON:
    {{
        "is_relevant": true/false,
        "confidence_score": 0-10,
        "trigger_type": "Groundbreaking" | "Renovation" | "project_win" | "other",
        "summary": "1-sentence summary of the project/event"
    }}
    """
    
    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        print(f"Analysis Error: {e}")
        return {"is_relevant": False, "confidence_score": 0}

def monitor_leads():
    if not APIFY_TOKEN:
        print("❌ Error: APIFY_API_KEY not found in environment.")
        return

    client = ApifyClient(APIFY_TOKEN)
    print(f"🚀 Starting Real-Time Monitor for {len(LEADS)} accounts...")
    
    valid_triggers = []

    # BATCHING: To save tokens, we could group queries, but for accuracy/relevance, distinct queries are better.
    # Cost: Google News Scraper is very cheap per run.
    
    for lead in LEADS:
        print(f"🔎 Scanning: {lead['name']}...")
        
        # Construct Query: Company Name + San Diego context OR General keywords
        # We focus on San Diego / SoCal based on strategy, but national wins might clear.
        # Broader query: "{Company}" AND ({keywords})
        query = f'"{lead["name"]}" {KEYWORDS}'
        
        # Run Actor
        run_input = {
            "query": query,
            "maxItems": 3, # Limit to 3 top results to save tokens
            "language": "en-US",
            "timeRange": f"{DAYS_BACK}d" # "2d"
        }
        
        try:
            # Switch to 'apify/google-search-scraper'
            # Query format for News: "{Company} {Keywords}"
            # We add "news" to ensure fresh content
            search_query = f'{lead["name"]} {KEYWORDS} news'
            
            run_input = {
                "queries": search_query, # Pass as string (one per line if multiple)
                "resultsPerPage": 5, 
                "countryCode": "us",
                "maxPagesPerQuery": 1,
            }
            
            # Actor: apify/google-search-scraper
            run = client.actor("apify/google-search-scraper").call(run_input=run_input)
            
            # Fetch results
            dataset_items = client.dataset(run["defaultDatasetId"]).list_items().items
            
            if not dataset_items:
                print("   No search results found.")
                continue
            
            # 'organicResults' is usually the list in the items
            # The dataset often contains 1 item per query with 'organicResults' list inside
            for result_page in dataset_items:
                organic_results = result_page.get("organicResults", [])
                
                for item in organic_results:
                    # Map to common format
                    news_item = {
                        "title": item.get("title"),
                        "description": item.get("description"),
                        "source": item.get("url"), # URL
                        "link": item.get("url")
                    }
                    
                    analysis = analyze_event_relevance(news_item, lead['name'])
                    
                    if analysis.get('is_relevant') and analysis.get('confidence_score') >= 7:
                        print(f"   ✅ TRIGGER: {analysis['summary']}")
                        valid_triggers.append({
                            "company": lead['name'],
                            "event": analysis['summary'],
                            "url": news_item['link'],
                            "date": datetime.now().isoformat() # Approx
                        })
                    else:
                        pass
                        # print(f"   (Skipping: Low Relevance - {analysis.get('trigger_type')})")
                    
        except Exception as e:
            print(f"   ❌ Scraping Error: {e}")

    # Output Results
    print("\n" + "="*50)
    print(f"🎯 MONITORING COMPLETE. Found {len(valid_triggers)} Verified Opportunities.")
    print("="*50)
    
    if valid_triggers:
        print(json.dumps(valid_triggers, indent=2))
        # In production, this would INSERT into Supabase 'triggered_companies'
        
if __name__ == "__main__":
    monitor_leads()
