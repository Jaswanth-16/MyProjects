WITH raw_totals AS (
 SELECT transaction_date, currency, sum(amount) raw_amount, count(*) raw_count
 FROM {{ ref('stg_transactions') }} WHERE status='SETTLED'
 GROUP BY 1,2
), ledger_totals AS (
 SELECT transaction_date, currency, sum(amount) ledger_amount, count(*) ledger_count
 FROM {{ ref('fct_ledger') }} WHERE status='SETTLED'
 GROUP BY 1,2
)
SELECT coalesce(r.transaction_date,l.transaction_date) transaction_date,
 coalesce(r.currency,l.currency) currency, r.raw_amount, l.ledger_amount,
 coalesce(r.raw_amount,0)-coalesce(l.ledger_amount,0) difference,
 r.raw_count, l.ledger_count
FROM raw_totals r FULL OUTER JOIN ledger_totals l
 ON r.transaction_date=l.transaction_date AND r.currency=l.currency
