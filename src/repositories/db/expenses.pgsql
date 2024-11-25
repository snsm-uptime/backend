WITH
    date_range AS (
        SELECT
            '{{ start_date }}'::DATE AS start_date,
            '{{ end_date }}'::DATE AS end_date
    )
SELECT
    {% for currency in currencies %}
    SUM(value) FILTER (
        WHERE
            currency = '{{ currency.name }}'
    ) AS {{ currency.name }}{% if not loop.last %},{% endif %}
    {% endfor %}
FROM
    transactions,
    date_range
WHERE
    date BETWEEN date_range.start_date AND date_range.end_date;