-- Fix SourcingCriteria JSON format to match TypeScript interface
-- The Edge Function expects flat keys like 'icp_industries', 'icp_location', etc.

UPDATE client_strategies
SET sourcing_criteria = '{
  "icp_industries": [
    "Marketing Agencies", "Creative Agencies", "UX/Product Studios", "PR/Comms", "Video Production", "Web/Dev Agencies",
    "Strategy Consultancies", "Management Consulting", "Boutique Consulting",
    "Legal Firms", "Accounting Firms", "Architecture", "Engineering",
    "Internal Ops Teams (Mid-Market)"
  ],
  "icp_location": "US, Canada, UK, Australia",
  "icp_keywords": ["document-heavy", "agency", "consultancy", "retainer", "project-based", "Google Workspace", "Slack"],
  "icp_negative_keywords": ["Microsoft 365 Only"],
  "icp_constraints": ["Company Size: 10-200 employees"],
  "target_count": 50
}'::jsonb
WHERE slug = 'command_f';
