#!/usr/bin/python

import requests
import pandas as pd
import sqlite3
import time
from datetime import datetime, timedelta

# Load API key
with open("api.key", "r") as f:
    API_KEY = f.read().strip()

sector_etfs = [
    "SPY",
    "XLK",
    "XLF",
    "XLE",
    "XLV",
    "XLI",
    "XLP",
    "XLY",
    "XLU",
    "XLB",
    "XLRE"
]

# Compute start_date for last 5 days
start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%dT00:00:00")

def get_data(symbol):

    url = "https://api.twelvedata.com/time_series"

    params = {
        "symbol": symbol,
        "interval": "1day",
        "start_date": start_date,
        "timezone": "America/New_York",
        "apikey": API_KEY
    }

    while True:
        r = requests.get(url, params=params)

        # Raise error if HTTP request fails
        r.raise_for_status()

        data = r.json()

        if data.get("status") == "ok":
            break

        message = str(data.get("message", "")).lower()
        code = str(data.get("code", "")).lower()

        is_rate_limited = "rate" in message and "limit" in message
        is_rate_limited = is_rate_limited or "rate_limit" in code

        if is_rate_limited:
            print(f"Rate limit exceeded for {symbol}. Waiting 60 seconds before retrying...")
            time.sleep(60)
            continue

        raise RuntimeError(f"API error for {symbol}: {data}")

    df = pd.DataFrame(data["values"])

    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime")

    df["open"] = df["open"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["close"] = df["close"].astype(float)
    df["volume"] = df["volume"].astype(float)

    return df


results = []
price_rows = []

for etf in sector_etfs:

    df = get_data(etf)
    print(df)

    if len(df) < 5:
        raise RuntimeError(f"Not enough data returned for {etf}")

    for row in df.itertuples(index=False):
        price_rows.append((
            etf,
            row.datetime.strftime("%Y-%m-%d %H:%M:%S"),
            row.open,
            row.high,
            row.low,
            row.close,
            row.volume,
        ))

    last5 = df.tail(5)

    ret_5d = (last5["close"].iloc[-1] / last5["close"].iloc[0] - 1) * 100
    vol_5d = last5["volume"].sum()

    results.append({
        "ETF": etf,
        "5D Return %": round(ret_5d, 2),
        "5D Volume": int(vol_5d)
    })

df_results = pd.DataFrame(results)

print(df_results.sort_values("5D Return %", ascending=False))

conn = sqlite3.connect("trading.db")
cursor = conn.cursor()

expected_columns = ["etf_symbol", "datetime", "open", "high", "low", "close", "volume"]
cursor.execute("PRAGMA table_info(etf)")
existing_columns = [row[1] for row in cursor.fetchall()]

if existing_columns and existing_columns != expected_columns:
    cursor.execute("DROP TABLE etf")

cursor.execute("""
CREATE TABLE IF NOT EXISTS etf (
    etf_symbol TEXT,
    datetime TEXT,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume REAL
)
""")

cursor.executemany(
    "INSERT INTO etf (etf_symbol, datetime, open, high, low, close, volume) VALUES (?, ?, ?, ?, ?, ?, ?)",
    price_rows,
)

conn.commit()
conn.close()
