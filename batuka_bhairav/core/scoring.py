import pandas as pd
import numpy as np

def calculate_sma(series, window=20):
    return series.rolling(window).mean()

def calculate_rsi(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi

def score_stock(df, sector_score=8, news_score=5, regime_score=3):
    if df is None or len(df) < 30:
        return 0, "Insufficient data"

    close = df["Close"]
    volume = df["Volume"]

    # --- Momentum (30) ---
   day_return = float((close.iloc[-1] - close.iloc[-2]) / close.iloc[-2] * 100)
    momentum_score = min(max(day_return * 6, 0), 30)

    # --- Volume (20) ---
    vol_avg = volume.tail(20).mean()
    vol_ratio = volume.iloc[-1] / vol_avg if vol_avg else 1
    if vol_ratio >= 2:
        volume_score = 18
    elif vol_ratio >= 1.5:
        volume_score = 12
    else:
        volume_score = 6

    # --- Breakout (10) ---
    sma20 = calculate_sma(close, 20).iloc[-1]
    rsi = calculate_rsi(close).iloc[-1]
    breakout_score = 0
    if close.iloc[-1] > sma20:
        breakout_score += 5
    if not pd.isna(rsi) and float(rsi) > 60:
        breakout_score += 5

    total = (
        momentum_score +
        volume_score +
        sector_score +
        news_score +
        breakout_score +
        regime_score
    )

    total = min(total, 100)

    explanation = f"""
Momentum: {momentum_score:.1f}/30
Volume: {volume_score}/20
Sector: {sector_score}/15
News: {news_score}/20
Breakout: {breakout_score}/10
Regime: {regime_score}/5
Total: {total:.1f}/100
"""

    return total, explanation.strip()
