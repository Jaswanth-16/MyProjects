from pyspark.sql import functions as F
s=spark.table('silver_sales')
p=spark.table('silver_products').select('product_id','category','product_name')
c=spark.table('silver_customers').select('customer_id','city')
f=s.join(p,'product_id').join(c,'customer_id')
(f.groupBy('sale_date','category','city')
 .agg(F.round(F.sum('revenue'),2).alias('total_revenue'),F.sum('quantity').alias('units_sold'),F.count('*').alias('transactions'))
 .write.format('delta').mode('overwrite').option('overwriteSchema','true').saveAsTable('gold_daily_sales'))
