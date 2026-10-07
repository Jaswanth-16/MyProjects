let
    Source = fnReadCsv(ExportFolder, "dim_date.csv"),
    Typed = Table.TransformColumnTypes(Source, {
        {"date_key", type date}, {"year", Int64.Type}, {"month", Int64.Type}, {"weekday_sunday_zero", Int64.Type}
    }, "en-US")
in
    Typed
