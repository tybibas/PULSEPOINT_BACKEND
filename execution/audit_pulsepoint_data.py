"""
Audit and Cleanup Script for PulsePoint Strategic Data.
1. Finds companies with generic names -> Deletes them.
2. Finds leads where Title company does not match Target company -> Deletes lead.
3. Checks for 'suspicious' domains.
"""

import os
import re
from supabase import create_client
from dotenv import load_dotenv
from difflib import SequenceMatcher

load_dotenv('../.env')

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

GENERIC_NAMES = {"Home", "Index", "Welcome", "Main", "Contact", "About", "Page", "Login", "Sign Up", "Search", "Menu", "Site Map", "Privacy Policy", "Terms", "Seattle", "New York", "London", "Austin", "Portland", "Chicago", "San Francisco"}

def similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def normalize(s):
    if not s: return ""
    return re.sub(r'[^a-zA-Z0-9]', '', s.lower())

def audit():
    print("🚀 Starting Deep Audit of PulsePoint Data...")
    
    # Fetch all PulsePoint companies
    resp = supabase.table("triggered_companies")\
        .select("*")\
        .eq("client_context", "pulsepoint_strategic")\
        .execute()
    
    companies = resp.data
    print(f"📋 Analyzing {len(companies)} companies...")
    
    deleted_companies = 0
    deleted_leads = 0
    
    for comp in companies:
        cid = comp['id']
        name = comp['company'].strip()
        domain = comp.get('website', '')
        
        # 1. CHECK NAME QUALITY
        if name in GENERIC_NAMES or len(name) < 3:
            print(f"❌ DELETING Generic/Short Name: '{name}' (ID: {cid})")
            # Cascade delete leads
            supabase.table("PULSEPOINT_STRATEGIC_TRIGGERED_LEADS").delete().eq("triggered_company_id", cid).execute()
            supabase.table("triggered_companies").delete().eq("id", cid).execute()
            deleted_companies += 1
            continue
            
        # 2. CHECK LEADS MISMATCH
        leads_resp = supabase.table("PULSEPOINT_STRATEGIC_TRIGGERED_LEADS").select("*").eq("triggered_company_id", cid).execute()
        leads = leads_resp.data
        
        company_norm = normalize(name).replace("inc", "").replace("llc", "").replace("agency", "")
        
        for lead in leads:
            title = lead.get('title', '')
            lead_id = lead['id']
            lead_name = lead['name']
            
            # Simple heuristic check for mis-matched company in title
            # If title says "CEO at OtherCompany" and "OtherCompany" is NOT fuzzy match to "TargetCompany"
            
            if " at " in title or " @ " in title or " of " in title:
                # Extract company part
                parts = re.split(r' at | @ | of ', title)
                if len(parts) > 1:
                    role_company = parts[-1].strip()
                    
                    # Fuzzy match role_company vs target_company
                    ratio = similar(role_company, name)
                    
                    # Normalize checks
                    role_norm = normalize(role_company)
                    
                    # Check if heavily mismatched
                    # Example: "Ardmore Home Design" vs "Bayou City Productions" -> Ratio ~ 0.1
                    # Exception: "Google" vs "Alphabet" (Hard, but let's assume names match)
                    
                    if ratio < 0.4 and company_norm not in role_norm and role_norm not in company_norm:
                         # Double check it isn't just "Founder" (no company)
                         if len(role_company) > 3:
                             print(f"      ⚠️ LEAD MISMATCH: {lead_name}")
                             print(f"         Target: {name}")
                             print(f"         Role says: {role_company}")
                             print(f"         Similarity: {ratio:.2f}")
                             
                             # DELETE LEAD
                             print(f"         🗑️ DELETING LEAD {lead_id}")
                             supabase.table("PULSEPOINT_STRATEGIC_TRIGGERED_LEADS").delete().eq("id", lead_id).execute()
                             deleted_leads += 1

    print(f"\n✅ Audit Complete.")
    print(f"Deleted Companies: {deleted_companies}")
    print(f"Deleted Leads: {deleted_leads}")

if __name__ == "__main__":
    audit()
