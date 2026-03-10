#!/usr/bin/python

import requests
import pandas as pd
import sqlite3
import time
from datetime import datetime, timedelta

import pandas as pd
import requests


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )


def load_api_key(path="api.key"):
    logging.info("Loading API key from %s", path)
    with open(path, "r") as key_file:
        return key_file.read().strip()


def get_sector_etfs():
    return [
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
        "XLRE",
    ]


def get_start_date(days_back=7):
    return (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%dT00:00:00")


def is_rate_limit_error(response_data):
    return (
        response_data.get("status") == "error"
        and response_data.get("code") == 429
        and "run out of api credits for the current minute"
        in str(response_data.get("message", "")).lower()
    )


def fetch_symbol_data(symbol, api_key, start_date):
    logging.info("Requesting API data for %s", symbol)
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": symbol,
        "interval": "1day",
        "start_date": start_date,
        "timezone": "America/New_York",
        "apikey": api_key,
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


def payload_to_dataframe(payload):
    logging.info("Converting payload to dataframe")
    df = pd.DataFrame(payload["values"])
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
        raise RuntimeError(f"Not enough data returned for {symbol}")

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

    return {
        "ETF": symbol,
        "5D Return %": round(ret_5d, 2),
        "5D Volume": int(vol_5d),
    }


def process_symbol(conn, symbol, api_key, start_date):
    payload = fetch_symbol_data(symbol, api_key, start_date)
    df = payload_to_dataframe(payload)
    logging.info("Fetched dataframe for %s with %s rows", symbol, len(df))
    print(df)
    insert_symbol_rows(conn, symbol, df)
    return calculate_symbol_metrics(symbol, df)


def main():
    configure_logging()
    logging.info("Starting ETF stats pull")

    api_key = load_api_key()
    start_date = get_start_date()
    symbols = get_sector_etfs()

    conn = open_database("trading.db")
    try:
        ensure_etf_table(conn)

        results = []
        for symbol in symbols:
            logging.info("Processing symbol %s", symbol)
            result = process_symbol(conn, symbol, api_key, start_date)
            results.append(result)

        df_results = pd.DataFrame(results)
        logging.info("Completed processing all symbols")
        print(df_results.sort_values("5D Return %", ascending=False))
    finally:
        logging.info("Closing database connection")
        conn.close()


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
