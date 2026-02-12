#!/usr/bin/env python3
import argparse
import json
import subprocess
import concurrent.futures
import os
import sys
import datetime

# Define the list of execution scripts to run
SCRIPTS = {
    "strategy": "execution/fetch_management_strategy.py",
    "peers": "execution/fetch_peer_group.py",
    "sanitization": "execution/analyze_sanitization_score.py",
    "sentiment_velocity": "execution/analyze_sentiment_velocity.py",
    "valuation_gap": "execution/calculate_valuation_gap.py",
    "activism_risk": "execution/check_activism_risk.py",
    "consensus_divergence": "execution/analyze_consensus_divergence.py",
    # Note: NCS score is calculated after we have sentiment data, or can be run partially if inputs are mock
    # For now we'll run it separately or integrate it logic-side after gathering data
}

# Add execution directory to path to allow import
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from execution.sanitize_data import sanitize_data

def run_script(script_name, script_path, ticker, extra_args=None):
    """
    Runs a single python script and captures its JSON output.
    """
    cmd = ["python3", script_path, "--ticker", ticker]
    if extra_args:
        cmd.extend(extra_args)
        
    try:
        # We need to pass the environment variables (API keys) to the subprocess
        env = os.environ.copy()
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        
        if result.returncode != 0:
            print(f"Error running {script_name}: {result.stderr}", file=sys.stderr)
            return script_name, {"error": result.stderr}
            
        try:
            data = json.loads(result.stdout)
            return script_name, data
        except json.JSONDecodeError:
            print(f"Invalid JSON from {script_name}: {result.stdout}", file=sys.stderr)
            return script_name, {"error": "Invalid JSON output", "raw": result.stdout}
            
    except Exception as e:
        print(f"Exception running {script_name}: {e}", file=sys.stderr)
        return script_name, {"error": str(e)}

def build_dossier(ticker):
    """
    Runs all scripts in parallel and aggregates results WITH SANITIZATION.
    """
    dossier = {
        "meta": {
            "ticker": ticker,
            "generated_at": datetime.datetime.now().isoformat(),
            "version": "1.0 (Live/Sanitized)"
        },
        "data": {}
    }

    # Prepare extra arguments for specific scripts
    script_args = {
        "valuation_gap": ["--assumption", "10% Growth (Automated Probe)"]
    }

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_script = {
            executor.submit(run_script, name, path, ticker, script_args.get(name)): name
            for name, path in SCRIPTS.items()
        }
        
        for future in concurrent.futures.as_completed(future_to_script):
            name, raw_data = future.result()
            
            # --- DATA NORMALIZATION LAYER ---
            # 1. Normalize/Sanitize the raw data before adding to dossier
            clean_data = sanitize_data(raw_data)
            dossier["data"][name] = clean_data
            # --------------------------------
            
    # Calculate NCS Score based on gathered sentiment (if available)
    # This is a bit of a placeholder logic binding; ideally NCS script takes CLI args
    # But for now we might just skip it or run it if we had the precise numbers.
    # We'll just append a placeholder or rely on the script being run manually if needed for precision.
    
    return dossier

def main():
    parser = argparse.ArgumentParser(description="Orchestrate the creation of a Strategic Intelligence Dossier.")
    parser.add_argument("--ticker", required=True, help="Target Stock Ticker")
    parser.add_argument("--output", help="Output file path (default: dossier_{ticker}.json)")
    
    args = parser.parse_args()
    
    print(f"Building dossier for {args.ticker}...", file=sys.stderr)
    dossier = build_dossier(args.ticker)
    
    output_path = args.output or f"dossier_{args.ticker}.json"
    with open(output_path, "w") as f:
        json.dump(dossier, f, indent=2)
        
    print(f"Dossier saved to {output_path}", file=sys.stderr)

if __name__ == "__main__":
    main()
