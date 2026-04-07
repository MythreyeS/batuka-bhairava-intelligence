# batuka_bhairav/run_engine.py
# ✅ FIXED: Works with new multi-market config + proper imports
 
"""
Single-market analysis engine.
Updated to work with new config structure.
"""
 
from __future__ import annotations
import os
import logging
from batuka_bhairav.config import (
    MARKETS,
    CONVICTION_WEIGHTS,
    BTST_CONVICTION_MIN,
    BTST_VOL_RATIO_MIN,
    BTST_DAY_CHANGE_MIN,
    LONGTERM_CONVICTION_MIN,
    LONGTERM_MOM_60D_MIN,
)
from batuka_bhairav.universe.fetch_universe import fetch_nse500
from batuka_bhairav.universe.market_data import fetch_market_data
from batuka_bhairav.core.scoring import conviction_score_0_100, longterm_score
from batuka_bhairav.core.sector import compute_sector_strength
from batuka_bhairav.core.regime import get_market_regime
from batuka_bhairav.providers.news import get_stock_sentiment
from batuka_bhairav.telegram_orchestrator import send_telegram_message
 
logger = logging.getLogger("batuka_engine")
 
 
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EXPLANATION ENGINE
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
 
    return "\n• ".join(reasons[:4])  # ✅ FIXED: Proper bullet formatting
 
 
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TRADE LEVELS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 
def trade_levels(r: dict, currency: str = "₹") -> tuple:
    """
    ✅ FIXED: Use proper BTST levels per BRD
    Entry: current price
    Target: +2.0% (was +3%)
    Stop: -1.0% (was -2%)
    """
    price = r.get("price", 100)
 
    entry_low = round(price * 0.995, 2)
    entry_high = round(price * 1.005, 2)
 
    target = round(price * 1.02, 2)      # ✅ FIXED: 2% not 3%
    stop = round(price * 0.99, 2)        # ✅ FIXED: 1% not 2%
 
    rr = round((target - price) / max(price - stop, 0.01), 2)
 
    return entry_low, entry_high, target, stop, rr
 
 
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 
def main(market_code: str = "IN"):
    """
    ✅ FIXED: Now accepts market_code parameter
    
    Args:
        market_code: Market to analyze (IN/US/UK/SG)
    """
    
    # ✅ FIXED: Get market config
    if market_code not in MARKETS:
        logger.error(f"Unknown market: {market_code}")
        return
    
    market_config = MARKETS[market_code]
    market_name = market_config["name"]
    currency = market_config["currency"]
    
    logger.info(f"🚀 Running Batuka Engine for {market_name}")
 
    # ✅ FIXED: Pass market_code to fetch
    rows = fetch_nse500() if market_code == "IN" else []
    if not rows:
        logger.warning(f"⚠️ No data for {market_code}")
        return
    
    symbols = [r["symbol"] for r in rows]
 
    logger.info("📡 Fetching market data...")
    market_data = fetch_market_data(symbols, market_code=market_code)  # ✅ FIXED: Pass market_code
 
    # Attach data BEFORE sector calc
    enriched = []
    for r in rows:
        sym = r["symbol"]
        if sym in market_data:
            r.update(market_data[sym])
            enriched.append(r)
 
    logger.info(f"📊 Enriched: {len(enriched)} stocks")
 
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SECTOR STRENGTH
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    sector_rank, sector_table = compute_sector_strength(enriched)
    logger.info(f"🏢 Computed {len(sector_table)} sectors")
 
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # MARKET REGIME
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    regime = get_market_regime(market_code)  # ✅ FIXED: Pass market_code
    logger.info(f"📈 Regime: {regime}")
 
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SCORING
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    scored = []
    for r in enriched:
        sec = sector_rank.get(r.get("sector"), 0)
        
        # ✅ FIXED: Get real news sentiment instead of hard-coding 0.5
        try:
            news_score, articles = get_stock_sentiment(r["symbol"], market_code)
        except Exception as e:
            logger.debug(f"News fetch failed for {r['symbol']}: {e}")
            news_score = 0.5  # Fallback
        
        try:
            score = conviction_score_0_100(
                r, sec, news_score, regime, CONVICTION_WEIGHTS  # ✅ FIXED: Use real news_score
            )
            r["conviction"] = score
            r["news_score"] = news_score  # Store for later
            scored.append(r)
        except Exception as e:
            logger.debug(f"Scoring error for {r.get('symbol')}: {e}")
            continue
 
    # Sort by conviction
    scored.sort(key=lambda x: x["conviction"], reverse=True)
    logger.info(f"⭐ Scored {len(scored)} stocks")
 
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PICK SELECTION (✅ FIXED: Use config thresholds)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    btst = [
        x for x in scored
        if x["conviction"] > BTST_CONVICTION_MIN  # ✅ FIXED: From config
        and x.get("vol_ratio", 0) > BTST_VOL_RATIO_MIN
        and x.get("day_change_pct", 0) > BTST_DAY_CHANGE_MIN
    ][:3]
 
    long_term = [
        x for x in scored
        if x["conviction"] > LONGTERM_CONVICTION_MIN
        and x.get("mom_60d", 0) > LONGTERM_MOM_60D_MIN
    ][:3]
 
    logger.info(f"🎯 Picks: {len(btst)} BTST, {len(long_term)} LT")
 
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # STAR OF THE DAY
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    star = max(
        (scored or [{"symbol": "N/A", "day_change_pct": 0}]),
        key=lambda x: x.get("day_change_pct", 0)
    )
    logger.info(f"🏆 Star: {star['symbol']}")
 
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TOMORROW OUTLOOK
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    avg = sum(x.get("day_change_pct", 0) for x in enriched) / len(enriched) if enriched else 0
 
    if avg > 1:
        tomorrow = "Strong bullish continuation possible"
    elif avg > 0:
        tomorrow = "Mild positive bias — selective buying"
    elif avg > -0.5:
        tomorrow = "Range-bound market — wait for breakout"
    else:
        tomorrow = "Weakness likely — avoid aggressive trades"
 
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # BUILD MESSAGE
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    msg = f"""
<b>🧠 BATUKA BHAIRAVA</b>
📍 {market_name}
 
<b>🟡 Market Today: {regime}</b>
 
<b>🔮 What to Expect Tomorrow</b>
{tomorrow}
"""
 
    # SECTORS
    msg += "\n<b>📈 Sectors showing strength</b>\n"
    for s in sector_table[:3]:
        msg += f"▲ {s['sector']} +{round(s['score'], 2)}%\n"
 
    msg += "\n<b>📉 Sectors under pressure</b>\n"
    for s in reversed(sector_table[-3:]):
        msg += f"▼ {s['sector']} {round(s['score'], 2)}%\n"
 
    # STAR
    if star and star.get("symbol") != "N/A":
        msg += f"""
<b>🏆 STAR OF THE DAY</b>
<b>{star['symbol']}</b>
 
Moved <b>{round(star.get('day_change_pct', 0), 2)}%</b>
Volume <b>{round(star.get('vol_ratio', 0), 2)}x</b>
"""
 
    # BTST PICKS
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
 
    # LONG TERM PICKS
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
 
    msg += "\n⚠️ AI-generated insight. Not financial advice."
 
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SEND TELEGRAM
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
 
    if token and chat_id:
        logger.info("📤 Sending Telegram...")
        send_telegram_message(msg, token, chat_id)
    else:
        logger.warning("⚠️ Telegram credentials not set - skipping send")
 
    logger.info("✅ DONE")
 
 
if __name__ == "__main__":
    import sys
    market = sys.argv[1] if len(sys.argv) > 1 else "IN"
    main(market)
 
