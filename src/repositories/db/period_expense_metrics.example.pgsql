WITH
    date_range AS (
        SELECT
            '2024-01-01'::DATE AS start_date,
            '2024-11-25'::DATE AS end_date,
            'montly'::TEXT AS period -- 'weekly', 'monthly', 'yearly'
    ),
    transactions_filtered AS (
        SELECT
            t.*,
            CASE
                WHEN dr.period = 'monthly' THEN date_trunc('month', t.date)
                WHEN dr.period = 'weekly' THEN date_trunc('week', t.date)
                WHEN dr.period = 'yearly' THEN date_trunc('year', t.date)
            END AS period_start
        FROM
            transactions t,
            date_range dr
        WHERE
            t.date BETWEEN dr.start_date AND dr.end_date
    ),
    currency_aggregates AS (
        SELECT
            period_start,
            currency,
            SUM(value) AS total_value,
            COUNT(*) AS transaction_count,
            ROUND(CAST(AVG(value) AS numeric), 2) AS avg_transaction_value,
            ROUND(CAST(MIN(value) AS numeric), 2) AS min_value,
            ROUND(CAST(MAX(value) AS numeric), 2) AS max_value
        FROM
            transactions_filtered
        GROUP BY
            period_start,
            currency
    ),
    percentage_contributions AS (
        SELECT
            *,
            ROUND(
                CAST(
                    total_value * 100.0 / SUM(total_value) OVER (
                        PARTITION BY
                            period_start
                    ) AS numeric
                ),
                2
            ) AS pct_total
        FROM
            currency_aggregates
    )
SELECT
    period_start,
    -- USD Metrics
    COALESCE(
        MAX(
            CASE
                WHEN currency = 'USD' THEN total_value
            END
        ),
        0
    ) AS total_usd,
    COALESCE(
        MAX(
            CASE
                WHEN currency = 'USD' THEN transaction_count
            END
        ),
        0
    ) AS transaction_count_usd,
    COALESCE(
        MAX(
            CASE
                WHEN currency = 'USD' THEN avg_transaction_value
            END
        ),
        0
    ) AS avg_transaction_usd,
    COALESCE(
        MAX(
            CASE
                WHEN currency = 'USD' THEN min_value
            END
        ),
        0
    ) AS min_value_usd,
    COALESCE(
        MAX(
            CASE
                WHEN currency = 'USD' THEN max_value
            END
        ),
        0
    ) AS max_value_usd,
    COALESCE(
        MAX(
            CASE
                WHEN currency = 'USD' THEN pct_total
            END
        ),
        0
    ) AS pct_total_usd,
    -- CRC Metrics
    COALESCE(
        MAX(
            CASE
                WHEN currency = 'CRC' THEN total_value
            END
        ),
        0
    ) AS total_crc,
    COALESCE(
        MAX(
            CASE
                WHEN currency = 'CRC' THEN transaction_count
            END
        ),
        0
    ) AS transaction_count_crc,
    COALESCE(
        MAX(
            CASE
                WHEN currency = 'CRC' THEN avg_transaction_value
            END
        ),
        0
    ) AS avg_transaction_crc,
    COALESCE(
        MAX(
            CASE
                WHEN currency = 'CRC' THEN min_value
            END
        ),
        0
    ) AS min_value_crc,
    COALESCE(
        MAX(
            CASE
                WHEN currency = 'CRC' THEN max_value
            END
        ),
        0
    ) AS max_value_crc,
    COALESCE(
        MAX(
            CASE
                WHEN currency = 'CRC' THEN pct_total
            END
        ),
        0
    ) AS pct_total_crc
FROM
    percentage_contributions
GROUP BY
    period_start
ORDER BY
    period_start;