# batuka_bhairav/run_engine.py
# ── Schedule-aware: MORNING / BTST / CLOSING / WEEKEND ────────────────────
from __future__ import annotations

import json, os
from datetime import datetime
import pytz

from batuka_bhairav.config import (
    ACTIVE_MARKET, MARKET_NAME, MARKET_CURRENCY, MARKET_TIMEZONE,
    UNIVERSE_CSV, INDEX_SYMBOL, INDEX_LABEL,
    CONVICTION_WEIGHTS, BTST_CAPITAL_PER_TRADE,
    BTST_TARGET_PCT, BTST_STOP_PCT, NEWS_FEEDS,
)
from batuka_bhairav.core.regime        import get_market_regime
from batuka_bhairav.core.sector        import compute_sector_strength
from batuka_bhairav.core.man_of_match  import pick_man_of_match
from batuka_bhairav.core.scoring       import (
    compute_stock_features, sector_strength_score,
    conviction_score_0_100, intraday_score, longterm_score,
    build_btst_card, build_intraday_card, build_longterm_card,
)
from batuka_bhairav.providers.prices   import fetch_ohlcv_batch
from batuka_bhairav.providers.news     import fetch_all_news, summarize_news
from batuka_bhairav.core.anticipation  import build_tomorrow_view
from batuka_bhairav.telegram_message   import render_message
from batuka_bhairav.telegram           import send_telegram
from batuka_bhairav.core.explainability import build_explainability_record
import pandas as pd


def get_run_type() -> str:
    """
    Determines what kind of run this is based on env var or time.
    RUN_TYPE env var: MORNING / BTST / CLOSING / WEEKEND
    """
    run_type = os.getenv("RUN_TYPE", "").upper()
    if run_type in ("MORNING", "BTST", "CLOSING", "WEEKEND"):
        return run_type

    tz  = pytz.timezone(MARKET_TIMEZONE)
    now = datetime.now(tz)

    if now.weekday() >= 5:
        return "WEEKEND"

    hour = now.hour
    if hour < 11:
        return "MORNING"
    elif hour < 15:
        return "BTST"
    else:
        return "CLOSING"


def load_universe():
    """
    Dynamically fetches the full stock universe for the active market.
    NSE 500 from NSE official CSV → Wikipedia fallback → cached CSV.
    S&P 500 from Wikipedia. FTSE 100 from Wikipedia. SGX from cache.
    """
    from batuka_bhairav.universe.fetch_universe import load_universe as _fetch
    rows = _fetch(ACTIVE_MARKET)
    print(f"[Batuka] Universe loaded: {len(rows)} stocks for {ACTIVE_MARKET}")
    return rows


def _enrich(card, sym, name, conv, chg, sector, currency, features) -> dict:
    close = card.get("entry", card.get("close", 0))
    atr   = features.get("atr", close * 0.015)
    if "buy_low" not in card:
        buy_low  = round(max(close - 0.5 * atr, close * 0.97) / 10) * 10
        buy_high = round(close / 10) * 10
        if buy_low >= buy_high:
            buy_low = round((close * 0.975) / 10) * 10
        card["buy_low"]  = buy_low
        card["buy_high"] = buy_high
    card.update({
        "symbol": sym, "name": name, "conviction": conv,
        "day_change_pct": chg, "sector": sector, "currency": currency,
        "vol_ratio": features.get("vol_ratio", 1),
        "intraday_pct": features.get("intraday_pct", 0),
        "rsi": features.get("rsi", 50),
    })
    return card


def write_dashboard_json(payload: dict):
    os.makedirs("docs/data", exist_ok=True)
    path = f"docs/data/{ACTIVE_MARKET}.json"
    with open(path, "w") as f:
        json.dump(payload, f, indent=2, default=str)
    print(f"[Dashboard] Written → {path}")


def main():
    run_type = get_run_type()
    print(f"[Batuka] Market={ACTIVE_MARKET} | {MARKET_NAME} | RunType={run_type}")

    # 1. Universe — full live fetch
    universe = load_universe()
    symbols  = [u["symbol"] for u in universe]
    name_map = {u["symbol"]: u.get("name", u["symbol"].replace(".NS","")) for u in universe}
    sec_map  = {u["symbol"]: u.get("sector", "Unknown") for u in universe}

    # 2. Prices
    price_map = fetch_ohlcv_batch(symbols)

    # 3. Regime
    index_map = fetch_ohlcv_batch([INDEX_SYMBOL])
    idx_df    = index_map.get(INDEX_SYMBOL)
    regime    = get_market_regime(idx_df)
    print(f"[Batuka] Regime: {regime}")

    # 4. Features
    rows = []
    for sym in symbols:
        df   = price_map.get(sym)
        feat = compute_stock_features(df)
        if not feat:
            continue
        rows.append({
            "symbol": sym,
            "name":   name_map.get(sym, sym),
            "sector": sec_map.get(sym, "Unknown"),
            **feat,
        })

    if not rows:
        send_telegram(f"Batuka Bhairava — {MARKET_NAME}\n\n⚠ No valid stock data today.")
        return

    # 5. Sector strength
    sector_rank, sector_table = compute_sector_strength(rows)

    # 6. News — market relevant only
    news_items    = fetch_all_news(limit_per_feed=10)
    news_summary  = summarize_news(news_items, max_items=8)
    news_drivers  = news_summary.get("drivers", [])
    news_sentiment= news_summary.get("sentiment", 0.5)
    print(f"[Batuka] News: {len(news_drivers)} relevant articles found")

    # 7. Man of the match
    man_of_match = pick_man_of_match(rows)

    # 8. Score all 3 strategies
    scored_btst = []
    scored_intraday = []
    scored_longterm = []
    explainability_records = []
    
    for r in rows:
        sec_score = sector_strength_score(sector_rank, r["sector"])
        scored_btst.append({**r,
            "conviction": conviction_score_0_100(r, sec_score, news_sentiment, regime, CONVICTION_WEIGHTS)})
        scored_intraday.append({**r,
            "conviction": intraday_score(r, sec_score, regime)})
        scored_longterm.append({**r,
            "conviction": longterm_score(r, sec_score, regime)})

    scored_btst.sort(    key=lambda x: x["conviction"], reverse=True)
    scored_intraday.sort(key=lambda x: x["conviction"], reverse=True)
    scored_longterm.sort(key=lambda x: x["conviction"], reverse=True)

    # 9. BTST cards
    btst_cards = []
    if regime in ("BULLISH", "NEUTRAL"):
        for s in [x for x in scored_btst if x["conviction"] >= 70][:5]:
            raw = build_btst_card(s["symbol"], s["close"],
                                  BTST_CAPITAL_PER_TRADE, BTST_TARGET_PCT, BTST_STOP_PCT)
            if raw:
                btst_cards.append(_enrich(raw, s["symbol"], s["name"],
                    s["conviction"], s.get("day_change_pct",0), s["sector"], MARKET_CURRENCY, s))

    # 10. Intraday cards
    intraday_cards = []
    for s in [x for x in scored_intraday if x["conviction"] >= 65][:5]:
        card = build_intraday_card(s["symbol"], s, BTST_CAPITAL_PER_TRADE,
                                   s["name"], MARKET_CURRENCY)
        if card:
            card["conviction"] = s["conviction"]
            card["sector"]     = s["sector"]
            intraday_cards.append(card)

    # 11. Long-term cards
    longterm_cards = []
    for s in [x for x in scored_longterm if x["conviction"] >= 65][:5]:
        card = build_longterm_card(s["symbol"], s, BTST_CAPITAL_PER_TRADE * 3,
                                   s["name"], MARKET_CURRENCY)
        if card:
            card["conviction"] = s["conviction"]
            card["sector"]     = s["sector"]
            longterm_cards.append(card)

    # 12. Tomorrow outlook
    tomorrow = build_tomorrow_view(regime, sector_table, news_summary)

    # 13. Render & send
    message = render_message(
        regime         = {"regime": regime, "index": INDEX_LABEL},
        sector_table   = sector_table,
        man_of_match   = man_of_match,
        news_drivers   = news_drivers,
        tomorrow       = tomorrow,
        btst_cards     = btst_cards,
        intraday_cards = intraday_cards,
        longterm_cards = longterm_cards,
        market_name    = MARKET_NAME,
        currency       = MARKET_CURRENCY,
        run_type       = run_type,
    )
    send_telegram(message)

    # 14. Dashboard JSON
    idx_close = idx_sma20 = None
    if idx_df is not None and not idx_df.empty:
        try:
            idx_close = round(float(idx_df["Close"].iloc[-1]), 2)
            idx_sma20 = round(float(idx_df["Close"].rolling(20).mean().iloc[-1]), 2)
        except Exception:
            pass

    write_dashboard_json({
        "market_code":    ACTIVE_MARKET,
        "market_name":    MARKET_NAME,
        "currency":       MARKET_CURRENCY,
        "generated_at":   datetime.now(pytz.timezone(MARKET_TIMEZONE)).isoformat(),
        "regime":         regime,
        "index_label":    INDEX_LABEL,
        "index_close":    idx_close,
        "index_sma20":    idx_sma20,
        "total_scanned":  len(rows),
        "run_type":       run_type,
        "sector_table":   sector_table[:10],
        "man_of_match":   man_of_match,
        "news_drivers":   news_drivers[:6],
        "news_sentiment": news_sentiment,
        "btst_cards":     btst_cards,
        "intraday_cards": intraday_cards,
        "longterm_cards": longterm_cards,
        "tomorrow":       tomorrow,
    })
    print(f"[Batuka] Done. BTST={len(btst_cards)} Intraday={len(intraday_cards)} LT={len(longterm_cards)}")


if __name__ == "__main__":
    main()
