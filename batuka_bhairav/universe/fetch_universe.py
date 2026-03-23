# batuka_bhairav/universe/fetch_universe.py
# ── Dynamically fetches full NSE 500 / S&P 500 / FTSE 100 / SGX ───────────
from __future__ import annotations

import os
import time
import pandas as pd
from typing import List, Dict

CACHE_DIR = "batuka_bhairav/universe"


# ── Symbol normalizers ────────────────────────────────────────────────────
def _ns(sym: str) -> str:
    sym = str(sym).strip().upper().replace(" ", "").replace("&", "")
    return sym if sym.endswith(".NS") else sym + ".NS"

def _l(sym: str) -> str:
    sym = str(sym).strip().upper()
    return sym if sym.endswith(".L") else sym + ".L"


# ── NSE 500 — from NSE official CSV ───────────────────────────────────────
def fetch_nse500() -> List[Dict]:
    """
    Downloads full Nifty 500 constituent list directly from NSE India.
    Falls back to Wikipedia, then to cached CSV.
    Returns [{symbol, name, sector}, ...]
    """
    cache = f"{CACHE_DIR}/nifty500.csv"

    # ── Method 1: NSE official constituents CSV (most reliable) ──────────
    try:
        url = "https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/html,application/xhtml+xml,*/*",
            "Referer": "https://www.nseindia.com",
        }
        df = pd.read_csv(url, storage_options={"User-Agent": "Mozilla/5.0"})
        df.columns = [c.strip().lower() for c in df.columns]

        # NSE CSV has: Company Name, Industry, Symbol, Series, ISIN Code
        sym_col  = next((c for c in df.columns if "symbol" in c), None)
        name_col = next((c for c in df.columns if "company" in c or "name" in c), None)
        sec_col  = next((c for c in df.columns if "industry" in c or "sector" in c), None)

        if sym_col:
            rows = []
            for _, r in df.iterrows():
                sym  = _ns(str(r[sym_col]).strip())
                name = str(r[name_col]).strip() if name_col else sym.replace(".NS","")
                sec  = str(r[sec_col]).strip()  if sec_col  else "Unknown"
                rows.append({"symbol": sym, "name": name, "sector": sec})

            if len(rows) > 100:
                # Save to cache
                pd.DataFrame(rows).to_csv(cache, index=False)
                print(f"[Universe] NSE official: {len(rows)} stocks fetched")
                return rows

    except Exception as e:
        print(f"[Universe] NSE official failed: {e}")

    # ── Method 2: Wikipedia ───────────────────────────────────────────────
    try:
        tables = pd.read_html("https://en.wikipedia.org/wiki/NIFTY_500")
        for t in tables:
            cols = [c.lower() for c in t.columns.astype(str)]
            if any("symbol" in c for c in cols):
                sym_col  = next((c for c in t.columns if "symbol" in str(c).lower()), None)
                name_col = next((c for c in t.columns if "company" in str(c).lower()), None)
                sec_col  = next((c for c in t.columns if "sector" in str(c).lower() or "industry" in str(c).lower()), None)
                if sym_col:
                    rows = []
                    for _, r in t.iterrows():
                        sym  = _ns(str(r[sym_col]))
                        name = str(r[name_col]).strip() if name_col else sym.replace(".NS","")
                        sec  = str(r[sec_col]).strip()  if sec_col  else "Unknown"
                        rows.append({"symbol": sym, "name": name, "sector": sec})
                    if len(rows) > 100:
                        pd.DataFrame(rows).to_csv(cache, index=False)
                        print(f"[Universe] Wikipedia: {len(rows)} NSE stocks fetched")
                        return rows
    except Exception as e:
        print(f"[Universe] Wikipedia failed: {e}")

    # ── Method 3: Cached CSV fallback ────────────────────────────────────
    if os.path.exists(cache):
        df = pd.read_csv(cache)
        rows = df.to_dict("records")
        # ensure all have name column
        for r in rows:
            if "name" not in r and "company" in r:
                r["name"] = r["company"]
            elif "name" not in r:
                r["name"] = str(r.get("symbol","")).replace(".NS","")
        print(f"[Universe] Cache fallback: {len(rows)} stocks")
        return rows

    print("[Universe] WARNING: All methods failed, using minimal fallback")
    return [
        {"symbol": s, "name": s.replace(".NS",""), "sector": "Unknown"}
        for s in ["RELIANCE.NS","HDFCBANK.NS","INFY.NS","TCS.NS","ICICIBANK.NS",
                  "SBIN.NS","BAJFINANCE.NS","HINDUNILVR.NS","ITC.NS","LT.NS"]
    ]


# ── S&P 500 — from Wikipedia ──────────────────────────────────────────────
def fetch_sp500() -> List[Dict]:
    cache = f"{CACHE_DIR}/usa500.csv"
    try:
        df = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]
        rows = []
        for _, r in df.iterrows():
            sym  = str(r.get("Symbol","")).strip().replace(".","-")
            name = str(r.get("Security","")).strip()
            sec  = str(r.get("GICS Sector","Unknown")).strip()
            if sym:
                rows.append({"symbol": sym, "name": name, "sector": sec})
        if rows:
            pd.DataFrame(rows).to_csv(cache, index=False)
            print(f"[Universe] S&P 500: {len(rows)} stocks fetched")
            return rows
    except Exception as e:
        print(f"[Universe] S&P 500 fetch failed: {e}")

    # Fallback cache
    if os.path.exists(cache):
        return pd.read_csv(cache).to_dict("records")

    return [{"symbol": s, "name": s, "sector": "Unknown"}
            for s in ["AAPL","MSFT","NVDA","AMZN","META","GOOGL","TSLA","JPM","V","UNH"]]


# ── FTSE 100 — from Wikipedia ─────────────────────────────────────────────
def fetch_ftse100() -> List[Dict]:
    cache = f"{CACHE_DIR}/ftse100.csv"
    try:
        tables = pd.read_html("https://en.wikipedia.org/wiki/FTSE_100_Index")
        for t in tables:
            cols = [c.lower() for c in t.columns.astype(str)]
            if any("ticker" in c or "symbol" in c for c in cols):
                sym_col  = next((c for c in t.columns if "ticker" in str(c).lower() or "symbol" in str(c).lower()), None)
                name_col = next((c for c in t.columns if "company" in str(c).lower() or "name" in str(c).lower()), None)
                sec_col  = next((c for c in t.columns if "sector" in str(c).lower() or "industry" in str(c).lower()), None)
                if sym_col:
                    rows = []
                    for _, r in t.iterrows():
                        sym  = _l(str(r[sym_col]))
                        name = str(r[name_col]).strip() if name_col else sym.replace(".L","")
                        sec  = str(r[sec_col]).strip()  if sec_col  else "Unknown"
                        rows.append({"symbol": sym, "name": name, "sector": sec})
                    if len(rows) > 50:
                        pd.DataFrame(rows).to_csv(cache, index=False)
                        print(f"[Universe] FTSE 100: {len(rows)} stocks fetched")
                        return rows
    except Exception as e:
        print(f"[Universe] FTSE 100 fetch failed: {e}")

    if os.path.exists(cache):
        return pd.read_csv(cache).to_dict("records")

    return [{"symbol": s, "name": s.replace(".L",""), "sector": "Unknown"}
            for s in ["SHEL.L","AZN.L","HSBA.L","ULVR.L","BP.L"]]


# ── SGX — static (no good public source) ─────────────────────────────────
def fetch_sgx() -> List[Dict]:
    cache = f"{CACHE_DIR}/sgx.csv"
    if os.path.exists(cache):
        return pd.read_csv(cache).to_dict("records")
    return [
        {"symbol": "D05.SI",  "name": "DBS Group",          "sector": "Banking"},
        {"symbol": "O39.SI",  "name": "OCBC Bank",           "sector": "Banking"},
        {"symbol": "U11.SI",  "name": "UOB",                 "sector": "Banking"},
        {"symbol": "Z74.SI",  "name": "Singtel",             "sector": "Telecom"},
        {"symbol": "C6L.SI",  "name": "Singapore Airlines",  "sector": "Aviation"},
        {"symbol": "S68.SI",  "name": "SGX",                 "sector": "Financial Services"},
        {"symbol": "BN4.SI",  "name": "Keppel",              "sector": "Infrastructure"},
        {"symbol": "U96.SI",  "name": "Sembcorp Industries",  "sector": "Utilities"},
        {"symbol": "C38U.SI", "name": "CapitaLand ICCT",     "sector": "REIT"},
        {"symbol": "A17U.SI", "name": "Ascendas REIT",       "sector": "REIT"},
    ]


# ── Master loader ─────────────────────────────────────────────────────────
def load_universe(market_code: str) -> List[Dict]:
    """
    Main entry point. Fetches live universe for any market.
    Always tries live fetch first, falls back to cache.
    """
    fetchers = {
        "IN": fetch_nse500,
        "US": fetch_sp500,
        "UK": fetch_ftse100,
        "SG": fetch_sgx,
    }
    fn = fetchers.get(market_code.upper())
    if not fn:
        raise ValueError(f"Unknown market: {market_code}")
    return fn()
