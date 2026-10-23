import csv,random,datetime,pathlib
random.seed(700)
p=pathlib.Path(__file__).parent
products=[(i,f'Product {i}',random.choice(['Rice','Oil','Dal']),random.randint(40,600)) for i in range(1,31)]
customers=[(i,f'Customer {i}',random.choice(['Hyderabad','Bhimavaram','Vijayawada'])) for i in range(1,201)]
for name,header,rows in [('products.csv',['product_id','product_name','category','unit_price'],products),('customers.csv',['customer_id','customer_name','city'],customers)]:
 with (p/name).open('w',newline='') as f:
  w=csv.writer(f);w.writerow(header);w.writerows(rows)
with (p/'sales.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['sale_id','sale_date','customer_id','product_id','quantity','unit_price'])
 for i in range(1,2001):
  pr=random.choice(products);w.writerow([i,(datetime.date(2025,1,1)+datetime.timedelta(days=random.randrange(365))).isoformat(),random.choice(customers)[0],pr[0],random.randint(1,10),pr[3]])
print('Generated 3 deterministic sample CSV datasets')
