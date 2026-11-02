SELECT * FROM {{ ref('daily_reconciliation') }}
WHERE abs(difference) > 0.01 OR coalesce(raw_count,-1) != coalesce(ledger_count,-1)
