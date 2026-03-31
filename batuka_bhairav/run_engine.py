from __future__ import annotations

import os
from datetime import datetime

import pytz

from batuka_bhairav.core.config import (
    ACTIVE_MARKET,
    MARKET_NAME,
    MARKET_CURRENCY,
    MARKET_TIMEZONE,
    INDEX_LABEL,
    CONVICTION_WEIGHTS,
)
from batuka_bhairav.core.data_fetch import get_market_rows, get_index_data
from batuka_bhairav.core.scoring import (
    conviction_score_0_100,
    intraday_score,
    longterm_score,
)
from batuka_bhairav.core.sector import sector_strength_score, build_sector_table
from batuka_bhairav.core.news import get_news_drivers, compute_news_sentiment
from batuka_bhairav.core.regime import detect_market_regime
from batuka_bhairav.core.dashboard import write_dashboard_json
from batuka_bhairav.core.explainability import build_explainability_record


def main():
    print("🚀 Running Batuka Bhairava Engine...")

    # -------------------------------
    # STEP 1 — FETCH DATA
    # -------------------------------
    rows = get_market_rows()
    print(f"Fetched {len(rows)} stocks")

    idx_close, idx_sma20 = get_index_data()

    # -------------------------------
    # STEP 2 — MARKET REGIME
    # -------------------------------
    regime = detect_market_regime(idx_close, idx_sma20)
    print(f"Market regime: {regime}")

    # -------------------------------
    # STEP 3 — NEWS
    # -------------------------------
    news_drivers = get_news_drivers()
    news_sentiment = compute_news_sentiment(news_drivers)
    print(f"News sentiment: {news_sentiment}")

    # -------------------------------
    # STEP 4 — SECTOR STRENGTH
    # -------------------------------
    sector_table = build_sector_table(rows)
    sector_rank = {row["sector"]: row["score"] for row in sector_table}

    # -------------------------------
    # STEP 5 — SCORING
    # -------------------------------
    scored_btst = []
    scored_intraday = []
    scored_longterm = []
    explainability_records = []

    for r in rows:
        sec_score = sector_strength_score(sector_rank, r["sector"])

        btst_conviction = conviction_score_0_100(
            r,
            sec_score,
            news_sentiment,
            regime,
            CONVICTION_WEIGHTS
        )

        intraday_conviction = intraday_score(r, sec_score, regime)
        longterm_conviction = longterm_score(r, sec_score, regime)

        scored_btst.append({
            **r,
            "conviction": btst_conviction
        })

        scored_intraday.append({
            **r,
            "conviction": intraday_conviction
        })

        scored_longterm.append({
            **r,
            "conviction": longterm_conviction
        })

        # 🔥 NEW — Explainability record
        explainability_records.append(
            build_explainability_record(
                symbol=r["symbol"],
                name=r["name"],
                sector=r["sector"],
                features=r,
                sector_score=sec_score,
                news_score=news_sentiment,
                regime=regime,
                conviction=btst_conviction,
            )
        )

    # -------------------------------
    # STEP 6 — SORT & SELECT TOP PICKS
    # -------------------------------
    scored_btst.sort(key=lambda x: x["conviction"], reverse=True)
    scored_intraday.sort(key=lambda x: x["conviction"], reverse=True)
    scored_longterm.sort(key=lambda x: x["conviction"], reverse=True)

    btst_cards = scored_btst[:10]
    intraday_cards = scored_intraday[:10]
    longterm_cards = scored_longterm[:10]

    # -------------------------------
    # STEP 7 — MAN OF THE MATCH
    # -------------------------------
    man_of_match = btst_cards[0] if btst_cards else None

    # -------------------------------
    # STEP 8 — TOMORROW OUTLOOK
    # -------------------------------
    tomorrow = {
        "regime": regime,
        "bias": "Bullish continuation" if regime == "BULLISH" else
                "Sideways consolidation" if regime == "NEUTRAL" else
                "Cautious / Bearish bias",
        "note": "Based on index trend + sentiment"
    }

    # -------------------------------
    # STEP 9 — WRITE DASHBOARD JSON
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

        # 🔥 CRITICAL FOR SPRINT 1
        "explainability": explainability_records,
    }

    write_dashboard_json(output_payload)

    print("✅ Engine run completed successfully!")


if __name__ == "__main__":
    main()
