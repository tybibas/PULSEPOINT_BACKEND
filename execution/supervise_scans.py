
import os
import sys
import json
import random
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Add execution dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from monitor_companies_job import get_supabase
except ImportError:
    # Try importing from parent if run directly
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from execution.monitor_companies_job import get_supabase

from openai import OpenAI

load_dotenv()

AUDITOR_MODEL = "gpt-4o" # Stronger check

def supervise_scans():
    print("🕵️ Supervisor Agent Awakening...")
    
    supabase = get_supabase()
    openai_key = os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        print("❌ No OpenAI Key found.")
        return

    client = OpenAI(api_key=openai_key)

    # 1. Fetch Recent Logs (Last 24h)
    yesterday = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    try:
        logs = supabase.table("monitor_scan_log") \
            .select("*") \
            .gt("completed_at", yesterday) \
            .execute()
    except Exception as e:
        print(f"⚠️ Error fetching logs: {e}")
        return

    if not logs.data:
        print("No scans found in last 24h.")
        return

    print(f"📄 Analyzing {len(logs.data)} scan logs...")

    # 2. Collect Decisions
    triggered_pool = []
    rejected_pool = []

    for row in logs.data:
        analysis_log = row.get('analysis_log') or []
        for entry in analysis_log:
            # We ONLY audit entries that have reasoning/snippet (New Logic)
            if not entry.get('reasoning') or not entry.get('content_snippet'):
                continue
            
            entry['_meta_company'] = row.get('company_name', 'Unknown')
            
            if entry.get('decision') == 'triggered':
                triggered_pool.append(entry)
            elif entry.get('decision') == 'rejected':
                rejected_pool.append(entry)
            elif entry.get('decision') == 'pass':
                 # 'pass' usually means 'passed relevance check' but not yet 'triggered'
                 # We can treat relevance passes as interesting to audit
                 pass

    print(f"📊 Pool: {len(triggered_pool)} Triggered, {len(rejected_pool)} Rejected (with reasoning)")

    # 3. Sample
    sample_size = 3
    audit_batch = []
    
    if triggered_pool:
        audit_batch.extend(random.sample(triggered_pool, min(len(triggered_pool), sample_size)))
    if rejected_pool:
        audit_batch.extend(random.sample(rejected_pool, min(len(rejected_pool), sample_size)))

    if not audit_batch:
        print("Nothing to audit. (Maybe logs are from before the update?)")
        return

    print(f"🔬 Auditing {len(audit_batch)} decisions...")

    discrepancies = []

    for item in audit_batch:
        print(f"  • Reviewing: {item.get('title')[:40]}... ({item.get('decision').upper()})")
        
        prompt = f"""You are a QA Supervisor auditing a junior AI analyst.

DECISION TO REVIEW:
Title: {item.get('title')}
Content Snippet: "{item.get('content_snippet')}"
Company: {item.get('_meta_company')}

OFFICIAL DECISION: {item.get('decision').upper()}
JUNIOR REASONING: "{item.get('reasoning')}"

TASK:
Do you AGREE with this decision?
- If the content is clearly irrelevant/garbage and they Rejected -> AGREE.
- If the content is a clear, valid business trigger and they Triggered -> AGREE.
- If they missed a clear trigger (False Negative) -> DISAGREE.
- If they triggered on garbage (False Positive) -> DISAGREE.

RESPONSE FORMAT (JSON):
{{
    "agreement": "AGREE" | "DISAGREE",
    "supervisor_reasoning": "Explain why.",
    "severity": "low" | "high" (only if DISAGREE)
}}
"""
        try:
            resp = client.chat.completions.create(
                model=AUDITOR_MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            audit = json.loads(resp.choices[0].message.content)
            
            if audit['agreement'] == 'DISAGREE':
                print(f"    🚩 DISCREPANCY FOUND! ({audit['severity']})")
                print(f"    Supervisor: {audit['supervisor_reasoning']}")
                discrepancies.append({
                    "item": item,
                    "audit": audit
                })
            else:
                print(f"    ✅ Agreed.")
                
        except Exception as e:
            print(f"    ⚠️ Audit failed: {e}")

    # 4. Report
    print("\n" + "="*40)
    print("📝 SUPERVISOR REPORT")
    print("="*40)
    if discrepancies:
        print(f"❌ {len(discrepancies)} DISCREPANCIES FOUND")
        for d in discrepancies:
            item = d['item']
            audit = d['audit']
            print(f"\n[HIGH ALERT] {item.get('decision').upper()} -> SHOULD BE OPPOSITE?")
            print(f"Title: {item.get('title')}")
            print(f"Junior: {item.get('reasoning')}")
            print(f"Supervisor: {audit['supervisor_reasoning']}")
    else:
        print("✅ ALL CHECKS PASSED. System is healthy.")
    print("="*40)

if __name__ == "__main__":
    supervise_scans()
