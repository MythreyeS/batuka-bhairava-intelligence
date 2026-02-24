# batuka_bhairav/providers/prices.py

import yfinance as yf
import pandas as pd
from typing import Dict


# ---------------------------------------------------------
# 🔹 Fetch Stock OHLCV Batch
# ---------------------------------------------------------
def fetch_ohlcv_batch(
    symbols: list,
    period: str = "1mo",
    interval: str = "1d"
) -> Dict[str, pd.DataFrame]:
    """
    Fetch OHLCV data safely for multiple symbols.
    Skips failed downloads instead of crashing.
    """

    result = {}

    for symbol in symbols:
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
                print(f"⚠ No data for {symbol}")
                continue

            df = df.dropna()

            if len(df) < 5:
                print(f"⚠ Insufficient data for {symbol}")
                continue

            result[symbol] = df

        except Exception as e:
            print(f"❌ Failed for {symbol}: {e}")
            continue

    return result


# ---------------------------------------------------------
# 🔹 Fetch Index OHLC (For Regime Detection)
# ---------------------------------------------------------
def fetch_index_ohlc(
    symbol: str = "^NSEI",   # NIFTY 50
    period: str = "1mo",
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
