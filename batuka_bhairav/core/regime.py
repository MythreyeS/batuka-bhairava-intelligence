# batuka_bhairav/core/regime.py
# ✅ FIXED: Market-aware regime detection with proper index symbols

"""
Market regime detector (BULLISH / BEARISH / NEUTRAL).
✅ FIXED: Now accepts market_code to use correct index
✅ Per BRD Section 4.3: Uses SMA-20 and SMA-50 comparison
"""

from __future__ import annotations
import yfinance as yf
import logging
from batuka_bhairav.config import MARKETS

logger = logging.getLogger("batuka_regime")


def get_market_regime(market_code: str = "IN", df=None) -> str:
    """
    Detect market regime for given market.
    
    ✅ FIXED: Now accepts market_code parameter (was hardcoded before)
    
    Regime detection logic (BRD Section 4.3):
    - BULLISH: Close > SMA-20 AND Close > SMA-50
    - BEARISH: Close < SMA-20 AND Close < SMA-50
    - NEUTRAL: All other cases

    Args:
        market_code: Market code (IN/US/UK/SG) - ✅ FIXED
        df: Optional pre-fetched index dataframe

    Returns:
        str: "BULLISH", "BEARISH", or "NEUTRAL"
    """
    
    if market_code not in MARKETS:
        logger.warning(f"Unknown market: {market_code}, defaulting to NEUTRAL")
        return "NEUTRAL"

    market_config = MARKETS[market_code]
    index_symbol = market_config["index"]  # ✅ FIXED: Get index for this market
    market_name = market_config["name"]
    
    # Try to fetch index data if not provided
    if df is None or (hasattr(df, "empty") and df.empty):
        try:
            logger.debug(f"Fetching regime index for {market_code}: {index_symbol}")
            ticker = yf.Ticker(index_symbol)
            df = ticker.history(period="3mo")  # 3 months for SMA calculation
        except Exception as e:
            logger.warning(f"Failed to fetch regime index {index_symbol}: {e}")
            df = None

    # Fallback to NEUTRAL if no data
    if df is None or df.empty or "Close" not in df.columns:
        logger.warning(f"No index data for {market_name}, regime = NEUTRAL")
        return "NEUTRAL"

    try:
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # REGIME CALCULATION
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        close = float(df["Close"].iloc[-1])
        
        # SMA-20 (for recent trend)
        if len(df) >= 20:
            sma20 = float(df["Close"].rolling(20).mean().iloc[-1])
        else:
            sma20 = close  # Fallback if insufficient data
        
        # SMA-50 (for medium-term trend)
        if len(df) >= 50:
            sma50 = float(df["Close"].rolling(50).mean().iloc[-1])
        else:
            sma50 = sma20  # Fallback if insufficient data

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # REGIME DETERMINATION
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        above_sma20 = close > sma20
        above_sma50 = close > sma50

        if above_sma20 and above_sma50:
            regime = "BULLISH"
        elif (not above_sma20) and (not above_sma50):
            regime = "BEARISH"
        else:
            regime = "NEUTRAL"

        logger.debug(
            f"{market_code} ({index_symbol}): "
            f"Close={close:.2f} | SMA20={sma20:.2f} ({'+' if above_sma20 else '-'}) | "
            f"SMA50={sma50:.2f} ({'+' if above_sma50 else '-'}) → {regime}"
        )

        return regime

    except Exception as e:
        logger.error(f"Error calculating regime for {market_code}: {e}")
        return "NEUTRAL"


def get_all_market_regimes() -> dict[str, str]:
    """
    ✅ NEW: Get regime for all 4 markets at once
    
    Returns:
        Dict {market_code: regime}
    """
    regimes = {}
    for market_code in ["IN", "US", "UK", "SG"]:
        regimes[market_code] = get_market_regime(market_code)
    
    return regimes
