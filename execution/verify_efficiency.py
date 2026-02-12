import hashlib

def generate_search_hash(urls: list) -> str:
    """
    Create a deterministic fingerprint of the search results.
    Sorts URLs to ensure [A, B] == [B, A].
    """
    if not urls: return ""
    
    # Normalize: lowercase, strip query params if needed (simplest is just sorted list)
    sorted_urls = sorted([u.lower().strip() for u in urls if u])
    content = "|".join(sorted_urls)
    
    print(f"   Debug Content: {content[:100]}...")
    return hashlib.md5(content.encode()).hexdigest()

def test_fingerprinting():
    print("🚀 Testing Search Fingerprinting Logic...")
    
    # Scenario 1: Identical Lists (Different Order)
    list1 = ["https://example.com/news/1", "https://example.com/news/2"]
    list2 = ["https://example.com/news/2", "https://example.com/news/1"]
    
    hash1 = generate_search_hash(list1)
    hash2 = generate_search_hash(list2)
    
    print(f"   List 1 Hash: {hash1}")
    print(f"   List 2 Hash: {hash2}")
    
    if hash1 == hash2:
        print("   ✅ SUCCESS: Order independence verified.")
    else:
        print("   ❌ FAIL: Order affected hash.")

    # Scenario 2: New Content
    list3 = ["https://example.com/news/1", "https://example.com/news/2", "https://example.com/news/3"]
    hash3 = generate_search_hash(list3)
    
    print(f"   List 3 Hash: {hash3}")
    
    if hash3 != hash1:
        print("   ✅ SUCCESS: New content generated new hash.")
    else:
        print("   ❌ FAIL: Hash collision with new content.")

    # Scenario 3: Real World (Google URLs often have tracking params)
    list4 = ["https://example.com/news/1?utm_source=google", "https://example.com/news/2"]
    # Our simple logic currently keeps params. This is safer for "exact match" but might be too strict.
    # User approved "Result Set" matching. If URL changes slightly, we Rescan. This is acceptable for safety.
    pass

if __name__ == "__main__":
    test_fingerprinting()
