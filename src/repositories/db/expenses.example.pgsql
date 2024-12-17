WITH
    date_range AS (
        SELECT
            '2022-01-01'::DATE AS start_date,
            '2024-11-25'::DATE AS end_date
    )
SELECT
    ROUND(
        CAST(
            SUM(t.value) FILTER (
                WHERE
                    c.code = 'CRC'
            ) AS NUMERIC
        ),
        2
    ) AS CRC,
    ROUND(
        CAST(
            SUM(t.value) FILTER (
                WHERE
                    c.code = 'MXP'
            ) AS NUMERIC
        ),
        2
    ) AS MXP,
    ROUND(
        CAST(
            SUM(t.value) FILTER (
                WHERE
                    c.code = 'USD'
            ) AS NUMERIC
        ),
        2
    ) AS USD
FROM
    transactions t
    INNER JOIN currencies c ON t.currency_id = c.id,
    date_range
WHERE
    date BETWEEN date_range.start_date AND date_range.end_date;