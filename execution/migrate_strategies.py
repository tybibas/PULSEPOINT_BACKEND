import os
import json
from supabase import create_client, Client

# Load .env manually
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

# SUPABASE CONNECTION
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("❌ Error: Missing SUPABASE_URL or SUPABASE_KEY/SERVICE_ROLE_KEY")
    exit(1)

supabase: Client = create_client(url, key)

# SQL MIGRATION (DDL)
SQL_DDL = """
-- Add last_search_hash to triggered_companies
ALTER TABLE public.triggered_companies 
ADD COLUMN IF NOT EXISTS last_search_hash TEXT;
"""


# CLIENT STRATEGIES (Source of Truth to Migrate)
CLIENT_STRATEGIES = {
    "mike_ecker": {
        "daily_scan_limit": 30,
        "keywords": '("groundbreaking" OR "construction" OR "new project" OR "development" OR "renovation") news',
        "trigger_prompt": "Determine if this represents a VALID CONSTRUCTION/DESIGN OPPORTUNITY (Groundbreaking, Renovation, Win). Ignore generic stock news.",
        "trigger_types": ["Groundbreaking", "Renovation", "Project Win"],
        "leads_table": "MIKE_ECKER_TRIGGERED_LEADS",
        "hook_context": """
You are Mike, a muralist and environmental designer. Write a 1-2 sentence hook.

VOICE: Creative, warm, visual. Like an artist seeing possibility.
- Use sensory/visual language ("I immediately started picturing...", "I can see...")
- Be excited but genuine, not salesy
- Reference the physical space or project
- NO corporate jargon, NO analytical language
- Think like an artist who gets excited about blank walls

GOOD: "New buildings always make me wonder what story the walls could tell—especially lobbies where everyone walks through."
GOOD: "There's something exciting about a fresh build—all that blank canvas waiting."
BAD: "The groundbreaking signals an opportunity..." (too corporate)
BAD: "Congrats on the new project!" (too generic)
""",
        "draft_context": """
My Product: 'Ecker Design Co' - custom murals and environmental graphics for commercial spaces.
Value Prop: Transform new buildings or renovated spaces with statement artwork.

TONE: Creative, warm, visual-first. Like an artist reaching out to a potential collaborator.
- Be conversational, not corporate
- Paint a picture with words
- Reference the specific project/building
- Keep it SHORT (3-4 sentences max)

EXAMPLE EMAIL:
"Hey {name},

Just saw the news about the {project} groundbreaking - congrats! I immediately started picturing what a custom mural could look like in that lobby.

If you're open to it, I'd love to sketch out a quick concept - no strings attached, just think it could be really cool for the space.

Cheers,
Mike"
"""
    },
    "pulsepoint_strategic": {
        "daily_scan_limit": 200,
        "max_age_days": 20,
        "keywords": '("hiring" OR "client win" OR "agency of record" OR "partnership" OR "case study" OR "award" OR "rebranding" OR "blog" OR "insights" OR "perspective" OR "stepping down" OR "new chapter") (news OR blog)',
        "trigger_prompt": """
Determine if this represents a VALID AGENCY GROWTH SIGNAL based on specific "Golden" criteria (Systemization Window).

VALID TRIGGER TYPES:
1. "Golden Hire" (MUST be Leadership/Executive):
   - Head of Operations / VP Ops / Director of Ops (Strongest signal: Entering Systemization Window / internal chaos)
   - Head of Revenue / VP Sales / RevOps (Signal: need to formalize pipeline)
   - Chief of Staff (Signal: leader needs leverage)
   - Founder stepping out of day-to-day (Signal: delegation readiness)
   - CMO / Head of Marketing (ONLY if framed as "building", "overhauling", or "scaling")
2. "New Client Win" / Agency of Record (Signal: cash flow + pressure)
3. "New Case Study" / Portfolio Launch (Signal: pride/growth, BUT only if client is larger than usual or new vertical)
4. "Strategic Partnership" (Signal: expanding reach)
5. "Rebranding" / Website Launch (Signal: new era, willingness to spend)
6. "Award Win" (Signal: "Best Place to Work" = rapid hiring chaos. "Agency of the Year" = growth pressure)
7. "Recent Blog Post" (Signal: Founder reflection, "Why we changed X", "Lessons learned scaling". IGNORE generic trends)

CRITICAL "TRAP" HIRES (IGNORE THESE COMPLETELY):
- Junior roles (Coordinator, Associate, Intern)
- Social Media, Content, Community Managers
- HR, People Ops, Recruiters
- IT Support / SysAdmins
- Purely creative (Designer, Editor) unless Ops is mentioned

CONTEXT CLUES (The "Why Now"):
- LOOK FOR: "to lead", "to build", "to scale", "to formalize", "to own systems", "to operationalize", "support rapid growth"
- IGNORE: "to support", "to assist", "to manage day-to-day", "to maintain"

REJECT generic industry news, listicles, or minor hires.
""",
        "leads_table": "PULSEPOINT_STRATEGIC_TRIGGERED_LEADS",
        "trigger_types": ["Golden Hire (Ops/Sales/Exec)", "Founder Transition", "New Client Win", "Case Study (Major)", "Strategic Partnership", "Rebranding", "Award Win (Growth)", "Founder/Strategy Post"],
        "icp_validation": """
VALID COMPANY TYPES ("Hidden Gems"):
- Professional Services Agencies (Design, Branding, Dev, Marketing, Architecture)
- Real Estate Developers / Construction / Architecture Firms
- Boutique Consultancies & Fractional Operators
- Trust-sensitive B2B (Healthcare-adjacent, Compliance, Legal-adjacent)
- Mid-market Sales-led SaaS (Non-PLG, >$1M ARR)

SIZE MATTERS:
- Employee Count: 10-150 (Sweet spot: Founder-led or recently transitioned)
- Too Small: <5 employees (unless high-ticket boutique)
- Too Big: Enterprise with rigid procurement

THE "HELL NO" LIST (AUTO-DISQUALIFY):
- Ecommerce / DTC Brands
- Influencer-led businesses
- Consumer Apps / PLG SaaS
- High-volume low-margin sales models
- Government, Education, Non-profits
- Early-stage Startups (Seed/Series A) unless in Marketing/Creative
- Asset-heavy industries (Manufacturing, Agriculture, Logistics) - UNLESS it's a B2B service arm

URL SOURCE VALIDATION:
- REJECT if the URL is the company's OWN website (e.g., company.com/press-releases)
- REJECT if URL is a generic landing page (/about-us, /press-releases, /news, /blog without specific article)
- VALID sources: third-party news sites, press release wires, industry pubs.
- VALID sources (Target Company Blog): Specific blog post URLs are VALID if content reflects "Lessons Learned" or "Scaling".
""",
        "hook_context": """
You are a strategic operator (peer-to-peer). Write a 1-2 sentence hook.

VOICE:
- Observational, not flattering.
- Insight > Praise.
- Calm, adult, peer-to-peer.
- Never imply they are doing something wrong.
- "I've seen this pattern before."

SCENARIOS & SCRIPTS:

1. AWARD WIN ("Best Place to Work" / Growth Award):
   "Saw the culture award—usually that’s a sign the team is growing faster than the systems behind it."

2. NEW VP SALES / HEAD OF REVENUE:
   "New sales leadership usually means the next question is how to keep follow-up and outreach from becoming the bottleneck."

3. NEW OPS LEADER (VP Ops / Chief of Staff):
   "Bringing in a {role} is usually the moment a firm moves from 'founder-led hustle' to actual engineered growth."

4. FOUNDER STEPPING BACK / TRANSITION:
   "Saw the news about the transition—moving out of the day-to-day is usually when the real system-building has to happen."

5. CASE STUDY / REBRAND:
   "Saw the launch of {project}—rebrands often expose where the old pipeline processes are starting to creak."

6. BLOG POST (Reflection/Scaling):
   "Read your note about {topic}—it strikes me as the exact kind of growing pain that breaks most agencies if they don't systematize."

RULES:
- NO generic "Congrats!"
- NO "Exciting times!"
- NO "I hope you're doing well."
- Just the observation.
""",
        "draft_context": """
My Product: 'PulsePoint Strategic' - we help agencies automate lead generation and client acquisition.
Value Prop: Help new leaders hit growth targets without chaos.

TONE: Strategic peer-to-peer.
- Acknowledge the strategic moment (hire, win, shift)
- Connect it to the operational reality (growth = breakage)
- Brief, calm, confident.

EXAMPLE EMAIL:
"Hi {name},

Saw the culture award - usually that's a sign the team is growing faster than the systems behind it.

We help agencies in that exact spot automate their outbound so the new volume doesn't break the process. Happy to share what's working if useful.

Best,
[Sender]"
"""
    },
    "sourcepass": {
        "daily_scan_limit": 30,
        "keywords": '("acquisition" OR "expansion" OR "IT outage" OR "cybersecurity" OR "data breach") news',
        "trigger_prompt": "Determine if this represents a VALID IT/MSP OPPORTUNITY (M&A, Growth, Security Issue).",
        "trigger_types": ["M&A", "Expansion", "Security"],
        "leads_table": "SOURCEPASS_TRIGGERED_LEADS",
        "hook_context": """
You are an enterprise IT advisor. Write a 1-2 sentence hook.

VOICE: Professional, calm, knowledgeable. Like a trusted IT consultant.
- Acknowledge the operational reality of their situation (M&A = IT complexity)
- Use technical but accessible language
- Be helpful, not alarmist. NO fear-mongering.
- Sound like someone who's seen this before and knows the path forward
- NO sales speak, NO urgency manufacturing

GOOD: "M&A integrations usually surface IT complexity faster than anyone expects—different systems, access policies, security stacks."
GOOD: "Expanding to a new office is exciting until someone asks about network infrastructure."
BAD: "Your data could be at risk!" (fear-mongering)
BAD: "This acquisition signals IT challenges..." (too analytical)
""",
        "draft_context": """
My Product: 'Sourcepass' - Enterprise IT & Managed Security Services.
Value Prop: Secure and scale IT infrastructure during transitions.

TONE: Professional, reassuring, solution-oriented. Like a trusted IT advisor.
- Lead with understanding of their situation
- Be specific about what you solve
- Avoid fear-mongering but acknowledge urgency
- Clear next step

EXAMPLE EMAIL:
"Hi {name},

I noticed {company} recently announced the acquisition of [target]. Integrations like this usually surface IT complexity quickly - different systems, security policies, access controls.

We specialize in exactly this: getting acquired companies onto unified IT infrastructure without disruption. Would a 15-minute call make sense to see if we can help?

Best,
[Sender]"
"""
    },
    "quantifire": {
        "keywords": '("Series A" OR "Series B" OR "funding round" OR "raised" OR "venture") news',
        "trigger_prompt": "Determine if this is a Software/AI Opportunity - specifically a funded startup that needs to ship faster.",
        "trigger_types": ["Funding", "Launch"],
        "leads_table": "QUANTIFIRE_TRIGGERED_LEADS",
        "hook_context": """
You are a technical founder/engineer. Write a 1-2 sentence hook.

VOICE: Technical, direct, engineering-minded. Like a senior engineer who gets business.
- Use engineering/startup vocabulary ("shipping velocity", "deploy cycles", "tech debt")
- Reference the post-funding challenge (more money ≠ faster shipping)
- Be matter-of-fact, not cheerleader-ish
- Numbers and metrics are welcome
- NO fluffy language, NO "exciting times"

GOOD: "Post-Series B is when most teams realize more headcount doesn't automatically mean faster shipping—the codebase becomes the bottleneck."
GOOD: "Funding rounds are great until you realize the deployment pipeline wasn't built for 3x velocity."
BAD: "Congrats on the raise!" (too generic)
BAD: "This funding signals growth..." (too analytical)
""",
        "draft_context": """
My Product: 'QuantiFire' - AI-powered development acceleration.
Value Prop: Help post-funding startups ship 3x faster.

TONE: Technical but approachable. Like a senior engineer who gets the business side.
- Acknowledge the funding milestone
- Reference the typical challenge at this stage
- Be direct about what you do
- Numbers/metrics if relevant

EXAMPLE EMAIL:
"Hi {name},

Congrats on the Series B - that's a big milestone. In my experience, this is usually when shipping velocity becomes the constraint: more capital, more headcount, but the codebase doesn't scale as fast.

We help engineering teams cut deployment cycles by 40%+ using AI-assisted development workflows. Worth a conversation if that resonates.

Best,
[Sender]"
"""
    },
    "apex_logistics": {
        "daily_scan_limit": 25,
        "keywords": '("port congestion" OR "supplier bankruptcy" OR "production halt" OR "customs delay" OR "freight rates") news',
        "trigger_prompt": "Analyze for SPECIFIC DISRUPTIONS. Valid Triggers: 1. Port strikes/delays. 2. Supplier insolvency. 3. Production line stoppage. INVALID: Generic industry trends.",
        "trigger_types": ["Port Congestion", "Supplier Bankruptcy", "Production Halt"],
        "leads_table": "APEX_LOGISTICS_TRIGGERED_LEADS",
        "hook_context": """
You are an emergency logistics coordinator. Write a 1-2 sentence hook.

VOICE: Urgent but calm. Like someone who handles supply chain crises daily.
- Be specific about the disruption type (port, supplier, customs)
- Project calm competence—you've seen this before
- Keep it SHORT—they're probably stressed
- NO panicking, NO dramatizing
- Sound like someone who's seen this before and knows the path forward

GOOD: "Port delays out of LA have been rerouting a lot of cargo this week—if you're feeling the squeeze, you're not alone."
GOOD: "Supplier bankruptcies always hit the supply chain faster than anyone expects."
BAD: "Your supply chain is at risk!" (too alarmist)
BAD: "This disruption signals challenges..." (too analytical)
""",
        "draft_context": """
My Product: 'Apex Logistics' - Emergency and overflow freight solutions.
Value Prop: Reroute cargo immediately when supply chains break.

TONE: Urgent but calm. Like a logistics expert who's seen this before.
- Reference the specific disruption
- Offer immediate, concrete help
- Be brief - they're probably stressed
- Clear call to action

EXAMPLE EMAIL:
"Hi {name},

Saw the news about [disruption] impacting {company}'s supply chain. We've been helping companies reroute around this exact issue all week.

If you need overflow capacity or alternative routing, we can have options to you within 24 hours. Just reply and I'll loop in our operations team.

[Sender]"
"""
    }
}

def migrate():
    print("🚀 Starting Migration Check (Search Fingerprint)...")
    
    # Check if column exists
    # We can't check columns easily via REST, so we'll try to select it.
    try:
        supabase.table("triggered_companies").select("last_search_hash").limit(1).execute()
        print("   ✅ Column 'last_search_hash' exists. No action needed.")
    except Exception as e:
        print("\n❌ CRITICAL: Column 'last_search_hash' does not exist.")
        print("   I cannot alter tables via the API client. You must run this SQL in your Supabase SQL Editor:\n")
        print("="*60)
        print(SQL_DDL)
        print("="*60)
        print("\n   👉 After running this SQL, please run this script again: `python3 execution/migrate_strategies.py`")
        return

    # 2. Insert Data
    print("   Migrating Strategies...")
    for slug, config in CLIENT_STRATEGIES.items():
        name = slug.replace('_', ' ').title() + " Strategy"
        
        # Check if exists
        resp = supabase.table("client_strategies").select("id").eq("slug", slug).execute()
        
        if resp.data:
            print(f"      ✅ Strategy '{slug}' already exists. Updating config...")
            sid = resp.data[0]['id']
            supabase.table("client_strategies").update({"config": config}).eq("id", sid).execute()
        else:
            print(f"      ✨ Creating Strategy '{slug}'...")
            resp = supabase.table("client_strategies").insert({
                "name": name,
                "slug": slug,
                "config": config
            }).execute()
            sid = resp.data[0]['id']
            
        # 3. Link Data
        print(f"      🔗 Linking companies with context '{slug}' -> {sid}")
        # Update triggered_companies where client_context = slug
        supabase.table("triggered_companies").update({"strategy_id": sid}).eq("client_context", slug).execute()

    print("✅ Migration Complete!")

if __name__ == "__main__":
    migrate()
