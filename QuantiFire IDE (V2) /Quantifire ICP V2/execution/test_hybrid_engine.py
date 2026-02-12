#!/usr/bin/env python3
"""
Test script for Hybrid Email Engine.
Tests all three trigger types: EVENT, LEADERSHIP, VOLATILITY
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from templates.prompts import get_trigger_type, generate_hook_prompt, assemble_email
from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def test_trigger_classification():
    """Test trigger type detection"""
    print("=" * 60)
    print("TEST 1: Trigger Classification")
    print("=" * 60)
    
    test_cases = [
        ("Capital Markets Day", None, "EVENT"),
        ("CMD", None, "EVENT"),
        ("Investor Conference", None, "EVENT"),
        ("CFO Appointment", None, "LEADERSHIP"),
        ("New CFO announced", None, "LEADERSHIP"),
        ("Head of IR appointed", None, "LEADERSHIP"),
        ("Stock Drop", None, "VOLATILITY"),
        ("Update", "-15.2%", "VOLATILITY"),  # Negative performance
        ("Update", "+10.5%", "EVENT"),  # Positive performance, defaults to EVENT
    ]
    
    all_passed = True
    for event_type, performance, expected in test_cases:
        result = get_trigger_type(event_type, performance)
        status = "✓" if result == expected else "✗"
        if result != expected:
            all_passed = False
        print(f"  {status} '{event_type}' + '{performance}' → {result} (expected: {expected})")
    
    print(f"\nResult: {'PASSED' if all_passed else 'FAILED'}")
    return all_passed


def test_hook_generation():
    """Test OpenAI hook generation for each trigger type"""
    print("\n" + "=" * 60)
    print("TEST 2: Hook Generation (OpenAI)")
    print("=" * 60)
    
    if not OPENAI_API_KEY:
        print("  ⚠ OPENAI_API_KEY not set, skipping...")
        return False
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    test_cases = [
        {
            "trigger_type": "EVENT",
            "contact_name": "Claire-Marie",
            "company_name": "Allianz SE",
            "event_date": "2026-02-15",
            "role": None,
            "performance": "+28.1%"
        },
        {
            "trigger_type": "LEADERSHIP",
            "contact_name": "Martin Mildner",
            "company_name": "Scout24 SE",
            "event_date": None,
            "role": "Chief Financial Officer",
            "performance": "-5.7%"
        },
        {
            "trigger_type": "VOLATILITY",
            "contact_name": "Anna Dimitrova",
            "company_name": "Zalando SE",
            "event_date": None,
            "role": None,
            "performance": "-15.5%"
        }
    ]
    
    all_passed = True
    for case in test_cases:
        print(f"\n  Testing {case['trigger_type']} trigger...")
        
        prompt = generate_hook_prompt(**case)
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You generate exactly one sentence. No quotes. No extra text."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=150
        )
        
        hook = response.choices[0].message.content.strip()
        
        # Validate: should be one sentence, no quotes
        is_valid = (
            len(hook) > 20 and  # Minimum length
            len(hook) < 400 and  # Maximum length
            not hook.startswith('"') and
            not hook.startswith("'")
        )
        
        status = "✓" if is_valid else "✗"
        if not is_valid:
            all_passed = False
        
        print(f"    {status} Hook: {hook[:100]}...")
    
    print(f"\nResult: {'PASSED' if all_passed else 'FAILED'}")
    return all_passed


def test_email_assembly():
    """Test final email assembly"""
    print("\n" + "=" * 60)
    print("TEST 3: Email Assembly")
    print("=" * 60)
    
    hook = "With your Capital Markets Day approaching, ensuring your new strategic pillars land correctly with skeptics on the register is likely top of mind."
    
    email = assemble_email(
        hook=hook,
        contact_name="Claire-Marie Coste-Lepoutre",
        company_name="Allianz SE",
        sender_name="Test User"
    )
    
    # Validate structure
    checks = [
        ("Starts with greeting", email.startswith("Hi Claire-Marie")),
        ("Contains hook", hook in email),
        ("Contains 'Fiduciary Risk Audits'", "Fiduciary Risk Audits" in email),
        ("Contains 'Narrative Gap'", "Narrative Gap" in email),
        ("Contains company name", "Allianz SE" in email),
        ("Contains sender name", "Test User" in email),
        ("Contains QuantiFire", "QuantiFire" in email),
    ]
    
    all_passed = True
    for name, passed in checks:
        status = "✓" if passed else "✗"
        if not passed:
            all_passed = False
        print(f"  {status} {name}")
    
    print(f"\n--- Sample Email ---\n{email}\n--- End ---")
    print(f"\nResult: {'PASSED' if all_passed else 'FAILED'}")
    return all_passed


if __name__ == "__main__":
    print("\n🔧 HYBRID EMAIL ENGINE - TEST SUITE\n")
    
    results = []
    results.append(("Trigger Classification", test_trigger_classification()))
    results.append(("Hook Generation", test_hook_generation()))
    results.append(("Email Assembly", test_email_assembly()))
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {status}: {name}")
    
    all_passed = all(r[1] for r in results)
    print(f"\nOverall: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
