#!/usr/bin/env python3
"""
personalization_research.py

Gathers "Consulting Grade" research context for each company to power
high-specificity personalized email hooks.

Three archetypes:
1. Transcript Miner - Simulates Q&A friction from company context
2. Peer Gap - Identifies valuation disparity with sector peers
3. Event Context - Ties upcoming events to narrative risk

Usage:
    from execution.personalization_research import get_personalization_context
    context = get_personalization_context(company_data, all_companies)
"""

import json
import os
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# PEER VALUATION DATA
# ============================================================================

def calculate_implied_pe(market_cap: float, price: float) -> Optional[float]:
    """
    Estimate P/E ratio from market cap and price.
    This is a rough proxy—real P/E would need earnings data.
    For now, use relative market cap / price as a valuation proxy.
    """
    if not market_cap or not price or price <= 0:
        return None
    # Simplified: shares outstanding * approximation
    # We'll use market_cap / (price * 1M) as a rough "scale" metric
    return round(market_cap / (price * 1_000_000), 1)


def find_sector_peers(company_data: Dict, all_companies: List[Dict], limit: int = 3) -> List[Dict]:
    """
    Find sector/industry peers for comparison.
    Returns list of peer companies with valuation data.
    """
    target_sector = company_data.get("sector", "")
    target_industry = company_data.get("industry", "")
    target_ticker = company_data.get("ticker", "")
    
    peers = []
    
    for c in all_companies:
        if c.get("ticker") == target_ticker:
            continue
            
        # Prefer same industry, fallback to sector
        same_industry = c.get("industry") == target_industry
        same_sector = c.get("sector") == target_sector
        
        if same_industry or same_sector:
            change = c.get("fifty_two_week_change", 0) or 0
            peers.append({
                "name": c.get("name"),
                "ticker": c.get("ticker"),
                "market_cap": c.get("market_cap", 0),
                "price": c.get("current_price", 0),
                "performance": change * 100,
                "same_industry": same_industry
            })
    
    # Sort by industry match first, then by market cap
    peers.sort(key=lambda x: (not x["same_industry"], -x.get("market_cap", 0)))
    
    return peers[:limit]


def calculate_peer_gap(company_data: Dict, peers: List[Dict]) -> Optional[Dict]:
    """
    Calculate valuation gap between company and its best peer.
    Returns dict with peer name, company performance, peer performance, and gap.
    """
    if not peers:
        return None
    
    company_perf = (company_data.get("fifty_two_week_change", 0) or 0) * 100
    
    # Find the peer with the biggest positive gap (outperforming this company)
    best_gap = None
    best_peer = None
    
    for peer in peers:
        peer_perf = peer.get("performance", 0)
        gap = peer_perf - company_perf
        
        if gap > 10:  # Significant gap threshold
            if best_gap is None or gap > best_gap:
                best_gap = gap
                best_peer = peer
    
    if best_peer:
        return {
            "peer_name": best_peer["name"],
            "peer_ticker": best_peer["ticker"],
            "company_performance": round(company_perf, 1),
            "peer_performance": round(best_peer["performance"], 1),
            "gap": round(best_gap, 1)
        }
    
    return None


# ============================================================================
# TRANSCRIPT SIMULATION (Context Generation)
# ============================================================================

def generate_transcript_context(company_data: Dict) -> Optional[Dict]:
    """
    Simulate transcript friction points from company description and financials.
    In a real system, this would call an earnings transcript API.
    
    Returns context that can be used for "Transcript Miner" archetype.
    """
    description = company_data.get("description", "")
    sector = company_data.get("sector", "")
    industry = company_data.get("industry", "")
    change = (company_data.get("fifty_two_week_change", 0) or 0) * 100
    
    # Identify potential friction topics based on sector and performance
    friction_topics = []
    
    # Sector-specific anxieties
    sector_anxieties = {
        "Consumer Cyclical": ["consumer demand visibility", "inventory levels", "discretionary spending outlook"],
        "Technology": ["AI investment returns", "cloud growth deceleration", "margin compression"],
        "Financial Services": ["credit quality", "net interest margin pressure", "regulatory capital"],
        "Healthcare": ["pipeline milestones", "pricing pressure", "patent cliff exposure"],
        "Industrials": ["order book visibility", "supply chain normalization", "margin recovery"],
        "Basic Materials": ["commodity price volatility", "volume guidance", "energy cost pass-through"],
        "Consumer Defensive": ["private label competition", "promotional intensity", "volume vs price mix"],
        "Utilities": ["rate case outcomes", "renewable transition costs", "grid investment returns"],
        "Communication Services": ["subscriber growth", "ARPU trends", "content cost discipline"],
        "Real Estate": ["occupancy rates", "rental growth sustainability", "refinancing risk"],
    }
    
    friction_topics = sector_anxieties.get(sector, ["forward guidance", "margin outlook", "capital allocation"])
    
    # Performance-based context
    if change < -20:
        context_tone = "defensive"
        analyst_mood = "skeptical buy-side pushing on recovery timeline"
    elif change < 0:
        context_tone = "cautious"
        analyst_mood = "analysts questioning near-term visibility"
    elif change > 50:
        context_tone = "high expectations"
        analyst_mood = "buy-side concerned about sustainability of outperformance"
    else:
        context_tone = "neutral"
        analyst_mood = "market seeking clarity on forward guidance"
    
    return {
        "friction_topic": friction_topics[0],
        "secondary_topic": friction_topics[1] if len(friction_topics) > 1 else None,
        "context_tone": context_tone,
        "analyst_mood": analyst_mood,
        "sector": sector,
        "industry": industry
    }


# ============================================================================
# EVENT CONTEXT
# ============================================================================

def generate_event_context(company_data: Dict) -> Dict:
    """
    Generate event-based context for personalization.
    Uses stock performance as the primary "event" driver.
    """
    change = (company_data.get("fifty_two_week_change", 0) or 0) * 100
    name = company_data.get("name", "")
    
    # Determine narrative risk based on performance
    if change > 100:
        event_type = "exceptional_outperformance"
        narrative_risk = "expectations may be outpacing fundamentals"
        urgency = "before momentum investors start taking profits"
    elif change > 30:
        event_type = "strong_performance"
        narrative_risk = "success narrative may be masking emerging risks"
        urgency = "while the story is still being written"
    elif change < -30:
        event_type = "significant_underperformance"
        narrative_risk = "recovery narrative may not be landing with skeptics"
        urgency = "before the bear case becomes consensus"
    elif change < -10:
        event_type = "underperformance"
        narrative_risk = "valuation gap may reflect narrative disconnect"
        urgency = "ahead of the next major catalyst"
    else:
        event_type = "neutral"
        narrative_risk = "share of voice may be lower than warranted"
        urgency = "before competitors capture mindshare"
    
    return {
        "event_type": event_type,
        "performance": round(change, 1),
        "narrative_risk": narrative_risk,
        "urgency": urgency
    }


# ============================================================================
# MAIN CONTEXT BUILDER
# ============================================================================

def get_personalization_context(company_data: Dict, all_companies: List[Dict]) -> Dict:
    """
    Build comprehensive personalization context for a company.
    
    Returns dict with:
    - recommended_archetype: 'transcript_miner', 'peer_gap', or 'event_context'
    - transcript_context: Simulated Q&A friction data
    - peer_context: Valuation gap with competitors
    - event_context: Performance-based narrative risk
    - company_basics: Name, sector, performance
    """
    name = company_data.get("name", "")
    ticker = company_data.get("ticker", "")
    change = (company_data.get("fifty_two_week_change", 0) or 0) * 100
    
    # Gather all context types
    transcript_context = generate_transcript_context(company_data)
    peers = find_sector_peers(company_data, all_companies)
    peer_gap = calculate_peer_gap(company_data, peers)
    event_context = generate_event_context(company_data)
    
    # Select recommended archetype based on available data quality
    # Priority: Peer Gap (if significant) > Transcript (if underperforming) > Event
    if peer_gap and peer_gap["gap"] > 20:
        recommended_archetype = "peer_gap"
    elif transcript_context and abs(change) > 20:
        recommended_archetype = "transcript_miner"
    else:
        recommended_archetype = "event_context"
    
    return {
        "recommended_archetype": recommended_archetype,
        "transcript_context": transcript_context,
        "peer_context": {
            "peers": peers,
            "gap_analysis": peer_gap
        },
        "event_context": event_context,
        "company_basics": {
            "name": name,
            "ticker": ticker,
            "sector": company_data.get("sector"),
            "industry": company_data.get("industry"),
            "performance": round(change, 1),
            "market_cap": company_data.get("market_cap")
        }
    }


# ============================================================================
# CLI TEST
# ============================================================================

if __name__ == "__main__":
    # Test with sample data
    DAX_FILE = "dax_constituents.json"
    
    if os.path.exists(DAX_FILE):
        with open(DAX_FILE, 'r') as f:
            companies = json.load(f)
        
        # Test first 3 companies
        for company in companies[:3]:
            print(f"\n{'='*60}")
            print(f"Company: {company['name']}")
            print(f"{'='*60}")
            
            context = get_personalization_context(company, companies)
            print(f"Recommended Archetype: {context['recommended_archetype']}")
            print(f"Performance: {context['company_basics']['performance']}%")
            
            if context['peer_context']['gap_analysis']:
                gap = context['peer_context']['gap_analysis']
                print(f"Peer Gap: {gap['peer_name']} outperforms by {gap['gap']}%")
            
            if context['transcript_context']:
                tc = context['transcript_context']
                print(f"Friction Topic: {tc['friction_topic']}")
                print(f"Analyst Mood: {tc['analyst_mood']}")
    else:
        print(f"Error: {DAX_FILE} not found")
