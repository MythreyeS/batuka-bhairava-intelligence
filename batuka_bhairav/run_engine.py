# batuka_bhairav/run_engine.py
# ── Enhanced: multi-market + dashboard JSON output ─────────────────────────
from __future__ import annotations

import json
import os
from datetime import datetime
import pytz

from batuka_bhairav.config import (
    ACTIVE_MARKET, MARKET_NAME, MARKET_CURRENCY, MARKET_TIMEZONE,
    UNIVERSE_CSV, INDEX_SYMBOL, INDEX_LABEL,
    CONVICTION_WEIGHTS, BTST_CAPITAL_PER_TRADE,
    BTST_TARGET_PCT, BTST_STOP_PCT, NEWS_FEEDS,
)
from batuka_bhairav.core.regime   import get_market_regime
from batuka_bhairav.core.sector   import compute_sector_strength
from batuka_bhairav.core.man_of_match import pick_man_of_match
from batuka_bhairav.core.scoring  import (
    compute_stock_features, sector_strength_score,
    conviction_score_0_100, build_btst_card,
)
from batuka_bhairav.providers.prices import fetch_ohlcv_batch
from batuka_bhairav.providers.news   import fetch_all_news
from batuka_bhairav.core.anticipation import summarize_news, build_tomorrow_view
from batuka_bhairav.telegram_message  import render_message
from batuka_bhairav.telegram          import send_telegram

import pandas as pd


# ── Helpers ────────────────────────────────────────────────────────────────
def get_day_context():
    tz  = pytz.timezone(MARKET_TIMEZONE)
    now = datetime.now(tz)
    return "WEEKEND" if now.weekday() >= 5 else "WEEKDAY"


def load_universe() -> pd.DataFrame:
    if not os.path.exists(UNIVERSE_CSV):
        raise FileNotFoundError(f"Universe CSV not found: {UNIVERSE_CSV}")
    df = pd.read_csv(UNIVERSE_CSV)
    if "symbol" not in df.columns:
        raise ValueError("Universe CSV must have a 'symbol' column.")
    if "sector" not in df.columns:
        df["sector"] = "UNKNOWN"
    # support both 'company' and 'name' column
    if "name" not in df.columns and "company" in df.columns:
        df["name"] = df["company"]
    elif "name" not in df.columns:
        df["name"] = df["symbol"]
    return df[["symbol", "sector", "name"]].dropna(subset=["symbol"])


def _safe_card(card: dict, symbol: str, name: str, conviction: float,
               day_change_pct: float, sector: str, currency: str) -> dict:
    """Enrich a BTST card with buy-range, name, conviction."""
    close = card.get("entry", 0)
    atr   = card.get("atr", close * 0.015) if card.get("atr") else close * 0.015

    buy_low  = round(max(close - 0.5 * atr, close * 0.97) / 10) * 10
    buy_high = round(close / 10) * 10
    if buy_low >= buy_high:
        buy_low = round((close * 0.975) / 10) * 10

    return {
        **card,
        "symbol":        symbol,
        "name":          name,
        "buy_low":       buy_low,
        "buy_high":      buy_high,
        "conviction":    conviction,
        "day_change_pct":day_change_pct,
        "sector":        sector,
        "currency":      currency,
    }


# ── Dashboard JSON writer ──────────────────────────────────────────────────
def write_dashboard_json(payload: dict):
    """
    Writes docs/data/<MARKET>.json  →  picked up by the web dashboard.
    GitHub Actions commits this file; GitHub Pages serves it.
    """
    os.makedirs("docs/data", exist_ok=True)
    path = f"docs/data/{ACTIVE_MARKET}.json"
    with open(path, "w") as f:
        json.dump(payload, f, indent=2, default=str)
    print(f"[Dashboard] Written → {path}")


# ── Main engine ────────────────────────────────────────────────────────────
def main():
    day_type = get_day_context()
    print(f"[Batuka] Market={ACTIVE_MARKET} | {MARKET_NAME} | {day_type}")

    # 1. Universe
    uni      = load_universe()
    symbols  = uni["symbol"].astype(str).tolist()
    name_map = dict(zip(uni["symbol"], uni["name"]))

    # 2. Prices
    price_map = fetch_ohlcv_batch(symbols)

    # 3. Regime
    index_map = fetch_ohlcv_batch([INDEX_SYMBOL])
    idx_df    = index_map.get(INDEX_SYMBOL)
    regime    = get_market_regime(idx_df)
    print(f"[Batuka] Regime: {regime}")

    # 4. Features
    rows = []
    for _, r in uni.iterrows():
        sym  = str(r["symbol"])
        sec  = str(r["sector"])
        name = str(r["name"])
        df   = price_map.get(sym)
        feat = compute_stock_features(df)
        if not feat:
            continue
        rows.append({"symbol": sym, "sector": sec, "name": name, **feat})

    if not rows:
        msg = f"Batuka Bhairava — {MARKET_NAME}\n\n⚠ No valid stock data today."
        send_telegram(msg)
        return

    # 5. Sector strength
    sector_rank, sector_table = compute_sector_strength(rows)

    # 6. News
    news_items   = fetch_all_news(limit_per_feed=10)
    news_summary = summarize_news(news_items, max_items=8)
    news_drivers  = news_summary.get("drivers", [])
    news_sentiment= news_summary.get("sentiment", 0.5)

    # 7. Man of the match
    man_of_match = pick_man_of_match(rows)

    # 8. Conviction scoring
    scored = []
    for r in rows:
        sec_score  = sector_strength_score(sector_rank, r.get("sector"))
        conviction = conviction_score_0_100(
            r, sec_score, news_sentiment, regime, CONVICTION_WEIGHTS
        )
        scored.append({**r, "conviction": conviction, "score": conviction})

    scored.sort(key=lambda x: x["conviction"], reverse=True)

    # 9. BTST cards
    btst_cards = []
    if regime in ("BULLISH", "NEUTRAL"):
        for s in [x for x in scored if x["conviction"] >= 70][:5]:
            raw = build_btst_card(
                symbol=s["symbol"],
                close_price=s["close"],
                capital=BTST_CAPITAL_PER_TRADE,
                target_pct=BTST_TARGET_PCT,
                stop_pct=BTST_STOP_PCT,
            )
            if raw:
                card = _safe_card(
                    raw, s["symbol"], name_map.get(s["symbol"], s["symbol"]),
                    s["conviction"], s.get("day_change_pct", 0),
                    s.get("sector", ""), MARKET_CURRENCY,
                )
                btst_cards.append(card)

    # 10. Tomorrow outlook
    tomorrow = build_tomorrow_view(regime, sector_table, news_summary)

    # 11. Telegram
    message = render_message(
        regime       = {"regime": regime, "index": INDEX_LABEL},
        sector_table = sector_table,
        man_of_match = man_of_match,
        news_drivers = news_drivers,
        tomorrow     = tomorrow,
        btst_cards   = btst_cards,
        market_name  = MARKET_NAME,
        currency     = MARKET_CURRENCY,
    )
    if day_type == "WEEKEND":
        message = message.replace("Market Wrap", "Weekend Synopsis\nLast Trading Session Review")
    send_telegram(message)

    # 12. Dashboard JSON  ← NEW
    idx_close = None
    idx_sma20 = None
    if idx_df is not None and not idx_df.empty:
        try:
            idx_close = round(float(idx_df["Close"].iloc[-1]), 2)
            idx_sma20 = round(float(idx_df["Close"].rolling(20).mean().iloc[-1]), 2)
        except Exception:
            pass

    dashboard_payload = {
        "market_code":    ACTIVE_MARKET,
        "market_name":    MARKET_NAME,
        "currency":       MARKET_CURRENCY,
        "generated_at":   datetime.now(pytz.timezone(MARKET_TIMEZONE)).isoformat(),
        "regime":         regime,
        "index_label":    INDEX_LABEL,
        "index_close":    idx_close,
        "index_sma20":    idx_sma20,
        "total_scanned":  len(rows),
        "sector_table":   sector_table[:10],
        "man_of_match":   man_of_match,
        "news_drivers":   news_drivers[:6],
        "news_sentiment": news_sentiment,
        "btst_cards":     btst_cards,
        "tomorrow":       tomorrow,
    }
    write_dashboard_json(dashboard_payload)

    print(f"[Batuka] Done. {len(btst_cards)} BTST picks.")


if __name__ == "__main__":
    main()
