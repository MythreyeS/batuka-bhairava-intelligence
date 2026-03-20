# batuka_bhairav/core/scoring.py
from __future__ import annotations

import numpy as np


# -------------------------------------------------------
# Utility: Safe scalar extraction (prevents pandas errors)
# -------------------------------------------------------
def _safe_float(val) -> float:
    """
    Safely convert Series / scalar / None to float.
    Prevents future pandas TypeError.
    """
    if val is None:
        return np.nan

    # If pandas Series
    if hasattr(val, "iloc"):
        if len(val) > 0:
            return float(val.iloc[0])
        return np.nan

    try:
        return float(val)
    except Exception:
        return np.nan


# -------------------------------------------------------
# Feature Engineering
# -------------------------------------------------------
def compute_stock_features(df) -> dict | None:
    """
    Extracts last-day & previous-day features safely.
    Returns None if insufficient or corrupt data.
    """

    if df is None or df.empty or len(df) < 2:
        return None

    last = df.iloc[-1]
    prev = df.iloc[-2]

    open_ = _safe_float(last.get("Open"))
    close = _safe_float(last.get("Close"))
    prev_close = _safe_float(prev.get("Close"))
    vol = _safe_float(last.get("Volume"))
    prev_vol = _safe_float(prev.get("Volume"))
    high = _safe_float(last.get("High"))

    # Guard against invalid numbers
    if any(np.isnan(x) for x in [open_, close, prev_close]) or prev_close <= 0:
        return None

    # % changes
    day_change_pct = ((close - prev_close) / prev_close) * 100.0
    gap_pct = ((open_ - prev_close) / prev_close) * 100.0

    # Volume ratio
    if prev_vol and prev_vol > 0:
        vol_ratio = vol / prev_vol
    else:
        vol_ratio = 1.0

    # Momentum
    mom_1d = (close - prev_close) / prev_close

    # Close near high (breakout proxy)
    close_near_high = 1.0 if high > 0 and (close / high) >= 0.98 else 0.0

    return {
        "open": float(open_),
        "close": float(close),
        "prev_close": float(prev_close),
        "day_change_pct": float(day_change_pct),
        "gap_pct": float(gap_pct),
        "vol_ratio": float(vol_ratio),
        "mom_1d": float(mom_1d),
        "close_near_high": float(close_near_high),
    }


# -------------------------------------------------------
# Sector Strength Normalization
# -------------------------------------------------------
def sector_strength_score(sector_rank: dict, sector: str) -> float:
    """
    Converts normalized sector score (-1..+1) into 0..1 scale.
    """

    if not sector or sector not in sector_rank:
        return 0.5

    x = sector_rank[sector]
    return float(max(0.0, min(1.0, 0.5 + x)))


# -------------------------------------------------------
# Conviction Scoring Engine
# -------------------------------------------------------
def conviction_score_0_100(
    features: dict,
    sector_score_0_1: float,
    news_score_0_1: float,
    regime: str,
    weights: dict
) -> float:
    """
    Weighted conviction score (0..100)
    """

    # --- Price Momentum Normalization (-3% to +3%)
    mom = max(0.0, min(1.0, (features["day_change_pct"] + 3.0) / 6.0))

    # --- Volume Expansion (2x = max)
    vol = max(0.0, min(1.0, features["vol_ratio"] / 2.0))

    # --- Breakout Proxy
    tech = 0.7 if features["close_near_high"] >= 1.0 else 0.4

    # --- Regime Fit
    if regime == "BULLISH":
        reg_fit = 1.0
    elif regime == "NEUTRAL":
        reg_fit = 0.6
    else:
        reg_fit = 0.0

    total = 0.0
    total += weights["price_momentum"] * mom
    total += weights["volume_expansion"] * vol
    total += weights["sector_strength"] * sector_score_0_1
    total += weights["news_sentiment"] * news_score_0_1
    total += weights["breakout_technical"] * tech
    total += weights["market_regime_fit"] * reg_fit

    return float(round(total, 2))


# -------------------------------------------------------
# BTST Trade Card Builder
# -------------------------------------------------------
def build_btst_card(
    symbol: str,
    close_price: float,
    capital: int,
    target_pct: float,
    stop_pct: float
) -> dict:
    """
    Generates BTST trade card.
    """

    if close_price <= 0:
        return None

    entry = close_price
    target = entry * (1.0 + target_pct)
    stop = entry * (1.0 - stop_pct)

    qty = int(capital // entry)
    risk_per_share = entry - stop
    reward_per_share = target - entry

    rr = (reward_per_share / risk_per_share) if risk_per_share > 0 else 0.0

    return {
        "symbol": symbol,
        "entry": round(entry, 2),
        "target": round(target, 2),
        "stop": round(stop, 2),
        "qty": qty,
        "rr": round(rr, 2),
    }
