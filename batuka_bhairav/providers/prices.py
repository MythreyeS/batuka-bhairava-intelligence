# batuka_bhairav/providers/prices.py
from __future__ import annotations

import math
from typing import Dict, List, Tuple
import pandas as pd
import yfinance as yf

from batuka_bhairav.config import YFINANCE_PERIOD, YFINANCE_INTERVAL, YFINANCE_BATCH_SIZE


def _chunk(lst: List[str], n: int) -> List[List[str]]:
    return [lst[i:i+n] for i in range(0, len(lst), n)]


def fetch_ohlcv_batch(symbols: List[str]) -> Dict[str, pd.DataFrame]:
    """
    Returns: dict(symbol -> df with columns Open High Low Close Volume)
    Uses yf.download with multiple tickers in batches for speed & reliability.
    """
    out: Dict[str, pd.DataFrame] = {}
    symbols = [s.strip() for s in symbols if s and isinstance(s, str)]
    if not symbols:
        return out

    for batch in _chunk(symbols, YFINANCE_BATCH_SIZE):
        tickers = " ".join(batch)
        df = yf.download(
            tickers=tickers,
            period=YFINANCE_PERIOD,
            interval=YFINANCE_INTERVAL,
            group_by="ticker",
            auto_adjust=False,
            threads=True,
            progress=False,
        )
        if df is None or len(df) == 0:
            continue

        # Single ticker case
        if isinstance(df.columns, pd.Index) and "Close" in df.columns:
            sym = batch[0]
            out[sym] = df.dropna(how="all")
            continue

        # Multi ticker (MultiIndex columns)
        for sym in batch:
            try:
                sub = df[sym].dropna(how="all")
                if len(sub) > 0:
                    out[sym] = sub
            except Exception:
                continue

    return out


def fetch_index_ohlc(symbol: str) -> pd.DataFrame:
    df = yf.download(
        tickers=symbol,
        period=YFINANCE_PERIOD,
        interval=YFINANCE_INTERVAL,
        progress=False,
    )
    if df is None:
        return pd.DataFrame()
    return df.dropna(how="all")
