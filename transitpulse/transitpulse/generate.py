"""Deterministic fictional trips; no employer or third-party data."""

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import random

from .validation import iso


def write_jsonl(path, records):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='\n') as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True, allow_nan=False) + '\n')


def generate(output_dir, count=10_000, seed=42):
    if not 100 <= count <= 20_000:
        raise ValueError('count must be 100-20000 to keep demo batches within 10 MiB')
    output_dir = Path(output_dir)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError('input directory is not empty; choose a new workspace')
    rng = random.Random(seed)
    start = datetime(2026, 1, 1, 5, tzinfo=timezone.utc)

    def make_trip(index, new=False):
        day = 30 + (index % 3) if new else index % 30
        departure = start + timedelta(days=day, minutes=(index * 13) % 900)
        arrival = departure + timedelta(minutes=rng.randint(20, 70))
        cancelled = rng.random() < 0.04
        capacity = rng.choice([40, 45, 50])
        passengers = 0 if cancelled else rng.randint(8, capacity)
        delay = rng.choices([-2, 0, 2, 4, 7, 12, 20], [5, 20, 25, 20, 15, 10, 5])[0]
        actual = None if cancelled else arrival + timedelta(minutes=delay)
        return dict(
            trip_id=f'T{index:07d}', route_id=f'R{index % 6 + 1:02d}',
            scheduled_departure_utc=iso(departure), scheduled_arrival_utc=iso(arrival),
            actual_arrival_utc=iso(actual) if actual else None,
            status='cancelled' if cancelled else 'completed', passengers=passengers,
            capacity=capacity, revenue_paise=passengers * rng.choice([2500, 3000, 4000, 5000]),
            updated_at_utc=iso(arrival + timedelta(minutes=60)),
        )

    initial = [make_trip(i) for i in range(count)]
    corrections = []
    for row in initial[:100]:
        changed = dict(row)
        # Correct a non-additive field too: consumers must upsert, not append facts.
        changed['route_id'] = f"R{int(row['route_id'][1:]) % 6 + 1:02d}"
        changed['updated_at_utc'] = iso(start + timedelta(days=35))
        corrections.append(changed)
    new = [make_trip(count + i, new=True) for i in range(200)]
    duplicate = [dict(row) for row in corrections[:30]]
    stale = [dict(row) for row in initial[:20]]
    bad = [dict(initial[i], trip_id=f'BAD{i:03d}', passengers=-1) for i in range(10)]
    delta = corrections + new + duplicate + stale + bad
    # Preserve ordering of the correction/duplicate/stale groups for a verifiable demo.
    write_jsonl(output_dir / 'initial.jsonl', initial)
    write_jsonl(output_dir / 'delta.jsonl', delta)
    expected = dict(seed=seed, initial_rows=count, delta_rows=len(delta), expected_unique_trips=count + 200,
                    delta_inserted=200, delta_updated=100, delta_unchanged=30, delta_stale=20, delta_rejected=10)
    (output_dir / 'expected.json').write_text(json.dumps(expected, indent=2) + '\n', encoding='utf-8')
    return expected
