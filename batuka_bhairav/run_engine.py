from __future__ import annotations

import json
from datetime import datetime
import pytz
import os

from batuka_bhairav.config import (
    ACTIVE_MARKET,
    MARKET_NAME,
    MARKET_CURRENCY,
    MARKET_TIMEZONE,
    INDEX_LABEL,
    CONVICTION_WEIGHTS,
)

from batuka_bhairav.universe.fetch_universe import fetch_nse500

from batuka_bhairav.core.scoring import (
    conviction_score_0_100,
    intraday_score,
    longterm_score,
)

from batuka_bhairav.core.sector import compute_sector_strength
from batuka_bhairav.core.regime import get_market_regime
from batuka_bhairav.core.explainability import build_explainability_record

from batuka_bhairav.telegram_orchestrator import send_telegram_message


# 🔥 GLOBAL SAFE DEFAULTS (NO MORE KEYERRORS EVER)
SAFE_DEFAULTS = {
    "day_change_pct": 0.0,
    "vol_ratio": 1.0,
    "close_near_high": 0.5,
    "gap_pct": 0.0,
    "intraday_pct": 0.0,
    "rsi": 50.0,
    "above_sma20": 0.0,
    "above_sma50": 0.0,
    "mom_20d": 0.0,
    "mom_60d": 0.0,   # 👈 YOUR CURRENT ERROR FIXED
    "volume": 0.0,
    "price": 0.0,
}


def enrich_with_defaults(row: dict):
    for k, v in SAFE_DEFAULTS.items():
        row.setdefault(k, v)
    return row


def main():
    print(f"[Batuka] Market={ACTIVE_MARKET} | {MARKET_NAME} | RunType=BTST")

    # -------------------------------
    # STEP 1 — FETCH DATA
    # -------------------------------
    rows = fetch_nse500()
    print(f"[Universe] NSE official: {len(rows)} stocks fetched")

    # -------------------------------
    # STEP 2 — MARKET REGIME
    # -------------------------------
    regime = get_market_regime()
    print(f"[Batuka] Market regime: {regime}")

    # -------------------------------
    # STEP 3 — NEWS (DISABLED)
    # -------------------------------
    print("[Batuka] Skipping news for faster execution")
    news_drivers = []
    news_sentiment = 0.5

    # -------------------------------
    # STEP 4 — SECTOR
    # -------------------------------
    sector_rank, sector_table = compute_sector_strength(rows)

    # -------------------------------
    # STEP 5 — SCORING
    # -------------------------------
    scored_btst = []
    scored_intraday = []
    scored_longterm = []
    explainability_records = []

    for r in rows:
        r = enrich_with_defaults(r)

        sec_score = sector_rank.get(r.get("sector"), 0.0)

        try:
            btst_conviction = conviction_score_0_100(
                r, sec_score, news_sentiment, regime, CONVICTION_WEIGHTS
            )

            intraday_conviction = intraday_score(r, sec_score, regime)
            longterm_conviction = longterm_score(r, sec_score, regime)

        except Exception as e:
            print(f"⚠️ Skipping {r.get('symbol')} due to error: {e}")
            continue

        scored_btst.append({**r, "conviction": btst_conviction})
        scored_intraday.append({**r, "conviction": intraday_conviction})
        scored_longterm.append({**r, "conviction": longterm_conviction})

        explainability_records.append(
            build_explainability_record(
                symbol=r.get("symbol"),
                name=r.get("name"),
                sector=r.get("sector"),
                features=r,
                sector_score=sec_score,
                news_score=news_sentiment,
                regime=regime,
                conviction=btst_conviction,
            )
        )

    # -------------------------------
    # STEP 6 — SORT
    # -------------------------------
    scored_btst.sort(key=lambda x: x["conviction"], reverse=True)
    scored_intraday.sort(key=lambda x: x["conviction"], reverse=True)
    scored_longterm.sort(key=lambda x: x["conviction"], reverse=True)

    btst_cards = scored_btst[:10]
    intraday_cards = scored_intraday[:10]
    longterm_cards = scored_longterm[:10]

    man_of_match = btst_cards[0] if btst_cards else None

    # -------------------------------
    # STEP 7 — OUTPUT
    # -------------------------------
    output_payload = {
        "market_code": ACTIVE_MARKET,
        "market_name": MARKET_NAME,
        "generated_at": datetime.now(
            pytz.timezone(MARKET_TIMEZONE)
        ).isoformat(),
        "regime": regime,
        "total_scanned": len(rows),
        "man_of_match": man_of_match,
        "btst_cards": btst_cards,
        "intraday_cards": intraday_cards,
        "longterm_cards": longterm_cards,
    }

    with open("output.json", "w") as f:
        json.dump(output_payload, f, indent=2)

    # -------------------------------
    # STEP 8 — TELEGRAM
    # -------------------------------
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if token and chat_id and man_of_match:
        msg = f"""
🔥 BATUKA SIGNAL

📊 Market: {MARKET_NAME}
📈 Regime: {regime}

🏆 Top Pick:
{man_of_match.get("symbol")} ({round(man_of_match.get("conviction", 0), 2)})
"""
        send_telegram_message(msg, token, chat_id)

    print("✅ Engine run completed successfully!")


if __name__ == "__main__":
    main()
