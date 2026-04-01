import yfinance as yf
import pandas as pd


def compute_rsi(series, period=14):
    delta = series.diff()

    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()

    rs = gain / loss
    return 100 - (100 / (1 + rs))


def fetch_market_data(symbols):
    data = {}

    for sym in symbols:
        try:
            ticker = yf.Ticker(sym)
            df = ticker.history(period="3mo")

            if df.empty or len(df) < 30:
                continue

            close = df["Close"]
            volume = df["Volume"]

            rsi = compute_rsi(close).iloc[-1]

            sma20 = close.rolling(20).mean().iloc[-1]
            sma50 = close.rolling(50).mean().iloc[-1]

            latest = close.iloc[-1]
            prev = close.iloc[-2]

            day_change = ((latest - prev) / prev) * 100

            high = df["High"].iloc[-1]
            low = df["Low"].iloc[-1]

            gap_pct = ((df["Open"].iloc[-1] - prev) / prev) * 100

            data[sym] = {
                "price": float(latest),
                "day_change_pct": float(day_change),
                "volume": float(volume.iloc[-1]),
                "vol_ratio": float(volume.iloc[-1] / volume.rolling(20).mean().iloc[-1]),
                "rsi": float(rsi),
                "above_sma20": 1.0 if latest > sma20 else 0.0,
                "above_sma50": 1.0 if latest > sma50 else 0.0,
                "mom_20d": float((latest - close.iloc[-20]) / close.iloc[-20] * 100),
                "mom_60d": float((latest - close.iloc[-60]) / close.iloc[-60] * 100),
                "intraday_pct": float((latest - df["Open"].iloc[-1]) / df["Open"].iloc[-1] * 100),
                "gap_pct": float(gap_pct),
                "close_near_high": float((latest - low) / (high - low)) if high != low else 0.5,
            }

        except Exception:
            continue

    return data
