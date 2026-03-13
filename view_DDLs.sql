DROP VIEW IF EXISTS v_etf_signal_rank;
DROP VIEW IF EXISTS v_etf_signals;
DROP VIEW IF EXISTS v_etf_enriched;
DROP VIEW IF EXISTS v_latest_etf;

CREATE OR REPLACE VIEW v_latest_etf AS
SELECT DISTINCT ON (etf)
    etf,
    date,
    open,
    high,
    low,
    close,
    volume
FROM etf_flows
ORDER BY etf, date DESC;

CREATE OR REPLACE VIEW v_etf_enriched AS
SELECT
    etf,
    date,
    open,
    high,
    low,
    close,
    volume,
    AVG(close) OVER (
        PARTITION BY etf
        ORDER BY date
        ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
    ) AS ma_5,
    AVG(close) OVER (
        PARTITION BY etf
        ORDER BY date
        ROWS BETWEEN 9 PRECEDING AND CURRENT ROW
    ) AS ma_10,
    AVG(volume) OVER (
        PARTITION BY etf
        ORDER BY date
        ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
    ) AS vol_avg_5,
    AVG(volume) OVER (
        PARTITION BY etf
        ORDER BY date
        ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
    ) AS vol_avg_20,
    (high - low) AS range_1d,
    AVG(high - low) OVER (
        PARTITION BY etf
        ORDER BY date
        ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
    ) AS range_avg_5,
    (close - LAG(close, 1) OVER (PARTITION BY etf ORDER BY date))
        / NULLIF(LAG(close, 1) OVER (PARTITION BY etf ORDER BY date), 0) AS ret_1d,
    (close - LAG(close, 3) OVER (PARTITION BY etf ORDER BY date))
        / NULLIF(LAG(close, 3) OVER (PARTITION BY etf ORDER BY date), 0) AS ret_3d,
    (close - LAG(close, 5) OVER (PARTITION BY etf ORDER BY date))
        / NULLIF(LAG(close, 5) OVER (PARTITION BY etf ORDER BY date), 0) AS ret_5d,
    (close - AVG(close) OVER (
        PARTITION BY etf
        ORDER BY date
        ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
    )) / NULLIF(
        STDDEV_SAMP(close) OVER (
            PARTITION BY etf
            ORDER BY date
            ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
        ),
        0
    ) AS zscore_5d
FROM etf_flows;

CREATE OR REPLACE VIEW v_etf_signals AS
SELECT
    etf,
    date,
    open,
    high,
    low,
    close,
    volume,
    ma_5,
    ma_10,
    ret_1d,
    ret_3d,
    ret_5d,
    range_1d,
    range_avg_5,
    vol_avg_5,
    vol_avg_20,
    zscore_5d,
    CASE
        WHEN vol_avg_5 IS NULL OR vol_avg_5 = 0 THEN NULL
        ELSE volume / vol_avg_5
    END AS vol_ratio_5,
    CASE
        WHEN vol_avg_20 IS NULL OR vol_avg_20 = 0 THEN NULL
        ELSE volume / vol_avg_20
    END AS vol_ratio_20,
    CASE
        WHEN range_avg_5 IS NULL OR range_avg_5 = 0 THEN NULL
        ELSE range_1d / range_avg_5
    END AS range_ratio_5,
    CASE
        WHEN ma_5 IS NULL THEN NULL
        ELSE (close - ma_5) / NULLIF(ma_5, 0)
    END AS dist_ma_5,
    CASE
        WHEN ma_10 IS NULL THEN NULL
        ELSE (close - ma_10) / NULLIF(ma_10, 0)
    END AS dist_ma_10
FROM v_etf_enriched;

CREATE OR REPLACE VIEW v_etf_signal_rank AS
SELECT
    etf,
    date,
    ret_1d,
    ret_3d,
    ret_5d,
    vol_ratio_5,
    vol_ratio_20,
    range_ratio_5,
    dist_ma_5,
    dist_ma_10,
    zscore_5d,
    (
        COALESCE(ret_3d, 0) * 0.5
        + COALESCE(ret_5d, 0) * 0.5
        + COALESCE(vol_ratio_5, 1) * 0.25
        + COALESCE(range_ratio_5, 1) * 0.25
    ) AS momentum_score,
    (
        ABS(COALESCE(zscore_5d, 0)) * 0.6
        + ABS(COALESCE(dist_ma_5, 0)) * 0.4
    ) AS mean_reversion_score
FROM v_etf_signals;
