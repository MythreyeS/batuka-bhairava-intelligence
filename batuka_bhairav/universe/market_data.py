from __future__ import annotations

import yfinance as yf
import pandas as pd


# -------------------------------
# 📊 RSI CALCULATION
# -------------------------------
def compute_rsi(series, period=14):
    delta = series.diff()

    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()

    rs = gain / (loss + 1e-9)
    rsi = 100 - (100 / (1 + rs))

    return rsi


# -------------------------------
# 🚀 FETCH MARKET DATA
# -------------------------------
def fetch_market_data(symbols):
    result = {}

    for sym in symbols[:200]:  # limit for speed (can increase later)
        try:
            ticker = yf.Ticker(sym + ".NS")
            hist = ticker.history(period="3mo")

            if hist.empty or len(hist) < 50:
                continue

            close = hist["Close"]
            volume = hist["Volume"]

            latest = close.iloc[-1]
            prev = close.iloc[-2]

            # -----------------------
            # FEATURES
            # -----------------------
            day_change_pct = ((latest - prev) / prev) * 100

            sma20 = close.rolling(20).mean().iloc[-1]
            sma50 = close.rolling(50).mean().iloc[-1]

            avg_vol = volume.rolling(20).mean().iloc[-1]
            vol_ratio = volume.iloc[-1] / (avg_vol + 1e-9)

            mom_20d = ((latest - close.iloc[-20]) / close.iloc[-20]) * 100
            mom_60d = ((latest - close.iloc[-40]) / close.iloc[-40]) * 100

            rsi_series = compute_rsi(close)
            rsi = rsi_series.iloc[-1]

            result[sym] = {
                "price": round(latest, 2),
                "day_change_pct": round(day_change_pct, 2),
                "vol_ratio": round(vol_ratio, 2),
                "mom_20d": round(mom_20d, 2),
                "mom_60d": round(mom_60d, 2),
                "rsi": round(rsi, 2),
                "above_sma20": latest > sma20,
                "above_sma50": latest > sma50,
            }

        except Exception:
            continue

    return result
