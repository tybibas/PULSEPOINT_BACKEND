#!/usr/bin/env python3
import os
import json
import argparse
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv
from supabase import create_client

# Specific imports to keep main scope clean
from apify_client import ApifyClient
from openai import OpenAI

load_dotenv()

# ==================== CONFIGURATION ====================
APIFY_TOKEN = os.environ.get("APIFY_API_KEY")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

# ==================== HELPERS ====================

def get_db():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def get_ai():
    return OpenAI(api_key=OPENAI_KEY)

def get_apify():
    return ApifyClient(APIFY_TOKEN)

def fetch_sourcing_criteria(supabase, strategy_id: str) -> dict:
    """Read the JSONB criteria from the DB."""
    try:
        resp = supabase.table("client_strategies").select("sourcing_criteria").eq("id", strategy_id).execute()
        if resp.data and len(resp.data) > 0:
            return resp.data[0].get("sourcing_criteria", {})
        return {}
    except Exception as e:
        print(f"❌ DB Error: {e}")
        return {}

def build_advanced_queries(criteria: dict) -> List[str]:
    """
    Construct high-precision Google queries.
    Focus on finding "Lists" or "Directories" or "News" that mention the keywords.
    """
    industries = criteria.get("icp_industries", [])
    keywords = criteria.get("icp_keywords", [])
    location = criteria.get("icp_location", "United States")
    
    queries = []
    
    # Base Terms
    base_terms = " OR ".join([f'"{k}"' for k in keywords[:3]]) if keywords else ""
    ind_terms = " OR ".join([f'"{i}"' for i in industries[:3]]) if industries else ""
    
    # 1. "Best X in Y" (Capture Directory/Listicle overlap)
    # e.g., "Top Branding Agencies in Austin"
    if industries and location:
        queries.append(f'top {industries[0]} companies in "{location}" -jobs -careers')
        
    # 2. Competitor/Related (if keywords provided)
    if base_terms:
         queries.append(f'{base_terms} "{location}" ("about us" OR "our team") -site:linkedin.com')
         
    # 3. News Trigger (Recent funding, growth)
    if ind_terms:
        queries.append(f'{ind_terms} ("series a" OR "raised" OR "growth" OR "hiring") "{location}" site:techcrunch.com OR site:businesswire.com OR site:prnewswire.com')
        
    return queries

def search_google(queries: List[str], max_results: int = 50) -> List[dict]:
    """
    Run Deep Google Search.
    Returns: List of {title, url, description, snippet}
    """
    client = get_apify()
    all_results = []
    seen_urls = set()
    
    print(f"🔍 Running {len(queries)} Google Searches...")
    
    for q in queries:
        try:
            run_input = {
                "queries": q,
                "resultsPerPage": 20, # Fetch more to filter down
                "maxPagesPerQuery": 2,
                "countryCode": "us",
            }
            run = client.actor("apify/google-search-scraper").call(run_input=run_input)
            
            dataset = client.dataset(run["defaultDatasetId"])
            for item in dataset.iterate_items():
                for res in item.get("organicResults", []):
                    url = res.get("url")
                    if url and url not in seen_urls:
                        # Basic Cleanup filters
                        if "linkedin.com" in url or "glassdoor.com" in url or "indeed.com" in url:
                            continue
                            
                        seen_urls.add(url)
                        all_results.append(res)
                        
            if len(all_results) >= max_results:
                break
                
        except Exception as e:
            print(f"⚠️ Search failed for '{q}': {e}")
            
    return all_results[:max_results]

# ==================== THE AI GATEKEEPER ====================

def ai_gatekeeper_check(company_data: dict, criteria: dict) -> Tuple[bool, str, dict]:
    """
    The "Deep Specificity" Engine.
    Passes company info (from search result) + Constraints to GPT-4o.
    
    Returns: (Passed, Reason, ExtractedData)
    """
    client = get_ai()
    
    constraints = criteria.get("icp_constraints", [])
    negatives = criteria.get("icp_negative_keywords", [])
    
    prompt = f"""
    You are a Strict Investment Analyst. 
    Analyze this company based on the provided search result.
    
    SEARCH RESULT:
    Title: {company_data.get('title')}
    Desc: {company_data.get('description')}
    URL: {company_data.get('url')}
    
    ICP REQUIREMENTS:
    - Must match Industries: {criteria.get('icp_industries')}
    - Location: {criteria.get('icp_location')}
    
    STRICT CONSTRAINTS (Fail if violated):
    {json.dumps(constraints, indent=2)}
    
    NEGATIVE KEYWORDS (Fail if present):
    {json.dumps(negatives, indent=2)}
    
    TASK:
    1. Extract Company Name (clean version).
    2. Determine if they are a VALID FIT.
    3. If there is insufficient info to disqualify, lean towards "Tentative Pass" (we will enrich later).
    4. If they violate a constraint, REJECT immediately.
    
    Return JSON:
    {{
        "company_name": "Name",
        "is_fit": true/false,
        "reason": "Why fit or why rejected",
        "confidence": 1-10
    }}
    """
    
    try:
        resp = client.chat.completions.create(
            model="gpt-4o", # Use Smart Model for Gatekeeping
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        content = json.loads(resp.choices[0].message.content)
        return (content.get("is_fit", False), content.get("reason", "Unknown"), content)
    except Exception as e:
        return (False, f"AI Error: {e}", {})

# ==================== ENRICHMENT & INSERTION ====================

def enrich_and_insert(supabase, valid_companies: List[dict], client_context: str, strategy_id: str):
    """
    1. Check duplicates
    2. Find Website (if missing)
    3. Insert to triggered_companies
    """
    count = 0
    for comp in valid_companies:
        name = comp.get("company_name", "Unknown")
        print(f"   💾 Processing: {name}")
        
        # 1. Deduplication
        # Check against ALL triggered companies to avoid re-pitching known leads
        clean_name = name.lower().replace("inc", "").replace("llc", "").strip()
        existing = supabase.table("triggered_companies").select("id").ilike("company", f"%{clean_name}%").execute()
        
        if existing.data:
            print(f"      Duplicate detected. Skipping.")
            continue
            
        # 2. Insert
        # We insert as 'active' so the monitor job picks them up for Deep Scanning tomorrow
        data = {
            "company": name,
            "client_context": client_context,
            "strategy_id": strategy_id,
            "website": comp.get("url"), # Start with search URL
            "monitoring_status": "active",
            "last_monitored_at": "2000-01-01 00:00:00", # Force immediate scan
            "events_history": [{"source": "auto_sourced", "date": datetime.now().isoformat()}]
        }
        
        try:
            supabase.table("triggered_companies").insert(data).execute()
            print(f"      ✅ Inserted {name}")
            count += 1
        except Exception as e:
            print(f"      ❌ Insert Failed: {e}")
            
    print(f"\n🎉 Successfully Sourced {count} New Accounts.")

# ==================== MAIN ====================

def source_new_accounts(strategy_id: str):
    print(f"🚀 Starting Automated Sourcing (Strategy: {strategy_id})")
    
    db = get_db()
    
    # 1. Get Criteria
    # First get the slug/context for the strategy
    strat_resp = db.table("client_strategies").select("slug, sourcing_criteria").eq("id", strategy_id).execute()
    if not strat_resp.data:
        print("❌ Strategy not found.")
        return
        
    criteria = strat_resp.data[0].get("sourcing_criteria", {})
    client_context = strat_resp.data[0].get("slug")
    
    if not criteria:
        print("❌ No sourcing criteria defined.")
        return

    print(f"📋 Criteria: {len(criteria)} rules found.")
    
    # 2. Build & Run Search
    queries = build_advanced_queries(criteria)
    # Overshoot Logic: We want 100? Scrape 300.
    target_count = criteria.get("target_count", 50)
    raw_results = search_google(queries, max_results=target_count * 3)
    
    print(f"📬 Retrieved {len(raw_results)} Raw Candidates. Gatekeeping...")
    
    # 3. AI Gatekeeper Loop
    valid_companies = []
    
    for res in raw_results:
        if len(valid_companies) >= target_count:
            break
            
        is_fit, reason, data = ai_gatekeeper_check(res, criteria)
        
        if is_fit:
            print(f"   ✅ PASS: {data.get('company_name')} ({reason})")
            # Enhance data with original URL if AI didn't provide one
            if not data.get("url"): data["url"] = res.get("url")
            valid_companies.append(data)
        else:
            # print(f"   ⛔ REJECT: {data.get('company_name')} ({reason})")
            pass
            
    print(f"💎 Validated {len(valid_companies)} Fits.")
    
    # 4. Commit
    enrich_and_insert(db, valid_companies, client_context, strategy_id)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy_id", required=True, help="UUID of the client strategy")
    args = parser.parse_args()
    
    source_new_accounts(args.strategy_id)
