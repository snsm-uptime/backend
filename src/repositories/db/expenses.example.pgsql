WITH
    date_range AS (
        SELECT
            '2024-12-05 00:00:00'::DATE AS start_date,
            '2024-12-21 00:00:00'::DATE AS end_date
    )
SELECT
    c.symbol || ' ' || to_char(SUM(t.value), 'FM999,999,999,990.00') AS formatted_total,
    c.code AS currency_code
FROM
    transactions t
    INNER JOIN currencies c ON t.currency_id = c.id,
    date_range
WHERE
    t.date BETWEEN date_range.start_date AND date_range.end_date
GROUP BY
    c.symbol,
    c.code
ORDER BY
    c.code;