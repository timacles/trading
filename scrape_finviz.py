#!/usr/bin/env python3

import argparse
import logging
import re
from datetime import date

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import requests
import yaml

DEFAULT_URL = "https://finviz.com/groups.ashx?g=industry&v=140&o=relativevolume&st=d1"

EXPECTED_COLUMNS = {
    "no": "rank",
    "no.": "rank",
    "name": "industry",
    "perf_week": "perf_week",
    "perf_month": "perf_month",
    "perf_quart": "perf_quart",
    "perf_half": "perf_half",
    "perf_year": "perf_year",
    "perf_ytd": "perf_ytd",
    "avg_volume": "avg_volume",
    "rel_volume": "rel_volume",
    "change": "change",
    "volume": "volume",
}


def configure_logging():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def parse_args():
    parser = argparse.ArgumentParser(description="Scrape Finviz industry groups table into Postgres.")
    parser.add_argument("--url", default=DEFAULT_URL, help="Finviz groups URL to scrape.")
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to config.yaml with postgres settings (default: config.yaml).",
    )
    parser.add_argument("--db-host", default="localhost", help="Postgres host.")
    parser.add_argument("--db-port", type=int, default=5432, help="Postgres port.")
    parser.add_argument("--db-name", default="financials", help="Postgres database name.")
    parser.add_argument("--db-user", default=None, help="Postgres user (defaults to OS user).")
    parser.add_argument("--db-password", default=None, help="Postgres password (optional).")
    parser.add_argument(
        "--as-of-date",
        default=None,
        help="Override as-of date (YYYY-MM-DD). Defaults to today.",
    )
    return parser.parse_args()


def fetch_html(url):
    logging.info("Fetching %s", url)
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Connection": "keep-alive",
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text


def normalize_column_name(name):
    name = str(name).strip().lower()
    name = re.sub(r"[%$]", "", name)
    name = re.sub(r"\s+", "_", name)
    return name


def parse_number(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if text in {"", "-", "—"}:
        return None
    text = text.replace(",", "")

    is_percent = False
    if text.endswith("%"):
        is_percent = True
        text = text[:-1]

    multiplier = 1.0
    match = re.match(r"^([-+]?\d*\.?\d+)([KMBT])?$", text, re.IGNORECASE)
    if not match:
        return None

    number = float(match.group(1))
    suffix = match.group(2)
    if suffix:
        suffix = suffix.upper()
        if suffix == "K":
            multiplier = 1_000
        elif suffix == "M":
            multiplier = 1_000_000
        elif suffix == "B":
            multiplier = 1_000_000_000
        elif suffix == "T":
            multiplier = 1_000_000_000_000

    value = number * multiplier
    return value if not is_percent else value


def find_target_table(tables):
    for table in tables:
        normalized_cols = [normalize_column_name(col) for col in table.columns]
        if "name" in normalized_cols and "rel_volume" in normalized_cols:
            return table
    if tables:
        return tables[0]
    raise RuntimeError("No tables found in HTML.")


def map_and_validate_columns(table):
    table = table.copy()
    normalized = [normalize_column_name(col) for col in table.columns]
    mapped = []
    for col in normalized:
        if col not in EXPECTED_COLUMNS:
            raise RuntimeError(f"Unexpected column in table: {col}")
        mapped.append(EXPECTED_COLUMNS[col])
    table.columns = mapped

    required = {
        "rank",
        "industry",
        "perf_week",
        "perf_month",
        "perf_quart",
        "perf_half",
        "perf_year",
        "perf_ytd",
        "avg_volume",
        "rel_volume",
        "change",
        "volume",
    }
    missing = required - set(table.columns)
    if missing:
        raise RuntimeError(f"Missing expected columns: {sorted(missing)}")
    return table


def extract_rows(table):
    table = table.fillna("")
    rows = []
    for _, row in table.iterrows():
        industry = str(row["industry"]).strip()
        if not industry:
            continue
        rows.append(
            (
                int(parse_number(row["rank"])) if str(row["rank"]).strip() else None,
                industry,
                parse_number(row["perf_week"]),
                parse_number(row["perf_month"]),
                parse_number(row["perf_quart"]),
                parse_number(row["perf_half"]),
                parse_number(row["perf_year"]),
                parse_number(row["perf_ytd"]),
                parse_number(row["avg_volume"]),
                parse_number(row["rel_volume"]),
                parse_number(row["change"]),
                parse_number(row["volume"]),
            )
        )
    return rows


def open_db(args):
    config = {}
    if args.config:
        try:
            with open(args.config, "r") as config_file:
                config = yaml.safe_load(config_file) or {}
        except FileNotFoundError:
            logging.warning("Config file not found: %s (continuing with CLI/defaults)", args.config)

    db_config = config.get("postgres", {}) if isinstance(config, dict) else {}

    conn_kwargs = {
        "host": db_config.get("host", args.db_host),
        "port": db_config.get("port", args.db_port),
        "dbname": db_config.get("dbname", args.db_name),
    }
    user = args.db_user if args.db_user is not None else db_config.get("user")
    password = args.db_password if args.db_password is not None else db_config.get("password")
    if user:
        conn_kwargs["user"] = user
    if password:
        conn_kwargs["password"] = password
    return psycopg2.connect(**conn_kwargs)


def ensure_table(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS industry_flows (
                id BIGSERIAL PRIMARY KEY,
                as_of_date DATE NOT NULL,
                rank INTEGER,
                industry TEXT NOT NULL,
                perf_week DOUBLE PRECISION,
                perf_month DOUBLE PRECISION,
                perf_quart DOUBLE PRECISION,
                perf_half DOUBLE PRECISION,
                perf_year DOUBLE PRECISION,
                perf_ytd DOUBLE PRECISION,
                avg_volume DOUBLE PRECISION,
                rel_volume DOUBLE PRECISION,
                change DOUBLE PRECISION,
                volume DOUBLE PRECISION,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                UNIQUE (as_of_date, industry)
            )
            """
        )
    conn.commit()


def upsert_rows(conn, as_of_date_value, rows):
    values = [
        (as_of_date_value,) + row
        for row in rows
    ]

    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO industry_flows (
                as_of_date,
                rank,
                industry,
                perf_week,
                perf_month,
                perf_quart,
                perf_half,
                perf_year,
                perf_ytd,
                avg_volume,
                rel_volume,
                change,
                volume
            )
            VALUES %s
            ON CONFLICT (as_of_date, industry)
            DO UPDATE SET
                rank = EXCLUDED.rank,
                perf_week = EXCLUDED.perf_week,
                perf_month = EXCLUDED.perf_month,
                perf_quart = EXCLUDED.perf_quart,
                perf_half = EXCLUDED.perf_half,
                perf_year = EXCLUDED.perf_year,
                perf_ytd = EXCLUDED.perf_ytd,
                avg_volume = EXCLUDED.avg_volume,
                rel_volume = EXCLUDED.rel_volume,
                change = EXCLUDED.change,
                volume = EXCLUDED.volume
            """,
            values,
        )
    conn.commit()


def main():
    configure_logging()
    args = parse_args()

    as_of = date.fromisoformat(args.as_of_date) if args.as_of_date else date.today()
    html = fetch_html(args.url)
    tables = pd.read_html(html)
    table = find_target_table(tables)
    table = map_and_validate_columns(table)

    rows = extract_rows(table)
    logging.info("Parsed %s rows", len(rows))

    if not rows:
        raise RuntimeError("No rows parsed from the table.")

    conn = open_db(args)
    try:
        ensure_table(conn)
        upsert_rows(conn, as_of, rows)
        logging.info("Inserted %s rows into industry_flows", len(rows))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
