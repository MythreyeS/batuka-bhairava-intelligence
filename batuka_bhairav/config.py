# batuka_bhairav/config.py
# ✅ FIXED: Multi-market aware configuration with proper parameters
 
"""
Multi-market configuration for BATUKA BHAIRAVA INTELLIGENCE
Markets: India (NIFTY 500), USA (S&P 500), UK (FTSE 100), Singapore (STI)
"""
 
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MARKETS CONFIGURATION (BRD Section 5.1)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 
MARKETS = {
    "IN": {
        "name": "India (NSE)",
        "index": "^NSEI",
        "index_name": "NIFTY 50",
        "universe_csv": "batuka_bhairav/universe/nifty500.csv",
        "suffix": ".NS",  # ✅ FIXED: Market suffix for yfinance
        "currency": "₹",
        "currency_code": "INR",
        "timezone": "Asia/Kolkata",
        "market_open": "09:15",
        "market_close": "15:30",
        "pre_market_time": "09:00",
        "post_market_time": "15:45",
        "lunch_break": None,
    },
    "US": {
        "name": "USA (NYSE/NASDAQ)",
        "index": "^GSPC",
        "index_name": "S&P 500",
        "universe_csv": "batuka_bhairav/universe/usa500.csv",
        "suffix": "",  # ✅ FIXED: US stocks don't need suffix
        "currency": "$",
        "currency_code": "USD",
        "timezone": "America/New_York",
        "market_open": "09:30",
        "market_close": "16:00",
        "pre_market_time": "09:00",
        "post_market_time": "16:15",
        "lunch_break": None,
    },
    "UK": {
        "name": "United Kingdom (LSE)",
        "index": "^FTSE",
        "index_name": "FTSE 100",
        "universe_csv": "batuka_bhairav/universe/ftse100.csv",
        "suffix": ".L",  # ✅ FIXED: UK suffix for LSE
        "currency": "£",
        "currency_code": "GBP",
        "timezone": "Europe/London",
        "market_open": "08:00",
        "market_close": "16:30",
        "pre_market_time": "07:30",
        "post_market_time": "16:15",
        "lunch_break": None,
    },
    "SG": {
        "name": "Singapore (SGX)",
        "index": "^STI",
        "index_name": "STI",
        "universe_csv": "batuka_bhairav/universe/sgx.csv",
        "suffix": ".SI",  # ✅ FIXED: Singapore suffix
        "currency": "S$",
        "currency_code": "SGD",
        "timezone": "Asia/Singapore",
        "market_open": "09:00",
        "market_close": "17:00",
        "pre_market_time": "08:30",
        "post_market_time": "17:15",
        "lunch_break": ("12:00", "13:00"),
    },
}
 
 
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DATA FETCHING CONFIGURATION (BRD Section 4.1)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 
# ✅ FIXED: Proper batch size per BRD requirement
YFINANCE_PERIOD = "3mo"  # 3 months of daily data
YFINANCE_INTERVAL = "1d"  # Daily candles
YFINANCE_BATCH_SIZE = 75  # Batch size to avoid rate limiting
YFINANCE_TIMEOUT = 10  # seconds per symbol
 
# Maximum symbols to fetch per market (for safety)
MAX_SYMBOLS_PER_MARKET = {
    "IN": 500,  # NIFTY 500
    "US": 500,  # S&P 500
    "UK": 100,  # FTSE 100
    "SG": 50,   # SGX (smaller)
}
 
 
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONVICTION SCORING WEIGHTS (BRD Section 6)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 
# ✅ BTST CONVICTION SCORE WEIGHTS (100 points total)
BTST_CONVICTION_WEIGHTS = {
    "price_momentum": 30,       # Strong positive day = high score
    "volume_expansion": 20,     # Volume 2× or more = full score
    "sector_strength": 15,      # Stock in leading sector gains bonus
    "news_sentiment": 20,       # ✅ FIXED: Source-credibility-weighted
    "breakout_technical": 10,   # Close near high = bullish exhaustion
    "market_regime_fit": 5,     # BULLISH=1.0, NEUTRAL=0.6, BEARISH=0.0
}
 
# INTRADAY CONVICTION SCORE WEIGHTS
INTRADAY_CONVICTION_WEIGHTS = {
    "gap_score": 25,            # Rewards gap-up opens
    "intraday_move": 25,        # Strong close vs open
    "volume": 20,               # Higher denominator, tighter filter
    "close_near_high": 15,      # Momentum confirmation
    "rsi_filter": 10,           # Not overbought/oversold
    "regime": 5,                # Market regime
}
 
# LONG-TERM CONVICTION SCORE WEIGHTS
LONGTERM_CONVICTION_WEIGHTS = {
    "trend": 25,                # Above SMA20 & SMA50 = strong uptrend
    "mom_20d": 20,              # Recent 4-week trend
    "mom_60d": 15,              # Medium-term drift
    "rsi_quality": 20,          # Healthy entry (45-65 sweet spot)
    "sector_strength": 10,      # Sector score
    "volume_expansion": 5,      # Volume confirmation
    "regime": 5,                # Market regime
}
 
# Use BTST weights as default for backward compatibility
CONVICTION_WEIGHTS = BTST_CONVICTION_WEIGHTS
 
 
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PICK SELECTION THRESHOLDS (BRD Section 6)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 
# ✅ FIXED: Configurable thresholds (were hardcoded in run_all_markets.py)
 
# BTST pick criteria (BRD 6.1)
BTST_CONVICTION_MIN = 70      # conviction > 70
BTST_VOL_RATIO_MIN = 1.2      # vol_ratio > 1.2
BTST_DAY_CHANGE_MIN = 0.5     # day_change% > 0.5
BTST_MAX_PICKS = 3            # max 3 picks per market
 
# Intraday pick criteria
INTRADAY_CONVICTION_MIN = 60
INTRADAY_MAX_PICKS = 3
 
# Long-term pick criteria (BRD 6.3)
LONGTERM_CONVICTION_MIN = 65  # conviction > 65
LONGTERM_MOM_60D_MIN = 5      # mom_60d > 5%
LONGTERM_MAX_PICKS = 3        # max 3 picks per market
 
 
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAN-OF-MATCH CRITERIA (BRD Section 7.2)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 
# ✅ FIXED: Proper thresholds per BRD
MOM_MIN_ABS_PCT_MOVE = 1.75   # |day_change%| ≥ 1.75 OR
MOM_MIN_VOL_RATIO = 1.80      # vol_ratio ≥ 1.80
 
 
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TRADE CARD PARAMETERS (BRD Section 6.4)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 
# Default capital allocation per strategy
DEFAULT_CAPITAL_BTST = 5000        # ₹5,000 or $5,000 per strategy
DEFAULT_CAPITAL_INTRADAY = 5000
DEFAULT_CAPITAL_LONGTERM = 5000
 
# ✅ FIXED: Proper trade levels per BRD
BTST_TARGET_PCT = 0.02            # +2.0% target
BTST_STOP_PCT = 0.01              # -1.0% stop
 
INTRADAY_TARGET_ATR_MULT = 2.0    # Target: +2×ATR
INTRADAY_STOP_ATR_MULT = 0.5      # Stop: entry - 0.5×ATR
 
LONGTERM_TARGET_PCT = 0.12        # +12% target
LONGTERM_STOP_ATR_MULT = 2.0      # Stop: close - 2×ATR
 
 
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NEWS SENTIMENT CONFIGURATION (BRD Section 5.2-5.3)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 
# ✅ FIXED: Comprehensive news feed configuration
 
NEWS_FEEDS = {
    "IN": {  # India - 25 feeds across 5 tiers
        "tier_1_official": {
            "weight": 0.99,
            "feeds": [
                "https://www.nseindia.com/feed",
                "https://www.bseindia.com/feed",
                "https://www.rbi.org.in/feed",
                "https://www.sebi.gov.in/feed",
            ]
        },
        "tier_2_premium": {
            "weight": 0.90,
            "feeds": [
                "https://feeds.economictimes.indiatimes.com/markets",
                "https://feeds.business-standard.com/markets",
                "https://feeds.livemint.com/markets",
            ]
        },
        "tier_3_broad": {
            "weight": 0.83,
            "feeds": [
                "https://feeds.moneycontrol.com/markets",
                "https://feeds.ndtvprofit.com/markets",
                "https://feeds.financialexpress.com/markets",
                "https://feeds.thehindu.com/business",
            ]
        },
        "tier_4_wire": {
            "weight": 0.93,
            "feeds": [
                "https://feeds.reuters.com/reuters/indiabusinessnews",
            ]
        },
        "tier_5_specialised": {
            "weight": 0.72,
            "feeds": [
                "https://feeds.zeebiz.com/markets",
            ]
        },
    },
    "US": {  # USA - Major financial feeds
        "tier_1": {
            "weight": 0.98,
            "feeds": [
                "https://feeds.bloomberg.com/markets/news",
                "https://feeds.cnbc.com/cnbc/markets",
            ]
        },
        "tier_2": {
            "weight": 0.90,
            "feeds": [
                "https://feeds.reuters.com/reuters/finance",
                "https://feeds.wsj.com/xml/rss/3_7085.xml",
            ]
        },
    },
    "UK": {  # UK - Financial Times, Reuters, etc
        "tier_1": {
            "weight": 0.98,
            "feeds": [
                "https://feeds.ft.com/markets",
            ]
        },
        "tier_2": {
            "weight": 0.90,
            "feeds": [
                "https://feeds.bbc.com/news/business",
                "https://feeds.guardian.com/business",
            ]
        },
    },
    "SG": {  # Singapore - SGX, Business Times
        "tier_1": {
            "weight": 0.98,
            "feeds": [
                "https://feeds.sgx.com/markets",
            ]
        },
        "tier_2": {
            "weight": 0.90,
            "feeds": [
                "https://feeds.businesstimes.com.sg/markets",
            ]
        },
    },
}
 
# Positive sentiment keywords (financial lexicon)
POSITIVE_KEYWORDS = [
    "gain", "up", "rally", "surge", "jump", "breakout", "bull",
    "buy", "strong", "outperform", "upgrade", "beat", "exceed",
    "growth", "profit", "dividend", "positive", "recovery",
]
 
# Negative sentiment keywords
NEGATIVE_KEYWORDS = [
    "fall", "down", "drop", "crash", "loss", "bear", "sell",
    "weak", "underperform", "downgrade", "miss", "decline",
    "loss", "risk", "warning", "concern", "negative",
]
 
 
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TELEGRAM CONFIGURATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 
# ✅ FIXED: Retry configuration
TELEGRAM_RETRY_ATTEMPTS = 3
TELEGRAM_RETRY_BACKOFF = [2, 4, 8]  # exponential backoff: 2s, 4s, 8s
TELEGRAM_TIMEOUT = 30
 
# Report timing configuration per market
REPORT_SCHEDULE = {
    "IN": {
        "pre_market": "08:45",      # 30 min before 09:15 open
        "post_market": "15:45",     # 15 min before 15:30 close
        "weekend": "09:00",         # Sunday
    },
    "US": {
        "pre_market": "09:00",      # 30 min before 09:30 open
        "post_market": "16:15",     # 15 min before 16:00 close
        "weekend": "09:00",         # Sunday
    },
    "UK": {
        "pre_market": "07:30",      # 30 min before 08:00 open
        "post_market": "16:15",     # 15 min before 16:30 close
        "weekend": "09:00",
    },
    "SG": {
        "pre_market": "08:30",      # 30 min before 09:00 open
        "post_market": "17:15",     # 15 min before 17:00 close
        "weekend": "09:00",
    },
}
 
 
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TECHNICAL INDICATOR CONFIGURATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 
SMA_PERIOD_SHORT = 20  # SMA-20
SMA_PERIOD_LONG = 50   # SMA-50
RSI_PERIOD = 14        # RSI(14)
ATR_PERIOD = 14        # ATR(14)
 
# RSI zones
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
RSI_SWEET_SPOT_MIN = 45
RSI_SWEET_SPOT_MAX = 65
 
# Close near high threshold
CLOSE_NEAR_HIGH_PCT = 0.98  # Close ≥ 98% of day high
 
 
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LOGGING & OUTPUT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 
LOG_LEVEL = "INFO"
OUTPUT_DIR = "."  # Current directory for JSON outputs
 
# JSON output file pattern
OUTPUT_PATTERN = "output_{market}.json"
CONSOLIDATED_OUTPUT = "output_consolidated.json"
 
# GitHub Pages publish directory
DOCS_DATA_DIR = "docs/data"
 
