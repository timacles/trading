#!/usr/bin/env python3

import argparse
import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from generate_daily_report import (
    classify_market,
    configure_logging,
    get_bond_stats,
    get_breadth,
    get_latest_date,
    get_latest_industry_date,
    get_top_industry_momentum,
    get_top_industry_reversion,
    get_top_mean_reversion,
    get_top_momentum,
    get_top_momentum_pos3d,
    get_volatility_averages,
    load_config,
    open_database,
)


def parse_args():
    parser = argparse.ArgumentParser(description="Generate daily ETF flow report (JSON).")
    parser.add_argument(
        "--output",
        default="daily_report.json",
        help="Output JSON path.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of top momentum and mean reversion rows.",
    )
    return parser.parse_args()


def to_float(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return value


def to_int(value):
    if value is None:
        return None
    return int(value)


def to_iso_date(value):
    if value is None:
        return None
    return value.isoformat()


def build_momentum_payload(rows):
    payload = []
    for row in rows:
        etf, etf_name, ret_1d, ret_3d, ret_5d, vol_ratio_5, range_ratio_5, score = row
        payload.append(
            {
                "etf": etf,
                "name": etf_name,
                "ret_1d": to_float(ret_1d),
                "ret_3d": to_float(ret_3d),
                "ret_5d": to_float(ret_5d),
                "vol_ratio_5": to_float(vol_ratio_5),
                "range_ratio_5": to_float(range_ratio_5),
                "momentum_score": to_float(score),
            }
        )
    return payload


def build_mean_reversion_payload(rows):
    payload = []
    for row in rows:
        etf, etf_name, ret_1d, ret_3d, ret_5d, dist_ma_5, zscore_5d, score = row
        payload.append(
            {
                "etf": etf,
                "name": etf_name,
                "ret_1d": to_float(ret_1d),
                "ret_3d": to_float(ret_3d),
                "ret_5d": to_float(ret_5d),
                "dist_ma_5": to_float(dist_ma_5),
                "zscore_5d": to_float(zscore_5d),
                "mean_reversion_score": to_float(score),
            }
        )
    return payload


def build_bond_payload(rows):
    payload = []
    for row in rows:
        etf, etf_name, ret_1d, ret_3d, ret_5d, vol_ratio_5, range_ratio_5 = row
        payload.append(
            {
                "etf": etf,
                "name": etf_name,
                "ret_1d": to_float(ret_1d),
                "ret_3d": to_float(ret_3d),
                "ret_5d": to_float(ret_5d),
                "vol_ratio_5": to_float(vol_ratio_5),
                "range_ratio_5": to_float(range_ratio_5),
            }
        )
    return payload


def build_industry_momentum_payload(rows):
    payload = []
    for row in rows:
        industry, perf_week, perf_month, rel_volume, change, score = row
        payload.append(
            {
                "industry": industry,
                "perf_week": to_float(perf_week),
                "perf_month": to_float(perf_month),
                "rel_volume": to_float(rel_volume),
                "change": to_float(change),
                "momentum_score": to_float(score),
            }
        )
    return payload


def build_industry_reversion_payload(rows):
    payload = []
    for row in rows:
        industry, perf_week, perf_quart, rel_volume, change, score = row
        payload.append(
            {
                "industry": industry,
                "perf_week": to_float(perf_week),
                "perf_quart": to_float(perf_quart),
                "rel_volume": to_float(rel_volume),
                "change": to_float(change),
                "mean_reversion_score": to_float(score),
            }
        )
    return payload


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

            industry_date = get_latest_industry_date(cursor)
            bond_symbols = ["AGG", "BND", "TLT", "LQD", "HYG", "JNK", "TIP", "EMB"]

            breadth = get_breadth(cursor, report_date)
            advancers, decliners, avg_ret_1d, avg_vol_ratio_5, avg_range_ratio_5 = breadth

            market_direction = classify_market(advancers, decliners, avg_ret_1d)

            bond_stats = get_bond_stats(cursor, report_date, bond_symbols)
            volatility_averages = get_volatility_averages(cursor, report_date)
            avg_range_1d, avg_range_avg_5, avg_range_ratio_5 = volatility_averages

            momentum_rows = get_top_momentum(cursor, report_date, args.top)
            momentum_pos3d_rows = get_top_momentum_pos3d(cursor, report_date, args.top)
            mean_reversion_rows = get_top_mean_reversion(cursor, report_date, args.top)

            if industry_date:
                industry_momentum_rows = get_top_industry_momentum(
                    cursor, industry_date, args.top
                )
                industry_reversion_rows = get_top_industry_reversion(
                    cursor, industry_date, args.top
                )
            else:
                industry_momentum_rows = []
                industry_reversion_rows = []

            payload = {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "report_date": to_iso_date(report_date),
                "market_direction": market_direction,
                "breadth": {
                    "as_of_date": to_iso_date(report_date),
                    "advancers": to_int(advancers),
                    "decliners": to_int(decliners),
                    "avg_ret_1d": to_float(avg_ret_1d),
                    "avg_vol_ratio_5": to_float(avg_vol_ratio_5),
                    "avg_range_ratio_5": to_float(avg_range_ratio_5),
                },
                "industry": {
                    "as_of_date": to_iso_date(industry_date),
                    "top_momentum": build_industry_momentum_payload(
                        industry_momentum_rows
                    ),
                    "top_mean_reversion": build_industry_reversion_payload(
                        industry_reversion_rows
                    ),
                },
                "bond_treasury": {
                    "as_of_date": to_iso_date(report_date),
                    "symbols": bond_symbols,
                    "rows": build_bond_payload(bond_stats),
                    "volatility_averages": {
                        "avg_range_1d": to_float(avg_range_1d),
                        "avg_range_avg_5": to_float(avg_range_avg_5),
                        "avg_range_ratio_5": to_float(avg_range_ratio_5),
                    },
                },
                "sector_etfs": {
                    "as_of_date": to_iso_date(report_date),
                    "top_momentum": build_momentum_payload(momentum_rows),
                    "top_momentum_pos3d": build_momentum_payload(momentum_pos3d_rows),
                    "top_mean_reversion": build_mean_reversion_payload(mean_reversion_rows),
                },
            }

            report_path.write_text(json.dumps(payload, indent=2, sort_keys=False))
            logging.info("Wrote report to %s", report_path)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
