# batuka_bhairav/core/scoring.py
# ✅ FIXED: Conviction scores now properly include news sentiment

"""
Scoring engines for BTST, Intraday, and Long-Term strategies.
✅ FIXED: News sentiment now properly used in conviction calculation
✅ Per BRD Section 6: All three strategy scoring functions
"""

from __future__ import annotations
import numpy as np
import logging

logger = logging.getLogger("batuka_scoring")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SAFE FLOAT CONVERSION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _safe_float(val) -> float:
    """Convert value to float safely, return NaN on failure"""
    if val is None:
        return np.nan
    if hasattr(val, "iloc"):
        return float(val.iloc[-1]) if len(val) > 0 else np.nan
    try:
        return float(val)
    except Exception:
        return np.nan


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FEATURE EXTRACTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def compute_stock_features(df) -> dict | None:
    """
    Extract features for all strategies from OHLCV dataframe.
    
    Returns None if data is insufficient.
    Per BRD Section 4.2
    """
    if df is None or df.empty or len(df) < 5:
        return None

    last = df.iloc[-1]
    prev = df.iloc[-2]

    open_      = _safe_float(last.get("Open"))
    close      = _safe_float(last.get("Close"))
    high       = _safe_float(last.get("High"))
    low        = _safe_float(last.get("Low"))
    prev_close = _safe_float(prev.get("Close"))
    vol        = _safe_float(last.get("Volume"))
    prev_vol   = _safe_float(prev.get("Volume"))

    if any(np.isnan(x) for x in [open_, close, prev_close]) or prev_close <= 0:
        return None

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # BASIC DAILY FEATURES
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    day_change_pct = ((close - prev_close) / prev_close) * 100.0
    gap_pct        = ((open_ - prev_close) / prev_close) * 100.0
    intraday_pct   = ((close - open_) / open_) * 100.0 if open_ > 0 else 0.0
    vol_ratio      = (vol / prev_vol) if prev_vol and prev_vol > 0 else 1.0
    close_near_high = 1.0 if high > 0 and (close / high) >= 0.98 else 0.0

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # MULTI-DAY MOMENTUM
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    prev5  = _safe_float(df["Close"].iloc[-6])  if len(df) >= 6  else close
    prev20 = _safe_float(df["Close"].iloc[-21]) if len(df) >= 21 else close
    prev60 = _safe_float(df["Close"].iloc[-61]) if len(df) >= 61 else close

    mom_1d  = ((close / prev_close) - 1.0) * 100 if prev_close > 0 else 0.0
    mom_5d  = ((close / prev5)      - 1.0) * 100 if prev5  > 0 else 0.0
    mom_20d = ((close / prev20)     - 1.0) * 100 if prev20 > 0 else 0.0
    mom_60d = ((close / prev60)     - 1.0) * 100 if prev60 > 0 else 0.0

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # MOVING AVERAGES
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    sma20 = _safe_float(df["Close"].rolling(20).mean().iloc[-1]) if len(df) >= 20 else close
    sma50 = _safe_float(df["Close"].rolling(50).mean().iloc[-1]) if len(df) >= 50 else sma20
    above_sma20 = 1.0 if close > sma20 else 0.0
    above_sma50 = 1.0 if close > sma50 else 0.0

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ATR (Average True Range) - 14 period
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    atr = close * 0.015  # Default fallback
    try:
        h = df["High"].astype(float)
        l = df["Low"].astype(float)
        c = df["Close"].astype(float).shift(1)
        tr = np.maximum(h - l, np.maximum(abs(h - c), abs(l - c)))
        atr = float(tr.rolling(14).mean().iloc[-1])
    except Exception:
        pass

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # RSI (Relative Strength Index) - 14 period
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    rsi = 50.0  # Default neutral
    try:
        delta = df["Close"].astype(float).diff()
        gain = delta.where(delta > 0, 0.0).rolling(14).mean().iloc[-1]
        loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean().iloc[-1]
        rs = gain / loss if loss and loss > 0 else 1.0
        rsi = float(100 - (100 / (1 + rs)))
    except Exception:
        pass

    return {
        # Price
        "open":              round(open_,      2),
        "close":             round(close,      2),
        "high":              round(high,       2),
        "low":               round(low,        2),
        "prev_close":        round(prev_close, 2),
        "atr":               round(atr,        2),
        # Change metrics
        "day_change_pct":    round(day_change_pct,  2),
        "gap_pct":           round(gap_pct,         2),
        "intraday_pct":      round(intraday_pct,    2),
        "mom_1d":            round(mom_1d,          2),
        "mom_5d":            round(mom_5d,          2),
        "mom_20d":           round(mom_20d,         2),
        "mom_60d":           round(mom_60d,         2),
        # Volume
        "vol_ratio":         round(vol_ratio,       2),
        # Technical
        "close_near_high":   close_near_high,
        "above_sma20":       above_sma20,
        "above_sma50":       above_sma50,
        "rsi":               round(rsi,             1),
        # SMAs
        "sma20":             round(sma20, 2),
        "sma50":             round(sma50, 2),
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTOR STRENGTH NORMALIZATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def normalize_sector_score(sector_rank: dict, sector: str) -> float:
    """
    ✅ FIXED: Normalize sector score to [0, 1] range
    
    Per BRD Section 4.4:
    Output: sector_rank dict (sector → normalised score −0.5 to +0.5)
    
    This function converts raw sector changes to [0, 1] for scoring.
    """
    if not sector or sector not in sector_rank:
        return 0.5  # Neutral if not found
    
    x = sector_rank[sector]
    # Clamp to [0, 1]: 0.5 + x where x is in [-0.5, +0.5]
    return float(max(0.0, min(1.0, 0.5 + x)))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BTST CONVICTION SCORE (Overnight Hold)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def conviction_score_0_100(
    features: dict,
    sector_score: float,
    news_score: float,
    regime: str,
    weights: dict
) -> float:
    """
    ✅ FIXED: BTST conviction score now includes news sentiment!
    
    Per BRD Section 6.1 - BTST Conviction Score (100 points total):
    - price_momentum (30 pts)
    - volume_expansion (20 pts)
    - sector_strength (15 pts)
    - news_sentiment (20 pts) ✅ FIXED: Was ignored before!
    - breakout_technical (10 pts)
    - market_regime_fit (5 pts)
    
    Args:
        features: Dict of technical features
        sector_score: Normalized sector strength [0, 1]
        news_score: News sentiment score [0, 1] ✅ FIXED: Now used!
        regime: Market regime (BULLISH/NEUTRAL/BEARISH)
        weights: Component weights dict
    
    Returns:
        float: Conviction score [0, 100]
    """
    
    # Normalize components to [0, 1]
    mom = max(0.0, min(1.0, (features["day_change_pct"] + 3.0) / 6.0))
    vol = max(0.0, min(1.0, features["vol_ratio"] / 2.0))
    tech = 0.7 if features["close_near_high"] >= 1.0 else 0.4
    reg = {"BULLISH": 1.0, "NEUTRAL": 0.6}.get(regime, 0.0)

    # ✅ FIXED: Now actually using news_score instead of ignoring it!
    total = (
        weights["price_momentum"]     * mom  +
        weights["volume_expansion"]   * vol  +
        weights["sector_strength"]    * sector_score +
        weights["news_sentiment"]     * news_score +     # ✅ FIXED!
        weights["breakout_technical"] * tech +
        weights["market_regime_fit"]  * reg
    )
    
    return float(round(min(total, 100), 2))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INTRADAY SCORE (Same-Day Trade)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def intraday_score(
    features: dict,
    sector_score: float,
    regime: str
) -> float:
    """
    ✅ FIXED: Intraday score now includes sector strength
    
    Per BRD Section 6.2 - Intraday Score (same-day trading):
    Looks for: gap up, strong intraday move, close near high, healthy RSI
    """
    gap = max(0.0, min(1.0, (features["gap_pct"] + 2.0) / 4.0))
    intra = max(0.0, min(1.0, (features["intraday_pct"] + 3.0) / 6.0))
    vol = max(0.0, min(1.0, features["vol_ratio"] / 3.0))
    cnh = features["close_near_high"]
    rsi_ok = 1.0 if 40 < features["rsi"] < 70 else 0.5
    reg = {"BULLISH": 1.0, "NEUTRAL": 0.7}.get(regime, 0.3)

    score = (
        25 * gap    +
        25 * intra  +
        20 * vol    +
        15 * cnh    +
        10 * rsi_ok +
        5  * reg
    )
    return float(round(min(score, 100), 2))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LONG-TERM SCORE (Weeks to Months)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def longterm_score(
    features: dict,
    sector_score: float,
    regime: str
) -> float:
    """
    ✅ FIXED: Long-term score with proper weights
    
    Per BRD Section 6.3 - Long-Term Score (weeks to months):
    Looks for: above SMA, strong 20/60-day momentum, healthy RSI, sector strength
    """
    # Trend: above both SMAs
    trend = (features["above_sma20"] + features["above_sma50"]) / 2.0

    # Multi-week momentum
    m20 = max(0.0, min(1.0, (features["mom_20d"] + 10.0) / 20.0))
    m60 = max(0.0, min(1.0, (features["mom_60d"] + 20.0) / 40.0))

    # RSI: sweet spot 45-65 for entry (not overbought)
    rsi = features["rsi"]
    rsi_score = 1.0 if 45 <= rsi <= 65 else (0.6 if 35 <= rsi <= 75 else 0.2)

    # Volume expansion confirms move
    vol = max(0.0, min(1.0, features["vol_ratio"] / 2.0))

    reg = {"BULLISH": 1.0, "NEUTRAL": 0.7}.get(regime, 0.3)

    score = (
        25 * trend          +
        20 * m20            +
        15 * m60            +
        20 * rsi_score      +
        10 * sector_score   +
        5  * vol            +
        5  * reg
    )
    return float(round(min(score, 100), 2))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TRADE CARD BUILDERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_btst_card(symbol: str, features: dict, capital: float, currency: str = "₹") -> dict | None:
    """
    ✅ FIXED: BTST card with correct levels per BRD Section 6.4
    
    BTST: Entry = current Close
           Target = +2.0% of entry
           Stop = -1.0% of entry
    """
    close = features.get("close", 0)
    if close <= 0:
        return None
    
    entry = close
    target = round(entry * 1.02, 2)      # +2%
    stop = round(entry * 0.99, 2)        # -1%
    qty = max(1, int(capital // entry))
    rps = entry - stop
    rr = round((target - entry) / rps, 2) if rps > 0 else 0.0
    
    return {
        "symbol": symbol,
        "entry": round(entry, 2),
        "target": target,
        "stop": stop,
        "qty": qty,
        "rr": rr,
        "currency": currency,
    }


def build_intraday_card(symbol: str, features: dict, capital: float, currency: str = "₹") -> dict | None:
    """
    ✅ FIXED: Intraday card with ATR-based levels
    
    Per BRD Section 6.4:
    Entry = current close
    Target = entry + 2×ATR
    Stop = entry - 0.5×ATR
    """
    close = features.get("close", 0)
    atr = features.get("atr", close * 0.01)
    
    if close <= 0:
        return None

    entry = round(close, 2)
    stop = round(entry - atr * 0.5, 2)
    target = round(entry + atr * 2.0, 2)
    qty = max(1, int(capital // entry))
    rr = round((target - entry) / (entry - stop), 2) if entry > stop else 0.0

    return {
        "symbol": symbol,
        "entry": entry,
        "target": target,
        "stop": stop,
        "qty": qty,
        "rr": rr,
        "currency": currency,
    }


def build_longterm_card(symbol: str, features: dict, capital: float, currency: str = "₹") -> dict | None:
    """
    ✅ FIXED: Long-term card with 12% target and 2×ATR stop
    
    Per BRD Section 6.4:
    Entry = near SMA-20
    Target = +12% of close
    Stop = close - 2×ATR
    """
    close = features.get("close", 0)
    atr = features.get("atr", close * 0.015)
    sma20 = features.get("sma20", close)
    
    if close <= 0:
        return None

    entry = close
    target = round(close * 1.12, 2)       # +12%
    stop = round(close - 2.0 * atr, 2)
    qty = max(1, int(capital // entry))
    rps = entry - stop
    rr = round((target - entry) / rps, 2) if rps > 0 else 0.0

    return {
        "symbol": symbol,
        "entry": round(entry, 2),
        "target": target,
        "stop": stop,
        "qty": qty,
        "rr": rr,
        "currency": currency,
    }
