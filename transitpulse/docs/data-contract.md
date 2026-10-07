# Data contract and metric definitions

Input: UTF-8 JSON Lines, one object per nonblank line. Extra/missing fields, duplicate
JSON keys and non-finite JSON numbers are rejected. All routes and trips are fictional.

| Field | Contract |
|---|---|
| trip_id | 1–64 letters, digits, underscores or hyphens; business key |
| route_id | R01–R06; must exist in dim_route |
| scheduled_departure_utc | Timezone-aware ISO 8601 timestamp |
| scheduled_arrival_utc | After departure, scheduled duration at most 24 hours |
| actual_arrival_utc | Completed: between departure and update time; cancelled: null |
| status | completed or cancelled |
| passengers | Integer, zero through capacity; zero for cancelled trips |
| capacity | Integer, 1–200 |
| revenue_paise | Integer, 0–100,000,000; zero for cancelled trips |
| updated_at_utc | Timezone-aware timestamp at/after scheduled and actual arrival |

This is a **post-trip feed**. It does not accept planned trips or pre-departure cancellation
events. UTC normalization occurs before comparing versions. `service_date` is derived
from scheduled departure in UTC, not Indian local service-day boundaries.

| Metric | Definition |
|---|---|
| Scheduled trips | Number of current trip facts, including cancellations |
| Completed trips | Facts with status completed |
| On-time arrivals | Completed trips arriving no more than five minutes late; early arrivals included |
| On-time percentage | On-time completed trips / all completed trips |
| Cancellation percentage | Cancelled trips / scheduled trips |
| Average arrival delay | Mean actual minus scheduled arrival in minutes, completed trips only; early values are negative |
| Passengers | Sum of passengers across current facts |
| Revenue INR | Sum of integer revenue_paise / 100 |
| Load factor | Sum passengers / sum capacity of completed trips |

Zero denominators yield null in SQL, blank in DAX and N/A in the HTML dashboard.
The static SVG preview displays zero when no completed-trip rate exists; it is a compact
demonstration graphic rather than the authoritative metric export. Default demo data has
completed trips on every route. Use `kpis.json` for exact machine-readable values.

`fact_trip` relates many-to-one to `dim_route` by route_id and `dim_date` by service_date.
`route_daily` contains additive counts/sums so rates can be recalculated correctly after
filtering; averaging route-level percentages would give incorrect overall results.

Money remains integer paise in storage. SQLite computed ratios and display percentages
use floating point. This project does not model refunds, transfers, standing passengers,
currency conversion or fare reconciliation.
