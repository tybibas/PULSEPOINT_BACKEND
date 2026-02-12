#!/usr/bin/env python3
"""
ICP Lead Sourcing Script

Finds companies matching an ICP definition with recent trigger events.
Uses Apify for Google search and optionally Apollo for contact enrichment.

USAGE:
    python source_icp_leads.py --icp "path/to/icp_definition.md" --output "path/to/leads.json"

ENVIRONMENT:
    APIFY_API_KEY - Required for news search
    APOLLO_API_KEY - Optional for contact enrichment
    OPENAI_API_KEY - Required for ICP analysis
"""

import os
import json
import argparse
import re
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

# Supabase client (optional — write-through to DB)
def get_supabase():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if url and key:
        from supabase import create_client
        return create_client(url, key)
    return None

# Lazy imports for API clients
def get_apify_client():
    from apify_client import ApifyClient
    return ApifyClient(os.environ.get("APIFY_API_KEY"))

def get_openai_client():
    from openai import OpenAI
    return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def parse_icp_file(icp_path: str) -> dict:
    """Extract ICP parameters from markdown file."""
    with open(icp_path, 'r') as f:
        content = f.read()
    
    # Default structure
    icp = {
        "industries": [],
        "titles": [],
        "company_size": "",
        "geography": "",
        "keywords": [],
        "trigger_types": []
    }
    
    # Parse sections (basic markdown parsing)
    sections = re.split(r'\n##\s+', content)
    for section in sections:
        lower = section.lower()
        if 'industry' in lower or 'segment' in lower:
            # Capture content, then split by comma
            raw_lines = re.findall(r'[-*]\s*(?:\*\*[^*]+\*\*[:\s]*|[^:\n]+:\s*)?(.+)', section)
            icp["industries"] = []
            for line in raw_lines:
                # Split by comma or slash, strip whitespace
                parts = re.split(r'[,/]', line)
                icp["industries"].extend([p.strip() for p in parts if p.strip()])
                
        elif 'title' in lower or 'role' in lower:
            raw_lines = re.findall(r'[-*]\s*(?:\*\*[^*]+\*\*[:\s]*|[^:\n]+:\s*)?(.+)', section)
            icp["titles"] = []
            for line in raw_lines:
                parts = re.split(r'[,/]', line)
                icp["titles"].extend([p.strip() for p in parts if p.strip()])
        elif 'geography' in lower or 'location' in lower:
            match = re.search(r'[-*]\s*(?:\*\*[^*]+\*\*[:\s]*|[^:\n]+:\s*)?(.+)', section)
            if match:
                icp["geography"] = match.group(1).strip()
        elif 'trigger' in lower or 'event' in lower:
            raw_lines = re.findall(r'[-*]\s*(?:\*\*[^*]+\*\*[:\s]*|[^:\n]+:\s*)?(.+)', section)
            icp["trigger_types"] = [l.strip() for l in raw_lines if l.strip()]
        elif 'keyword' in lower:
            icp["keywords"] = re.findall(r'[-*]\s*(.+)', section)
    
    return icp


def build_search_query(icp: dict, trigger_type: str) -> str:
    """Build Google search query from ICP."""
    parts = []
    
    # Add trigger keywords
    if trigger_type:
        parts.append(f'"{trigger_type}"')
    
    # Add industry context
    if icp.get("industries"):
        industry_or = " OR ".join([f'"{i}"' for i in icp["industries"][:3]])
        parts.append(f'({industry_or})')
    
    # Add geography
    if icp.get("geography"):
        parts.append(f'"{icp["geography"]}"')
    
    # Add "news" to filter for recent events
    parts.append("news")
    
    return " ".join(parts)


def search_for_companies(queries: List[str], apify_client, max_results: int = 20) -> List[dict]:
    """Run Google searches and aggregate results."""
    all_results = []
    seen_urls = set()
    
    for query in queries:
        print(f"  🔍 Searching: {query[:60]}...")
        
        try:
            # Calculate needed pages
            # Google often limits to 10 per page despite request
            # We want max_results total. 15 leads * 3 buffer = 45 raw. 45/10 = 5 pages.
            needed_raw = max_results
            dataset_items_per_page = 10 
            pages_needed = int(needed_raw / dataset_items_per_page) + 2 # buffer
            
            # Cap at reasonable limit to avoid infinite loop cost
            pages_needed = min(pages_needed, 20)

            run_input = {
                "queries": query,
                "resultsPerPage": 100, # Request 100 anyway
                "maxPagesPerQuery": pages_needed,
                "countryCode": "us",
                "languageCode": "en"
            }
            
            print(f"   Using config: {run_input['resultsPerPage']} res/page, {run_input['maxPagesPerQuery']} pages")
            
            run = apify_client.actor("apify/google-search-scraper").call(run_input=run_input)
            
            # Check if dataset exists
            if not run or not run.get("defaultDatasetId"):
                print("   ⚠️ No dataset returned from Apify")
                continue
                
            try:
                # Correct way to get items
                dataset_client = apify_client.dataset(run["defaultDatasetId"])
                list_page = dataset_client.list_items()
                items = list_page.items
                print(f"   Retrieved {len(items)} pages/items from dataset")
            except Exception as e:
                print(f"   ⚠️ Error retrieving dataset items: {e}")
                items = []

            for page in items:
                # In google scraper, each item is a page result containing organicResults
                for result in page.get("organicResults", []):
                    url = result.get("url", "")
                    if url not in seen_urls:
                        seen_urls.add(url)
                        all_results.append({
                            "title": result.get("title", ""),
                            "description": result.get("description", ""),
                            "url": url,
                            "query": query
                        })
                        
                        if len(all_results) >= max_results:
                            return all_results
                            
        except Exception as e:
            print(f"  ⚠️ Search error: {e}")
    
    return all_results


def analyze_result_for_icp(result: dict, icp: dict, openai_client) -> Optional[dict]:
    """Use AI to determine if a search result matches ICP and extract company info."""
    
    prompt = f"""Analyze this news result and determine if it represents a company matching our Ideal Customer Profile.

NEWS RESULT:
Title: {result['title']}
Description: {result['description']}
URL: {result['url']}

ICP CRITERIA:
- Industries: {', '.join(icp.get('industries', ['any']))}
- Target Titles: {', '.join(icp.get('titles', ['executives']))}
- Geography: {icp.get('geography', 'United States ONLY')}
- Trigger Types: {', '.join(icp.get('trigger_types', ['any news']))}
 
TASK:
1. Determine if this represents a real company with a recent trigger event
2. VERIFY LOCATION: Must be in the United States. If unsure or international, REJECT.
3. If yes, extract the company name and event details
4. Rate confidence 1-10
 
Return JSON only:
{{
    "is_match": true/false,
    "confidence": 1-10,
    "company_name": "extracted name or null",
    "location_check": "US or International",
    "event_type": "type of trigger event",
    "event_title": "brief summary of event",
    "event_context": "1-2 sentence context",
    "rejection_reason": "why not a match (if applicable)"
}}"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"  ⚠️ Analysis error: {e}")
        return None


def find_contacts_for_company(company_name: str, titles: List[str], apollo_key: str = None) -> List[dict]:
    """Find contacts at a company. Uses Apollo if available, otherwise returns placeholder."""
    
    if not apollo_key:
        # Return placeholder for manual enrichment
        return [{
            "name": "[TO BE ENRICHED]",
            "title": titles[0] if titles else "Decision Maker",
            "email": "",
            "linkedin_url": "",
            "needs_enrichment": True
        }]
    
    # Apollo people search
    import requests
    
    contacts = []
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache"
    }
    
    for title in titles[:2]:  # Limit to 2 titles
        try:
            url = "https://api.apollo.io/v1/mixed_people/search"
            payload = {
                "api_key": apollo_key,
                "q_organization_name": company_name,
                "person_titles": [title],
                "per_page": 2
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            data = response.json()
            
            for person in data.get("people", []):
                contacts.append({
                    "name": person.get("name", ""),
                    "title": person.get("title", ""),
                    "email": person.get("email", ""),
                    "linkedin_url": person.get("linkedin_url", ""),
                    "needs_enrichment": not bool(person.get("email"))
                })
                
        except Exception as e:
            print(f"  ⚠️ Apollo error for {title}: {e}")
    
    if not contacts:
        return [{
            "name": "[TO BE ENRICHED]",
            "title": titles[0] if titles else "Decision Maker",
            "email": "",
            "linkedin_url": "",
            "needs_enrichment": True
        }]
    
    return contacts


def source_leads(icp_path: str, output_path: str, client_name: str = None, max_companies: int = 15):
    """Main function to source ICP-fit leads."""
    
    print("=" * 60)
    print("ICP Lead Sourcing")
    print("=" * 60)
    
    # Check API keys
    if not os.environ.get("APIFY_API_KEY"):
        print("❌ APIFY_API_KEY not set in environment")
        return
    if not os.environ.get("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set in environment")
        return
    
    apollo_key = os.environ.get("APOLLO_API_KEY")
    if not apollo_key:
        print("⚠️ APOLLO_API_KEY not set - contacts will need manual enrichment")
    
    # Parse ICP
    print(f"\n📋 Parsing ICP from: {icp_path}")
    icp = parse_icp_file(icp_path)
    print(f"   Industries: {icp['industries']}")
    print(f"   Titles: {icp['titles']}")
    print(f"   Geography: {icp['geography']}")
    print(f"   Triggers: {icp['trigger_types']}")
    
    # Build search queries
    queries = []
    for trigger in icp.get("trigger_types", ["news"])[:3]:
        queries.append(build_search_query(icp, trigger))
    
    if not queries:
        queries = [build_search_query(icp, "")]
    
    print(f"\n🔍 Running {len(queries)} searches...")
    
    # Search
    apify_client = get_apify_client()
    results = search_for_companies(queries, apify_client, max_results=max_companies * 3)
    print(f"   Found {len(results)} raw results")
    
    # Analyze and filter
    print(f"\n🧠 Analyzing for ICP fit...")
    openai_client = get_openai_client()
    
    matched_companies = []
    seen_companies = set()
    
    for result in results:
        if len(matched_companies) >= max_companies:
            break
            
        analysis = analyze_result_for_icp(result, icp, openai_client)
        
        if analysis and analysis.get("is_match") and analysis.get("confidence", 0) >= 6:
            company_name = analysis.get("company_name", "")
            if company_name:
                company_name = company_name.strip()
            
            if company_name and company_name.lower() not in seen_companies:
                seen_companies.add(company_name.lower())
                
                print(f"   ✅ {company_name} ({analysis.get('event_type')})")
                
                # Find contacts
                contacts = find_contacts_for_company(
                    company_name, 
                    icp.get("titles", ["CEO"]),
                    apollo_key
                )
                
                matched_companies.append({
                    "name": company_name,
                    "website": "",  # Would need additional lookup
                    "event_type": analysis.get("event_type", "NEWS"),
                    "event_title": analysis.get("event_title", ""),
                    "event_context": analysis.get("event_context", ""),
                    "event_source_url": result.get("url", ""),
                    "contacts": contacts
                })
    
    # Build output
    output = {
        "_generated_at": datetime.now().isoformat(),
        "_icp_source": icp_path,
        "client_name": client_name or "NEW_CLIENT",
        "client_context": (client_name or "new_client").lower().replace(" ", "_"),
        "companies": matched_companies
    }
    
    # Write JSON output (backward-compatible)
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    # Write-through to Supabase triggered_companies
    client_context = output["client_context"]
    supabase = get_supabase()
    db_inserted = 0
    if supabase:
        for comp in matched_companies:
            name = comp.get("name", "").strip()
            if not name:
                continue
            # Dedup check
            existing = supabase.table("triggered_companies").select("id").ilike("company", f"%{name}%").limit(1).execute()
            if existing.data:
                continue
            try:
                supabase.table("triggered_companies").insert({
                    "company": name,
                    "client_context": client_context,
                    "website": comp.get("website", ""),
                    "monitoring_status": "active",
                    "last_monitored_at": "2000-01-01 00:00:00",
                    "events_history": [{
                        "source": "icp_sourced",
                        "event_type": comp.get("event_type", "NEWS"),
                        "event_title": comp.get("event_title", ""),
                        "date": datetime.now().isoformat()
                    }]
                }).execute()
                db_inserted += 1
            except Exception as e:
                print(f"  ⚠️ DB insert error for {name}: {e}")
    
    print(f"\n" + "=" * 60)
    print(f"✅ Sourced {len(matched_companies)} companies")
    print(f"📁 Output: {output_path}")
    if supabase:
        print(f"💾 Inserted {db_inserted} new companies into Supabase")
    
    # Summary
    needs_enrichment = sum(
        1 for c in matched_companies 
        for contact in c.get("contacts", []) 
        if contact.get("needs_enrichment")
    )
    if needs_enrichment:
        print(f"⚠️ {needs_enrichment} contacts need email enrichment")
        print(f"   Run: python execution/find_lead_emails.py --input {output_path}")
    
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Source ICP-fit leads")
    parser.add_argument("--icp", required=True, help="Path to ICP definition markdown file")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument("--client", help="Client name (e.g., 'Acme Corp')")
    parser.add_argument("--max", type=int, default=15, help="Max companies to find (default: 15)")
    
    args = parser.parse_args()
    source_leads(args.icp, args.output, args.client, args.max)
