import csv
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

def test_synthetic_transaction_integrity():
    path = Path(__file__).resolve().parents[1] / 'seeds' / 'transactions.csv'
    with path.open(newline='') as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) >= 5
    assert len({r['transaction_id'] for r in rows}) == len(rows)
    assert all(r['status'] in {'SETTLED','PENDING','REVERSED'} for r in rows)
    totals = defaultdict(Decimal)
    for r in rows:
        if r['status'] == 'SETTLED':
            totals[(r['transaction_date'],r['currency'])] += Decimal(r['amount'])
    assert totals[('2026-10-01','USD')] == Decimal('1050.00')
