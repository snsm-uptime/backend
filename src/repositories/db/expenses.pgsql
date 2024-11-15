WITH
    date_range AS (
        SELECT
            '{{ start_date }}'::DATE AS start_date,
            '{{ end_date }}'::DATE AS end_date
    )
SELECT
    to_char(
        COALESCE(
            (
                SELECT
                    SUM(value)
                FROM
                    transactions,
                    date_range
                WHERE
                    currency = 'USD'
                    AND date BETWEEN date_range.start_date AND date_range.end_date
            ),
            0
        ),
        'FM$999,999,999,990.00'
    ) AS usd,
    to_char(
        COALESCE(
            (
                SELECT
                    SUM(value)
                FROM
                    transactions,
                    date_range
                WHERE
                    currency = 'CRC'
                    AND date BETWEEN date_range.start_date AND date_range.end_date
            ),
            0
        ),
        'FM₡999,999,999,990.00'
    ) AS colones;