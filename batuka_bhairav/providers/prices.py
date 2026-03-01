# batuka_bhairav/providers/prices.py

import yfinance as yf
import pandas as pd
from typing import Dict


# ---------------------------------------------------------
# 🔹 Utility: Clean Symbol
# ---------------------------------------------------------
def _clean_symbol(symbol: str) -> str:
    return symbol.replace("$", "").strip()


# ---------------------------------------------------------
# 🔹 Fetch Stock OHLCV Batch
# ---------------------------------------------------------
def fetch_ohlcv_batch(
    symbols: list,
    period: str = "3mo",        # 🔥 CHANGED from 1mo → 3mo
    interval: str = "1d"
) -> Dict[str, pd.DataFrame]:
    """
    Fetch OHLCV data safely for multiple symbols.
    Uses 3mo period to avoid Yahoo throttling.
    Skips failed downloads instead of crashing.
    """

    result = {}

    for symbol in symbols:
        sym = _clean_symbol(symbol)

        try:
            df = yf.download(
                sym,
                period=period,
                interval=interval,
                progress=False,
                auto_adjust=True,
                threads=False,
            )

            if df is None or df.empty:
                print(f"⚠ No data for {sym}")
                continue

            df = df.dropna()

            if len(df) < 20:  # ensure enough data for regime & SMA
                print(f"⚠ Insufficient data for {sym}")
                continue

            result[symbol] = df

        except Exception as e:
            print(f"❌ Failed for {sym}: {e}")
            continue

    return result


# ---------------------------------------------------------
# 🔹 Fetch Index OHLC (For Regime Detection)
# ---------------------------------------------------------
def fetch_index_ohlc(
    symbol: str = "^NSEI",
    period: str = "3mo",        # 🔥 CHANGED from 1mo → 3mo
    interval: str = "1d"
) -> pd.DataFrame:
    """
    Fetch OHLC data for index.
    Used by regime detection.
    """

    try:
        df = yf.download(
            symbol,
            period=period,
            interval=interval,
            progress=False,
            auto_adjust=True,
            threads=False,
        )

        if df is None or df.empty:
            raise ValueError(f"No index data for {symbol}")

        return df.dropna()

    except Exception as e:
        raise RuntimeError(f"Index fetch failed: {e}")
