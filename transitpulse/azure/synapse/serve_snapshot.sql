-- Optional: run in a user database in an EXISTING Synapse serverless SQL workspace.
-- Replace __STORAGE_ACCOUNT__ and __SNAPSHOT_ID__ with the committed HEAD values.
-- Grant the workspace managed identity Storage Blob Data Reader on the container.
-- Authentication and SQL permissions must be configured by the workspace administrator.
-- Do not use a wildcard across snapshots: every snapshot contains the full current state.

CREATE DATABASE SCOPED CREDENTIAL TransitPulseIdentity
WITH IDENTITY = 'Managed Identity';
GO
CREATE EXTERNAL DATA SOURCE TransitPulseLake
WITH (
    LOCATION = 'https://__STORAGE_ACCOUNT__.dfs.core.windows.net/transitpulse',
    CREDENTIAL = TransitPulseIdentity
);
GO
CREATE OR ALTER VIEW dbo.FactTrip AS
SELECT *
FROM OPENROWSET(
    BULK 'snapshots/__SNAPSHOT_ID__/gold/fact_trip.csv',
    DATA_SOURCE = 'TransitPulseLake',
    FORMAT = 'CSV',
    PARSER_VERSION = '2.0',
    HEADER_ROW = TRUE
) WITH (
    trip_id VARCHAR(64),
    route_id VARCHAR(3),
    service_date DATE,
    scheduled_departure_utc VARCHAR(32),
    scheduled_arrival_utc VARCHAR(32),
    actual_arrival_utc VARCHAR(32),
    status VARCHAR(12),
    passengers INT,
    capacity INT,
    revenue_paise BIGINT,
    delay_minutes FLOAT,
    on_time INT,
    updated_at_utc VARCHAR(32),
    payload_hash VARCHAR(64)
) AS trips;
GO
SELECT route_id,
    COUNT_BIG(*) AS scheduled_trips,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed_trips,
    100.0 * SUM(on_time) / NULLIF(SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END), 0) AS on_time_pct,
    SUM(CAST(revenue_paise AS BIGINT)) / 100.0 AS revenue_inr
FROM dbo.FactTrip
GROUP BY route_id;
