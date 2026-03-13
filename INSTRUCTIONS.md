# Momentum Scalper (1-5 Day Holds) - Instructions

## Overview
This project supports a short-term momentum scalper focused on 1-5 day holds in key ETFs. It uses a local Postgres database of OHLCV data to detect recent flows, momentum bursts, and mean reversion setups for entries over the next few days.

## Objectives
- Identify near-term momentum opportunities and mean reversion setups.
- Use recent OHLCV flows to score and rank candidates.
- Produce a short list of actionable entries with clear triggers and invalidation.
- Keep analysis fast, repeatable, and focused on the next 1-5 trading days.

## Data Source
- Local Postgres database stores OHLCV for key ETFs.
- Query the most recent data for each symbol and compute short-horizon signals.
- Use the newest available trading day as the anchor for all calculations.

## Core Signals (Short Horizon)
- **Momentum**: 1-3 day return, 5-day return, and distance from short-term moving average.
- **Mean Reversion**: z-score of 5-10 day returns, distance from 5/10 day moving average.
- **Flow Proxy**: volume spike vs. 5/20 day average, dollar volume acceleration.
- **Volatility**: 5-day ATR or range expansion vs. recent average.

## Setup Types
- **Momentum Continuation**: strong 1-3 day move with volume confirmation and trend alignment.
- **Mean Reversion**: extended move with exhaustion signals and a clear reversion target.
- **Breakout/Breakdown**: range compression followed by directional expansion with volume.

## Workflow (Daily or On-Demand)
1. **Fetch Data**
   - Query latest OHLCV for the ETF universe.
   - Ensure no missing recent bars; prefer the most recent completed session.

2. **Compute Signals**
   - Calculate short-term returns, moving averages, volume ratios, and range metrics.
   - Normalize to allow cross-ETF comparison.

3. **Rank Candidates**
   - Score by setup type (momentum vs. mean reversion) and confidence.
   - Keep a short list of top 5-10 candidates.

4. **Generate Trade Notes**
   - Entry trigger (price/level or condition).
   - Invalidation level (tight, consistent with 1-5 day hold).
   - Target or expected move window.
   - Time stop: exit if the move does not develop within 3-5 sessions.

## ETF Universe (Initial)
- **Broad Market**: SPY, QQQ, DIA, IWM
- **Sectors**: XLK, XLF, XLE, XLI, XLB, XLP, XLU, XLV, XLY
- **Rates/Credit**: TLT, LQD, HYG
- **Commodities**: GLD, SLV, USO
- **Volatility/Hedging (optional)**: VXX, SH, PSQ

## Output Format
- **Daily Scan Summary**: date, market tone, notable flows.
- **Candidates Table**: symbol, setup type, score, key signals.
- **Trade Notes**: entry trigger, invalidation, target/time stop.

## Notes
- Focus on recent flows and short-term structure, not long-term themes.
- Avoid overfitting: use a small, consistent feature set.
- This is a decision aid, not financial advice.
