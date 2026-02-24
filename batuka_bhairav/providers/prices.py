# batuka_bhairav/providers/prices.py

import yfinance as yf
import pandas as pd


def fetch_ohlcv_batch(symbols, period="1mo", interval="1d"):
    """
    Fetch OHLCV data safely.
    Skips failed symbols instead of crashing engine.
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
