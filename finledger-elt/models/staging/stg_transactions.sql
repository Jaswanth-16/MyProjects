WITH ranked AS (
 SELECT transaction_id, account_id, transaction_date, amount, currency,
        upper(status) AS status, updated_at,
        row_number() over(partition by transaction_id order by updated_at desc) AS rn
 FROM {{ source('finance_raw', 'RAW_TRANSACTIONS') }}
)
SELECT transaction_id, account_id, transaction_date, amount, currency, status, updated_at
FROM ranked WHERE rn=1
