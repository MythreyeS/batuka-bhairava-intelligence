# batuka_bhairav/config.py
# ── Enhanced with multi-market support ────────────────────────────────────
import os

# ── Active market — set via env var MARKET (default: IN) ──────────────────
ACTIVE_MARKET = os.getenv("MARKET", "IN").upper()

# ── Market definitions ─────────────────────────────────────────────────────
MARKETS = {
    "IN": {
        "name":          "India (NSE)",
        "index":         "^NSEI",
        "index_label":   "NIFTY 50",
        "currency":      "₹",
        "timezone":      "Asia/Kolkata",
        "universe_csv":  "batuka_bhairav/universe/nifty500.csv",
        "news_feeds": [
            {"source": "Moneycontrol", "rss": "https://www.moneycontrol.com/rss/marketreports.xml"},
            {"source": "Moneycontrol", "rss": "https://www.moneycontrol.com/rss/business.xml"},
            {"source": "NDTV Profit",  "rss": "https://feeds.feedburner.com/ndtvprofit-latest"},
        ],
    },
    "US": {
        "name":          "USA (NYSE/NASDAQ)",
        "index":         "^GSPC",
        "index_label":   "S&P 500",
        "currency":      "$",
        "timezone":      "America/New_York",
        "universe_csv":  "batuka_bhairav/universe/usa500.csv",
        "news_feeds": [
            {"source": "Reuters",     "rss": "https://feeds.reuters.com/reuters/businessNews"},
            {"source": "MarketWatch", "rss": "https://feeds.marketwatch.com/marketwatch/topstories/"},
        ],
    },
    "UK": {
        "name":          "UK (LSE)",
        "index":         "^FTSE",
        "index_label":   "FTSE 100",
        "currency":      "£",
        "timezone":      "Europe/London",
        "universe_csv":  "batuka_bhairav/universe/ftse100.csv",
        "news_feeds": [
            {"source": "Reuters", "rss": "https://feeds.reuters.com/reuters/UKBusinessNews"},
        ],
    },
    "SG": {
        "name":          "Singapore (SGX)",
        "index":         "^STI",
        "index_label":   "STI",
        "currency":      "S$",
        "timezone":      "Asia/Singapore",
        "universe_csv":  "batuka_bhairav/universe/sgx.csv",
        "news_feeds":    [],
    },
}

# ── Active market config (used everywhere) ─────────────────────────────────
_cfg = MARKETS.get(ACTIVE_MARKET, MARKETS["IN"])

MARKET_NAME     = _cfg["name"]
MARKET_CURRENCY = _cfg["currency"]
MARKET_TIMEZONE = _cfg["timezone"]
UNIVERSE_CSV    = _cfg["universe_csv"]
INDEX_SYMBOL    = _cfg["index"]
INDEX_LABEL     = _cfg["index_label"]
NEWS_FEEDS      = _cfg["news_feeds"]

# ── Keep old name for backward compat ─────────────────────────────────────
NIFTY_INDEX = INDEX_SYMBOL

# ── Price fetching ─────────────────────────────────────────────────────────
YFINANCE_PERIOD     = "3mo"
YFINANCE_INTERVAL   = "1d"
YFINANCE_BATCH_SIZE = 75

# ── Scoring ────────────────────────────────────────────────────────────────
MOM_MIN_ABS_PCT_MOVE     = 1.75
MOM_MIN_VOL_RATIO        = 1.80
MOM_MAX_ROWS_IN_TELEGRAM = 30
SECTOR_TOP_N             = 3
SECTOR_BOTTOM_N          = 3

SOURCE_WEIGHT = {
    "NSE":               1.00,
    "Reuters":           0.95,
    "NDTV Profit":       0.90,
    "ET Markets":        0.90,
    "Moneycontrol":      0.85,
    "Business Standard": 0.85,
    "MarketWatch":       0.80,
    "Livemint":          0.85,
}

CONVICTION_WEIGHTS = {
    "price_momentum":     30,
    "volume_expansion":   20,
    "sector_strength":    15,
    "news_sentiment":     20,
    "breakout_technical": 10,
    "market_regime_fit":   5,
}

# ── BTST trade defaults ────────────────────────────────────────────────────
BTST_CAPITAL_PER_TRADE = float(os.getenv("BTST_CAPITAL", "5000"))
BTST_TARGET_PCT        = 0.020   # 2%
BTST_STOP_PCT          = 0.010   # 1%
