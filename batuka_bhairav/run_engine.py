from __future__ import annotations

import os

from batuka_bhairav.config import (
    ACTIVE_MARKET,
    MARKET_NAME,
    CONVICTION_WEIGHTS,
)

from batuka_bhairav.universe.fetch_universe import fetch_nse500
from batuka_bhairav.universe.market_data import fetch_market_data

from batuka_bhairav.core.scoring import (
    conviction_score_0_100,
    longterm_score,
)

from batuka_bhairav.core.sector import compute_sector_strength
from batuka_bhairav.core.regime import get_market_regime

from batuka_bhairav.telegram_orchestrator import send_telegram_message


# -------------------------------
# 🧠 EXPLANATION ENGINE
# -------------------------------
def explain_stock(r):
    reasons = []

    if r.get("above_sma20") and r.get("above_sma50"):
        reasons.append("price above key moving averages (uptrend)")

    if r.get("mom_20d", 0) > 1:
        reasons.append(f"short-term momentum +{round(r['mom_20d'],1)}%")

    if r.get("mom_60d", 0) > 5:
        reasons.append(f"strong medium-term trend +{round(r['mom_60d'],1)}%")

    if r.get("vol_ratio", 0) > 1.3:
        reasons.append("high volume — institutional activity")

    if 45 < r.get("rsi", 50) < 65:
        reasons.append("RSI balanced — healthy trend")

    return reasons[:4]


# -------------------------------
# 🎯 TRADE LOGIC
# -------------------------------
def trade_levels(r):
    price = r["price"]

    entry_low = round(price * 0.995, 2)
    entry_high = round(price * 1.01, 2)

    target = round(price * 1.03, 2)
    stop = round(price * 0.98, 2)

    rr = round((target - price) / max(price - stop, 0.01), 2)

    return entry_low, entry_high, target, stop, rr


# -------------------------------
# 🚀 MAIN ENGINE
# -------------------------------
def main():
    print("🚀 Running Batuka Engine")

    rows = fetch_nse500()
    symbols = [r["symbol"] for r in rows]

    print("📡 Fetching market data...")
    market_data = fetch_market_data(symbols)

    # attach data BEFORE sector calc
    enriched = []
    for r in rows:
        sym = r["symbol"]
        if sym in market_data:
            r.update(market_data[sym])
            enriched.append(r)

    # -------------------------------
    # FIX: sectors now computed on REAL DATA
    # -------------------------------
    sector_rank, sector_table = compute_sector_strength(enriched)

    regime = get_market_regime()

    scored = []
    for r in enriched:
        sec = sector_rank.get(r.get("sector"), 0)

        try:
            score = conviction_score_0_100(
                r, sec, 0.5, regime, CONVICTION_WEIGHTS
            )
            r["conviction"] = score
            scored.append(r)
        except:
            continue

    # -------------------------------
    # SORT
    # -------------------------------
    scored.sort(key=lambda x: x["conviction"], reverse=True)

    # -------------------------------
    # 🔥 STRONG PICKS ONLY
    # -------------------------------
    btst = [
        x for x in scored
        if x["conviction"] > 70
        and x["vol_ratio"] > 1.2
        and x["day_change_pct"] > 0.5
    ][:3]

    long_term = [
        x for x in scored
        if x["conviction"] > 65
        and x["mom_60d"] > 5
    ][:3]

    # -------------------------------
    # ⭐ STAR OF THE DAY
    # -------------------------------
    star = max(scored, key=lambda x: x["day_change_pct"])

    # -------------------------------
    # 🔮 TOMORROW VIEW
    # -------------------------------
    avg = sum(x["day_change_pct"] for x in enriched) / len(enriched)

    if avg > 1:
        tomorrow = "Strong bullish continuation possible"
    elif avg > 0:
        tomorrow = "Mild positive bias — selective buying"
    elif avg > -0.5:
        tomorrow = "Range-bound market — wait for breakout"
    else:
        tomorrow = "Weakness likely — avoid aggressive trades"

    # -------------------------------
    # 🧾 MESSAGE
    # -------------------------------
    msg = f"""
🧠 <b>BATUKA BHAIRAVA</b>
📍 {MARKET_NAME}

🟡 <b>Market Today: {regime}</b>

🔮 <b>What to Expect Tomorrow</b>
{tomorrow}
"""

    # -------------------------------
    # 📊 SECTORS (REAL VALUES NOW)
    # -------------------------------
    msg += "\n📈 <b>Sectors showing strength</b>\n"
    for s in sector_table[:3]:
        msg += f"▲ {s['sector']} +{round(s['score'],2)}%\n"

    msg += "\n📉 <b>Sectors under pressure</b>\n"
    for s in sector_table[-3:]:
        msg += f"▼ {s['sector']} {round(s['score'],2)}%\n"

    # -------------------------------
    # ⭐ STAR
    # -------------------------------
    msg += f"""
🏆 <b>STAR OF THE DAY</b>
{star['symbol']}

Moved {round(star['day_change_pct'],2)}%
Volume {round(star['vol_ratio'],2)}x
"""

    # -------------------------------
    # 🌙 BTST PICKS
    # -------------------------------
    msg += "\n🌙 <b>BTST PICKS</b>\n"

    for i, r in enumerate(btst, 1):
        reasons = "\n• ".join(explain_stock(r))
        e1, e2, t, s, rr = trade_levels(r)

        msg += f"""
{i}. <b>{r['symbol']}</b>

Entry: {e1}-{e2}
Target: {t} | Stop: {s}

📊 Why:
• {reasons}

Risk/Reward: {rr}x
"""

    # -------------------------------
    # 📈 LONG TERM
    # -------------------------------
    msg += "\n📈 <b>LONG TERM PICKS</b>\n"

    for i, r in enumerate(long_term, 1):
        reasons = "\n• ".join(explain_stock(r))

        msg += f"""
{i}. <b>{r['symbol']}</b>

📊 Why:
• {reasons}

Conviction: {round(r['conviction'],1)}
"""

    msg += "\n⚠️ AI-generated insight. Not financial advice."

    # -------------------------------
    # 🚀 TELEGRAM
    # -------------------------------
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if token and chat_id:
        send_telegram_message(msg, token, chat_id)

    print("✅ DONE")


if __name__ == "__main__":
    main()
