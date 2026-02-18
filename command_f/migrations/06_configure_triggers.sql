-- Configure Command F Trigger Types and Prompts
-- This ensures the Sourcing Engine knows *what* signals to look for (Hiring, Expansion, etc.)

UPDATE client_strategies
SET config = config || '{
  "trigger_types": [
    "New Client Win",
    "Expansion",
    "Hiring (Ops/Delivery)",
    "Tool Migration",
    "Funding",
    "Leadership Change"
  ],
  "trigger_prompt": "Look for companies that are effectively \"document-heavy service orgs\" experiencing growth or operational complexity. \n\nStrongest signals:\n1. \"New Client Win\" or \"AOR Appointment\": Implies immediate delivery pressure.\n2. \"Hiring Ops/Delivery/PMs\": Implies scaling pains and need for onboarding efficiency.\n3. \"Tool Migration\" (Notion, Drive, etc.): Implies active attention to knowledge management.\n\nAvoid: Generic marketing fluff. We want operational pain signals."
}'::jsonb
WHERE slug = 'command_f';
