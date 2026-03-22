#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    import jsonschema
except ImportError as exc:  # pragma: no cover - dependency failure path
    raise SystemExit(
        "Missing dependency: jsonschema. Install it in your environment or run this script "
        "with the project virtualenv."
    ) from exc


STYLE = """
:root {
  --bg: #0d1117;
  --bg-deep: #090c12;
  --panel: rgba(18, 24, 34, 0.86);
  --panel-strong: rgba(23, 30, 42, 0.94);
  --border: rgba(167, 185, 210, 0.14);
  --text: #edf3ff;
  --muted: #9daec9;
  --shadow: 0 26px 60px rgba(0, 0, 0, 0.34);
  --bullish: #5ad08c;
  --bearish: #ff7d6e;
  --neutral: #e6c15a;
  --mixed: #a78bfa;
  --risk-on: #5ad08c;
  --risk-off: #ff8a78;
  --transitional: #e6c15a;
  --long: #5ad08c;
  --short: #ff7d6e;
  --watch: #8ea2ff;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  font-family: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", Georgia, serif;
  color: var(--text);
  background:
    radial-gradient(circle at top left, rgba(43, 92, 146, 0.26), transparent 32%),
    radial-gradient(circle at top right, rgba(29, 143, 100, 0.18), transparent 30%),
    radial-gradient(circle at bottom, rgba(90, 53, 123, 0.22), transparent 34%),
    linear-gradient(180deg, #101620 0%, var(--bg) 45%, var(--bg-deep) 100%);
}

.shell {
  max-width: 1220px;
  margin: 0 auto;
  padding: 32px 20px 48px;
}

.hero {
  background: linear-gradient(135deg, rgba(17, 29, 44, 0.98), rgba(28, 54, 70, 0.94));
  color: #f4f8ff;
  border-radius: 28px;
  padding: 28px 30px;
  box-shadow: var(--shadow);
  position: relative;
  overflow: hidden;
}

.hero::after {
  content: "";
  position: absolute;
  inset: auto -80px -120px auto;
  width: 280px;
  height: 280px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(121, 174, 255, 0.18), transparent 65%);
}

.eyebrow {
  margin: 0 0 6px;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  font: 600 0.75rem/1.2 "Avenir Next", "Segoe UI", sans-serif;
  opacity: 0.75;
}

h1, h2, h3, p { margin: 0; }

.hero h1 {
  font-size: clamp(2rem, 4vw, 3.5rem);
  line-height: 0.95;
  max-width: 9ch;
}

.hero-grid {
  margin-top: 24px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 14px;
}

.hero-stat,
.panel,
.bucket {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 22px;
  box-shadow: var(--shadow);
}

.hero-stat {
  padding: 16px 18px;
  color: var(--text);
}

.label {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 999px;
  font: 700 0.78rem/1 "Avenir Next", "Segoe UI", sans-serif;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.label.regime-risk-off, .label.direction-bearish, .label.direction-short, .label.setup-hedge {
  background: rgba(255, 125, 110, 0.14);
  color: var(--bearish);
}

.label.regime-risk-on, .label.direction-bullish, .label.direction-long, .label.setup-continuation {
  background: rgba(90, 208, 140, 0.14);
  color: var(--bullish);
}

.label.regime-mixed, .label.direction-mixed, .label.style-mixed, .label.exposure-market-neutral {
  background: rgba(167, 139, 250, 0.15);
  color: var(--mixed);
}

.label.regime-transitional, .label.direction-neutral, .label.style-mean-reversion, .label.setup-mean-reversion {
  background: rgba(230, 193, 90, 0.16);
  color: var(--neutral);
}

.label.style-momentum, .label.exposure-net-long, .label.exposure-selective-long {
  background: rgba(90, 208, 140, 0.14);
  color: var(--bullish);
}

.label.exposure-net-short, .label.exposure-selective-short {
  background: rgba(255, 125, 110, 0.14);
  color: var(--bearish);
}

.label.setup-watchlist {
  background: rgba(142, 162, 255, 0.14);
  color: var(--watch);
}

.label.setup-hedge, .label.exposure-mixed {
  background: rgba(157, 173, 201, 0.12);
  color: #d1daea;
}

.stat-title,
.section-title,
.kicker {
  font: 700 0.86rem/1.2 "Avenir Next", "Segoe UI", sans-serif;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
}

.stat-value {
  margin-top: 12px;
  font-size: 1.35rem;
  font-weight: 700;
  line-height: 1.15;
}

.section {
  margin-top: 22px;
}

.panel {
  padding: 24px;
}

.section-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.section-title {
  color: var(--text);
}

.positioning-grid,
.signals-grid,
.bucket-grid {
  display: grid;
  gap: 18px;
}

.positioning-grid {
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
}

.signals-grid {
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
}

.bucket-grid {
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
}

.narrative {
  min-height: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.narrative p,
.bucket p,
li {
  font-size: 1rem;
  line-height: 1.55;
}

.table-shell {
  overflow-x: auto;
  border: 1px solid var(--border);
  border-radius: 18px;
  background: rgba(12, 18, 27, 0.72);
}

table {
  width: 100%;
  min-width: 720px;
  border-collapse: collapse;
}

th,
td {
  padding: 14px 16px;
  text-align: left;
  vertical-align: top;
  border-bottom: 1px solid var(--border);
}

th {
  font: 700 0.82rem/1.2 "Avenir Next", "Segoe UI", sans-serif;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
  background: rgba(255, 255, 255, 0.02);
}

td {
  font-size: 0.98rem;
  line-height: 1.5;
}

tbody tr:last-child td {
  border-bottom: 0;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 14px;
}

.chip {
  display: inline-flex;
  align-items: center;
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(31, 40, 56, 0.96);
  border: 1px solid var(--border);
  font: 600 0.92rem/1 "Avenir Next", "Segoe UI", sans-serif;
  color: var(--text);
}

ul {
  margin: 16px 0 0;
  padding-left: 20px;
}

li + li {
  margin-top: 10px;
}

.bucket {
  padding: 22px;
  background: var(--panel-strong);
}

.bucket-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.bucket-title {
  font-size: 1.4rem;
  line-height: 1.05;
}

.bucket-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

.bucket-block + .bucket-block {
  margin-top: 18px;
}

.risk-note {
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(255, 125, 110, 0.08);
  border: 1px solid rgba(255, 125, 110, 0.16);
}

.muted {
  color: var(--muted);
}

@media (max-width: 720px) {
  .shell {
    padding: 18px 14px 32px;
  }

  .hero,
  .panel,
  .bucket {
    border-radius: 20px;
  }

  .hero {
    padding: 22px 18px;
  }

  .panel,
  .bucket {
    padding: 18px;
  }
}
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a market analysis JSON report into a standalone HTML dashboard."
    )
    parser.add_argument("-i", "--input", required=True, type=Path, help="Path to the report JSON file.")
    parser.add_argument(
        "-s",
        "--schema",
        type=Path,
        default=Path("report_schema.json"),
        help="Path to the JSON schema file. Defaults to report_schema.json.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Path for the generated HTML file. Defaults to trade_report_ddMonYY.html based on report_date.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"File not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc.msg} at line {exc.lineno} column {exc.colno}") from exc


def validate_report(report: dict, schema: dict) -> None:
    try:
        jsonschema.validate(instance=report, schema=schema)
    except jsonschema.ValidationError as exc:
        path = ".".join(str(part) for part in exc.absolute_path)
        location = path or "<root>"
        raise SystemExit(f"Schema validation failed at {location}: {exc.message}") from exc


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def humanize(value: str) -> str:
    parts = value.replace("%", " %").replace("_", " ").split()
    return " ".join(part.upper() if len(part) <= 3 and any(ch.isdigit() for ch in part) else part.capitalize() for part in parts)


def format_date(date_text: str) -> str:
    return datetime.strptime(date_text, "%Y-%m-%d").strftime("%B %d, %Y")


def percent(value: float) -> str:
    return f"{value * 100:.0f}%"


def label(text: str, kind: str, value: str) -> str:
    cls = f"label {kind}-{value}"
    return f'<span class="{esc(cls)}">{esc(humanize(text))}</span>'


def chips(items: list[str]) -> str:
    if not items:
        return '<p class="muted">None highlighted.</p>'
    return '<div class="chips">' + "".join(f'<span class="chip">{esc(item)}</span>' for item in items) + "</div>"


def bullet_list(items: list[str], empty_text: str) -> str:
    if not items:
        return f'<p class="muted">{esc(empty_text)}</p>'
    return "<ul>" + "".join(f"<li>{esc(item)}</li>" for item in items) + "</ul>"


def strategy_text(bucket: dict) -> str:
    return f"{humanize(bucket['setup_type'])} {humanize(bucket['direction'])}"


def render_allocation_table(buckets: list[dict]) -> str:
    rows = []
    for bucket in buckets:
        rows.append(
            f"""
            <tr>
              <td>{esc(bucket["theme"])}</td>
              <td>{esc(strategy_text(bucket))}</td>
              <td>{esc(", ".join(bucket["etfs"]))}</td>
              <td>{esc(bucket["exposure_band"])}</td>
            </tr>
            """
        )
    return f"""
    <div class="table-shell">
      <table>
        <thead>
          <tr>
            <th>Allocation Bucket</th>
            <th>Strategy</th>
            <th>Specific Symbols</th>
            <th>Alloc %</th>
          </tr>
        </thead>
        <tbody>
          {''.join(rows)}
        </tbody>
      </table>
    </div>
    """


def render_bucket(bucket: dict) -> str:
    direction = bucket["direction"]
    setup_type = bucket["setup_type"]
    meta = [
        label(direction, "direction", direction),
        f'<span class="chip">{esc(bucket["exposure_band"])}</span>',
        f'<span class="chip">{esc(bucket["time_horizon"])}</span>',
        label(setup_type, "setup", setup_type),
    ]
    return f"""
    <article class="bucket">
      <div class="bucket-head">
        <div>
          <p class="kicker">Allocation Bucket</p>
          <h3 class="bucket-title">{esc(bucket["theme"])}</h3>
        </div>
        {label(direction, "direction", direction)}
      </div>
      <div class="bucket-meta">{''.join(meta)}</div>
      <div class="bucket-block">
        <p class="stat-title">Specific Symbols</p>
        <p>{esc(", ".join(bucket["etfs"]))}</p>
      </div>
      <div class="bucket-block">
        <p class="stat-title">Evidence</p>
        {bullet_list(bucket["evidence"], "No evidence provided.")}
      </div>
      <div class="bucket-block risk-note">
        <p class="stat-title">Risk / Invalidation</p>
        <p>{esc(bucket["risk_or_invalidation"])}</p>
      </div>
    </article>
    """


def render_html(report: dict) -> str:
    positioning = report["market_positioning"]
    framework = report["concrete_allocation_framework"]
    allocation_table = render_allocation_table(framework["allocation_buckets"])

    hero_stats = [
        ("Regime", label(positioning["regime"], "regime", positioning["regime"])),
        ("Directional Bias", label(positioning["directional_bias"], "direction", positioning["directional_bias"])),
        ("Confidence", esc(percent(positioning["confidence"]))),
        ("Trade Style", label(positioning["preferred_trade_style"], "style", positioning["preferred_trade_style"])),
        ("Net Exposure", label(framework["net_exposure"], "exposure", framework["net_exposure"])),
    ]

    hero_cards = "".join(
        f"""
        <div class="hero-stat">
          <p class="stat-title">{esc(title)}</p>
          <div class="stat-value">{value}</div>
        </div>
        """
        for title, value in hero_stats
    )

    bucket_cards = "".join(render_bucket(bucket) for bucket in framework["allocation_buckets"])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Market Analysis Report - {esc(report["report_date"])}</title>
  <style>{STYLE}</style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <p class="eyebrow">Macro Dashboard</p>
      <h1>Market Analysis Report</h1>
      <p class="muted" style="color: rgba(255,247,240,0.78); margin-top: 12px;">Report date: {esc(format_date(report["report_date"]))}</p>
      <div class="hero-grid">{hero_cards}</div>
    </section>

    <section class="section panel">
      <div class="section-head">
        <h2 class="section-title">Positioning Outlook</h2>
        <p class="muted">Short-term posture and swing context</p>
      </div>
      <div class="positioning-grid">
        <article class="narrative">
          <p class="kicker">1-5 Day View</p>
          <p>{esc(positioning["short_term_view_1_5d"])}</p>
        </article>
        <article class="narrative">
          <p class="kicker">Swing View</p>
          <p>{esc(positioning["swing_view"])}</p>
        </article>
      </div>
    </section>

    <section class="section panel">
      <div class="section-head">
        <h2 class="section-title">Theme Map</h2>
        <p class="muted">Leadership and reversal candidates</p>
      </div>
      <p class="kicker">Leadership Themes</p>
      {chips(positioning["leadership_themes"])}
      <p class="kicker" style="margin-top: 20px;">Reversal Themes</p>
      {chips(positioning["reversal_themes"])}
    </section>

    <section class="section signals-grid">
      <article class="panel">
        <div class="section-head">
          <h2 class="section-title">Supporting Signals</h2>
          <p class="muted">What confirms the stance</p>
        </div>
        {bullet_list(positioning["supporting_signals"], "No supporting signals provided.")}
      </article>
      <article class="panel">
        <div class="section-head">
          <h2 class="section-title">Conflicting Signals</h2>
          <p class="muted">What could interrupt the base case</p>
        </div>
        {bullet_list(positioning["conflicting_signals"], "No conflicting signals provided.")}
      </article>
    </section>

    <section class="section panel">
      <div class="section-head">
        <h2 class="section-title">Allocation Table</h2>
        <p class="muted">Bucket, strategy, symbols, and allocation</p>
      </div>
      {allocation_table}
    </section>

    <section class="section panel">
      <div class="section-head">
        <div>
          <h2 class="section-title">Allocation Framework</h2>
          <p class="muted" style="margin-top: 6px;">Preferred trade types: {esc(", ".join(framework["preferred_trade_types"]))}</p>
        </div>
        {label(framework["net_exposure"], "exposure", framework["net_exposure"])}
      </div>
      <div class="bucket-grid">
        {bucket_cards}
      </div>
    </section>
  </main>
</body>
</html>
"""


def main() -> int:
    args = parse_args()
    report = load_json(args.input)
    schema = load_json(args.schema)
    validate_report(report, schema)
    html_output = render_html(report)
    output_path = args.output or Path(
        f"trade_report_{datetime.strptime(report['report_date'], '%Y-%m-%d').strftime('%d%b%y')}.html"
    )
    output_path.write_text(html_output, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
