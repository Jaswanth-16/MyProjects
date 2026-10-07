// Create a Text parameter named ExportFolder pointing to one immutable export directory.
let
    Source = fnReadCsv(ExportFolder, "fact_trip.csv"),
    Nulls = Table.ReplaceValue(Source, "", null, Replacer.ReplaceValue,
        {"actual_arrival_utc", "delay_minutes", "on_time"}),
    Typed = Table.TransformColumnTypes(Nulls, {
        {"trip_id", type text}, {"route_id", type text}, {"service_date", type date},
        {"status", type text}, {"passengers", Int64.Type}, {"capacity", Int64.Type},
        {"revenue_paise", Int64.Type}, {"delay_minutes", type number}, {"on_time", Int64.Type}
    }, "en-US")
in
    Typed
