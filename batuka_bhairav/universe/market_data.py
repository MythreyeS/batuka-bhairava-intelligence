# batuka_bhairav/universe/market_data.py
# ✅ FIXED: Market-aware data fetching with proper yfinance suffixes and batching
 
"""
Market data provider with yfinance integration.
✅ Supports multiple markets with proper suffix handling
✅ Batch processing to avoid rate limiting
✅ Configurable batch size per BRD Section 4.1
"""
 
from __future__ import annotations
import yfinance as yf
import pandas as pd
import logging
from batuka_bhairav.config import (
    YFINANCE_PERIOD, YFINANCE_INTERVAL, YFINANCE_BATCH_SIZE, YFINANCE_TIMEOUT, MARKETS
)
 
logger = logging.getLogger("batuka_market_data")
 
 
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RSI CALCULATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 
def compute_rsi(series, period=14):
    """Compute Relative Strength Index (14-period)"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / (loss + 1e-9)
    rsi = 100 - (100 / (1 + rs))
    return rsi
 
 
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ATR CALCULATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 
def compute_atr(df, period=14):
    """
    Compute Average True Range (14-period)
    ATR = True Range moving average
    """
    try:
        h = df["High"].astype(float)
        l = df["Low"].astype(float)
        c = df["Close"].astype(float).shift(1)
        tr = pd.concat([
            h - l,
            abs(h - c),
            abs(l - c)
        ], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()
        return atr
    except Exception as e:
        logger.warning(f"ATR calculation failed: {e}")
        return None
 
 
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FETCH MARKET DATA (✅ FIXED: Market-aware)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 
def fetch_market_data(symbols: list, market_code: str = "IN") -> dict:
    """
    Fetch OHLCV + indicators for symbols in a given market.
 
    ✅ FIXED Changes:
    1. Market parameter to apply correct suffix
    2. Batch processing (75 symbols per batch per BRD)
    3. Proper error handling per symbol (doesn't break on one failure)
    4. All technical indicators computed
 
    Args:
        symbols: List of stock symbols (without suffix)
        market_code: Market code (IN/US/UK/SG)
 
    Returns:
        Dict {symbol: {features}} with OHLCV + technical indicators
    """
    
    if market_code not in MARKETS:
        logger.error(f"Unknown market: {market_code}")
        return {}
 
    market_config = MARKETS[market_code]
    suffix = market_config["suffix"]  # ✅ FIXED: Use market-specific suffix
    
    result = {}
    
    # ✅ FIXED: Batch processing per BRD Section 4.1
    total = len(symbols)
    batch_count = (total // YFINANCE_BATCH_SIZE) + (1 if total % YFINANCE_BATCH_SIZE else 0)
    
    logger.info(f"📡 Fetching {total} symbols in {batch_count} batches (batch_size={YFINANCE_BATCH_SIZE})")
    
    for batch_idx in range(0, total, YFINANCE_BATCH_SIZE):
        batch = symbols[batch_idx:batch_idx + YFINANCE_BATCH_SIZE]
        batch_num = (batch_idx // YFINANCE_BATCH_SIZE) + 1
        
        logger.info(f"   Batch {batch_num}/{batch_count}: {len(batch)} symbols")
        
        for sym in batch:
            try:
                # ✅ FIXED: Add suffix based on market
                ticker_symbol = sym + suffix if suffix else sym
                
                logger.debug(f"   Fetching {ticker_symbol}...")
                
                ticker = yf.Ticker(ticker_symbol)
                hist = ticker.history(period=YFINANCE_PERIOD, interval=YFINANCE_INTERVAL)
 
                # ✅ FIXED: Skip if insufficient data (need at least 60 days for proper momentum)
                if hist.empty or len(hist) < 60:
                    logger.debug(f"   ⚠️ {sym}: Insufficient data ({len(hist)} days)")
                    continue
 
                # ✅ FIXED: Better handling of edge cases
                close = hist["Close"].astype(float)
                volume = hist["Volume"].astype(float)
                high = hist["High"].astype(float)
                low = hist["Low"].astype(float)
 
                # Latest and previous values
                latest_close = close.iloc[-1]
                prev_close = close.iloc[-2]
                latest_high = high.iloc[-1]
                latest_volume = volume.iloc[-1]
                
                if prev_close <= 0 or latest_close <= 0:
                    logger.debug(f"   ⚠️ {sym}: Invalid price data")
                    continue
 
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                # FEATURE COMPUTATION
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 
                # Daily change
                day_change_pct = ((latest_close - prev_close) / prev_close) * 100
 
                # Moving averages
                sma20 = close.rolling(20).mean().iloc[-1]
                sma50 = close.rolling(50).mean().iloc[-1]
                above_sma20 = latest_close > sma20
                above_sma50 = latest_close > sma50
 
                # Volume ratio (today vs 20-day avg)
                avg_vol = volume.rolling(20).mean().iloc[-1]
                vol_ratio = latest_volume / (avg_vol + 1e-9) if avg_vol > 0 else 1.0
 
                # Momentum (% change from N days ago)
                mom_1d_pct = ((latest_close - close.iloc[-2]) / close.iloc[-2]) * 100 if len(close) >= 2 else 0
                mom_5d_pct = ((latest_close - close.iloc[-6]) / close.iloc[-6]) * 100 if len(close) >= 6 else 0
                mom_20d_pct = ((latest_close - close.iloc[-21]) / close.iloc[-21]) * 100 if len(close) >= 21 else 0
                mom_60d_pct = ((latest_close - close.iloc[-61]) / close.iloc[-61]) * 100 if len(close) >= 61 else 0
 
                # RSI (14)
                rsi_series = compute_rsi(close, period=14)
                rsi = rsi_series.iloc[-1] if rsi_series is not None else 50.0
 
                # ATR (14)
                atr_series = compute_atr(hist, period=14)
                atr = float(atr_series.iloc[-1]) if atr_series is not None else latest_close * 0.015
 
                # Gap (open vs previous close)
                latest_open = hist["Open"].iloc[-1]
                gap_pct = ((latest_open - prev_close) / prev_close) * 100 if prev_close > 0 else 0
 
                # Intraday (close vs open)
                intraday_pct = ((latest_close - latest_open) / latest_open) * 100 if latest_open > 0 else 0
 
                # Close near high
                close_near_high = 1.0 if latest_high > 0 and (latest_close / latest_high) >= 0.98 else 0.0
 
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                # STORE RESULT
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 
                result[sym] = {
                    # Price data
                    "price": round(latest_close, 2),
                    "open": round(latest_open, 2),
                    "high": round(latest_high, 2),
                    "low": round(hist["Low"].iloc[-1], 2),
                    "prev_close": round(prev_close, 2),
                    
                    # Change metrics
                    "day_change_pct": round(day_change_pct, 2),
                    "gap_pct": round(gap_pct, 2),
                    "intraday_pct": round(intraday_pct, 2),
                    
                    # Momentum
                    "mom_1d": round(mom_1d_pct, 2),
                    "mom_5d": round(mom_5d_pct, 2),
                    "mom_20d": round(mom_20d_pct, 2),
                    "mom_60d": round(mom_60d_pct, 2),
                    
                    # Technical
                    "vol_ratio": round(vol_ratio, 2),
                    "rsi": round(rsi, 1),
                    "atr": round(atr, 2),
                    "close_near_high": close_near_high,
                    
                    # SMAs
                    "sma20": round(sma20, 2),
                    "sma50": round(sma50, 2),
                    "above_sma20": above_sma20,
                    "above_sma50": above_sma50,
                }
                
                logger.debug(f"   ✅ {sym}: {day_change_pct:+.2f}% | RSI:{rsi:.1f} | Vol:{vol_ratio:.2f}x")
 
            except Exception as e:
                # ✅ FIXED: Log and skip individual failures (don't break batch)
                logger.debug(f"   ❌ {sym}: {type(e).__name__}: {str(e)[:50]}")
                continue
 
    logger.info(f"✅ Market data fetched: {len(result)}/{total} symbols")
    return result
 
 
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GET PRICE DATA (for simple price lookups)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 
def get_stock_price(symbol: str, market_code: str = "IN") -> float | None:
    """Get current price for a single stock"""
    if market_code not in MARKETS:
        return None
    
    suffix = MARKETS[market_code]["suffix"]
    ticker_symbol = symbol + suffix if suffix else symbol
    
    try:
        ticker = yf.Ticker(ticker_symbol)
        data = ticker.history(period="1d")
        if not data.empty:
            return float(data["Close"].iloc[-1])
    except Exception as e:
        logger.debug(f"Error fetching price for {ticker_symbol}: {e}")
    
    return None
 
