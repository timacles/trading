#!/usr/bin/python

import requests
import pandas as pd
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

    r = requests.get(url, params=params)

    # Raise error if HTTP request fails
    r.raise_for_status()

    data = r.json()

    if data.get("status") != "ok":
        raise RuntimeError(f"API error for {symbol}: {data}")

    df = pd.DataFrame(data["values"])

    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime")

    df["close"] = df["close"].astype(float)
    df["volume"] = df["volume"].astype(float)

    return df


results = []

for etf in sector_etfs:

    df = get_data(etf)
    print(df)

    if len(df) < 5:
        raise RuntimeError(f"Not enough data returned for {etf}")

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
