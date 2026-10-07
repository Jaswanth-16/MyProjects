let
    Source = fnReadCsv(ExportFolder, "dim_route.csv"),
    Typed = Table.TransformColumnTypes(Source, {
        {"route_id", type text}, {"route_name", type text}, {"depot", type text}, {"distance_km", type number}
    }, "en-US")
in
    Typed
