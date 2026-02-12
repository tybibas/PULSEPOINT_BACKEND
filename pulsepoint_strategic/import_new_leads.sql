-- 0. CLEANUP (Delete existing duplicates to avoid double-entry)
DELETE FROM public."PULSEPOINT_STRATEGIC_TRIGGERED_LEADS" WHERE email IN ('nicole@designwomb.com', 'matteo.bologna@mucca.com', 'jenn@jenndavid.com', 'shaun@bandb-studio.co.uk', 'stepan.azaryan@backbonebranding.com', 'anjelika@dd.nyc', 'katie.klencheski@smakkstudios.com', 'dpatrick@skidmorestudio.com', 'aaron@mavrk.one', 'nikola@brandettes.com', 'alison@umaimarketing.com', 'kevin@swigstudio.com', 'jeff@zenpack.us', 'kevin@strangerandstranger.com', 'jonathan.f@pearlfisher.com', 'danielle@designsakestudio.com', 'grant@grantedesigns.com', 'mmahler@meghanmahlerdesign.com');
DELETE FROM public.triggered_companies WHERE company IN ('Design Womb', 'Mucca Design', 'Jenn David Design', 'B&B Studio', 'Backbone Branding', 'DD.NYC', 'SMAKK Studios', 'Skidmore Studio', 'MAVRK Studio', 'Brandettes', 'UMAI Marketing', 'Swig Studio', 'Zenpack', 'Stranger & Stranger', 'Pearlfisher', 'Design Sake Studio', 'Grantedesigns', 'Meghan Mahler Design');

-- 1. INSERT COMPANIES
INSERT INTO public.triggered_companies (id, company, event_type, event_title, event_context, event_source_url, created_at)
VALUES
    (
        '6157b3d1-6f2c-4c35-9f57-d019da2c77be', 
        'Design Womb', 
        'TRIGGER_DETECTED', 
        'Matched Ideal Customer Profile', 
        'Trigger detected: High-End Packaging Agency Lookalike', 
        'https://designwomb.com',
        NOW()
    ),
    (
        '00b4f5a4-2006-415d-b0cd-300c67bcd090', 
        'Mucca Design', 
        'TRIGGER_DETECTED', 
        'Matched Ideal Customer Profile', 
        'Trigger detected: High-End Packaging Agency Lookalike', 
        'https://mucca.com',
        NOW()
    ),
    (
        'c36d5616-0061-44c8-8cce-c41fe91b46a5', 
        'Jenn David Design', 
        'TRIGGER_DETECTED', 
        'Matched Ideal Customer Profile', 
        'Trigger detected: High-End Packaging Agency Lookalike', 
        'https://jenndavid.com',
        NOW()
    ),
    (
        '270c617d-ac37-4362-a849-2665dc90808e', 
        'B&B Studio', 
        'TRIGGER_DETECTED', 
        'Matched Ideal Customer Profile', 
        'Trigger detected: High-End Packaging Agency Lookalike', 
        'https://bandb-studio.co.uk',
        NOW()
    ),
    (
        '5764ab8a-fc13-4ec3-bad4-493e5ceab9c5', 
        'Backbone Branding', 
        'TRIGGER_DETECTED', 
        'Matched Ideal Customer Profile', 
        'Trigger detected: High-End Packaging Agency Lookalike', 
        'https://backbonebranding.com',
        NOW()
    ),
    (
        '1913097e-e11b-4d72-8fae-b5eafc65d284', 
        'DD.NYC', 
        'TRIGGER_DETECTED', 
        'Matched Ideal Customer Profile', 
        'Trigger detected: High-End Packaging Agency Lookalike', 
        'https://dd.nyc',
        NOW()
    ),
    (
        'aff471c7-5ca1-43cb-8b22-e7c5d5a7991d', 
        'SMAKK Studios', 
        'TRIGGER_DETECTED', 
        'Matched Ideal Customer Profile', 
        'Trigger detected: High-End Packaging Agency Lookalike', 
        'https://smakkstudios.com',
        NOW()
    ),
    (
        '40c6bc63-4dec-4d53-b8ad-c5f5c834e888', 
        'Skidmore Studio', 
        'TRIGGER_DETECTED', 
        'Matched Ideal Customer Profile', 
        'Trigger detected: High-End Packaging Agency Lookalike', 
        'https://skidmorestudio.com',
        NOW()
    ),
    (
        '828bb22b-94ab-41bd-bb61-6689ab142e12', 
        'MAVRK Studio', 
        'TRIGGER_DETECTED', 
        'Matched Ideal Customer Profile', 
        'Trigger detected: High-End Packaging Agency Lookalike', 
        'https://mavrk.studio',
        NOW()
    ),
    (
        '1293206b-c5cd-46a8-82d8-f4848072511a', 
        'Brandettes', 
        'TRIGGER_DETECTED', 
        'Matched Ideal Customer Profile', 
        'Trigger detected: High-End Packaging Agency Lookalike', 
        'https://brandettes.com',
        NOW()
    ),
    (
        '2c4ef79d-f398-4902-9eb0-f50d56a9abaa', 
        'UMAI Marketing', 
        'TRIGGER_DETECTED', 
        'Matched Ideal Customer Profile', 
        'Trigger detected: High-End Packaging Agency Lookalike', 
        'https://umaimarketing.com',
        NOW()
    ),
    (
        '0e6fc1c9-5c45-4dde-be02-177f6798fd76', 
        'Swig Studio', 
        'TRIGGER_DETECTED', 
        'Matched Ideal Customer Profile', 
        'Trigger detected: High-End Packaging Agency Lookalike', 
        'https://swigstudio.com',
        NOW()
    ),
    (
        'ec1b1e02-1b90-4833-b386-d4cae4b31aeb', 
        'Zenpack', 
        'TRIGGER_DETECTED', 
        'Matched Ideal Customer Profile', 
        'Trigger detected: High-End Packaging Agency Lookalike', 
        'https://zenpack.us',
        NOW()
    ),
    (
        'e8d48171-1475-4a69-a585-b736eb3f512e', 
        'Stranger & Stranger', 
        'TRIGGER_DETECTED', 
        'Matched Ideal Customer Profile', 
        'Trigger detected: High-End Packaging Agency Lookalike', 
        'https://strangerandstranger.com',
        NOW()
    ),
    (
        'e30248cb-bd01-4ff6-b9c4-261dd7dce2f0', 
        'Pearlfisher', 
        'TRIGGER_DETECTED', 
        'Matched Ideal Customer Profile', 
        'Trigger detected: High-End Packaging Agency Lookalike', 
        'https://pearlfisher.com',
        NOW()
    ),
    (
        '63a13f65-3b68-4d8b-8a43-b432f99ac06d', 
        'Design Sake Studio', 
        'TRIGGER_DETECTED', 
        'Matched Ideal Customer Profile', 
        'Trigger detected: High-End Packaging Agency Lookalike', 
        'https://designsakestudio.com',
        NOW()
    ),
    (
        '620f7f98-ff72-4125-8eb4-646afae72518', 
        'Grantedesigns', 
        'TRIGGER_DETECTED', 
        'Matched Ideal Customer Profile', 
        'Trigger detected: High-End Packaging Agency Lookalike', 
        'https://grantedesigns.com',
        NOW()
    ),
    (
        '930cd4ec-c5ba-4295-a8ba-27bf2ba7b246', 
        'Meghan Mahler Design', 
        'TRIGGER_DETECTED', 
        'Matched Ideal Customer Profile', 
        'Trigger detected: High-End Packaging Agency Lookalike', 
        'https://meghanmahlerdesign.com',
        NOW()
    )
ON CONFLICT (id) DO NOTHING;

-- 2. INSERT LEADS
INSERT INTO public."PULSEPOINT_STRATEGIC_TRIGGERED_LEADS" (triggered_company_id, name, title, email, contact_status, email_subject, email_body, is_selected, created_at, updated_at)
VALUES
    (
        '6157b3d1-6f2c-4c35-9f57-d019da2c77be', 
        'Nicole LaFave', 
        'Founder/Principal', 
        'nicole@designwomb.com', 
        'pending', 
        'Scrappy USC student / idea for Design Womb', 
        'Hi Nicole,

I’m a student at USC studying automation.

I’ve been talking with boutique agency owners and noticed a specific bottleneck: you need to find new clients, but you don''t have time for manual research (and mass automation feels too spammy).

My partner and I built a human-in-the-loop AI system to fix this.

It handles the heavy lifting (scanning the market for buying signals and drafting the note), but nothing sends without your approval. It does 90% of the work; you keep 100% of the control.

I''m not trying to sell you another subscription. Just figured seeing a concrete example of how to scale outreach without losing your "founder voice" could be useful clarity for the business.

Mind if I send a 60-second Loom video showing how it works?

Best, 
Ty', 
        true,
        NOW(),
        NOW()
    ),
    (
        '00b4f5a4-2006-415d-b0cd-300c67bcd090', 
        'Matteo Bologna', 
        'Founder/Principal', 
        'matteo.bologna@mucca.com', 
        'pending', 
        'Scrappy USC student / idea for Mucca Design', 
        'Hi Matteo,

I’m a student at USC studying automation.

I’ve been talking with boutique agency owners and noticed a specific bottleneck: you need to find new clients, but you don''t have time for manual research (and mass automation feels too spammy).

My partner and I built a human-in-the-loop AI system to fix this.

It handles the heavy lifting (scanning the market for buying signals and drafting the note), but nothing sends without your approval. It does 90% of the work; you keep 100% of the control.

I''m not trying to sell you another subscription. Just figured seeing a concrete example of how to scale outreach without losing your "founder voice" could be useful clarity for the business.

Mind if I send a 60-second Loom video showing how it works?

Best, 
Ty', 
        true,
        NOW(),
        NOW()
    ),
    (
        'c36d5616-0061-44c8-8cce-c41fe91b46a5', 
        'Jenn David Connolly', 
        'Founder/Principal', 
        'jenn@jenndavid.com', 
        'pending', 
        'Scrappy USC student / idea for Jenn David Design', 
        'Hi Jenn,

I’m a student at USC studying automation.

I’ve been talking with boutique agency owners and noticed a specific bottleneck: you need to find new clients, but you don''t have time for manual research (and mass automation feels too spammy).

My partner and I built a human-in-the-loop AI system to fix this.

It handles the heavy lifting (scanning the market for buying signals and drafting the note), but nothing sends without your approval. It does 90% of the work; you keep 100% of the control.

I''m not trying to sell you another subscription. Just figured seeing a concrete example of how to scale outreach without losing your "founder voice" could be useful clarity for the business.

Mind if I send a 60-second Loom video showing how it works?

Best, 
Ty', 
        true,
        NOW(),
        NOW()
    ),
    (
        '270c617d-ac37-4362-a849-2665dc90808e', 
        'Shaun Bowen', 
        'Founder/Principal', 
        'shaun@bandb-studio.co.uk', 
        'pending', 
        'Scrappy USC student / idea for B&B Studio', 
        'Hi Shaun,

I’m a student at USC studying automation.

I’ve been talking with boutique agency owners and noticed a specific bottleneck: you need to find new clients, but you don''t have time for manual research (and mass automation feels too spammy).

My partner and I built a human-in-the-loop AI system to fix this.

It handles the heavy lifting (scanning the market for buying signals and drafting the note), but nothing sends without your approval. It does 90% of the work; you keep 100% of the control.

I''m not trying to sell you another subscription. Just figured seeing a concrete example of how to scale outreach without losing your "founder voice" could be useful clarity for the business.

Mind if I send a 60-second Loom video showing how it works?

Best, 
Ty', 
        true,
        NOW(),
        NOW()
    ),
    (
        '5764ab8a-fc13-4ec3-bad4-493e5ceab9c5', 
        'Stepan Azaryan', 
        'Founder/Principal', 
        'stepan.azaryan@backbonebranding.com', 
        'pending', 
        'Scrappy USC student / idea for Backbone Branding', 
        'Hi Stepan,

I’m a student at USC studying automation.

I’ve been talking with boutique agency owners and noticed a specific bottleneck: you need to find new clients, but you don''t have time for manual research (and mass automation feels too spammy).

My partner and I built a human-in-the-loop AI system to fix this.

It handles the heavy lifting (scanning the market for buying signals and drafting the note), but nothing sends without your approval. It does 90% of the work; you keep 100% of the control.

I''m not trying to sell you another subscription. Just figured seeing a concrete example of how to scale outreach without losing your "founder voice" could be useful clarity for the business.

Mind if I send a 60-second Loom video showing how it works?

Best, 
Ty', 
        true,
        NOW(),
        NOW()
    ),
    (
        '1913097e-e11b-4d72-8fae-b5eafc65d284', 
        'Anjelika Kour', 
        'Founder/Principal', 
        'anjelika@dd.nyc', 
        'pending', 
        'Scrappy USC student / idea for DD.NYC', 
        'Hi Anjelika,

I’m a student at USC studying automation.

I’ve been talking with boutique agency owners and noticed a specific bottleneck: you need to find new clients, but you don''t have time for manual research (and mass automation feels too spammy).

My partner and I built a human-in-the-loop AI system to fix this.

It handles the heavy lifting (scanning the market for buying signals and drafting the note), but nothing sends without your approval. It does 90% of the work; you keep 100% of the control.

I''m not trying to sell you another subscription. Just figured seeing a concrete example of how to scale outreach without losing your "founder voice" could be useful clarity for the business.

Mind if I send a 60-second Loom video showing how it works?

Best, 
Ty', 
        true,
        NOW(),
        NOW()
    ),
    (
        'aff471c7-5ca1-43cb-8b22-e7c5d5a7991d', 
        'Katie Klencheski', 
        'Founder/Principal', 
        'katie.klencheski@smakkstudios.com', 
        'pending', 
        'Scrappy USC student / idea for SMAKK Studios', 
        'Hi Katie,

I’m a student at USC studying automation.

I’ve been talking with boutique agency owners and noticed a specific bottleneck: you need to find new clients, but you don''t have time for manual research (and mass automation feels too spammy).

My partner and I built a human-in-the-loop AI system to fix this.

It handles the heavy lifting (scanning the market for buying signals and drafting the note), but nothing sends without your approval. It does 90% of the work; you keep 100% of the control.

I''m not trying to sell you another subscription. Just figured seeing a concrete example of how to scale outreach without losing your "founder voice" could be useful clarity for the business.

Mind if I send a 60-second Loom video showing how it works?

Best, 
Ty', 
        true,
        NOW(),
        NOW()
    ),
    (
        '40c6bc63-4dec-4d53-b8ad-c5f5c834e888', 
        'Drew Patrick', 
        'Founder/Principal', 
        'dpatrick@skidmorestudio.com', 
        'pending', 
        'Scrappy USC student / idea for Skidmore Studio', 
        'Hi Drew,

I’m a student at USC studying automation.

I’ve been talking with boutique agency owners and noticed a specific bottleneck: you need to find new clients, but you don''t have time for manual research (and mass automation feels too spammy).

My partner and I built a human-in-the-loop AI system to fix this.

It handles the heavy lifting (scanning the market for buying signals and drafting the note), but nothing sends without your approval. It does 90% of the work; you keep 100% of the control.

I''m not trying to sell you another subscription. Just figured seeing a concrete example of how to scale outreach without losing your "founder voice" could be useful clarity for the business.

Mind if I send a 60-second Loom video showing how it works?

Best, 
Ty', 
        true,
        NOW(),
        NOW()
    ),
    (
        '828bb22b-94ab-41bd-bb61-6689ab142e12', 
        'Aaron Swinton', 
        'Founder/Principal', 
        'aaron@mavrk.one', 
        'pending', 
        'Scrappy USC student / idea for MAVRK Studio', 
        'Hi Aaron,

I’m a student at USC studying automation.

I’ve been talking with boutique agency owners and noticed a specific bottleneck: you need to find new clients, but you don''t have time for manual research (and mass automation feels too spammy).

My partner and I built a human-in-the-loop AI system to fix this.

It handles the heavy lifting (scanning the market for buying signals and drafting the note), but nothing sends without your approval. It does 90% of the work; you keep 100% of the control.

I''m not trying to sell you another subscription. Just figured seeing a concrete example of how to scale outreach without losing your "founder voice" could be useful clarity for the business.

Mind if I send a 60-second Loom video showing how it works?

Best, 
Ty', 
        true,
        NOW(),
        NOW()
    ),
    (
        '1293206b-c5cd-46a8-82d8-f4848072511a', 
        'Nikola Cline', 
        'Founder/Principal', 
        'nikola@brandettes.com', 
        'pending', 
        'Scrappy USC student / idea for Brandettes', 
        'Hi Nikola,

I’m a student at USC studying automation.

I’ve been talking with boutique agency owners and noticed a specific bottleneck: you need to find new clients, but you don''t have time for manual research (and mass automation feels too spammy).

My partner and I built a human-in-the-loop AI system to fix this.

It handles the heavy lifting (scanning the market for buying signals and drafting the note), but nothing sends without your approval. It does 90% of the work; you keep 100% of the control.

I''m not trying to sell you another subscription. Just figured seeing a concrete example of how to scale outreach without losing your "founder voice" could be useful clarity for the business.

Mind if I send a 60-second Loom video showing how it works?

Best, 
Ty', 
        true,
        NOW(),
        NOW()
    ),
    (
        '2c4ef79d-f398-4902-9eb0-f50d56a9abaa', 
        'Alison Smith', 
        'Founder/Principal', 
        'alison@umaimarketing.com', 
        'pending', 
        'Scrappy USC student / idea for UMAI Marketing', 
        'Hi Alison,

I’m a student at USC studying automation.

I’ve been talking with boutique agency owners and noticed a specific bottleneck: you need to find new clients, but you don''t have time for manual research (and mass automation feels too spammy).

My partner and I built a human-in-the-loop AI system to fix this.

It handles the heavy lifting (scanning the market for buying signals and drafting the note), but nothing sends without your approval. It does 90% of the work; you keep 100% of the control.

I''m not trying to sell you another subscription. Just figured seeing a concrete example of how to scale outreach without losing your "founder voice" could be useful clarity for the business.

Mind if I send a 60-second Loom video showing how it works?

Best, 
Ty', 
        true,
        NOW(),
        NOW()
    ),
    (
        '0e6fc1c9-5c45-4dde-be02-177f6798fd76', 
        'Kevin Roberson', 
        'Founder/Principal', 
        'kevin@swigstudio.com', 
        'pending', 
        'Scrappy USC student / idea for Swig Studio', 
        'Hi Kevin,

I’m a student at USC studying automation.

I’ve been talking with boutique agency owners and noticed a specific bottleneck: you need to find new clients, but you don''t have time for manual research (and mass automation feels too spammy).

My partner and I built a human-in-the-loop AI system to fix this.

It handles the heavy lifting (scanning the market for buying signals and drafting the note), but nothing sends without your approval. It does 90% of the work; you keep 100% of the control.

I''m not trying to sell you another subscription. Just figured seeing a concrete example of how to scale outreach without losing your "founder voice" could be useful clarity for the business.

Mind if I send a 60-second Loom video showing how it works?

Best, 
Ty', 
        true,
        NOW(),
        NOW()
    ),
    (
        'ec1b1e02-1b90-4833-b386-d4cae4b31aeb', 
        'Jeff Lin', 
        'Founder/Principal', 
        'jeff@zenpack.us', 
        'pending', 
        'Scrappy USC student / idea for Zenpack', 
        'Hi Jeff,

I’m a student at USC studying automation.

I’ve been talking with boutique agency owners and noticed a specific bottleneck: you need to find new clients, but you don''t have time for manual research (and mass automation feels too spammy).

My partner and I built a human-in-the-loop AI system to fix this.

It handles the heavy lifting (scanning the market for buying signals and drafting the note), but nothing sends without your approval. It does 90% of the work; you keep 100% of the control.

I''m not trying to sell you another subscription. Just figured seeing a concrete example of how to scale outreach without losing your "founder voice" could be useful clarity for the business.

Mind if I send a 60-second Loom video showing how it works?

Best, 
Ty', 
        true,
        NOW(),
        NOW()
    ),
    (
        'e8d48171-1475-4a69-a585-b736eb3f512e', 
        'Kevin Shaw', 
        'Founder/Principal', 
        'kevin@strangerandstranger.com', 
        'pending', 
        'Scrappy USC student / idea for Stranger & Stranger', 
        'Hi Kevin,

I’m a student at USC studying automation.

I’ve been talking with boutique agency owners and noticed a specific bottleneck: you need to find new clients, but you don''t have time for manual research (and mass automation feels too spammy).

My partner and I built a human-in-the-loop AI system to fix this.

It handles the heavy lifting (scanning the market for buying signals and drafting the note), but nothing sends without your approval. It does 90% of the work; you keep 100% of the control.

I''m not trying to sell you another subscription. Just figured seeing a concrete example of how to scale outreach without losing your "founder voice" could be useful clarity for the business.

Mind if I send a 60-second Loom video showing how it works?

Best, 
Ty', 
        true,
        NOW(),
        NOW()
    ),
    (
        'e30248cb-bd01-4ff6-b9c4-261dd7dce2f0', 
        'Jonathan Ford', 
        'Founder/Principal', 
        'jonathan.f@pearlfisher.com', 
        'pending', 
        'Scrappy USC student / idea for Pearlfisher', 
        'Hi Jonathan,

I’m a student at USC studying automation.

I’ve been talking with boutique agency owners and noticed a specific bottleneck: you need to find new clients, but you don''t have time for manual research (and mass automation feels too spammy).

My partner and I built a human-in-the-loop AI system to fix this.

It handles the heavy lifting (scanning the market for buying signals and drafting the note), but nothing sends without your approval. It does 90% of the work; you keep 100% of the control.

I''m not trying to sell you another subscription. Just figured seeing a concrete example of how to scale outreach without losing your "founder voice" could be useful clarity for the business.

Mind if I send a 60-second Loom video showing how it works?

Best, 
Ty', 
        true,
        NOW(),
        NOW()
    ),
    (
        '63a13f65-3b68-4d8b-8a43-b432f99ac06d', 
        'Danielle McWaters', 
        'Founder/Principal', 
        'danielle@designsakestudio.com', 
        'pending', 
        'Scrappy USC student / idea for Design Sake Studio', 
        'Hi Danielle,

I’m a student at USC studying automation.

I’ve been talking with boutique agency owners and noticed a specific bottleneck: you need to find new clients, but you don''t have time for manual research (and mass automation feels too spammy).

My partner and I built a human-in-the-loop AI system to fix this.

It handles the heavy lifting (scanning the market for buying signals and drafting the note), but nothing sends without your approval. It does 90% of the work; you keep 100% of the control.

I''m not trying to sell you another subscription. Just figured seeing a concrete example of how to scale outreach without losing your "founder voice" could be useful clarity for the business.

Mind if I send a 60-second Loom video showing how it works?

Best, 
Ty', 
        true,
        NOW(),
        NOW()
    ),
    (
        '620f7f98-ff72-4125-8eb4-646afae72518', 
        'Grant Pogosyan', 
        'Founder/Principal', 
        'grant@grantedesigns.com', 
        'pending', 
        'Scrappy USC student / idea for Grantedesigns', 
        'Hi Grant,

I’m a student at USC studying automation.

I’ve been talking with boutique agency owners and noticed a specific bottleneck: you need to find new clients, but you don''t have time for manual research (and mass automation feels too spammy).

My partner and I built a human-in-the-loop AI system to fix this.

It handles the heavy lifting (scanning the market for buying signals and drafting the note), but nothing sends without your approval. It does 90% of the work; you keep 100% of the control.

I''m not trying to sell you another subscription. Just figured seeing a concrete example of how to scale outreach without losing your "founder voice" could be useful clarity for the business.

Mind if I send a 60-second Loom video showing how it works?

Best, 
Ty', 
        true,
        NOW(),
        NOW()
    ),
    (
        '930cd4ec-c5ba-4295-a8ba-27bf2ba7b246', 
        'Meghan Mahler', 
        'Founder/Principal', 
        'mmahler@meghanmahlerdesign.com', 
        'pending', 
        'Scrappy USC student / idea for Meghan Mahler Design', 
        'Hi Meghan,

I’m a student at USC studying automation.

I’ve been talking with boutique agency owners and noticed a specific bottleneck: you need to find new clients, but you don''t have time for manual research (and mass automation feels too spammy).

My partner and I built a human-in-the-loop AI system to fix this.

It handles the heavy lifting (scanning the market for buying signals and drafting the note), but nothing sends without your approval. It does 90% of the work; you keep 100% of the control.

I''m not trying to sell you another subscription. Just figured seeing a concrete example of how to scale outreach without losing your "founder voice" could be useful clarity for the business.

Mind if I send a 60-second Loom video showing how it works?

Best, 
Ty', 
        true,
        NOW(),
        NOW()
    );