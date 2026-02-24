import pandas as pd
import yfinance as yf
import time

OUTPUT_FILE = "batuka_bhairav/universe/nifty500.csv"

def normalize_symbol(sym):
    sym = str(sym).strip().upper()
    if not sym.endswith(".NS"):
        sym += ".NS"
    return sym

def fetch_nifty500_from_wikipedia():
    print("Fetching NIFTY 500 list from Wikipedia...")
    url = "https://en.wikipedia.org/wiki/NIFTY_500"
    tables = pd.read_html(url)

    for table in tables:
        cols = [c.lower() for c in table.columns.astype(str)]
        if "symbol" in " ".join(cols):
            df = table.copy()
            break
    else:
        raise Exception("Could not find NIFTY 500 table.")

    # Clean columns
    symbol_col = [c for c in df.columns if "symbol" in str(c).lower()][0]
    name_col = [c for c in df.columns if "company" in str(c).lower()][0]

    df = df[[symbol_col, name_col]].copy()
    df.columns = ["symbol", "company"]

    df["symbol"] = df["symbol"].apply(normalize_symbol)

    return df

def fetch_sector_from_yfinance(symbol):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        sector = info.get("sector", "UNKNOWN")
        return sector
    except Exception:
        return "UNKNOWN"

def build_full_dataset():
    df = fetch_nifty500_from_wikipedia()

    sectors = []
    print("Fetching sectors from Yahoo Finance...")
    for i, row in df.iterrows():
        sym = row["symbol"]
        sector = fetch_sector_from_yfinance(sym)
        sectors.append(sector)

        print(f"{i+1}/{len(df)} {sym} → {sector}")
        time.sleep(0.5)  # avoid rate limit

    df["sector"] = sectors
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n✅ Saved full sector-mapped NIFTY 500 to {OUTPUT_FILE}")

if __name__ == "__main__":
    build_full_dataset()
