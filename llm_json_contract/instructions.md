# Instructions For Analyzing `daily_report.json`

## Purpose
Use `daily_report.json` as a machine-readable snapshot of recent market performance and cross-asset positioning. Your job is to analyze the data and return a strict JSON report that helps guide short-term trading decisions.

The output must support:
- short-term positioning for 1-5 day moves
- secondary swing-trade opportunities
- market regime identification
- concrete allocation guidance by theme

Do not rewrite the input data. Interpret it, rank the signals, and produce an actionable view.

## Input Structure
Expect the input JSON to contain these top-level fields:
- `generated_at`
- `report_date`
- `market_direction`
- `breadth`
- `industry`
- `bond_treasury`
- `sector_etfs`

### `market_direction`
Treat this as a summary hint, not the final answer. Confirm or challenge it using the rest of the dataset.

### `breadth`
This section describes how broad the move is across the tracked universe.

Fields:
- `as_of_date`
- `advancers`
- `decliners`
- `avg_ret_1d`
- `avg_vol_ratio_5`
- `avg_range_ratio_5`

Interpretation rules:
- Very low advancers relative to decliners implies broad internal weakness.
- Strongly negative `avg_ret_1d` reinforces bearish short-term pressure.
- Elevated `avg_vol_ratio_5` and `avg_range_ratio_5` imply expansion in participation and volatility.
- Negative breadth with elevated volume and range is stronger evidence than price alone.

### `industry`
This section shows relative leadership and oversold mean-reversion candidates at the industry level.

Subsections:
- `top_momentum`
- `top_mean_reversion`

Use `top_momentum` to identify:
- leading industries
- persistent themes
- sectors with relative strength despite a weak tape

Use `top_mean_reversion` to identify:
- heavily sold industries that may bounce
- areas where downside is already extended
- tactical reversal candidates, not automatic bullish signals

Important:
- Favor themes that appear multiple times across related industries.
- If momentum leaders are concentrated in one macro theme, treat that as meaningful leadership.
- If mean-reversion names are deeply negative but still broad risk appetite is weak, frame them as tactical bounce candidates rather than regime leadership.

### `bond_treasury`
This section gives cross-asset context on duration, credit, and defensive behavior.

Key fields:
- `symbols`
- `rows`
- `volatility_averages`

Each row contains:
- `etf`
- `name`
- `ret_1d`
- `ret_3d`
- `ret_5d`
- `vol_ratio_5`
- `range_ratio_5`

Interpretation rules:
- Weakness in both duration and credit generally signals broad pressure across defensive and risk-sensitive fixed income.
- Larger losses in `TLT` suggest duration stress or rate pressure.
- Weakness in `HYG` and `JNK` suggests credit risk aversion.
- If both Treasuries and credit are weak, do not describe the environment as a clean flight-to-safety regime.
- Elevated bond volatility supports a cautionary stance even if equities show isolated leadership.

### `sector_etfs`
This section is the most directly actionable for near-term positioning.

Subsections:
- `top_momentum`
- `top_momentum_pos3d`
- `top_mean_reversion`

Use `top_momentum` to identify:
- strongest relative performers by score
- defensive or offensive leadership
- broad ETF-level confirmation of industry trends

Use `top_momentum_pos3d` to identify:
- near-term continuation candidates
- themes with positive follow-through over the last 3 days
- tradeable short-term strength for 1-5 day windows

Use `top_mean_reversion` to identify:
- stretched downside setups
- likely tactical rebound candidates
- oversold areas that may work only if selling pressure stabilizes

Interpretation rules:
- Prefer ETF themes that align with industry momentum leadership.
- Distinguish continuation setups from reversal setups.
- When both are present, rank continuation setups higher unless breadth or positioning strongly favors snapback trades.

## Synthesis Framework
You must synthesize all sections into one regime view. Do not produce a section-by-section recap only.

Determine:
- overall regime: `risk_on`, `risk_off`, `mixed`, or `transitional`
- directional bias for the next 1-5 days
- whether the best opportunities are momentum continuation, tactical mean reversion, or a mix
- which themes have the strongest cross-confirmation
- which signals conflict with the dominant view

Ranking logic:
1. Breadth and market-wide participation define the baseline regime.
2. Sector ETF continuation data defines the best short-term trade direction.
3. Industry momentum confirms whether leadership is concentrated or broad.
4. Bond and credit behavior confirm whether risk appetite is healthy, stressed, or mixed.
5. Mean-reversion lists are secondary unless they are extreme and other data suggests selling is exhausted.

Cross-confirmation rules:
- A theme is stronger when it appears in both `industry.top_momentum` and `sector_etfs.top_momentum_pos3d`.
- A theme is weaker when it has isolated strength but breadth is very poor.
- A mean-reversion candidate is stronger when downside is extreme and the regime is `mixed` or `transitional`.
- In a strongly `risk_off` regime, avoid overstating bounce setups.

## Trading Objective
Optimize the report for:
- short-term trades over the next 1-5 trading days
- swing opportunities only as a secondary layer

Your output should help answer:
- What is the market rewarding right now?
- What is the market punishing right now?
- Is it better to press momentum or buy oversold reversals?
- How should capital be allocated across themes in the immediate term?

## Required Output
Return strict JSON only.

Rules:
- No Markdown
- No prose outside JSON
- No extra top-level keys beyond the schema below
- Every field must be populated
- Every array field must always be present, even when empty
- Use arrays when multiple signals or themes apply
- Keep explanations concise but specific
- Use the exact key names shown below
- Preserve the exact top-level key order shown below
- Preserve the exact nested key order shown below for `market_positioning`, `concrete_allocation_framework`, and each `allocation_buckets` item
- Do not use `null`
- Do not use empty strings
- `report_date` must match the input `report_date`
- `confidence` must be a number from `0.0` to `1.0`
- `leadership_themes` must contain 1 to 7 items
- `reversal_themes` must contain 0 to 7 items
- `supporting_signals` must contain 3 to 8 items
- `conflicting_signals` must contain 0 to 5 items
- `preferred_trade_types` must contain 1 to 6 items
- `allocation_buckets` must contain 3 to 6 items
- `evidence` in each allocation bucket must contain 2 to 4 items
- If no valid item exists for an optional analytical category, return an empty array rather than omitting the field
- `exposure_band` must be one of the exact strings listed below
- Keep all strings renderer-safe: plain text only, no Markdown, no code fences, no embedded JSON

```json
{
  "report_date": "YYYY-MM-DD",
  "market_positioning": {
    "regime": "risk_on | risk_off | mixed | transitional",
    "directional_bias": "bullish | bearish | neutral | mixed",
    "confidence": 0.0,
    "short_term_view_1_5d": "string",
    "swing_view": "string",
    "preferred_trade_style": "momentum | mean_reversion | mixed",
    "leadership_themes": ["string"],
    "reversal_themes": ["string"],
    "supporting_signals": ["string"],
    "conflicting_signals": ["string"]
  },
  "concrete_allocation_framework": {
    "net_exposure": "net_long | net_short | selective_long | selective_short | market_neutral | mixed",
    "preferred_trade_types": ["string"],
    "allocation_buckets": [
      {
        "theme": "string",
        "etfs": ["string"],
        "direction": "long | short | neutral",
        "exposure_band": "0-10% | 10-20% | 20-30% | 30-40%",
        "time_horizon": "1-5d | swing",
        "setup_type": "continuation | mean_reversion | hedge | watchlist",
        "evidence": ["string"],
        "risk_or_invalidation": "string"
      }
    ]
  }
}
```

## Field Guidance
### `market_positioning`
- `regime`: choose the dominant market state from the full dataset.
- `directional_bias`: reflect the likely direction of tradable risk over the next 1-5 days.
- `confidence`: number from `0.0` to `1.0`.
- `short_term_view_1_5d`: one concise statement about the immediate opportunity set.
- `swing_view`: one concise statement about the secondary multi-day setup environment.
- `preferred_trade_style`: choose the style with the best expected edge.
- `leadership_themes`: themes currently showing relative strength.
- `reversal_themes`: oversold themes worth monitoring for tactical bounces.
- `supporting_signals`: the strongest evidence behind the main stance.
- `conflicting_signals`: the strongest evidence that argues against overconfidence.

Cardinality rules:
- `leadership_themes`: 1 to 7 short theme labels
- `reversal_themes`: 0 to 7 short theme labels
- `supporting_signals`: 3 to 8 concise evidence statements
- `conflicting_signals`: 0 to 5 concise evidence statements

### `concrete_allocation_framework`
- `net_exposure`: define the broad capital posture.
- `preferred_trade_types`: list the trade types best suited to current conditions.
- `allocation_buckets`: allocate attention and risk by theme, not by single ticker unless the ETF/theme itself is the vehicle.
- `etfs`: include 1 or more concrete ETF tickers for each allocation bucket that express the theme.

Allocation rules:
- Use 3 to 6 buckets.
- Prefer thematic buckets such as `energy momentum`, `commodity continuation`, `defensive hedge`, `oversold rebound watchlist`, or `broad index short bias`.
- Every bucket must include an `etfs` array with 1 or more ticker symbols.
- Use the `etfs` list to map each bucket to the specific tradable vehicles that best express the theme.
- Hedge and watchlist buckets still need ETF symbols when the idea is expressed through ETFs.
- Use larger exposure bands only when cross-confirmation is strong.
- If conviction is low, keep buckets smaller and include more `watchlist` or `hedge` framing.
- Include at least one risk control or hedge bucket when the regime is `risk_off` or volatility is elevated.
- `preferred_trade_types` must contain 1 to 6 items.
- Each bucket `evidence` array must contain 2 to 4 concrete supporting statements.
- `risk_or_invalidation` must always be a single non-empty sentence.

Allowed values:
- `regime`: `risk_on`, `risk_off`, `mixed`, `transitional`
- `directional_bias`: `bullish`, `bearish`, `neutral`, `mixed`
- `preferred_trade_style`: `momentum`, `mean_reversion`, `mixed`
- `net_exposure`: `net_long`, `net_short`, `selective_long`, `selective_short`, `market_neutral`, `mixed`
- `direction`: `long`, `short`, `neutral`
- `exposure_band`: `0-10%`, `10-20%`, `20-30%`, `30-40%`
- `time_horizon`: `1-5d`, `swing`
- `setup_type`: `continuation`, `mean_reversion`, `hedge`, `watchlist`

Empty-state rules:
- If there are no strong reversal setups, return `"reversal_themes": []`.
- If there are no meaningful conflicting signals, return `"conflicting_signals": []`.
- Do not fabricate weak ideas just to avoid empty arrays.

Formatting rules:
- Use plain JSON strings only.
- Do not include percent signs inside `confidence`.
- Do not include numbering prefixes in list items.
- Keep theme labels short and reusable for UI display.
- Keep evidence and signal strings concise enough for direct rendering in HTML.

## Guardrails
- Do not invent macro catalysts, earnings narratives, or policy explanations not present in the data.
- Do not claim certainty.
- Do not turn every oversold asset into a buy.
- Do not ignore weak breadth just because a few themes have positive momentum.
- Do not describe the environment as healthy risk-on if bonds, credit, and breadth are all deteriorating.
- If signals conflict, reduce confidence and shift toward selective exposure.

## Decision Rules
- If breadth is strongly negative and participation is weak, default toward `risk_off` unless multiple other sections clearly disagree.
- If energy, commodities, or related industries lead while broad equities weaken, describe that as narrow leadership rather than broad bullishness.
- If `top_momentum_pos3d` is populated by only a few concentrated themes, treat those as tactical opportunities rather than proof of broad market strength.
- If mean-reversion candidates are dominated by deeply sold assets with poor breadth, classify them as bounce watchlists unless there is direct stabilization evidence.
- If bond ETFs and credit ETFs are both under pressure, keep a defensive or selective tone.

## Quality Standard
The final JSON should make it easy for another machine or agent to answer:
- What regime are we in?
- What themes deserve capital now?
- What themes are only tactical reversals?
- How aggressive should positioning be?
- What would invalidate the current trade posture?

Be decisive, but scale conviction to the evidence.
