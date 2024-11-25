WITH
    date_range AS (
        SELECT
            '{{ start_date }}'::DATE AS start_date,
            '{{ end_date }}'::DATE AS end_date,
            '{{ period }}'::time_period AS period -- 'daily', 'weekly', 'monthly', 'yearly'
    ),
    transactions_filtered AS (
        SELECT
            t.*,
            CASE
                WHEN dr.period = 'daily' THEN date_trunc('day', t.date)
                WHEN dr.period = 'weekly' THEN date_trunc('week', t.date)
                WHEN dr.period = 'monthly' THEN date_trunc('month', t.date)
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
            ) AS period_currency_pct
        FROM
            currency_aggregates
    )
SELECT
    period_start,
    currency,
    COALESCE(total_value, 0) AS total,
    COALESCE(transaction_count, 0) AS transaction_count,
    COALESCE(avg_transaction_value, 0) AS avg_transaction,
    COALESCE(min_value, 0) AS min_value,
    COALESCE(max_value, 0) AS max_value,
    COALESCE(period_currency_pct, 0) AS period_currency_pct
FROM
    percentage_contributions
ORDER BY
    period_start,
    currency;