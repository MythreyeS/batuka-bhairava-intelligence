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


def main():
    print(f"[Batuka] Market={ACTIVE_MARKET} | {MARKET_NAME}")

    # -------------------------------
    # STEP 1 — FETCH UNIVERSE
    # -------------------------------
    rows = fetch_nse500()
    print(f"[Universe] {len(rows)} stocks fetched")

    # -------------------------------
    # STEP 2 — FETCH REAL MARKET DATA
    # -------------------------------
    symbols = [r["symbol"] for r in rows]

    print("📡 Fetching real market data...")
    market_data = fetch_market_data(symbols)

    # -------------------------------
    # STEP 3 — MARKET REGIME
    # -------------------------------
    regime = get_market_regime()
    print(f"[Batuka] Regime: {regime}")

    # -------------------------------
    # STEP 4 — SECTOR
    # -------------------------------
    sector_rank, sector_table = compute_sector_strength(rows)

    scored_btst = []
    scored_intraday = []
    scored_longterm = []

    # -------------------------------
    # STEP 5 — SCORING
    # -------------------------------
    for r in rows:
        sym = r.get("symbol")

        if sym not in market_data:
            continue  # skip if no data

        # 🔥 inject REAL DATA
        r.update(market_data[sym])

        sec_score = sector_rank.get(r.get("sector"), 0.0)

        try:
            btst = conviction_score_0_100(
                r, sec_score, 0.5, regime, CONVICTION_WEIGHTS
            )
            intra = intraday_score(r, sec_score, regime)
            longt = longterm_score(r, sec_score, regime)
        except Exception:
            continue

        scored_btst.append({**r, "conviction": btst})
        scored_intraday.append({**r, "conviction": intra})
        scored_longterm.append({**r, "conviction": longt})

    # -------------------------------
    # STEP 6 — SORT
    # -------------------------------
    scored_btst.sort(key=lambda x: x["conviction"], reverse=True)
    scored_intraday.sort(key=lambda x: x["conviction"], reverse=True)
    scored_longterm.sort(key=lambda x: x["conviction"], reverse=True)

    # 🎯 ONLY REAL STRONG SIGNALS
    btst_cards = [x for x in scored_btst if x["conviction"] > 60][:5]
    intraday_cards = [x for x in scored_intraday if x["conviction"] > 60][:5]
    longterm_cards = [x for x in scored_longterm if x["conviction"] > 60][:5]

    man = btst_cards[0] if btst_cards else None

    # -------------------------------
    # STEP 7 — TELEGRAM MESSAGE
    # -------------------------------
    if not btst_cards:
        msg = f"""
🔥 BATUKA SIGNAL

📊 {MARKET_NAME}
📈 Regime: {regime}

⚠️ No strong signals today
"""
    else:

        def format_list(title, items):
            text = f"\n{title}\n"
            for i, x in enumerate(items, 1):
                text += f"{i}. {x['symbol']} ({round(x['conviction'],1)})\n"
            return text

        msg = f"""
🔥 BATUKA PREMIUM SIGNAL

📊 {MARKET_NAME}
📈 Regime: {regime}

🏆 Top Pick:
{man['symbol']} ({round(man['conviction'],1)})

{format_list("BTST", btst_cards)}
{format_list("Intraday", intraday_cards)}
{format_list("Long Term", longterm_cards)}

⚠️ AI generated insights
"""

    # -------------------------------
    # STEP 8 — SEND TELEGRAM
    # -------------------------------
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if token and chat_id:
        send_telegram_message(msg, token, chat_id)
    else:
        print("⚠️ Telegram not configured")

    # -------------------------------
    # STEP 9 — SAVE OUTPUT
    # -------------------------------
    with open("output.json", "w") as f:
        json.dump({"btst": btst_cards}, f, indent=2)

    print("✅ ENGINE RUN SUCCESS")


if __name__ == "__main__":
    main()
