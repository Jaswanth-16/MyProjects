"""Explicit contract validation; no third-party packages or silent coercion."""

from datetime import datetime, timezone
import hashlib
import json
import re

FIELDS = {
    'trip_id', 'route_id', 'scheduled_departure_utc', 'scheduled_arrival_utc',
    'actual_arrival_utc', 'status', 'passengers', 'capacity', 'revenue_paise',
    'updated_at_utc',
}


class InvalidRecord(ValueError):
    pass


def timestamp(value, name):
    if not isinstance(value, str):
        raise InvalidRecord(f'{name}: expected an ISO 8601 timestamp')
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as exc:
        raise InvalidRecord(f'{name}: invalid timestamp') from exc
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise InvalidRecord(f'{name}: timezone is required')
    return dt.astimezone(timezone.utc)


def iso(dt):
    return dt.isoformat(timespec='microseconds').replace('+00:00', 'Z')


def validate(record, routes):
    if not isinstance(record, dict):
        raise InvalidRecord('expected a JSON object')
    missing, extra = FIELDS - record.keys(), record.keys() - FIELDS
    if missing or extra:
        raise InvalidRecord(f'schema mismatch: missing={sorted(missing)}, extra={sorted(extra)}')
    row = dict(record)
    if not isinstance(row['trip_id'], str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', row['trip_id']):
        raise InvalidRecord('trip_id: expected 1-64 letters, digits, underscores or hyphens')
    if not isinstance(row['route_id'], str) or row['route_id'] not in routes:
        raise InvalidRecord('route_id: unknown route')
    if row['status'] not in ('completed', 'cancelled'):
        raise InvalidRecord('status: expected completed or cancelled')
    for name in ('passengers', 'capacity', 'revenue_paise'):
        if type(row[name]) is not int or row[name] < 0:
            raise InvalidRecord(f'{name}: expected a nonnegative integer')
    if not 1 <= row['capacity'] <= 200:
        raise InvalidRecord('capacity: must be between 1 and 200')
    if row['passengers'] > row['capacity']:
        raise InvalidRecord('passengers: exceeds capacity')
    if row['revenue_paise'] > 100_000_000:
        raise InvalidRecord('revenue_paise: exceeds the demo contract limit')
    departure = timestamp(row['scheduled_departure_utc'], 'scheduled_departure_utc')
    arrival = timestamp(row['scheduled_arrival_utc'], 'scheduled_arrival_utc')
    updated = timestamp(row['updated_at_utc'], 'updated_at_utc')
    if not 0 < (arrival - departure).total_seconds() <= 86400:
        raise InvalidRecord('scheduled duration: must be > 0 and <= 24 hours')
    if updated < arrival:
        raise InvalidRecord('updated_at_utc: must follow scheduled arrival for this post-trip feed')
    if row['status'] == 'cancelled':
        if row['actual_arrival_utc'] is not None or row['passengers'] != 0 or row['revenue_paise'] != 0:
            raise InvalidRecord('cancelled trip: actual arrival must be null; passengers and revenue must be zero')
        delay, on_time = None, None
    else:
        actual = timestamp(row['actual_arrival_utc'], 'actual_arrival_utc')
        if actual < departure or actual > updated:
            raise InvalidRecord('actual arrival: must be between departure and update time')
        delay = round((actual - arrival).total_seconds() / 60, 6)
        on_time = int(delay <= 5.0)
        row['actual_arrival_utc'] = iso(actual)
    row['scheduled_departure_utc'] = iso(departure)
    row['scheduled_arrival_utc'] = iso(arrival)
    row['updated_at_utc'] = iso(updated)
    # Canonical payload excludes derived columns; equivalent timezone spellings deduplicate.
    row['payload_hash'] = hashlib.sha256(
        json.dumps(row, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    ).hexdigest()
    row.update(service_date=departure.date().isoformat(), delay_minutes=delay, on_time=on_time)
    return row
