# batuka_bhairav/core/regime.py
from __future__ import annotations

import pandas as pd
from batuka_bhairav.config import NIFTY_INDEX
from batuka_bhairav.providers.prices import fetch_index_ohlc


def get_market_regime() -> dict:
    df = fetch_index_ohlc(NIFTY_INDEX)
    if df is None or df.empty or "Close" not in df.columns:
        return {"regime": "UNKNOWN", "close": None, "prev_close": None, "sma20": None, "change": None}

    close = float(df["Close"].iloc[-1])
    prev_close = float(df["Close"].iloc[-2]) if len(df) >= 2 else close
    sma20 = float(df["Close"].rolling(20).mean().iloc[-1]) if len(df) >= 20 else close

    change = close - prev_close
    change_pct = (change / prev_close) * 100 if prev_close else 0.0

    # Simple regime rule
    if close > sma20:
        regime = "BULLISH" if change_pct >= 0 else "NEUTRAL"
    else:
        regime = "BEARISH" if change_pct <= 0 else "NEUTRAL"

    return {
        "regime": regime,
        "close": close,
        "prev_close": prev_close,
        "change": change,
        "change_pct": change_pct,
        "sma20": sma20,
    }
