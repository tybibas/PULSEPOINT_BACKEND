-- Update Command F Client Profile and Strategy Configuration
-- Based on detailed user onboarding input

-- 1. Update Strategy Sourcing Criteria
UPDATE client_strategies
SET sourcing_criteria = '{
  "industries": [
    "Marketing Agencies", "Creative Agencies", "UX/Product Studios", "PR/Comms", "Video Production", "Web/Dev Agencies",
    "Strategy Consultancies", "Management Consulting", "Boutique Consulting",
    "Legal Firms", "Accounting Firms", "Architecture", "Engineering",
    "Internal Ops Teams (Mid-Market)"
  ],
  "company_size": { "min": 10, "max": 200 },
  "locations": ["US", "Canada", "UK", "Australia"],
  "technographics": {
    "must_have": ["Google Workspace", "Slack"],
    "nice_to_have": ["Dropbox", "Notion", "Confluence", "HubSpot", "Salesforce"],
    "avoid": ["Microsoft 365 Only"]
  },
  "keywords": ["document-heavy", "agency", "consultancy", "retainer", "project-based"]
}'::jsonb
WHERE slug = 'command_f';

-- 2. Update Client Profile Configurations
UPDATE client_profiles
SET 
  commercial_config = '{
    "average_deal_size": 15000,
    "sales_cycle_days": 45,
    "currency": "USD"
  }'::jsonb,

  scoring_config = '{
    "decision_maker_titles": [
      "Founder", "CEO", "COO", "Head of Operations",
      "Managing Director", "Partner", "Principal", 
      "Head of Client Services", "VP Operations", "Director of Operations", 
      "Head of Delivery", "PMO", "Program Director",
      "Head of Finance", "Controller",
      "CTO", "Head of Engineering", "IT Manager"
    ],
    "negative_titles": [
      "SDR", "BDR", "Marketing Coordinator", "Intern", 
      "Operations Associate", "Procurement", "Innovation Lead"
    ],
    "minimum_score_threshold": 60,
    "signal_weights": {
      "new_client": 25,
      "expansion": 20,
      "hiring_ops": 15,
      "tool_migration": 15,
      "funding": 10,
      "leadership_change": 10,
      "general_hiring": 5
    }
  }'::jsonb,

  voice_config = '{
    "tone": "Calm, founder-to-founder, smart, non-hype. Warm, precise, buyers-not-sellers.",
    "value_proposition": "Command F turns your company’s past work into usable leverage—instantly. We solve organizational memory drag by making past work accessible.",
    "forbidden_phrases": ["synergy", "paradigm shift", "disruptive", "AI magic", "revolutionize"],
    "cta_style": "clear",
    "messaging_angles": [
      "No more wasted time searching",
      "Stop re-creating work you already did",
      "Onboard new hires faster with instant context",
      "Protect margins by reducing non-billable hours"
    ]
  }'::jsonb
FROM client_strategies
WHERE client_profiles.strategy_id = client_strategies.id
AND client_strategies.slug = 'command_f';
