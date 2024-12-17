WITH
    date_range AS (
        SELECT
            '{{ start_date }}'::DATE AS start_date,
            '{{ end_date }}'::DATE AS end_date
    )
SELECT
    {% for currency in currencies %}
    SUM(t.value) FILTER (
        WHERE
            c.code = '{{ currency.name }}'
    ) AS {{ currency.name }}{% if not loop.last %},{% endif %}
    {% endfor %}
FROM
    transactions t
    INNER JOIN currencies c
    ON t.currency_id = c.id,
    date_range
WHERE
    date BETWEEN date_range.start_date AND date_range.end_date;