from __future__ import annotations

from typing import Dict, List


def normalize_component_scores(features: dict, sector_score: float, news_score: float, regime: str) -> dict:
    """
    Reconstruct the same normalized pieces used by conviction_score_0_100().
    This is for explainability only.
    """
    mom = max(0.0, min(1.0, (features.get("day_change_pct", 0.0) + 3.0) / 6.0))
    vol = max(0.0, min(1.0, features.get("vol_ratio", 1.0) / 2.0))
    tech = 0.7 if features.get("close_near_high", 0.0) >= 1.0 else 0.4
    reg = {"BULLISH": 1.0, "NEUTRAL": 0.6}.get(regime, 0.0)

    return {
        "price_momentum_norm": round(mom, 4),
        "volume_expansion_norm": round(vol, 4),
        "sector_strength_norm": round(float(sector_score), 4),
        "news_sentiment_norm": round(float(news_score), 4),
        "breakout_technical_norm": round(float(tech), 4),
        "market_regime_fit_norm": round(float(reg), 4),
    }


def build_rule_based_reasons(symbol: str, name: str, features: dict, sector: str, sector_score: float,
                             news_score: float, regime: str, conviction: float) -> List[str]:
    reasons = []

    day_change = features.get("day_change_pct", 0.0)
    vol_ratio = features.get("vol_ratio", 1.0)
    rsi = features.get("rsi", 50.0)
    mom_20d = features.get("mom_20d", 0.0)
    above_sma20 = features.get("above_sma20", 0.0)
    above_sma50 = features.get("above_sma50", 0.0)
    close_near_high = features.get("close_near_high", 0.0)

    if day_change > 0:
        reasons.append(f"{name} gained {day_change:.2f}% today, which supported price momentum.")
    else:
        reasons.append(f"{name} moved {day_change:.2f}% today, which limited momentum strength.")

    if vol_ratio >= 1.5:
        reasons.append(f"Volume was {vol_ratio:.2f}x versus the previous session, indicating strong participation.")
    else:
        reasons.append(f"Volume was only {vol_ratio:.2f}x of the previous session, so participation was moderate.")

    if close_near_high >= 1.0:
        reasons.append("The stock closed near the day’s high, which is a bullish technical signal.")
    else:
        reasons.append("The stock did not close very near the day’s high, so breakout confirmation was weaker.")

    if above_sma20 and above_sma50:
        reasons.append("It is trading above both the 20-day and 50-day moving averages.")
    elif above_sma20:
        reasons.append("It is trading above the 20-day moving average, but not strongly above longer trend support.")
    else:
        reasons.append("It is not strongly above key moving averages, which reduced trend quality.")

    if mom_20d > 0:
        reasons.append(f"20-day momentum is {mom_20d:.2f}%, showing recent trend support.")
    else:
        reasons.append(f"20-day momentum is {mom_20d:.2f}%, so medium-term trend support is weak.")

    if 45 <= rsi <= 70:
        reasons.append(f"RSI is {rsi:.1f}, which is in a healthy tradable range.")
    else:
        reasons.append(f"RSI is {rsi:.1f}, which is less ideal for a fresh entry.")

    reasons.append(f"Sector: {sector} | sector score contribution: {sector_score:.2f}")
    reasons.append(f"Market regime: {regime}")
    reasons.append(f"News sentiment input used by engine: {news_score:.2f}")
    reasons.append(f"Final conviction score: {conviction:.2f}/100")

    return reasons


def build_explainability_record(symbol: str, name: str, sector: str, features: dict,
                                sector_score: float, news_score: float, regime: str,
                                conviction: float) -> Dict:
    components = normalize_component_scores(
        features=features,
        sector_score=sector_score,
        news_score=news_score,
        regime=regime,
    )

    reasons = build_rule_based_reasons(
        symbol=symbol,
        name=name,
        features=features,
        sector=sector,
        sector_score=sector_score,
        news_score=news_score,
        regime=regime,
        conviction=conviction,
    )

    return {
        "symbol": symbol,
        "name": name,
        "sector": sector,
        "regime": regime,
        "news_sentiment": news_score,
        "sector_score": sector_score,
        "conviction": round(float(conviction), 2),
        "features": features,
        "components": components,
        "reasons": reasons,
    }


