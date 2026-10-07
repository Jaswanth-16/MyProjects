PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS dim_route (
    route_id TEXT PRIMARY KEY,
    route_name TEXT NOT NULL,
    depot TEXT NOT NULL,
    distance_km REAL NOT NULL CHECK (distance_km > 0)
);
INSERT OR IGNORE INTO dim_route VALUES
    ('R01', 'City Loop North', 'North', 12.4),
    ('R02', 'Technology Park', 'North', 18.0),
    ('R03', 'University Link', 'North', 9.5),
    ('R04', 'City Loop South', 'South', 14.2),
    ('R05', 'Central Station', 'South', 8.1),
    ('R06', 'Airport Connector', 'South', 24.0);

CREATE TABLE IF NOT EXISTS fact_trip (
    trip_id TEXT PRIMARY KEY,
    route_id TEXT NOT NULL REFERENCES dim_route(route_id),
    service_date TEXT NOT NULL,
    scheduled_departure_utc TEXT NOT NULL,
    scheduled_arrival_utc TEXT NOT NULL,
    actual_arrival_utc TEXT,
    status TEXT NOT NULL CHECK (status IN ('completed', 'cancelled')),
    passengers INTEGER NOT NULL CHECK (passengers >= 0),
    capacity INTEGER NOT NULL CHECK (capacity > 0 AND passengers <= capacity),
    revenue_paise INTEGER NOT NULL CHECK (revenue_paise >= 0),
    delay_minutes REAL,
    on_time INTEGER CHECK (on_time IN (0, 1) OR on_time IS NULL),
    updated_at_utc TEXT NOT NULL,
    payload_hash TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_trip_date_route ON fact_trip(service_date, route_id);

CREATE TABLE IF NOT EXISTS ingested_batch (
    batch_hash TEXT PRIMARY KEY,
    source_name TEXT NOT NULL,
    committed_at_utc TEXT NOT NULL,
    row_count INTEGER NOT NULL,
    max_updated_at_utc TEXT
);
CREATE TABLE IF NOT EXISTS run_audit (
    run_id TEXT PRIMARY KEY,
    batch_hash TEXT,
    source_name TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at_utc TEXT NOT NULL,
    finished_at_utc TEXT NOT NULL,
    metrics_json TEXT NOT NULL,
    error TEXT
);
CREATE TABLE IF NOT EXISTS quarantine (
    run_id TEXT NOT NULL REFERENCES run_audit(run_id),
    line_number INTEGER NOT NULL,
    reason TEXT NOT NULL,
    raw_record TEXT NOT NULL,
    PRIMARY KEY (run_id, line_number)
);

CREATE VIEW IF NOT EXISTS dim_date AS
SELECT DISTINCT service_date AS date_key,
    CAST(strftime('%Y', service_date) AS INTEGER) AS year,
    CAST(strftime('%m', service_date) AS INTEGER) AS month,
    CAST(strftime('%w', service_date) AS INTEGER) AS weekday_sunday_zero
FROM fact_trip;

CREATE VIEW IF NOT EXISTS route_daily AS
SELECT t.service_date, t.route_id, r.route_name, r.depot,
    COUNT(*) AS scheduled_trips,
    SUM(t.status = 'completed') AS completed_trips,
    SUM(t.status = 'cancelled') AS cancelled_trips,
    SUM(COALESCE(t.on_time, 0)) AS on_time_trips,
    SUM(t.passengers) AS passengers,
    SUM(CASE WHEN t.status = 'completed' THEN t.capacity ELSE 0 END) AS completed_capacity,
    SUM(t.revenue_paise) AS revenue_paise,
    SUM(COALESCE(t.delay_minutes, 0)) AS total_delay_minutes
FROM fact_trip t JOIN dim_route r ON t.route_id = r.route_id
GROUP BY t.service_date, t.route_id;

CREATE VIEW IF NOT EXISTS kpi_summary AS
SELECT COUNT(*) AS scheduled_trips,
    COALESCE(SUM(status = 'completed'), 0) AS completed_trips,
    COALESCE(SUM(status = 'cancelled'), 0) AS cancelled_trips,
    COALESCE(SUM(passengers), 0) AS passengers,
    COALESCE(SUM(revenue_paise), 0) AS revenue_paise,
    ROUND(100.0 * SUM(on_time) / NULLIF(SUM(status = 'completed'), 0), 2) AS on_time_pct,
    ROUND(100.0 * SUM(status = 'cancelled') / NULLIF(COUNT(*), 0), 2) AS cancellation_pct,
    ROUND(AVG(delay_minutes), 2) AS avg_delay_minutes,
    ROUND(100.0 * SUM(passengers) /
        NULLIF(SUM(CASE WHEN status = 'completed' THEN capacity ELSE 0 END), 0), 2) AS load_factor_pct
FROM fact_trip;
