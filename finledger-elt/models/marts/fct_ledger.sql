{{ config(materialized='incremental', unique_key='transaction_id', incremental_strategy='merge') }}
-- Re-scan deduplicated staging records to handle late corrections safely.
SELECT transaction_id, account_id, transaction_date, amount, currency, status, updated_at
FROM {{ ref('stg_transactions') }}
