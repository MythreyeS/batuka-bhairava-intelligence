# batuka_bhairav/run_engine.py

from __future__ import annotations

import pandas as pd
from datetime import datetime
import pytz

# 🔹 Config
from batuka_bhairav.config import (
    UNIVERSE_CSV,
    CONVICTION_WEIGHTS,
    BTST_CAPITAL_PER_TRADE,
    BTST_TARGET_PCT,
    BTST_STOP_PCT,
)

# 🔹 Core logic
from batuka_bhairav.core.regime import get_market_regime
from batuka_bhairav.core.sector import compute_sector_strength
from batuka_bhairav.core.man_of_match import pick_man_of_match
from batuka_bhairav.core.scoring import (
    compute_stock_features,
    sector_strength_score,
    conviction_score_0_100,
    build_btst_card,
)

# 🔹 Providers
from batuka_bhairav.providers.prices import fetch_ohlcv_batch
from batuka_bhairav.providers.news import fetch_all_news
from batuka_bhairav.core.anticipation import summarize_news, build_tomorrow_view

# 🔹 Messaging
from batuka_bhairav.telegram_message import render_message
from batuka_bhairav.telegram import send_telegram


# ---------------------------------------------------------
# 🔹 Helper: Weekend Detection
# ---------------------------------------------------------
def get_day_context():
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)
    weekday = now.weekday()  # 0=Mon ... 6=Sun

    if weekday >= 5:
        return "WEEKEND"
    return "WEEKDAY"


# ---------------------------------------------------------
# 🔹 Load Universe
# ---------------------------------------------------------
def load_universe() -> pd.DataFrame:
    df = pd.read_csv(UNIVERSE_CSV)

    if "symbol" not in df.columns:
        raise ValueError("Universe CSV must contain 'symbol' column.")

    if "sector" not in df.columns:
        df["sector"] = "UNKNOWN"

    return df[["symbol", "sector"]].dropna()


# ---------------------------------------------------------
# 🔹 Main Engine
# ---------------------------------------------------------
def main():

    # 🔹 Day Context
    day_type = get_day_context()

    # 🔹 Market Regime
    regime = get_market_regime()

    # 🔹 Load Universe
    uni = load_universe()
    symbols = uni["symbol"].astype(str).tolist()

    # 🔹 Fetch Price Data
    price_map = fetch_ohlcv_batch(symbols)

    # 🔹 Build Feature Rows
    rows = []
    for _, r in uni.iterrows():
        sym = r["symbol"]
        sec = r["sector"]
        df = price_map.get(sym)

        feat = compute_stock_features(df)
        if not feat:
            continue

        rows.append({
            "symbol": sym,
            "sector": sec,
            **feat
        })

    # 🔹 Sector Strength
    sector_rank, sector_table = compute_sector_strength(rows)

    # 🔹 News Intelligence
    news_items = fetch_all_news(limit_per_feed=10)
    news_summary = summarize_news(news_items, max_items=8)
    news_drivers = news_summary["drivers"]
    news_sentiment = news_summary["sentiment"]

    # 🔹 Man of the Match (NOT limited to 5)
    man_of_match = pick_man_of_match(rows)

    # 🔹 Conviction Scoring
    scored = []
    for r in rows:
        sec_score = sector_strength_score(sector_rank, r.get("sector"))
        conviction = conviction_score_0_100(
            r,
            sec_score,
            news_sentiment,
            regime.get("regime"),
            CONVICTION_WEIGHTS
        )

        item = dict(r)
        item["conviction"] = conviction
        scored.append(item)

    scored.sort(key=lambda x: x["conviction"], reverse=True)

    # 🔹 BTST Action Cards
    btst_cards = []

    if regime.get("regime") in ("BULLISH", "NEUTRAL"):
        top_candidates = [s for s in scored if s["conviction"] >= 70][:3]

        for s in top_candidates:
            card = build_btst_card(
                symbol=s["symbol"],
                close_price=s["close"],
                capital=BTST_CAPITAL_PER_TRADE,
                target_pct=BTST_TARGET_PCT,
                stop_pct=BTST_STOP_PCT,
            )
            btst_cards.append(card)

    # 🔹 Tomorrow Scenarios
    tomorrow = build_tomorrow_view(
        regime.get("regime"),
        sector_table,
        news_summary
    )

    # 🔹 Render Message
    message = render_message(
        regime=regime,
        sector_table=sector_table,
        man_of_match=man_of_match,
        news_drivers=news_drivers,
        tomorrow=tomorrow,
        btst_cards=btst_cards,
    )

    # 🔹 Weekend Header Adjustment
    if day_type == "WEEKEND":
        message = message.replace(
            "Batuka Bhairava Intelligence — Market Wrap",
            "Batuka Bhairava Intelligence — Weekend Synopsis\nLast Trading Session Review"
        )

    # 🔹 Send Telegram
    send_telegram(message)


# ---------------------------------------------------------
if __name__ == "__main__":
    main()
