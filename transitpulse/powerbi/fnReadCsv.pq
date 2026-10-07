// Create a Blank Query named fnReadCsv and paste this function into Advanced Editor.
(ExportFolder as text, FileName as text) as table =>
let
    Source = Csv.Document(File.Contents(ExportFolder & "/" & FileName),
        [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true])
in
    Headers
