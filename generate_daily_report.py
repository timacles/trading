#!/usr/bin/env python3

import argparse
import datetime as dt
import logging
from pathlib import Path

import psycopg2
import yaml


REPORT_TEMPLATE = """# Daily Flow Report — {report_date}

## Market Direction
{market_direction}

## Breadth Summary
- Advancers: {advancers}
- Decliners: {decliners}
- Average 1D Return: {avg_ret_1d:.2%}
- Average Volume Ratio (5D): {avg_vol_ratio_5:.2f}
- Average Range Ratio (5D): {avg_range_ratio_5:.2f}

## Top Momentum Score (Today)
| ETF | 1D Ret | 3D Ret | 5D Ret | Vol Ratio 5D | Range Ratio 5D | Momentum Score |
| --- | --- | --- | --- | --- | --- | --- |
{momentum_rows}

## Top Mean Reversion Score (Today)
| ETF | 1D Ret | 3D Ret | 5D Ret | Dist MA(5) | ZScore(5D) | Mean Reversion Score |
| --- | --- | --- | --- | --- | --- | --- |
{mean_reversion_rows}
"""


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )


def load_config(path="config.yaml"):
    with open(path, "r") as config_file:
        return yaml.safe_load(config_file)


def open_database(config):
    return psycopg2.connect(**config["postgres"])


def fetch_one(cursor, query, params=None):
    cursor.execute(query, params or ())
    return cursor.fetchone()


def fetch_all(cursor, query, params=None):
    cursor.execute(query, params or ())
    return cursor.fetchall()


def get_latest_date(cursor):
    row = fetch_one(cursor, "SELECT MAX(date) FROM etf_flows;")
    return row[0]


def get_breadth(cursor, report_date):
    query = """
        SELECT
            SUM(CASE WHEN ret_1d > 0 THEN 1 ELSE 0 END) AS advancers,
            SUM(CASE WHEN ret_1d < 0 THEN 1 ELSE 0 END) AS decliners,
            AVG(ret_1d) AS avg_ret_1d,
            AVG(vol_ratio_5) AS avg_vol_ratio_5,
            AVG(range_ratio_5) AS avg_range_ratio_5
        FROM v_etf_signals
        WHERE date = %s
    """
    return fetch_one(cursor, query, (report_date,))


def get_top_momentum(cursor, report_date, limit):
    query = """
        SELECT
            etf,
            ret_1d,
            ret_3d,
            ret_5d,
            vol_ratio_5,
            range_ratio_5,
            momentum_score
        FROM v_etf_signal_rank
        WHERE date = %s
        ORDER BY momentum_score DESC NULLS LAST
        LIMIT %s
    """
    return fetch_all(cursor, query, (report_date, limit))


def get_top_mean_reversion(cursor, report_date, limit):
    query = """
        SELECT
            etf,
            ret_1d,
            ret_3d,
            ret_5d,
            dist_ma_5,
            zscore_5d,
            mean_reversion_score
        FROM v_etf_signal_rank
        WHERE date = %s
        ORDER BY mean_reversion_score DESC NULLS LAST
        LIMIT %s
    """
    return fetch_all(cursor, query, (report_date, limit))


def format_pct(value):
    if value is None:
        return "n/a"
    return f"{value:.2%}"


def format_num(value, precision=2):
    if value is None:
        return "n/a"
    return f"{value:.{precision}f}"


def build_momentum_rows(rows):
    lines = []
    for row in rows:
        etf, ret_1d, ret_3d, ret_5d, vol_ratio_5, range_ratio_5, score = row
        lines.append(
            f"| {etf} | {format_pct(ret_1d)} | {format_pct(ret_3d)} | "
            f"{format_pct(ret_5d)} | {format_num(vol_ratio_5)} | "
            f"{format_num(range_ratio_5)} | {format_num(score, 3)} |"
        )
    return "\n".join(lines) if lines else "| n/a | n/a | n/a | n/a | n/a | n/a | n/a |"


def build_mean_reversion_rows(rows):
    lines = []
    for row in rows:
        etf, ret_1d, ret_3d, ret_5d, dist_ma_5, zscore_5d, score = row
        lines.append(
            f"| {etf} | {format_pct(ret_1d)} | {format_pct(ret_3d)} | "
            f"{format_pct(ret_5d)} | {format_num(dist_ma_5, 4)} | "
            f"{format_num(zscore_5d, 3)} | {format_num(score, 3)} |"
        )
    return "\n".join(lines) if lines else "| n/a | n/a | n/a | n/a | n/a | n/a | n/a |"


def classify_market(advancers, decliners, avg_ret_1d):
    if advancers is None or decliners is None or avg_ret_1d is None:
        return "Insufficient data to classify market direction."

    if advancers > decliners and avg_ret_1d > 0:
        return "Risk-on / bullish. Breadth and average returns are positive."
    if decliners > advancers and avg_ret_1d < 0:
        return "Risk-off / bearish. Breadth and average returns are negative."
    return "Mixed / choppy. Breadth and average returns are inconclusive."


def parse_args():
    parser = argparse.ArgumentParser(description="Generate daily ETF flow report.")
    parser.add_argument(
        "--output",
        default="daily_report.md",
        help="Output markdown path.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=5,
        help="Number of top momentum and mean reversion rows.",
    )
    return parser.parse_args()


def main():
    configure_logging()
    args = parse_args()

    config = load_config()
    report_path = Path(args.output)

    conn = open_database(config)
    try:
        with conn.cursor() as cursor:
            report_date = get_latest_date(cursor)
            if report_date is None:
                raise RuntimeError("No data found in etf_flows.")

            breadth = get_breadth(cursor, report_date)
            advancers, decliners, avg_ret_1d, avg_vol_ratio_5, avg_range_ratio_5 = breadth

            market_direction = classify_market(advancers, decliners, avg_ret_1d)

            momentum_rows = build_momentum_rows(
                get_top_momentum(cursor, report_date, args.top)
            )
            mean_reversion_rows = build_mean_reversion_rows(
                get_top_mean_reversion(cursor, report_date, args.top)
            )

            report = REPORT_TEMPLATE.format(
                report_date=report_date.strftime("%Y-%m-%d"),
                market_direction=market_direction,
                advancers=advancers or 0,
                decliners=decliners or 0,
                avg_ret_1d=avg_ret_1d or 0.0,
                avg_vol_ratio_5=avg_vol_ratio_5 or 0.0,
                avg_range_ratio_5=avg_range_ratio_5 or 0.0,
                momentum_rows=momentum_rows,
                mean_reversion_rows=mean_reversion_rows,
            )

            report_path.write_text(report)
            logging.info("Wrote report to %s", report_path)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
