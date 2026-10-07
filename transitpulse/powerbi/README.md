# Build the Power BI report

The repository supplies import queries, measures and modelling instructions. A `.pbix`
file is not included; the generated HTML dashboard is available immediately as a preview.

1. Run the local demo. Find the export folder in `workspace/LATEST.json`.
2. In Power BI Desktop, create a **Text parameter** called `ExportFolder` with that exact
   folder path. Select one immutable snapshot, never combine multiple snapshots.
3. Create a blank query named `fnReadCsv`; paste [fnReadCsv.pq](fnReadCsv.pq) into Advanced Editor.
4. Create three more blank queries named `FactTrip`, `DimRoute` and `DimDate` using
   [FactTrip.pq](FactTrip.pq), [DimRoute.pq](DimRoute.pq) and [DimDate.pq](DimDate.pq).
5. Create single-direction one-to-many relationships:
   `DimRoute[route_id]` → `FactTrip[route_id]` and `DimDate[date_key]` → `FactTrip[service_date]`.
   Keep these dimensions on the filtering side. Do not relate route_daily to the same fact model.
6. Add the measures in [measures.dax](measures.dax) one at a time. Format rates as percentages,
   Revenue INR as INR currency, and delay as a decimal number.
7. Import [theme.json](theme.json). Build the layout below and save your own PBIX.

| Area | Visual and fields |
|---|---|
| Filters | Date range from DimDate; depot and route from DimRoute |
| Top row | Scheduled Trips, On-time %, Passengers, Revenue INR cards |
| Middle left | Bar chart: route_name against On-time % |
| Middle right | Line chart: date_key against Completed Trips |
| Bottom | Table: route_name, Scheduled Trips, Completed Trips, On-time %, Cancellation %, Revenue INR |

For the unfiltered default demo, Scheduled Trips should equal **10,200**, Passengers
**260,104**, Revenue INR **9,432,455**, On-time **70.32%** and Cancellation **4.20%**.
Compare the report with `kpis.json`; the DAX percentage measures store fractions, while
the JSON percentage fields store 0–100 values.

## Optional depot-level row security

Import [UserAccess.example.csv](UserAccess.example.csv) as `UserAccess` and replace its
example addresses with your test users. Keep this table disconnected. Create a role with
the expression in [depot-role.dax](depot-role.dax) on **DimRoute**. Test with View as / Other
user: a North viewer should only see R01–R03; an unknown user should see no routes.
Role membership and workspace access must also be configured and tested when publishing
to Power BI Service. The sample does not provision users or publish a report.

## Refresh

For another local snapshot, update ExportFolder and refresh. Power BI Service refresh of
local files requires an appropriate gateway or a supported cloud source. The optional
Synapse SQL view can expose one committed cloud snapshot; automatic view updates and
scheduled Power BI refresh are not included. DAX, RLS and imports require validation in
Power BI Desktop before claiming the report is deployed.
