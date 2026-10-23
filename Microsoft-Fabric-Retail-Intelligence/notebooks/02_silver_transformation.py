from pyspark.sql import functions as F
sales=spark.table('bronze_sales')
valid=(sales.dropDuplicates(['sale_id']).filter(
    F.col('sale_id').isNotNull() & F.col('customer_id').isNotNull() &
    F.col('product_id').isNotNull() & (F.col('quantity')>0) & (F.col('unit_price')>=0))
    .withColumn('sale_date',F.to_date('sale_date'))
    .withColumn('revenue',F.round(F.col('quantity')*F.col('unit_price'),2)))
valid.write.format('delta').mode('overwrite').option('overwriteSchema','true').saveAsTable('silver_sales')
for name,key in [('products','product_id'),('customers','customer_id')]:
    (spark.table(f'bronze_{name}').dropDuplicates([key]).filter(F.col(key).isNotNull())
     .write.format('delta').mode('overwrite').option('overwriteSchema','true').saveAsTable(f'silver_{name}'))
