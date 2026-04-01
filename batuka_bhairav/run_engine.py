from __future__ import annotations

import json
from datetime import datetime
import pytz
import os

from batuka_bhairav.config import (
    ACTIVE_MARKET,
    MARKET_NAME,
    MARKET_TIMEZONE,
    CONVICTION_WEIGHTS,
)

from batuka_bhairav.universe.fetch_universe import fetch_nse500
from batuka_bhairav.universe.market_data import fetch_market_data

from batuka_bhairav.core.scoring import (
    conviction_score_0_100,
    intraday_score,
    longterm_score,
)

from batuka_bhairav.core.sector import compute_sector_strength
from batuka_bhairav.core.regime import get_market_regime

from batuka_bhairav.telegram_orchestrator import send_telegram_message


# -------------------------------
# 🧠 EXPLAIN STOCK
# -------------------------------
def explain_stock(r):
    reasons = []

    if r["above_sma20"] and r["above_sma50"]:
        reasons.append("price above short & long-term averages")

    if r["mom_20d"] > 0:
        reasons.append(f"20d momentum +{round(r['mom_20d'],1)}%")

    if r["mom_60d"] > 0:
        reasons.append(f"60d momentum +{round(r['mom_60d'],1)}%")

    if r["vol_ratio"] > 1.2:
        reasons.append("volume above normal (institutional activity)")

    if 45 < r["rsi"] < 65:
        reasons.append("RSI balanced (no overbought/oversold)")

    return reasons[:4]


# -------------------------------
# 🎯 ENTRY / EXIT LOGIC
# -------------------------------
def generate_trade_levels(r):
    price = r["price"]

    entry_low = round(price * 0.99, 2)
    entry_high = round(price * 1.01, 2)

    target = round(price * 1.03, 2)
    stop = round(price * 0.98, 2)

    rr = round((target - price) / (price - stop), 2)

    return entry_low, entry_high, target, stop, rr


# -------------------------------
# 🚀 MAIN ENGINE
# -------------------------------
def main():
    print(f"[Batuka] Market={ACTIVE_MARKET} | {MARKET_NAME}")

    rows = fetch_nse500()
    print(f"[Universe] {len(rows)} stocks fetched")

    symbols = [r["symbol"] for r in rows]

    print("📡 Fetching real market data...")
    market_data = fetch_market_data(symbols)

    regime = get_market_regime()
    sector_rank, sector_table = compute_sector_strength(rows)

    scored_btst = []
    scored_longterm = []

    for r in rows:
        sym = r.get("symbol")

        if sym not in market_data:
            continue

        r.update(market_data[sym])

        sec = sector_rank.get(r.get("sector"), 0.0)

        try:
            btst = conviction_score_0_100(r, sec, 0.5, regime, CONVICTION_WEIGHTS)
            longt = longterm_score(r, sec, regime)
        except Exception:
            continue

        scored_btst.append({**r, "conviction": btst})
        scored_longterm.append({**r, "conviction": longt})

    scored_btst.sort(key=lambda x: x["conviction"], reverse=True)
    scored_longterm.sort(key=lambda x: x["conviction"], reverse=True)

    btst_cards = [x for x in scored_btst if x["conviction"] > 60][:3]
    longterm_cards = [x for x in scored_longterm if x["conviction"] > 60][:3]

    # -------------------------------
    # 📊 MARKET TEXT
    # -------------------------------
    market_text = {
        "BULLISH": "Market is trending strong — favor momentum stocks",
        "NEUTRAL": "Market is sideways — pick selectively",
        "BEARISH": "Market is weak — avoid aggressive trades",
    }[regime]

    # -------------------------------
    # 🧾 BUILD MESSAGE
    # -------------------------------
    msg = f"""
🧠 <b>BATUKA BHAIRAVA</b>
📍 {MARKET_NAME}

🟡 <b>Market Today: {regime}</b>
_{market_text}_
"""

    # -------------------------------
    # 📊 SECTORS
    # -------------------------------
    msg += "\n📈 <b>Sectors doing well</b>\n"
    for s in sector_table[:3]:
        msg += f"▲ {s['sector']} +{round(s['score'],2)}%\n"

    msg += "\n📉 <b>Sectors under pressure</b>\n"
    for s in sector_table[-3:]:
        msg += f"▼ {s['sector']} {round(s['score'],2)}%\n"

    # -------------------------------
    # 🏆 BTST PICKS
    # -------------------------------
    msg += "\n🌙 <b>BTST PICKS</b>\n"

    for i, r in enumerate(btst_cards, 1):
        reasons = explain_stock(r)
        entry_low, entry_high, target, stop, rr = generate_trade_levels(r)

        msg += f"""
{i}. <b>{r['symbol']}</b>

Entry: {entry_low} - {entry_high}
Target: {target} | Stop: {stop}

📊 Why:
• {"\n• ".join(reasons)}

Risk/Reward: {rr}x
"""

    # -------------------------------
    # 📈 LONG TERM
    # -------------------------------
    msg += "\n📈 <b>LONG TERM PICKS</b>\n"

    for i, r in enumerate(longterm_cards, 1):
        reasons = explain_stock(r)

        msg += f"""
{i}. <b>{r['symbol']}</b>

📊 Why:
• {"\n• ".join(reasons)}

Conviction: {round(r['conviction'],1)}
"""

    # -------------------------------
    # 📌 DISCLAIMER
    # -------------------------------
    msg += """
⚠️ This is AI-generated market intelligence.
Not financial advice.
"""

    # -------------------------------
    # 🚀 SEND TELEGRAM
    # -------------------------------
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if token and chat_id:
        send_telegram_message(msg, token, chat_id)

    print("✅ PREMIUM REPORT SENT")


if __name__ == "__main__":
    main()
