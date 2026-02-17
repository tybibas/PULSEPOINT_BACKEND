-- 1. Create Strategy
INSERT INTO client_strategies (slug, name, sourcing_criteria, config)
VALUES (
    'pulsepoint_strategic', 
    'PulsePoint Strategic', 
    '{}'::jsonb,
    '{ "leads_table": "PULSEPOINT_STRATEGIC_TRIGGERED_LEADS" }'::jsonb
)
ON CONFLICT (slug) DO UPDATE SET
    config = EXCLUDED.config;

-- 2. Create/Update Profile
INSERT INTO client_profiles (strategy_id, commercial_config, scoring_config, voice_config)
SELECT 
  id,
  '{ "average_deal_size": 25000, "sales_cycle_days": 60, "currency": "USD" }'::jsonb,
  '{ "decision_maker_titles": ["Founder", "Co-Founder", "CEO", "Managing Director", "Partner", "Principal", "Head of Growth", "VP Marketing", "Chief Strategy Officer", "Head of Client Services"], "minimum_score_threshold": 60, "signal_weights": { "funding": 15, "hiring": 10, "expansion": 10, "new_client": 20 } }'::jsonb,
  '{ "tone": "Consultative, founder-to-founder, calm, non-hype, strategically thoughtful", "value_proposition": "PulsePoint builds human-in-the-loop AI systems that monitor a curated set of high-fit companies and surface meaningful business signals (new client wins, product expansion, hiring shifts, funding, repositioning) at the right time — along with draft outreach grounded in context. We don’t automate spam. We help agencies initiate conversations when relevance is real.", "forbidden_phrases": ["cutting-edge", "revolutionary", "game-changing", "leverage synergies", "AI-powered growth engine", "guaranteed results", "10x", "disrupt", "fully automated outbound", "scale instantly", "blast emails", "no-brainer", "risk-free"], "cta_style": "soft" }'::jsonb
FROM client_strategies WHERE slug = 'pulsepoint_strategic'
ON CONFLICT (strategy_id) DO UPDATE SET
  commercial_config = EXCLUDED.commercial_config,
  scoring_config = EXCLUDED.scoring_config,
  voice_config = EXCLUDED.voice_config;
