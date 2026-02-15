
import unittest
from datetime import datetime, timedelta

def compute_deal_score(confidence, signal_type, signal_date, icp_match_score=5):
    """
    Computes a deterministic Deal Score (0-100).
    Components:
    1. Confidence (0-40): (conf/10) * 40
    2. Trigger Weight (0-30): Based on signal type
    3. Recency (0-20): Based on days since signal
    4. ICP Match (0-10): Input provided or default
    """
    # 1. Confidence Component (Max 40)
    # Ensure confidence is float 0-10
    try:
        conf = float(confidence)
    except:
        conf = 0.0
    conf_comp = round((min(max(conf, 0), 10) / 10) * 40)
    
    # 2. Trigger Weight Component (Max 30)
    weights = {
        "REAL_TIME_DETECTED": 30,
        "LINKEDIN_ACTIVITY": 18,
        "CONTEXT_ANCHOR": 15
    }
    # Normalize input and handle defaults
    stype = str(signal_type).upper() if signal_type else "UNKNOWN"
    # Fallback for nuanced types if needed, or simple exact match
    weight_comp = weights.get(stype, 10) # Default 10 for unknown
    
    # 3. Recency Component (Max 20)
    if not signal_date:
        recency_comp = 0
    else:
        # If signal_date is string, parse it? Assuming date object or datetime
        if isinstance(signal_date, str):
            try:
                # Handle YYYY-MM-DD
                dt = datetime.strptime(signal_date[:10], "%Y-%m-%d")
            except:
                dt = datetime.now() # Fallback
        else:
            dt = signal_date
            
        # If dt is naive, assume local/utc doesn't matter for diff days
        # Simplify: just take days diff
        delta = (datetime.now() - dt).days
        if delta <= 7:
            recency_comp = 20
        elif delta <= 14:
            recency_comp = 15
        elif delta <= 30:
            recency_comp = 8
        else:
            recency_comp = 0
            
    # 4. ICP Match Component (Max 10)
    icp_comp = min(max(icp_match_score, 0), 10)
    
    total = conf_comp + weight_comp + recency_comp + icp_comp
    return min(max(total, 0), 100)

class TestDealScore(unittest.TestCase):
    def test_perfect_score(self):
        # 10 conf + REAL_TIME + Today + 10 ICP
        score = compute_deal_score(10, "REAL_TIME_DETECTED", datetime.now(), 10)
        # 40 + 30 + 20 + 10 = 100
        print(f"Perfect Score: {score}")
        self.assertEqual(score, 100)

    def test_average_signal(self):
        # 7 conf + CONTEXT_ANCHOR + 3 weeks old + 5 ICP
        d = datetime.now() - timedelta(days=21)
        score = compute_deal_score(7, "CONTEXT_ANCHOR", d, 5)
        # Conf: (7/10)*40 = 28
        # Weight: 15
        # Recency: 8
        # ICP: 5
        # Total: 56
        print(f"Average Context Anchor: {score}")
        self.assertEqual(score, 56)

    def test_linkedin_fresh(self):
        # 8 conf + LINKEDIN + 2 days old + 5 ICP
        d = datetime.now() - timedelta(days=2)
        score = compute_deal_score(8, "LINKEDIN_ACTIVITY", d, 5)
        # Conf: 32
        # Weight: 18
        # Recency: 20
        # ICP: 5
        # Total: 75
        print(f"Fresh LinkedIn: {score}")
        self.assertEqual(score, 75)

    def test_garbage(self):
        # 2 conf + UNKNOWN + Old + 0 ICP
        d = datetime.now() - timedelta(days=100)
        score = compute_deal_score(2, "BLAH", d, 0)
        # Conf: 8
        # Weight: 10
        # Recency: 0
        # ICP: 0
        # Total: 18
        print(f"Garbage Signal: {score}")
        self.assertEqual(score, 18)

if __name__ == '__main__':
    unittest.main()
