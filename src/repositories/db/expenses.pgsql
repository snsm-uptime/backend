-- TODO: Use jinja to dynamically add any currency based on ENUM
WITH
    date_range AS (
        SELECT
            '{{ start_date }}'::DATE AS start_date,
            '{{ end_date }}'::DATE AS end_date
    )
SELECT
    (
        SELECT
            SUM(value)
        FROM
            transactions,
            date_range
        WHERE
            currency = 'USD'
            AND date BETWEEN date_range.start_date AND date_range.end_date
    ) AS usd,
    (
        SELECT
            SUM(value)
        FROM
            transactions,
            date_range
        WHERE
            currency = 'CRC'
            AND date BETWEEN date_range.start_date AND date_range.end_date
    ) AS colones;