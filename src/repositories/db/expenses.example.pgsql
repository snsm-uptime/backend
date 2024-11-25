WITH
    date_range AS (
        SELECT
            '2022-01-01'::DATE AS start_date,
            '2024-11-25'::DATE AS end_date
    )
SELECT
    ROUND(
        CAST(
            SUM(value) FILTER (
                WHERE
                    currency = 'CRC'
            ) AS NUMERIC
        ),
        2
    ) AS CRC,
    ROUND(
        CAST(
            SUM(value) FILTER (
                WHERE
                    currency = 'MXP'
            ) AS NUMERIC
        ),
        2
    ) AS MXP,
    ROUND(
        CAST(
            SUM(value) FILTER (
                WHERE
                    currency = 'USD'
            ) AS NUMERIC
        ),
        2
    ) AS USD
FROM
    transactions,
    date_range
WHERE
    date BETWEEN date_range.start_date AND date_range.end_date;