from __future__ import annotations

import os
from datetime import datetime
import pytz

# ✅ CONFIG (correct)
from batuka_bhairav.config import (
    ACTIVE_MARKET,
    MARKET_NAME,
    MARKET_CURRENCY,
    MARKET_TIMEZONE,
    INDEX_LABEL,
    CONVICTION_WEIGHTS,
)

# ✅ UNIVERSE (correct file)
from batuka_bhairav.universe.fetch_universe import fetch_nse500

# ✅ CORE MODULES
from batuka_bhairav.core.scoring import (
    conviction_score_0_100,
    intraday_score,
    longterm_score,
)

from batuka_bhairav.core.sector import compute_sector_strength
from batuka_bhairav.providers.news import get_news_drivers, compute_news_sentiment
from batuka_bhairav.core.regime import detect_market_regime
from batuka_bhairav.core.dashboard import write_dashboard_json
from batuka_bhairav.core.explainability import build_explainability_record


def main():
    print(f"[Batuka] Market={ACTIVE_MARKET} | {MARKET_NAME} | RunType=BTST")

    # -------------------------------
    # STEP 1 — FETCH DATA
    # -------------------------------
    rows = fetch_nse500()
    print(f"[Universe] NSE official: {len(rows)} stocks fetched")

    # -------------------------------
    # STEP 2 — INDEX (TEMP FIX)
    # -------------------------------
    # ⚠️ You don’t have index function yet
    idx_close = 0
    idx_sma20 = 0

    # -------------------------------
    # STEP 3 — MARKET REGIME
    # -------------------------------
    regime = detect_market_regime(idx_close, idx_sma20)
    print(f"[Batuka] Market regime: {regime}")

    # -------------------------------
    # STEP 4 — NEWS
    # -------------------------------
    news_drivers = get_news_drivers()
    news_sentiment = compute_news_sentiment(news_drivers)
    print(f"[Batuka] News sentiment: {news_sentiment}")

    # -------------------------------
    # STEP 5 — SECTOR STRENGTH (FIXED)
    # -------------------------------
    sector_rank, sector_table = compute_sector_strength(rows)

    # -------------------------------
    # STEP 6 — SCORING
    # -------------------------------
    scored_btst = []
    scored_intraday = []
    scored_longterm = []
    explainability_records = []

    for r in rows:
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

        # ✅ Explainability
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
    # STEP 7 — SORT
    # -------------------------------
    scored_btst.sort(key=lambda x: x["conviction"], reverse=True)
    scored_intraday.sort(key=lambda x: x["conviction"], reverse=True)
    scored_longterm.sort(key=lambda x: x["conviction"], reverse=True)

    btst_cards = scored_btst[:10]
    intraday_cards = scored_intraday[:10]
    longterm_cards = scored_longterm[:10]

    # -------------------------------
    # STEP 8 — MAN OF THE MATCH
    # -------------------------------
    man_of_match = btst_cards[0] if btst_cards else None

    # -------------------------------
    # STEP 9 — TOMORROW OUTLOOK
    # -------------------------------
    tomorrow = {
        "regime": regime,
        "bias": "Bullish continuation" if regime == "BULLISH" else
                "Sideways consolidation" if regime == "NEUTRAL" else
                "Cautious / Bearish bias",
        "note": "Based on index trend + sentiment"
    }

    # -------------------------------
    # STEP 10 — WRITE JSON
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
        "index_close": idx_close,
        "index_sma20": idx_sma20,
        "total_scanned": len(rows),
        "sector_table": sector_table[:10],
        "man_of_match": man_of_match,
        "news_drivers": news_drivers[:6],
        "news_sentiment": news_sentiment,
        "btst_cards": btst_cards,
        "intraday_cards": intraday_cards,
        "longterm_cards": longterm_cards,
        "tomorrow": tomorrow,
        "explainability": explainability_records,
    }

    write_dashboard_json(output_payload)

    print("✅ Engine run completed successfully!")


if __name__ == "__main__":
    main()
