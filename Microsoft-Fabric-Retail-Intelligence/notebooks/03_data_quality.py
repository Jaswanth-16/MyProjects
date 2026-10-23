from pyspark.sql import functions as F
s=spark.table('silver_sales')
checks={
 'nonempty':s.count()>0,
 'unique_sale_id':s.count()==s.select('sale_id').distinct().count(),
 'valid_revenue':s.filter(F.col('revenue').isNull() | (F.col('revenue')<0)).count()==0,
 'valid_dates':s.filter(F.col('sale_date').isNull()).count()==0,
 'customer_fk':s.join(spark.table('silver_customers'),'customer_id','left_anti').count()==0,
 'product_fk':s.join(spark.table('silver_products'),'product_id','left_anti').count()==0,
}
log=spark.createDataFrame([(k,bool(v)) for k,v in checks.items()],['check_name','passed']).withColumn('checked_at',F.current_timestamp())
log.write.format('delta').mode('append').saveAsTable('quality_results')
assert all(checks.values()),f'Data quality failures: {[k for k,v in checks.items() if not v]}'
