# batuka_bhairav/core/regime.py
from __future__ import annotations
from batuka_bhairav.config import INDEX_SYMBOL
from batuka_bhairav.providers.prices import fetch_ohlcv_batch


def get_market_regime(df=None) -> str:
    """
    Accepts an optional pre-fetched dataframe.
    If not provided, fetches it automatically.
    Returns a plain string: BULLISH / BEARISH / NEUTRAL
    """
    if df is None or (hasattr(df, "empty") and df.empty):
        result = fetch_ohlcv_batch([INDEX_SYMBOL])
        df = result.get(INDEX_SYMBOL)

    if df is None or df.empty or "Close" not in df.columns:
        return "NEUTRAL"

    try:
        close = float(df["Close"].iloc[-1])
        sma20 = float(df["Close"].rolling(20).mean().iloc[-1]) if len(df) >= 20 else close
        sma50 = float(df["Close"].rolling(50).mean().iloc[-1]) if len(df) >= 50 else sma20

        if close > sma20 and close > sma50:
            return "BULLISH"
        elif close < sma20 and close < sma50:
            return "BEARISH"
        else:
            return "NEUTRAL"
    except Exception:
        return "NEUTRAL"
