# batuka_bhairav/core/scoring.py
# ── Scoring for BTST + Intraday + Long Term ───────────────────────────────
from __future__ import annotations
import numpy as np


# ── Safe float ────────────────────────────────────────────────────────────
def _safe_float(val) -> float:
    if val is None:
        return np.nan
    if hasattr(val, "iloc"):
        return float(val.iloc[-1]) if len(val) > 0 else np.nan
    try:
        return float(val)
    except Exception:
        return np.nan


# ── Feature extraction ────────────────────────────────────────────────────
def compute_stock_features(df) -> dict | None:
    """
    Extracts features for ALL 3 strategies from OHLCV dataframe.
    Returns None if data is insufficient.
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

    # ── Basic daily features ──────────────────────────────────────────────
    day_change_pct = ((close - prev_close) / prev_close) * 100.0
    gap_pct        = ((open_ - prev_close) / prev_close) * 100.0
    intraday_pct   = ((close - open_) / open_) * 100.0 if open_ > 0 else 0.0
    vol_ratio      = (vol / prev_vol) if prev_vol and prev_vol > 0 else 1.0
    mom_1d         = (close - prev_close) / prev_close
    close_near_high = 1.0 if high > 0 and (close / high) >= 0.98 else 0.0

    # ── Multi-day momentum ────────────────────────────────────────────────
    prev5  = _safe_float(df["Close"].iloc[-6])  if len(df) >= 6  else close
    prev20 = _safe_float(df["Close"].iloc[-21]) if len(df) >= 21 else close
    prev60 = _safe_float(df["Close"].iloc[-61]) if len(df) >= 61 else close

    mom_5d  = ((close / prev5)  - 1.0) * 100 if prev5  > 0 else 0.0
    mom_20d = ((close / prev20) - 1.0) * 100 if prev20 > 0 else 0.0
    mom_60d = ((close / prev60) - 1.0) * 100 if prev60 > 0 else 0.0

    # ── Moving averages ───────────────────────────────────────────────────
    sma20 = _safe_float(df["Close"].rolling(20).mean().iloc[-1]) if len(df) >= 20 else close
    sma50 = _safe_float(df["Close"].rolling(50).mean().iloc[-1]) if len(df) >= 50 else sma20
    above_sma20 = 1.0 if close > sma20 else 0.0
    above_sma50 = 1.0 if close > sma50 else 0.0

    # ── ATR (volatility) ──────────────────────────────────────────────────
    try:
        h = df["High"].astype(float)
        l = df["Low"].astype(float)
        c = df["Close"].astype(float).shift(1)
        tr  = np.maximum(h - l, np.maximum(abs(h - c), abs(l - c)))
        atr = float(tr.rolling(14).mean().iloc[-1])
    except Exception:
        atr = close * 0.015

    # ── RSI (14) ──────────────────────────────────────────────────────────
    rsi = 50.0
    try:
        delta  = df["Close"].astype(float).diff()
        gain   = delta.where(delta > 0, 0.0).rolling(14).mean().iloc[-1]
        loss   = (-delta.where(delta < 0, 0.0)).rolling(14).mean().iloc[-1]
        rs     = gain / loss if loss and loss > 0 else 1.0
        rsi    = float(100 - (100 / (1 + rs)))
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
        "mom_1d":            round(mom_1d,          4),
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
        # SMAs (for buy range)
        "sma20":             round(sma20, 2),
        "sma50":             round(sma50, 2),
    }


# ── Sector strength ───────────────────────────────────────────────────────
def sector_strength_score(sector_rank: dict, sector: str) -> float:
    if not sector or sector not in sector_rank:
        return 0.5
    x = sector_rank[sector]
    return float(max(0.0, min(1.0, 0.5 + x)))


# ── BTST conviction score (overnight hold) ────────────────────────────────
def conviction_score_0_100(features, sector_score, news_score, regime, weights) -> float:
    mom    = max(0.0, min(1.0, (features["day_change_pct"] + 3.0) / 6.0))
    vol    = max(0.0, min(1.0, features["vol_ratio"] / 2.0))
    tech   = 0.7 if features["close_near_high"] >= 1.0 else 0.4
    reg    = {"BULLISH": 1.0, "NEUTRAL": 0.6}.get(regime, 0.0)

    total  = (
        weights["price_momentum"]     * mom  +
        weights["volume_expansion"]   * vol  +
        weights["sector_strength"]    * sector_score +
        weights["news_sentiment"]     * news_score +
        weights["breakout_technical"] * tech +
        weights["market_regime_fit"]  * reg
    )
    return float(round(total, 2))


# ── Intraday score (same-day trade) ──────────────────────────────────────
def intraday_score(features: dict, sector_score: float, regime: str) -> float:
    """
    Scores a stock for intraday trading (buy morning, sell evening).
    Looks for: gap up, high volume, strong intraday move, close near high.
    """
    gap      = max(0.0, min(1.0, (features["gap_pct"] + 2.0) / 4.0))
    intra    = max(0.0, min(1.0, (features["intraday_pct"] + 3.0) / 6.0))
    vol      = max(0.0, min(1.0, features["vol_ratio"] / 3.0))
    cnh      = features["close_near_high"]
    rsi_ok   = 1.0 if 40 < features["rsi"] < 70 else 0.5   # not overbought/oversold
    reg      = {"BULLISH": 1.0, "NEUTRAL": 0.7}.get(regime, 0.3)

    score = (
        25 * gap    +
        25 * intra  +
        20 * vol    +
        15 * cnh    +
        10 * rsi_ok +
        5  * reg
    )
    return float(round(min(score, 100), 2))


# ── Long-term score (weeks to months) ────────────────────────────────────
def longterm_score(features: dict, sector_score: float, regime: str) -> float:
    """
    Scores a stock for long-term investment (weeks to months).
    Looks for: above SMA, strong multi-week momentum, good RSI, sector strength.
    """
    # Trend: above both SMAs
    trend    = (features["above_sma20"] + features["above_sma50"]) / 2.0

    # Multi-week momentum
    m20      = max(0.0, min(1.0, (features["mom_20d"] + 10.0) / 20.0))
    m60      = max(0.0, min(1.0, (features["mom_60d"] + 20.0) / 40.0))

    # RSI: sweet spot 45-65 for entry (not overbought)
    rsi      = features["rsi"]
    rsi_score = 1.0 if 45 <= rsi <= 65 else (0.6 if 35 <= rsi <= 75 else 0.2)

    # Volume expansion confirms move
    vol      = max(0.0, min(1.0, features["vol_ratio"] / 2.0))

    reg      = {"BULLISH": 1.0, "NEUTRAL": 0.7}.get(regime, 0.3)

    score = (
        25 * trend       +
        20 * m20         +
        15 * m60         +
        20 * rsi_score   +
        10 * sector_score+
        5  * vol         +
        5  * reg
    )
    return float(round(min(score, 100), 2))


# ── Trade card builders ───────────────────────────────────────────────────
def build_btst_card(symbol, close_price, capital, target_pct, stop_pct) -> dict | None:
    if close_price <= 0:
        return None
    entry  = close_price
    target = round(entry * (1.0 + target_pct), 2)
    stop   = round(entry * (1.0 - stop_pct),   2)
    qty    = max(1, int(capital // entry))
    rps    = entry - stop
    rr     = round((target - entry) / rps, 2) if rps > 0 else 0.0
    return {
        "symbol": symbol, "entry": round(entry, 2),
        "target": target, "stop": stop, "qty": qty, "rr": rr,
    }


def build_intraday_card(symbol: str, features: dict, capital: float,
                        name: str = "", currency: str = "₹") -> dict | None:
    """
    Intraday: tighter stop (0.5% or 0.5×ATR), target 1–1.5%.
    Entry = current close (buy at open next day is also valid).
    """
    close = features.get("close", 0)
    atr   = features.get("atr",   close * 0.01)
    if close <= 0:
        return None

    stop_dist = max(atr * 0.5, close * 0.005)
    entry     = round(close, 2)
    stop      = round(entry - stop_dist, 2)
    target    = round(entry + stop_dist * 2.0, 2)   # 2:1 R:R
    qty       = max(1, int(capital // entry))
    rr        = round((target - entry) / stop_dist, 2)

    # Buy range: tight band around entry
    buy_low  = round((entry - stop_dist * 0.3) / 5) * 5
    buy_high = round((entry + stop_dist * 0.3) / 5) * 5

    return {
        "symbol":   symbol,
        "name":     name or symbol,
        "entry":    entry,
        "buy_low":  buy_low,
        "buy_high": buy_high,
        "target":   target,
        "stop":     stop,
        "qty":      qty,
        "rr":       rr,
        "currency": currency,
        "day_change_pct": features.get("day_change_pct", 0),
        "intraday_pct":   features.get("intraday_pct", 0),
        "vol_ratio":      features.get("vol_ratio", 1),
        "rsi":            features.get("rsi", 50),
    }


def build_longterm_card(symbol: str, features: dict, capital: float,
                        name: str = "", currency: str = "₹") -> dict | None:
    """
    Long-term: wider stop (2×ATR), target 10–15% over weeks.
    Entry ideally near SMA20 or recent breakout level.
    """
    close = features.get("close", 0)
    atr   = features.get("atr",   close * 0.015)
    sma20 = features.get("sma20", close)
    if close <= 0:
        return None

    # Buy zone: between SMA20 and current price (dip entry)
    buy_low  = round(max(sma20, close * 0.97) / 10) * 10
    buy_high = round(close / 10) * 10
    if buy_low >= buy_high:
        buy_low = round((close * 0.975) / 10) * 10

    stop   = round(close - 2.0 * atr, 2)
    target = round(close * 1.12, 2)    # 12% target
    qty    = max(1, int(capital // close))
    rps    = close - stop
    rr     = round((target - close) / rps, 2) if rps > 0 else 0.0

    return {
        "symbol":   symbol,
        "name":     name or symbol,
        "close":    close,
        "buy_low":  buy_low,
        "buy_high": buy_high,
        "target":   target,
        "stop":     stop,
        "qty":      qty,
        "rr":       rr,
        "currency": currency,
        "day_change_pct": features.get("day_change_pct", 0),
        "mom_20d":        features.get("mom_20d", 0),
        "mom_60d":        features.get("mom_60d", 0),
        "rsi":            features.get("rsi", 50),
        "above_sma20":    features.get("above_sma20", 0),
        "above_sma50":    features.get("above_sma50", 0),
    }
