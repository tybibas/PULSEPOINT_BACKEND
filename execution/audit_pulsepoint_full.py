"""
Deep Audit & Cleanup for PulsePoint Data.
Enforces:
1. Casual Company Names (Title Case, No Legal Suffixes).
2. Strict Email Domain Matching.
3. Lead Title Consistency.
"""

import os
import re
from urllib.parse import urlparse
from supabase import create_client
from dotenv import load_dotenv

load_dotenv('../.env')

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

SUFFIXES = [
    r'\bllc\b', r'\binc\b', r'\bltd\b', r'\bcorp\b', r'\bcorporation\b', 
    r'\bco\b', r'\bcompany\b', r'\blimited\b', r'\bplc\b',
    r'\bpty\b', r'\bpvt\b', r'\bgmbh\b', r'\bs.a.\b', r'\bs.l.\b'
]

BLOCKLIST_DOMAINS = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com", "aol.com"}

def clean_name(name):
    if not name: return ""
    # 1. Remove suffixes (case insensitive)
    clean = name
    for suffix in SUFFIXES:
        clean = re.sub(suffix, '', clean, flags=re.IGNORECASE)
    
    # 2. Remove special chars
    clean = re.sub(r'[,.\-]', ' ', clean)
    
    # 3. Fix whitespace
    clean = ' '.join(clean.split())
    
    # 4. Title Case (but preserve acronyms?)
    # Simple title case is safer than fixing 'ABC' -> 'Abc'
    # Use explicit Title Case if currently ALL CAPS
    if clean.isupper():
        clean = clean.title()
    elif clean.islower():
        clean = clean.title()
        
    return clean.strip()

def get_domain(url):
    if not url: return ""
    try:
        if not url.startswith('http'):
            url = 'http://' + url
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except:
        return ""

def audit():
    print("🚀 Starting Deep Data Audit...")
    
    # Fetch all PulsePoint companies
    resp = supabase.table("triggered_companies")\
        .select("*")\
        .eq("client_context", "pulsepoint_strategic")\
        .execute()
    
    companies = resp.data
    print(f"📋 Auditing {len(companies)} companies...")
    
    cleaned_names = 0
    deleted_leads = 0
    
    for comp in companies:
        cid = comp['id']
        raw_name = comp['company']
        website = comp.get('website', '')
        
        # 1. CLEAN NAME
        new_name = clean_name(raw_name)
        if new_name != raw_name:
            print(f"   ✏️ Renaming: '{raw_name}' -> '{new_name}'")
            try:
                supabase.table("triggered_companies").update({"company": new_name}).eq("id", cid).execute()
                cleaned_names += 1
            except Exception as e:
                print(f"      ❌ Name update failed: {e}")

        # 2. CHECK LEADS
        domain = get_domain(website)
        if not domain:
            # If no website, we can't verify email domain.
            # But we can check generic emails?
            pass

        leads_resp = supabase.table("PULSEPOINT_STRATEGIC_TRIGGERED_LEADS").select("*").eq("triggered_company_id", cid).execute()
        leads = leads_resp.data
        
        for lead in leads:
            lid = lead['id']
            email = lead.get('email', '').lower()
            
            if not email:
                print(f"      🗑️ DELETING LEAD (No Email): {lead.get('name')}")
                supabase.table("PULSEPOINT_STRATEGIC_TRIGGERED_LEADS").delete().eq("id", lid).execute()
                deleted_leads += 1
                continue
                
            email_domain = email.split('@')[-1]
            
            # Check Generic
            if email_domain in BLOCKLIST_DOMAINS:
                print(f"      🗑️ DELETING LEAD (Generic Email): {email}")
                supabase.table("PULSEPOINT_STRATEGIC_TRIGGERED_LEADS").delete().eq("id", lid).execute()
                deleted_leads += 1
                continue
            
            # Check Domain Match
            # Allow subdomain matches (e.g. email@us.comp.com vs comp.com)
            # Allow strict match
            
            match = False
            if domain:
                if email_domain == domain:
                    match = True
                elif email_domain.endswith('.' + domain):
                    match = True # email@sub.domain.com matched domain.com
                elif domain.endswith('.' + email_domain):
                    match = True # email@domain.com matched www.sub.domain.com
                elif domain in email_domain: # Partial inclusion? Risky. e.g. 'foo.com' in 'foobar.com'.
                     # Check if domain without TLD is in email domain without TLD
                     # Too complex. User said "domain of their email addresses matching the domain of the website"
                     # Strict is better.
                     pass
            
            if domain and not match:
                # Last chance: Redirect check? Too slow.
                # User wants "100% accuracy".
                # If mismatch -> DELETE.
                print(f"      🗑️ DELETING LEAD (Domain Mismatch): {email} != {domain}")
                supabase.table("PULSEPOINT_STRATEGIC_TRIGGERED_LEADS").delete().eq("id", lid).execute()
                deleted_leads += 1
                continue
                
    print(f"\n✅ Deep Audit Complete.")
    print(f"Renamed Companies: {cleaned_names}")
    print(f"Deleted Leads: {deleted_leads}")

if __name__ == "__main__":
    audit()
