#!/usr/bin/env python3
"""
🧠 BATUKA MULTI-MARKET ORCHESTRATOR
Run market analysis for India, US, UK, Singapore sequentially
Sends Telegram update for each market automatically
"""

from __future__ import annotations

import os
import json
import logging
import time
from datetime import datetime
import pytz

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# IMPORTS FROM BATUKA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from batuka_bhairav.config import MARKETS, CONVICTION_WEIGHTS
from batuka_bhairav.universe.fetch_universe import (
    fetch_nse500, fetch_sp500, fetch_ftse100, fetch_sgx
)
from batuka_bhairav.universe.market_data import fetch_market_data
from batuka_bhairav.core.scoring import conviction_score_0_100, longterm_score
from batuka_bhairav.core.sector import compute_sector_strength
from batuka_bhairav.core.regime import get_market_regime
from batuka_bhairav.telegram_orchestrator import send_telegram_message

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LOGGING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(name)s | %(levelname)s: %(message)s'
)
logger = logging.getLogger("batuka_orchestrator")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 1: FETCH UNIVERSE BY MARKET
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_universe(market_code: str) -> list[dict]:
    """
    Fetch stock universe for given market
    Returns: [{"symbol": "TCS", "name": "Tata Consultancy", "sector": "IT"}, ...]
    """
    logger.info(f"📥 Fetching universe for: {market_code}")
    
    try:
        if market_code == "IN":
            rows = fetch_nse500()
            logger.info(f"✅ India: {len(rows)} stocks")
        elif market_code == "US":
            rows = fetch_sp500()
            logger.info(f"✅ USA: {len(rows)} stocks")
        elif market_code == "UK":
            rows = fetch_ftse100()
            logger.info(f"✅ UK: {len(rows)} stocks")
        elif market_code == "SG":
            rows = fetch_sgx()
            logger.info(f"✅ Singapore: {len(rows)} stocks")
        else:
            logger.error(f"❌ Unknown market: {market_code}")
            return []
        
        return rows
    
    except Exception as e:
        logger.error(f"❌ Error fetching universe: {e}")
        return []


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 2: EXPLANATION ENGINE (from run_engine.py)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def explain_stock(r: dict) -> str:
    """Generate plain-English explanation for why stock scored high"""
    reasons = []

    if r.get("above_sma20") and r.get("above_sma50"):
        reasons.append("price above key moving averages (uptrend)")

    if r.get("mom_20d", 0) > 1:
        reasons.append(f"short-term momentum +{round(r['mom_20d'], 1)}%")

    if r.get("mom_60d", 0) > 5:
        reasons.append(f"strong medium-term trend +{round(r['mom_60d'], 1)}%")

    if r.get("vol_ratio", 0) > 1.3:
        reasons.append("high volume — institutional activity")

    if 45 < r.get("rsi", 50) < 65:
        reasons.append("RSI balanced — healthy trend")

    return "\n• ".join(reasons[:4])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 3: TRADE LEVELS (from run_engine.py)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def trade_levels(r: dict, currency_symbol: str = "₹") -> tuple:
    """Calculate entry, target, stop loss levels"""
    price = r.get("price", 100)

    entry_low = round(price * 0.995, 2)
    entry_high = round(price * 1.01, 2)

    target = round(price * 1.03, 2)
    stop = round(price * 0.98, 2)

    rr = round((target - price) / max(price - stop, 0.01), 2)

    return entry_low, entry_high, target, stop, rr


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 4: ANALYZE SINGLE MARKET
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def analyze_market(market_code: str) -> dict | None:
    """
    Complete market analysis pipeline:
    1. Fetch universe
    2. Fetch market data (OHLCV + indicators)
    3. Compute sectors
    4. Score stocks
    5. Generate picks
    6. Return payload
    """
    
    logger.info(f"\n{'='*70}")
    logger.info(f"🔍 ANALYZING MARKET: {market_code} - {MARKETS[market_code]['name']}")
    logger.info(f"{'='*70}")
    
    try:
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 1. FETCH UNIVERSE
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        rows = get_universe(market_code)
        if not rows:
            logger.error(f"❌ No stocks found for {market_code}")
            return None
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 2. FETCH MARKET DATA (OHLCV + technical indicators)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        logger.info(f"📡 Fetching market data for {len(rows)} stocks...")
        symbols = [r["symbol"] for r in rows]
        market_data = fetch_market_data(symbols)
        logger.info(f"✅ Got data for {len(market_data)} stocks")
        
        # Attach market data to universe rows
        enriched = []
        for r in rows:
            sym = r["symbol"]
            if sym in market_data:
                r.update(market_data[sym])
                enriched.append(r)
        
        logger.info(f"📊 Enriched: {len(enriched)} stocks with data")
        
        if not enriched:
            logger.error(f"❌ No enriched data for {market_code}")
            return None
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 3. COMPUTE SECTORS
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        sector_rank, sector_table = compute_sector_strength(enriched)
        logger.info(f"🏢 Sectors computed: {len(sector_table)} sectors")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 4. GET MARKET REGIME
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        regime = get_market_regime()
        logger.info(f"📈 Market Regime: {regime}")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 5. SCORE STOCKS
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        scored = []
        for r in enriched:
            sec = sector_rank.get(r.get("sector"), 0)
            
            try:
                score = conviction_score_0_100(
                    r, sec, 0.5, regime, CONVICTION_WEIGHTS
                )
                r["conviction"] = score
                scored.append(r)
            except Exception as e:
                logger.debug(f"⚠️ Scoring error for {r.get('symbol')}: {e}")
                continue
        
        # Sort by conviction
        scored.sort(key=lambda x: x["conviction"], reverse=True)
        logger.info(f"⭐ Scored {len(scored)} stocks")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 6. STRONG PICKS ONLY
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        btst = [
            x for x in scored
            if x.get("conviction", 0) > 70
            and x.get("vol_ratio", 0) > 1.2
            and x.get("day_change_pct", 0) > 0.5
        ][:3]
        
        long_term = [
            x for x in scored
            if x.get("conviction", 0) > 65
            and x.get("mom_60d", 0) > 5
        ][:3]
        
        logger.info(f"🎯 BTST picks: {len(btst)} | Long-term: {len(long_term)}")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 7. STAR OF THE DAY
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        star = max(
            (scored or [{"symbol": "N/A", "day_change_pct": 0}]),
            key=lambda x: x.get("day_change_pct", 0)
        )
        logger.info(f"🏆 Star: {star.get('symbol')} (+{star.get('day_change_pct', 0):.2f}%)")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 8. TOMORROW OUTLOOK
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        avg = sum(x.get("day_change_pct", 0) for x in enriched) / len(enriched)
        
        if avg > 1:
            tomorrow = "Strong bullish continuation possible"
        elif avg > 0:
            tomorrow = "Mild positive bias — selective buying"
        elif avg > -0.5:
            tomorrow = "Range-bound market — wait for breakout"
        else:
            tomorrow = "Weakness likely — avoid aggressive trades"
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 9. BUILD PAYLOAD
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        market_config = MARKETS[market_code]
        
        payload = {
            "market_code": market_code,
            "market_name": market_config["name"],
            "currency": market_config["currency"],
            "timezone": market_config["timezone"],
            "index_label": market_config["index_label"],
            "generated_at": datetime.now(
                pytz.timezone(market_config["timezone"])
            ).isoformat(),
            "regime": regime,
            "total_scanned": len(enriched),
            "sector_table": sector_table[:5],  # Top 5 sectors
            "star": star,
            "btst": btst,
            "long_term": long_term,
            "tomorrow": tomorrow,
        }
        
        logger.info(f"✅ {market_code} analysis complete")
        return payload
    
    except Exception as e:
        logger.error(f"❌ Exception in {market_code}: {e}", exc_info=True)
        return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 5: RENDER TELEGRAM MESSAGE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def render_message(payload: dict) -> str:
    """
    Render human-friendly telegram message from analysis payload
    """
    
    market_code = payload["market_code"]
    market_name = payload["market_name"]
    currency = payload["currency"]
    regime = payload["regime"]
    star = payload.get("star", {})
    btst = payload.get("btst", [])
    long_term = payload.get("long_term", [])
    sector_table = payload.get("sector_table", [])
    tomorrow = payload.get("tomorrow", "")
    
    msg = f"""
<b>🧠 BATUKA BHAIRAVA</b>
📍 {market_name}
🕐 {payload['generated_at'][-8:]}

<b>🟡 Market Today: {regime}</b>

"""
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SECTORS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    if sector_table:
        msg += "<b>📈 Sectors showing strength</b>\n"
        for s in sector_table[:3]:
            score = s.get("score", 0)
            msg += f"▲ {s['sector']} +{round(score, 2)}%\n"
        
        msg += "\n<b>📉 Sectors under pressure</b>\n"
        for s in reversed(sector_table[-3:]):
            score = s.get("score", 0)
            msg += f"▼ {s['sector']} {round(score, 2)}%\n"
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # STAR OF THE DAY
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    if star and star.get("symbol"):
        msg += f"""
<b>🏆 STAR OF THE DAY</b>
<b>{star['symbol']}</b>
{star.get('name', '')}

Moved <b>{round(star.get('day_change_pct', 0), 2)}%</b>
Volume <b>{round(star.get('vol_ratio', 0), 2)}x</b>
Conviction: {round(star.get('conviction', 0), 1)}
"""
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # BTST PICKS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    msg += "\n<b>🌙 BTST PICKS</b>\n"
    
    if btst:
        for i, r in enumerate(btst, 1):
            reasons = explain_stock(r)
            e1, e2, t, s, rr = trade_levels(r, currency)
            
            msg += f"""
<b>{i}. {r['symbol']}</b>

Entry: {currency}{e1}-{e2}
Target: {currency}{t} | Stop: {currency}{s}

📊 Why:
{reasons}

Risk/Reward: {rr}x
"""
    else:
        msg += "⚠️ No strong BTST setups today\n"
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # LONG TERM PICKS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    msg += "\n<b>📈 LONG TERM PICKS</b>\n"
    
    if long_term:
        for i, r in enumerate(long_term, 1):
            reasons = explain_stock(r)
            
            msg += f"""
<b>{i}. {r['symbol']}</b>

📊 Why:
{reasons}

Conviction: {round(r.get('conviction', 0), 1)}
"""
    else:
        msg += "⚠️ No strong long-term setups today\n"
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TOMORROW OUTLOOK
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    msg += f"""
<b>🔮 Tomorrow</b>
{tomorrow}

⚠️ AI-generated insight. Not financial advice.
"""
    
    return msg


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 6: MAIN ORCHESTRATOR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def run_all_markets():
    """
    Main orchestrator:
    1. Loop through IN, US, UK, SG
    2. Analyze each market
    3. Render telegram message
    4. Send with retry
    5. Save JSON
    """
    
    logger.info(f"\n{'='*70}")
    logger.info("🚀 BATUKA MULTI-MARKET ORCHESTRATOR START")
    logger.info(f"{'='*70}")
    logger.info(f"⏰ Time: {datetime.now(pytz.UTC).isoformat()}")
    logger.info(f"🌍 Markets: IN → US → UK → SG\n")
    
    # Get Telegram credentials
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("❌ TELEGRAM_TOKEN or TELEGRAM_CHAT_ID not set")
        logger.error("Set environment variables and try again")
        return
    
    markets = ["IN", "US", "UK", "SG"]
    results = {}
    
    for market_code in markets:
        try:
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # 1. ANALYZE MARKET
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            
            payload = analyze_market(market_code)
            
            if not payload:
                logger.warning(f"⚠️ Skipping {market_code} - no data")
                continue
            
            results[market_code] = payload
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # 2. RENDER MESSAGE
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            
            logger.info(f"📝 Rendering message for {market_code}...")
            message = render_message(payload)
            logger.info(f"   Message size: {len(message)} chars")
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # 3. SEND TELEGRAM
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            
            logger.info(f"📤 Sending Telegram for {market_code}...")
            success = send_telegram_message(
                message,
                TELEGRAM_TOKEN,
                TELEGRAM_CHAT_ID
            )
            
            if success:
                logger.info(f"✅ {market_code} telegram sent successfully")
            else:
                logger.error(f"❌ {market_code} telegram failed")
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # 4. SAVE JSON
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            
            json_file = f"output_{market_code}.json"
            with open(json_file, "w") as f:
                json.dump(payload, f, indent=2, default=str)
            logger.info(f"💾 Saved to {json_file}")
            
            # Small delay to avoid rate limiting
            time.sleep(2)
        
        except Exception as e:
            logger.error(f"❌ Exception in {market_code}: {e}", exc_info=True)
            continue
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SAVE CONSOLIDATED RESULTS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    with open("output_consolidated.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"💾 Consolidated results saved to output_consolidated.json")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SUMMARY
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    logger.info(f"\n{'='*70}")
    logger.info("✅ ORCHESTRATION COMPLETE")
    logger.info(f"{'='*70}")
    logger.info(f"Markets processed: {', '.join(results.keys())}")
    logger.info(f"Telegrams sent: {len(results)}")
    logger.info(f"✅ All done! Check Telegram for updates.\n")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ENTRY POINT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    run_all_markets()
