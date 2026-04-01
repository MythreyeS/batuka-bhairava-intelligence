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
# 🧠 EXPLAIN STOCK
# -------------------------------
def explain_stock(r):
    reasons = []

    if r.get("above_sma20") and r.get("above_sma50"):
        reasons.append("price above key moving averages")

    if r.get("mom_20d", 0) > 0:
        reasons.append(f"20d momentum +{round(r.get('mom_20d',0),1)}%")

    if r.get("mom_60d", 0) > 0:
        reasons.append(f"60d momentum +{round(r.get('mom_60d',0),1)}%")

    if r.get("vol_ratio", 0) > 1.2:
        reasons.append("volume spike (institutional activity)")

    if 45 < r.get("rsi", 50) < 65:
        reasons.append("RSI balanced")

    return reasons[:4]


# -------------------------------
# 🎯 TRADE LEVELS
# -------------------------------
def trade_levels(r):
    price = r.get("price", 0)

    entry_low = round(price * 0.99, 2)
    entry_high = round(price * 1.01, 2)

    target = round(price * 1.03, 2)
    stop = round(price * 0.98, 2)

    rr = round((target - price) / max(price - stop, 0.01), 2)

    return entry_low, entry_high, target, stop, rr


# -------------------------------
# 🚀 MAIN ENGINE
# -------------------------------
def main():
    print(f"[Batuka] {MARKET_NAME}")

    rows = fetch_nse500()
    symbols = [r["symbol"] for r in rows]

    print("📡 Fetching real market data...")
    market_data = fetch_market_data(symbols)

    regime = get_market_regime()
    sector_rank, sector_table = compute_sector_strength(rows)

    scored_btst = []
    scored_long = []

    for r in rows:
        sym = r.get("symbol")

        if sym not in market_data:
            continue

        r.update(market_data[sym])

        sec = sector_rank.get(r.get("sector"), 0.0)

        try:
            btst = conviction_score_0_100(
                r, sec, 0.5, regime, CONVICTION_WEIGHTS
            )
            longt = longterm_score(r, sec, regime)
        except Exception:
            continue

        scored_btst.append({**r, "conviction": btst})
        scored_long.append({**r, "conviction": longt})

    scored_btst.sort(key=lambda x: x["conviction"], reverse=True)
    scored_long.sort(key=lambda x: x["conviction"], reverse=True)

    # -------------------------------
    # 🔥 STRONG PICKS ONLY
    # -------------------------------
    btst_cards = [
        x for x in scored_btst
        if x["conviction"] > 70 and x["vol_ratio"] > 1.2
    ][:3]

    long_cards = [
        x for x in scored_long
        if x["conviction"] > 65
    ][:3]

    # -------------------------------
    # 🏆 STAR OF THE DAY
    # -------------------------------
    star = max(
        scored_btst,
        key=lambda x: x.get("day_change_pct", 0),
        default=None
    )

    # -------------------------------
    # 🔮 MARKET EXPECTATION
    # -------------------------------
    avg_market = sum(
        [r.get("day_change_pct", 0) for r in rows]
    ) / max(len(rows), 1)

    if avg_market > 0.8:
        tomorrow = "Strong bullish continuation possible"
    elif avg_market > 0:
        tomorrow = "Mild positive bias expected"
    elif avg_market > -0.5:
        tomorrow = "Range-bound market likely"
    else:
        tomorrow = "Weakness may continue"

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
    # 📊 SECTORS
    # -------------------------------
    msg += "\n📈 <b>Sectors doing well</b>\n"
    for s in sector_table[:3]:
        msg += f"▲ {s.get('sector')} {round(s.get('score',0),2)}%\n"

    msg += "\n📉 <b>Sectors under pressure</b>\n"
    for s in sector_table[-3:]:
        msg += f"▼ {s.get('sector')} {round(s.get('score',0),2)}%\n"

    # -------------------------------
    # 🏆 STAR
    # -------------------------------
    if star:
        msg += f"""
🏆 <b>STAR OF THE DAY</b>
{star['symbol']}

Moved {round(star.get('day_change_pct',0),2)}%
Volume {round(star.get('vol_ratio',1),2)}x
"""

    # -------------------------------
    # 🌙 BTST PICKS
    # -------------------------------
    msg += "\n🌙 <b>BTST PICKS</b>\n"

    for i, r in enumerate(btst_cards, 1):
        reasons = explain_stock(r)
        reason_text = "\n• ".join(reasons)

        entry_low, entry_high, target, stop, rr = trade_levels(r)

        msg += f"""
{i}. <b>{r['symbol']}</b>

Entry: {entry_low}-{entry_high}
Target: {target} | Stop: {stop}

📊 Why:
• {reason_text}

Risk/Reward: {rr}x
"""

    # -------------------------------
    # 📈 LONG TERM
    # -------------------------------
    msg += "\n📈 <b>LONG TERM PICKS</b>\n"

    for i, r in enumerate(long_cards, 1):
        reasons = explain_stock(r)
        reason_text = "\n• ".join(reasons)

        msg += f"""
{i}. <b>{r['symbol']}</b>

📊 Why:
• {reason_text}

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

    print("✅ REPORT SENT")


if __name__ == "__main__":
    main()
