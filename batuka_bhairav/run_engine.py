# batuka_bhairav/run_engine.py
from __future__ import annotations

import pandas as pd

from batuka_bhairav.config import (
    UNIVERSE_CSV,
    CONVICTION_WEIGHTS,
    BTST_CAPITAL_PER_TRADE,
    BTST_TARGET_PCT,
    BTST_STOP_PCT,
)

from batuka_bhairav.core.regime import get_market_regime
from batuka_bhairav.providers.prices import fetch_ohlcv_batch
from batuka_bhairav.providers.news import fetch_all_news
from batuka_bhairav.core.sector import compute_sector_strength
from batuka_bhairav.core.man_of_match import pick_man_of_match
from batuka_bhairav.core.scoring import (
    compute_stock_features,
    sector_strength_score,
    conviction_score_0_100,
    build_btst_card,
)
from batuka_bhairav.core.anticipation import summarize_news, build_tomorrow_view
from batuka_bhairav.core.telegram_message import render_message

from telegram import send_telegram


def load_universe() -> pd.DataFrame:
    df = pd.read_csv(UNIVERSE_CSV)

    # Expected columns:
    # symbol (yahoo formatted like RELIANCE.NS)
    # OPTIONAL: sector
    if "symbol" not in df.columns:
        raise ValueError("Universe CSV must have a 'symbol' column.")
    if "sector" not in df.columns:
        df["sector"] = "UNKNOWN"

    return df[["symbol", "sector"]].dropna()


def main():
    regime = get_market_regime()

    uni = load_universe()
    symbols = uni["symbol"].astype(str).tolist()

    # Prices
    price_map = fetch_ohlcv_batch(symbols)

    # Build per-stock rows
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

    # Sector strength
    sector_rank, sector_table = compute_sector_strength(rows)

    # News
    news_items = fetch_all_news(limit_per_feed=10)
    news_summary = summarize_news(news_items, max_items=8)
    news_drivers = news_summary["drivers"]
    news_sent = news_summary["sentiment"]

    # Man of the Match (NOT limited to 5)
    mom = pick_man_of_match(rows)

    # Conviction + BTST cards
    scored = []
    for r in rows:
        sec_score = sector_strength_score(sector_rank, r.get("sector"))
        conv = conviction_score_0_100(r, sec_score, news_sent, regime.get("regime"), CONVICTION_WEIGHTS)
        item = dict(r)
        item["conviction"] = conv
        scored.append(item)

    scored.sort(key=lambda x: x["conviction"], reverse=True)

    # BTST gating: do not send picks in BEARISH, reduce in NEUTRAL
    btst_cards = []
    if regime.get("regime") in ("BULLISH", "NEUTRAL"):
        # pick top conviction candidates (you can refine to exclude low liquidity later)
        top = [s for s in scored if s["conviction"] >= 70][:3]
        for s in top:
            btst_cards.append(build_btst_card(
                symbol=s["symbol"],
                close_price=s["close"],
                capital=BTST_CAPITAL_PER_TRADE,
                target_pct=BTST_TARGET_PCT,
                stop_pct=BTST_STOP_PCT
            ))

    tomorrow = build_tomorrow_view(regime.get("regime"), sector_table, news_summary)

    message = render_message(
        regime=regime,
        sector_table=sector_table,
        man_of_match=mom,
        news_drivers=news_drivers,
        tomorrow=tomorrow,
        btst_cards=btst_cards,
    )

    send_telegram(message)


if __name__ == "__main__":
    main()
