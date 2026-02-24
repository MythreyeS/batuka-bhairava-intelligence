# batuka_bhairav/core/scoring.py
from __future__ import annotations

import math
from typing import Dict, List, Tuple
import numpy as np


def compute_stock_features(df) -> dict | None:
    if df is None or df.empty or len(df) < 2:
        return None

    # last day + prev day
    last = df.iloc[-1]
    prev = df.iloc[-2]

    open_ = float(last.get("Open", np.nan))
    close = float(last.get("Close", np.nan))
    prev_close = float(prev.get("Close", np.nan))
    vol = float(last.get("Volume", np.nan))
    prev_vol = float(prev.get("Volume", np.nan))

    if any(np.isnan(x) for x in [open_, close, prev_close]) or prev_close == 0:
        return None

    day_change_pct = ((close - prev_close) / prev_close) * 100.0
    gap_pct = ((open_ - prev_close) / prev_close) * 100.0

    vol_ratio = (vol / prev_vol) if prev_vol and prev_vol > 0 else 1.0

    # simple momentum
    mom_1d = (close - prev_close) / prev_close

    # close near high (simple)
    high = float(last.get("High", close))
    close_near_high = 1.0 if high > 0 and (close / high) >= 0.98 else 0.0

    return {
        "open": open_,
        "close": close,
        "prev_close": prev_close,
        "day_change_pct": day_change_pct,
        "gap_pct": gap_pct,
        "vol_ratio": float(vol_ratio),
        "mom_1d": float(mom_1d),
        "close_near_high": close_near_high,
    }


def sector_strength_score(sector_rank: dict, sector: str) -> float:
    """
    sector_rank example: {"Banking": +1.2, "IT": -0.4, ...} normalized.
    Returns 0..1 where 1 means strongest sector.
    """
    if not sector or sector not in sector_rank:
        return 0.5
    # sector_rank is already normalized around 0; convert to 0..1
    x = sector_rank[sector]
    # clamp
    return float(max(0.0, min(1.0, 0.5 + x)))


def conviction_score_0_100(
    features: dict,
    sector_score_0_1: float,
    news_score_0_1: float,
    regime: str,
    weights: dict
) -> float:
    """
    weights out of 100, returns 0..100 conviction
    """

    # Price momentum (0..1)
    mom = max(0.0, min(1.0, (features["day_change_pct"] + 3.0) / 6.0))  # -3%..+3% mapped

    # Volume expansion (0..1)
    vol = max(0.0, min(1.0, features["vol_ratio"] / 2.0))  # 2x = full

    # Breakout/technical proxy (0..1)
    tech = 0.7 if features["close_near_high"] >= 1.0 else 0.4

    # Market regime fit (0..1)
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


def build_btst_card(symbol: str, close_price: float, capital: int, target_pct: float, stop_pct: float) -> dict:
    entry = close_price  # BTST uses close as reference; next open may gap
    target = entry * (1.0 + target_pct)
    stop = entry * (1.0 - stop_pct)

    qty = int(capital // entry) if entry > 0 else 0
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
