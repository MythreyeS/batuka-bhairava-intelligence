def compute_regime(close, sma):
    if close > sma:
        return "BULLISH", 5
    elif close < sma:
        return "BEARISH", 1
    return "NEUTRAL", 3

