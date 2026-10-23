# Fabric PySpark notebook. Upload generated CSV files to Files/raw/ first.
from pyspark.sql import functions as F
base='Files/raw'
for name in ('sales','products','customers'):
    df=(spark.read.option('header',True).option('inferSchema',True)
        .csv(f'{base}/{name}.csv').withColumn('_ingested_at',F.current_timestamp()))
    df.write.format('delta').mode('overwrite').option('overwriteSchema','true').saveAsTable(f'bronze_{name}')
