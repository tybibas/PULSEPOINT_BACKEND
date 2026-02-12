#!/bin/bash
set -e

# 1. Load Environment Variables (API Keys)
set -a
[ -f .env ] && source .env
set +a

# 2. Configure Library Paths for PDF Engine (WeasyPrint/Pango on macOS)
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_FALLBACK_LIBRARY_PATH

# 3. Check Arguments
if [ -z "$1" ]; then
    echo "Usage: ./run_pipeline.sh <TICKER>"
    exit 1
fi

TICKER=$1
echo "🚀 Starting Strategic Diagnostic for $TICKER..."

# Step 1: Orchestrate (Data Gathering)
echo "\n[1/3] Gathering Intelligence (Synthetic Analyst)..."
python3 orchestration/orchestrate_dossier.py --ticker "$TICKER" --output "dossier_$TICKER.json"

# Step 2: Synthesize (Narrative Generation)
echo "\n[2/3] Synthesizing Strategic Narrative..."
python3 orchestration/synthesize_report.py --ticker "$TICKER" --dossier "dossier_$TICKER.json" --output "report_content_$TICKER.json"

# Step 3: Render (PDF Generation)
echo "\n[3/3] Rendering Final PDF..."
python3 orchestration/render_report.py --ticker "$TICKER" --report "report_content_$TICKER.json"

echo "\n✅ DONE. Output: final_report_$TICKER.pdf"
