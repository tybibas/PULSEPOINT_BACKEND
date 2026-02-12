#!/usr/bin/env python3
import argparse
import json
import sys

def mock_data():
    """
    Returns mock NCS Score based on SOP-01.
    Formula: (% Pos Unscripted) - (% Skeptical/Neg)
    """
    pos_unscripted = 65
    skeptical = 40
    ncs = pos_unscripted - skeptical
    
    return {
        "positive_unscripted_percent": pos_unscripted,
        "skeptical_negative_percent": skeptical,
        "ncs_score": ncs,
        "adjustment_factor": "Audio Biomarkers Detected (Mock)",
        "final_ncs": ncs - 5  # Downweighting for audio biomarkers
    }

def calculate_ncs(pos_percent, neg_percent):
    """
    Calculates NCS based on inputs or defaults to mock if inputs are missing/placeholder.
    This script is more of a calculator than a fetcher, so it processes inputs.
    """
    if pos_percent is None or neg_percent is None:
        return mock_data()
    
    ncs = pos_percent - neg_percent
    return {
        "positive_unscripted_percent": pos_percent,
        "skeptical_negative_percent": neg_percent,
        "ncs_score": ncs
    }

def main():
    parser = argparse.ArgumentParser(description="Calculate Net Confidence Score (NCS).")
    parser.add_argument("--pos", type=float, help="Positive Unscripted Percentage")
    parser.add_argument("--neg", type=float, help="Skeptical/Negative Percentage")
    args = parser.parse_args()

    try:
        data = calculate_ncs(args.pos, args.neg)
        print(json.dumps(data, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
