WITH
    -- Step 1: Define Parameters
    params AS (
        SELECT
            '2024-01-01'::DATE AS start_date,
            '2024-11-25'::DATE AS end_date,
            'weekly'::time_period AS period,
            'USD'::TEXT AS filter_by -- Filter by currency code as text
    ),

    -- Step 2: Filter Transactions and Determine Period Start
    transactions_filtered AS (
        SELECT
            t.value,
            c.code AS currency_code, -- Join to get the currency code
            CASE
                WHEN pr.period = 'daily' THEN date_trunc('day', t.date)
                WHEN pr.period = 'weekly' THEN date_trunc('week', t.date)
                WHEN pr.period = 'monthly' THEN date_trunc('month', t.date)
                WHEN pr.period = 'yearly' THEN date_trunc('year', t.date)
            END AS period_start
        FROM
            transactions t
        INNER JOIN
            currencies c ON t.currency_id = c.id -- Join transactions with currencies table
        CROSS JOIN
            params pr
        WHERE
            t.date BETWEEN pr.start_date AND pr.end_date
            AND c.code = pr.filter_by -- Use currency code for filtering
    ),

    -- Step 3: Aggregate Data by Period and Currency
    currency_aggregates AS (
        SELECT
            period_start,
            currency_code, -- Aggregate by currency code
            SUM(value) AS total_value,
            COUNT(*) AS transaction_count,
            ROUND(CAST(AVG(value) AS numeric), 2) AS avg_transaction_value,
            ROUND(CAST(MIN(value) AS numeric), 2) AS min_value,
            ROUND(CAST(MAX(value) AS numeric), 2) AS max_value
        FROM
            transactions_filtered
        GROUP BY
            period_start, currency_code
    ),

    -- Step 4: Calculate Percentage Contributions Safely
    percentage_contributions AS (
        SELECT
            *,
            CASE
                WHEN SUM(total_value) OVER (PARTITION BY period_start) = 0 THEN 0
                ELSE ROUND(
                    CAST(
                        total_value * 100.0 / NULLIF(SUM(total_value) OVER (PARTITION BY period_start), 0) AS numeric
                    ),
                    2
                )
            END AS period_currency_pct
        FROM
            currency_aggregates
    )

-- Step 5: Final Output
SELECT
    to_char(period_start, 'YYYY-MM-DD'::text) AS period_start,
    COALESCE(total_value, 0) AS total,
    COALESCE(transaction_count, 0) AS transaction_count,
    COALESCE(avg_transaction_value, 0) AS avg_transaction,
    COALESCE(min_value, 0) AS min_value,
    COALESCE(max_value, 0) AS max_value,
    COALESCE(period_currency_pct, 0) AS period_currency_pct
FROM
    percentage_contributions
ORDER BY
    period_start, currency_code;
