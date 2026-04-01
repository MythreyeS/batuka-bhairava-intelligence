from __future__ import annotations

import json
from datetime import datetime
import pytz
import os

# ✅ CONFIG
from batuka_bhairav.config import (
    ACTIVE_MARKET,
    MARKET_NAME,
    MARKET_CURRENCY,
    MARKET_TIMEZONE,
    INDEX_LABEL,
    CONVICTION_WEIGHTS,
)

# ✅ UNIVERSE
from batuka_bhairav.universe.fetch_universe import fetch_nse500

# ✅ CORE
from batuka_bhairav.core.scoring import (
    conviction_score_0_100,
    intraday_score,
    longterm_score,
)

from batuka_bhairav.core.sector import compute_sector_strength
from batuka_bhairav.core.regime import get_market_regime
from batuka_bhairav.core.explainability import build_explainability_record

# ✅ TELEGRAM
from batuka_bhairav.telegram_orchestrator import send_telegram_message


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
    # STEP 3 — NEWS (DISABLED FOR SPEED)
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
        # 🔥 ALL REQUIRED FIELDS (FINAL FIX)
        r.setdefault("day_change_pct", 0.0)
        r.setdefault("vol_ratio", 1.0)
        r.setdefault("close_near_high", 0.5)
        r.setdefault("gap_pct", 0.0)
        r.setdefault("intraday_pct", 0.0)
        r.setdefault("rsi", 50.0)
        r.setdefault("above_sma20", 0.0)
        r.setdefault("above_sma50", 0.0)
        r.setdefault("mom_20d", 0.0)
        r.setdefault("volume", 0.0)
        r.setdefault("price", 0.0)

        sec_score = sector_rank.get(r.get("sector"), 0.0)

        btst_conviction = conviction_score_0_100(
            r,
            sec_score,
            news_sentiment,
            regime,
            CONVICTION_WEIGHTS
        )

        intraday_conviction = intraday_score(r, sec_score, regime)
        longterm_conviction = longterm_score(r, sec_score, regime)

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

    # -------------------------------
    # STEP 7 — MAN OF MATCH
    # -------------------------------
    man_of_match = btst_cards[0] if btst_cards else None

    # -------------------------------
    # STEP 8 — TOMORROW OUTLOOK
    # -------------------------------
    tomorrow = {
        "regime": regime,
        "bias": "Bullish continuation" if regime == "BULLISH"
        else "Sideways consolidation" if regime == "NEUTRAL"
        else "Cautious / Bearish bias",
        "note": "Based on index trend",
    }

    # -------------------------------
    # STEP 9 — SAVE JSON
    # -------------------------------
    output_payload = {
        "market_code": ACTIVE_MARKET,
        "market_name": MARKET_NAME,
        "currency": MARKET_CURRENCY,
        "generated_at": datetime.now(
            pytz.timezone(MARKET_TIMEZONE)
        ).isoformat(),
        "regime": regime,
        "index_label": INDEX_LABEL,
        "total_scanned": len(rows),
        "sector_table": sector_table[:10],
        "man_of_match": man_of_match,
        "news_drivers": news_drivers,
        "news_sentiment": news_sentiment,
        "btst_cards": btst_cards,
        "intraday_cards": intraday_cards,
        "longterm_cards": longterm_cards,
        "tomorrow": tomorrow,
        "explainability": explainability_records,
    }

    with open("output.json", "w") as f:
        json.dump(output_payload, f, indent=2)

    # -------------------------------
    # STEP 10 — TELEGRAM
    # -------------------------------
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if token and chat_id and man_of_match:
        msg = f"""
🔥 BATUKA SIGNAL ({ACTIVE_MARKET})

📊 Market: {MARKET_NAME}
📈 Regime: {regime}

🏆 Top Pick:
{man_of_match.get("symbol")} — Score: {round(man_of_match.get("conviction", 0), 2)}

📅 Outlook:
{tomorrow['bias']}
"""
        send_telegram_message(msg, token, chat_id)
    else:
        print("⚠️ Telegram not configured")

    print("✅ Engine run completed successfully!")


if __name__ == "__main__":
    main()
