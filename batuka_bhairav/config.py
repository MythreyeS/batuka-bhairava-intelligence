# batuka_bhairav/config.py
import os

ACTIVE_MARKET = os.getenv("MARKET", "IN").upper()

MARKETS = {
    "IN": {
        "name":         "India (NSE)",
        "index":        "^NSEI",
        "index_label":  "NIFTY 50",
        "currency":     "₹",
        "timezone":     "Asia/Kolkata",
        "universe_csv": "batuka_bhairav/universe/nifty500.csv",
        "news_feeds": [
            # ── TIER 1: Official Exchange & Regulatory (highest trust) ──────
            {"source": "NSE India",         "rss": "https://www.nseindia.com/api/rss?type=marketwatch"},
            {"source": "BSE India",         "rss": "https://www.bseindia.com/xml-data/corpfiling/AttachLive/rss.xml"},
            {"source": "RBI",               "rss": "https://www.rbi.org.in/scripts/rss.aspx?Id=2"},
            {"source": "SEBI",              "rss": "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=2&smid=0&rss=yes"},
            # ── TIER 2: Premium Financial News ──────────────────────────────
            {"source": "Economic Times",    "rss": "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms"},
            {"source": "Economic Times",    "rss": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"},
            {"source": "Economic Times",    "rss": "https://economictimes.indiatimes.com/markets/earnings/rssfeeds/2143429.cms"},
            {"source": "Business Standard", "rss": "https://www.business-standard.com/rss/markets-106.rss"},
            {"source": "Business Standard", "rss": "https://www.business-standard.com/rss/stocks-10601.rss"},
            {"source": "Business Standard", "rss": "https://www.business-standard.com/rss/finance-109.rss"},
            {"source": "Livemint",          "rss": "https://www.livemint.com/rss/markets"},
            {"source": "Livemint",          "rss": "https://www.livemint.com/rss/companies"},
            {"source": "Livemint",          "rss": "https://www.livemint.com/rss/money"},
            # ── TIER 3: Broad Financial Media ───────────────────────────────
            {"source": "Moneycontrol",      "rss": "https://www.moneycontrol.com/rss/marketreports.xml"},
            {"source": "Moneycontrol",      "rss": "https://www.moneycontrol.com/rss/business.xml"},
            {"source": "Moneycontrol",      "rss": "https://www.moneycontrol.com/rss/results.xml"},
            {"source": "NDTV Profit",       "rss": "https://feeds.feedburner.com/ndtvprofit-latest"},
            {"source": "NDTV Profit",       "rss": "https://feeds.feedburner.com/ndtvprofit-markets"},
            {"source": "Financial Express", "rss": "https://www.financialexpress.com/market/feed/"},
            {"source": "The Hindu Business","rss": "https://www.thehindubusinessline.com/markets/?service=rss"},
            {"source": "The Hindu Business","rss": "https://www.thehindubusinessline.com/companies/?service=rss"},
            # ── TIER 4: Wire & International ────────────────────────────────
            {"source": "Reuters India",     "rss": "https://feeds.reuters.com/reuters/INbusinessNews"},
            {"source": "Reuters India",     "rss": "https://feeds.reuters.com/reuters/INtopNews"},
            # ── TIER 5: Regional & Specialised ──────────────────────────────
            {"source": "Zee Business",      "rss": "https://www.zeebiz.com/rss/markets.xml"},
            {"source": "Zee Business",      "rss": "https://www.zeebiz.com/rss/companies.xml"},
        ],
    },
    "US": {
        "name":         "USA (NYSE/NASDAQ)",
        "index":        "^GSPC",
        "index_label":  "S&P 500",
        "currency":     "$",
        "timezone":     "America/New_York",
        "universe_csv": "batuka_bhairav/universe/usa500.csv",
        "news_feeds": [
            # ── TIER 1: Official & Wire ──────────────────────────────────────
            {"source": "Reuters",           "rss": "https://feeds.reuters.com/reuters/businessNews"},
            {"source": "Reuters",           "rss": "https://feeds.reuters.com/reuters/companyNews"},
            {"source": "Reuters",           "rss": "https://feeds.reuters.com/reuters/technologyNews"},
            {"source": "AP Business",       "rss": "https://feeds.apnews.com/rss/business"},
            # ── TIER 2: Premium Financial ───────────────────────────────────
            {"source": "CNBC",              "rss": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114"},
            {"source": "CNBC Markets",      "rss": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=20910258"},
            {"source": "MarketWatch",       "rss": "https://feeds.marketwatch.com/marketwatch/topstories/"},
            {"source": "MarketWatch",       "rss": "https://feeds.marketwatch.com/marketwatch/marketpulse/"},
            {"source": "Barrons",           "rss": "https://www.barrons.com/xml/rss/3_7510.xml"},
            # ── TIER 3: Investment Research ─────────────────────────────────
            {"source": "Seeking Alpha",     "rss": "https://seekingalpha.com/market_currents.xml"},
            {"source": "Motley Fool",       "rss": "https://www.fool.com/feeds/index.aspx"},
            {"source": "Benzinga",          "rss": "https://www.benzinga.com/feed"},
            {"source": "Yahoo Finance",     "rss": "https://finance.yahoo.com/news/rssindex"},
            {"source": "Investopedia",      "rss": "https://www.investopedia.com/feedbuilder/feed/getfeed?feedName=rss_headline"},
            # ── TIER 4: Macro & Fed ──────────────────────────────────────────
            {"source": "Fed Reserve",       "rss": "https://www.federalreserve.gov/feeds/press_all.xml"},
            {"source": "WSJ Markets",       "rss": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml"},
        ],
    },
    "UK": {
        "name":         "UK (LSE)",
        "index":        "^FTSE",
        "index_label":  "FTSE 100",
        "currency":     "£",
        "timezone":     "Europe/London",
        "universe_csv": "batuka_bhairav/universe/ftse100.csv",
        "news_feeds": [
            # ── TIER 1: Official & Wire ──────────────────────────────────────
            {"source": "Reuters UK",        "rss": "https://feeds.reuters.com/reuters/UKBusinessNews"},
            {"source": "Reuters UK",        "rss": "https://feeds.reuters.com/reuters/UKTopNews"},
            {"source": "Bank of England",   "rss": "https://www.bankofengland.co.uk/rss/news"},
            # ── TIER 2: Premium ──────────────────────────────────────────────
            {"source": "Financial Times",   "rss": "https://www.ft.com/rss/home/uk"},
            {"source": "BBC Business",      "rss": "https://feeds.bbci.co.uk/news/business/rss.xml"},
            {"source": "Guardian Business", "rss": "https://www.theguardian.com/uk/business/rss"},
            # ── TIER 3: Specialist ───────────────────────────────────────────
            {"source": "Sky News Business", "rss": "https://feeds.skynews.com/feeds/rss/business.xml"},
            {"source": "This is Money",     "rss": "https://www.thisismoney.co.uk/money/markets/index.rss"},
            {"source": "Shares Mag",        "rss": "https://www.sharesmagazine.co.uk/rss/news"},
            {"source": "Interactive Inv",   "rss": "https://www.iii.co.uk/rss/news"},
            {"source": "Proactive Inv",     "rss": "https://www.proactiveinvestors.co.uk/rss/news_rss.rss"},
        ],
    },
    "SG": {
        "name":         "Singapore (SGX)",
        "index":        "^STI",
        "index_label":  "STI",
        "currency":     "S$",
        "timezone":     "Asia/Singapore",
        "universe_csv": "batuka_bhairav/universe/sgx.csv",
        "news_feeds": [
            # ── TIER 1: Official Exchange ────────────────────────────────────
            {"source": "SGX",               "rss": "https://www.sgx.com/securities/company-announcements/rss"},
            {"source": "MAS Singapore",     "rss": "https://www.mas.gov.sg/rss/press-releases"},
            # ── TIER 2: Premium ──────────────────────────────────────────────
            {"source": "Business Times SG", "rss": "https://www.businesstimes.com.sg/rss/all"},
            {"source": "Business Times SG", "rss": "https://www.businesstimes.com.sg/rss/companies-markets"},
            {"source": "Straits Times",     "rss": "https://www.straitstimes.com/news/business/rss.xml"},
            {"source": "The Edge SG",       "rss": "https://www.theedgesingapore.com/rss.xml"},
            # ── TIER 3: Regional ─────────────────────────────────────────────
            {"source": "CNA Business",      "rss": "https://www.channelnewsasia.com/rssfeeds/8395990"},
            {"source": "Reuters Asia",      "rss": "https://feeds.reuters.com/reuters/AsiaBusinessNews"},
        ],
    },
}

# ── Active market config ───────────────────────────────────────────────────
_cfg = MARKETS.get(ACTIVE_MARKET, MARKETS["IN"])

MARKET_NAME     = _cfg["name"]
MARKET_CURRENCY = _cfg["currency"]
MARKET_TIMEZONE = _cfg["timezone"]
UNIVERSE_CSV    = _cfg["universe_csv"]
INDEX_SYMBOL    = _cfg["index"]
INDEX_LABEL     = _cfg["index_label"]
NEWS_FEEDS      = _cfg["news_feeds"]
NIFTY_INDEX     = INDEX_SYMBOL  # backward compat

# ── Price fetching ─────────────────────────────────────────────────────────
YFINANCE_PERIOD     = "3mo"
YFINANCE_INTERVAL   = "1d"
YFINANCE_BATCH_SIZE = 75

# ── Man of Match filters ───────────────────────────────────────────────────
MOM_MIN_ABS_PCT_MOVE     = 1.75
MOM_MIN_VOL_RATIO        = 1.80
MOM_MAX_ROWS_IN_TELEGRAM = 30
SECTOR_TOP_N             = 3
SECTOR_BOTTOM_N          = 3

# ── Source credibility weights (0–1) ──────────────────────────────────────
SOURCE_WEIGHT = {
    # ── India official ────────────────────────────────────────────────────
    "NSE India":         1.00,
    "BSE India":         1.00,
    "RBI":               0.98,
    "SEBI":              0.98,
    # ── India premium media ───────────────────────────────────────────────
    "Economic Times":    0.92,
    "Business Standard": 0.90,
    "Livemint":          0.88,
    "The Hindu Business":0.87,
    "Financial Express": 0.85,
    "NDTV Profit":       0.83,
    "Moneycontrol":      0.82,
    "Zee Business":      0.72,
    # ── US official & wire ────────────────────────────────────────────────
    "Fed Reserve":       1.00,
    "AP Business":       0.94,
    "Reuters":           0.93,
    "Reuters India":     0.93,
    # ── US premium ────────────────────────────────────────────────────────
    "WSJ Markets":       0.93,
    "Barrons":           0.90,
    "Financial Times":   0.92,
    "CNBC":              0.88,
    "CNBC Markets":      0.88,
    "MarketWatch":       0.85,
    "Seeking Alpha":     0.78,
    "Motley Fool":       0.75,
    "Benzinga":          0.73,
    "Yahoo Finance":     0.72,
    "Investopedia":      0.70,
    # ── UK official ───────────────────────────────────────────────────────
    "Bank of England":   1.00,
    "Reuters UK":        0.93,
    "BBC Business":      0.88,
    "Guardian Business": 0.83,
    "Sky News Business": 0.78,
    "This is Money":     0.72,
    "Shares Mag":        0.70,
    "Interactive Inv":   0.70,
    "Proactive Inv":     0.68,
    # ── SG official ───────────────────────────────────────────────────────
    "SGX":               1.00,
    "MAS Singapore":     0.98,
    "Business Times SG": 0.90,
    "Straits Times":     0.88,
    "CNA Business":      0.85,
    "Reuters Asia":      0.90,
    "The Edge SG":       0.80,
}

# ── Conviction scoring weights ─────────────────────────────────────────────
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
BTST_TARGET_PCT        = 0.020
BTST_STOP_PCT          = 0.010
