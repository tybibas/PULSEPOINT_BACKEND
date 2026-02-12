import json

def deduplicate():
    path = "pulsepoint_strategic/leads/leads.json"
    
    with open(path, "r") as f:
        data = json.load(f)

    unique_companies = []
    seen_names = set()
    
    duplicates_removed = 0
    
    for company in data["companies"]:
        name = company["name"]
        if name in seen_names:
            print(f"Removing duplicate: {name}")
            duplicates_removed += 1
            continue
            
        seen_names.add(name)
        unique_companies.append(company)
        
    data["companies"] = unique_companies
    
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        
    print(f"Deduplication complete. Removed {duplicates_removed} duplicates. Total remaining: {len(unique_companies)}")

if __name__ == "__main__":
    deduplicate()
