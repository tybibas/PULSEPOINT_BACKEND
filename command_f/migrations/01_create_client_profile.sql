-- 1. Create Strategy
INSERT INTO client_strategies (slug, name, sourcing_criteria, config)
VALUES (
    'command_f', 
    'Command F', 
    '{}'::jsonb,
    '{ "leads_table": "COMMAND_F_TRIGGERED_LEADS" }'::jsonb
)
ON CONFLICT (slug) DO UPDATE SET
    config = EXCLUDED.config;

-- 2. Create/Update Profile
INSERT INTO client_profiles (strategy_id, commercial_config, scoring_config, voice_config)
SELECT 
  id,
  '{ "average_deal_size": 15000, "sales_cycle_days": 45, "currency": "USD" }'::jsonb, -- Placeholder values
  '{ "decision_maker_titles": ["Founder", "CEO", "Head of Operations", "COO"], "minimum_score_threshold": 60, "signal_weights": { "funding": 10, "hiring": 15, "expansion": 15, "new_client": 10 } }'::jsonb, -- Placeholder values
  '{ "tone": "Direct, helpful, problem-solving, efficient", "value_proposition": "Command F helps you find what you need faster. We specialize in operational efficiency and workflow optimization.", "forbidden_phrases": ["synergy", "paradigm shift", "disruptive"], "cta_style": "clear" }'::jsonb -- Placeholder values
FROM client_strategies WHERE slug = 'command_f'
ON CONFLICT (strategy_id) DO UPDATE SET
  commercial_config = EXCLUDED.commercial_config,
  scoring_config = EXCLUDED.scoring_config,
  voice_config = EXCLUDED.voice_config;
