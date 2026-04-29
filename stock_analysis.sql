-- ============================================================
-- SEMICONDUCTOR STOCK ANALYSIS (2022–2025)
-- Tickers: NVDA, AMD, INTC, TSM
-- Author: Alex Sevilla
-- Tool: SQLite / DuckDB compatible
-- ============================================================
-- Schema:
--   stock_prices(date TEXT, ticker TEXT, open REAL, close REAL, average REAL)
-- ============================================================


-- ============================================================
-- QUERY 1: Retorno anual por ticker con ranking
-- Técnicas: Window functions (FIRST_VALUE, LAST_VALUE), RANK(), CTE
-- Insight: NVDA cayó -51% en 2022 y rebotó +246% en 2023
-- ============================================================
WITH yearly AS (
    SELECT
        ticker,
        strftime('%Y', date)                                               AS year,
        FIRST_VALUE(close) OVER (
            PARTITION BY ticker, strftime('%Y', date)
            ORDER BY date
        )                                                                  AS open_year,
        LAST_VALUE(close) OVER (
            PARTITION BY ticker, strftime('%Y', date)
            ORDER BY date
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        )                                                                  AS close_year
    FROM stock_prices
),
annual_returns AS (
    SELECT DISTINCT
        ticker,
        year,
        ROUND((close_year - open_year) / open_year * 100, 2)             AS annual_return_pct
    FROM yearly
)
SELECT
    ticker,
    year,
    annual_return_pct,
    RANK() OVER (PARTITION BY year ORDER BY annual_return_pct DESC)       AS rank_that_year
FROM annual_returns
ORDER BY year, rank_that_year;


-- ============================================================
-- QUERY 2: Top 10 días más volátiles (por % de movimiento intraday)
-- Técnicas: Expresiones aritméticas, CASE WHEN, ORDER BY con función
-- Insight: El día más volátil fue 2025-04-09 en todos los tickers
--          (reacción al anuncio de aranceles de Trump)
-- ============================================================
SELECT
    date,
    ticker,
    ROUND(open, 2)                                                        AS open,
    ROUND(close, 2)                                                       AS close,
    ROUND(ABS(close - open), 2)                                           AS abs_move_usd,
    ROUND((close - open) / open * 100, 2)                                 AS pct_move,
    CASE WHEN close > open THEN 'UP' ELSE 'DOWN' END                      AS direction
FROM stock_prices
ORDER BY ABS(close - open) / open DESC
LIMIT 10;


-- ============================================================
-- QUERY 3: Simulación — $1,000 invertidos por ticker en enero 2022
-- Técnicas: Self-join con subquery, CTEs, JOIN
-- Insight: $1,000 en NVDA valen $6,191 en 2025. INTC perdió -30%
-- ============================================================
WITH base AS (
    SELECT ticker, close AS base_price
    FROM stock_prices
    WHERE date = (SELECT MIN(date) FROM stock_prices)
),
latest AS (
    SELECT ticker, close AS last_price
    FROM stock_prices
    WHERE date = (SELECT MAX(date) FROM stock_prices)
)
SELECT
    b.ticker,
    ROUND(b.base_price, 2)                                                AS price_jan2022,
    ROUND(l.last_price, 2)                                                AS price_dec2025,
    ROUND(1000 * l.last_price / b.base_price, 2)                         AS value_of_1000_usd,
    ROUND((l.last_price - b.base_price) / b.base_price * 100, 2)         AS total_return_pct,
    CASE
        WHEN (l.last_price - b.base_price) / b.base_price > 0.5  THEN 'Strong Winner'
        WHEN (l.last_price - b.base_price) / b.base_price > 0    THEN 'Modest Gain'
        ELSE 'Loser'
    END                                                                   AS verdict
FROM base b
JOIN latest l ON b.ticker = l.ticker
ORDER BY total_return_pct DESC;


-- ============================================================
-- QUERY 4: Media móvil 30 y 90 días — señales de tendencia en NVDA
-- Técnicas: Window functions con ROWS BETWEEN, filtro por ticker
-- Insight: Cruce de MA30 sobre MA90 en feb-2023 marcó el inicio del rally IA
-- ============================================================
SELECT
    date,
    ticker,
    ROUND(close, 2)                                                        AS close,
    ROUND(AVG(close) OVER (
        PARTITION BY ticker
        ORDER BY date
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ), 2)                                                                  AS ma_30d,
    ROUND(AVG(close) OVER (
        PARTITION BY ticker
        ORDER BY date
        ROWS BETWEEN 89 PRECEDING AND CURRENT ROW
    ), 2)                                                                  AS ma_90d,
    CASE
        WHEN AVG(close) OVER (PARTITION BY ticker ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW)
           > AVG(close) OVER (PARTITION BY ticker ORDER BY date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW)
        THEN 'BULLISH'
        ELSE 'BEARISH'
    END                                                                    AS signal
FROM stock_prices
WHERE ticker = 'NVDA'
ORDER BY date;


-- ============================================================
-- QUERY 5: Mejor y peor trimestre por ticker
-- Técnicas: CASE para quarter logic, múltiples window functions, CTEs encadenados
-- Insight: NVDA Q2 2023 (+88%) fue el mejor trimestre del dataset
-- ============================================================
WITH quarterly AS (
    SELECT
        ticker,
        strftime('%Y', date) || '-Q' ||
            CASE
                WHEN CAST(strftime('%m', date) AS INT) <= 3 THEN '1'
                WHEN CAST(strftime('%m', date) AS INT) <= 6 THEN '2'
                WHEN CAST(strftime('%m', date) AS INT) <= 9 THEN '3'
                ELSE '4'
            END                                                            AS quarter,
        FIRST_VALUE(close) OVER (
            PARTITION BY ticker,
                strftime('%Y', date) ||
                CASE
                    WHEN CAST(strftime('%m', date) AS INT) <= 3 THEN '01'
                    WHEN CAST(strftime('%m', date) AS INT) <= 6 THEN '02'
                    WHEN CAST(strftime('%m', date) AS INT) <= 9 THEN '03'
                    ELSE '04'
                END
            ORDER BY date
        )                                                                  AS q_open,
        LAST_VALUE(close) OVER (
            PARTITION BY ticker,
                strftime('%Y', date) ||
                CASE
                    WHEN CAST(strftime('%m', date) AS INT) <= 3 THEN '01'
                    WHEN CAST(strftime('%m', date) AS INT) <= 6 THEN '02'
                    WHEN CAST(strftime('%m', date) AS INT) <= 9 THEN '03'
                    ELSE '04'
                END
            ORDER BY date
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        )                                                                  AS q_close
    FROM stock_prices
),
q_returns AS (
    SELECT DISTINCT
        ticker,
        quarter,
        ROUND((q_close - q_open) / q_open * 100, 2)                      AS q_return_pct
    FROM quarterly
),
ranked AS (
    SELECT *,
        RANK() OVER (PARTITION BY ticker ORDER BY q_return_pct DESC)      AS best_rank,
        RANK() OVER (PARTITION BY ticker ORDER BY q_return_pct ASC)       AS worst_rank
    FROM q_returns
)
SELECT
    ticker,
    quarter,
    q_return_pct,
    CASE WHEN best_rank = 1 THEN 'BEST QUARTER' ELSE 'WORST QUARTER' END  AS label
FROM ranked
WHERE best_rank = 1 OR worst_rank = 1
ORDER BY ticker, label;


-- ============================================================
-- QUERY 6 (BONUS): Correlación de rendimientos diarios — NVDA vs AMD
-- Técnicas: LAG(), correlación manual con AVG y subqueries correlacionados
-- Insight: NVDA y AMD tienen alta correlación, pero divergen en 2023
-- ============================================================
WITH daily_returns AS (
    SELECT
        date,
        ticker,
        ROUND((close - LAG(close) OVER (PARTITION BY ticker ORDER BY date))
            / LAG(close) OVER (PARTITION BY ticker ORDER BY date) * 100, 4) AS daily_ret
    FROM stock_prices
),
nvda AS (SELECT date, daily_ret AS ret_nvda FROM daily_returns WHERE ticker = 'NVDA'),
amd  AS (SELECT date, daily_ret AS ret_amd  FROM daily_returns WHERE ticker = 'AMD')
SELECT
    strftime('%Y', n.date)                                                 AS year,
    COUNT(*)                                                               AS trading_days,
    ROUND(AVG(n.ret_nvda), 4)                                             AS avg_daily_ret_nvda,
    ROUND(AVG(a.ret_amd), 4)                                              AS avg_daily_ret_amd,
    -- Correlación de Pearson simplificada
    ROUND(
        (AVG(n.ret_nvda * a.ret_amd) - AVG(n.ret_nvda) * AVG(a.ret_amd))
        /
        (
            SQRT(AVG(n.ret_nvda * n.ret_nvda) - AVG(n.ret_nvda) * AVG(n.ret_nvda))
            *
            SQRT(AVG(a.ret_amd * a.ret_amd) - AVG(a.ret_amd) * AVG(a.ret_amd))
        )
    , 4)                                                                   AS pearson_correlation
FROM nvda n
JOIN amd a ON n.date = a.date
WHERE n.ret_nvda IS NOT NULL AND a.ret_amd IS NOT NULL
GROUP BY year
ORDER BY year;