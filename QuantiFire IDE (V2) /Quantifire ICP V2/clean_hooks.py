import json
import re
import sys

FILE = "master_universe_queue.json"

def clean_hooks():
    try:
        with open(FILE, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading {FILE}: {e}")
        return

    cleaned_count = 0
    for row in data:
        hook = row.get("AI_Hook_Draft", "")
        # Check for double greeting pattern
        # "Hi Name,\n\nHi Name, ..."
        
        # Strategy: Remove leading "Hi Name," loops until only body remains?
        # Or just remove ALL "Hi Name," at start and re-add ONE.
        
        # 1. Normalize: remove all "Hi ..., " or "Dear ..., " from start
        # Use simple loop to catch multiple
        original_hook = hook
        
        # Strip simple "Hi Name," prefix multiple times
        # Regex: Start of string, Hi/Hello/Dear, name (anything until comma/newline), comma/newline, whitespace
        pattern = r'^(?:Hi|Hello|Dear)\s+[^,\n]+(?:,|\n)\s*'
        
        temp_hook = hook
        while re.match(pattern, temp_hook, re.IGNORECASE):
            temp_hook = re.sub(pattern, '', temp_hook, count=1, flags=re.IGNORECASE)
        
        # Now temp_hook is Hook + Body. 
        # Isolate the Hook (First paragraph before \n\n)
        temp_hook = temp_hook.strip()
        parts = temp_hook.split('\n\n')
        hook_text = parts[0].strip()
        
        # Capitalize first letter
        if hook_text:
            hook_text = hook_text[0].upper() + hook_text[1:]
        
        # Format as requested: "Hi Name, Hook."
        first_name = row.get("First_Name", "there").split()[0]
        # Ensure we don't duplicate greeting if hook_text already has it (unlikely after strip)
        new_hook = f"Hi {first_name}, {hook_text}"
        
        if new_hook != original_hook:
            row["AI_Hook_Draft"] = new_hook
            cleaned_count += 1
            print(f"Cleaned hook for {row['Company_Name']} ({row['Role']})")

    if cleaned_count > 0:
        with open(FILE, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Saved {cleaned_count} cleaned rows.")
    else:
        print("No rows needed cleaning.")

if __name__ == "__main__":
    clean_hooks()
