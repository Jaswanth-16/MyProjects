-- Execute in Lakehouse SQL analytics endpoint after notebooks run.
SELECT category, SUM(total_revenue) AS revenue, SUM(units_sold) AS units
FROM gold_daily_sales GROUP BY category ORDER BY revenue DESC;
SELECT city, SUM(total_revenue) AS revenue
FROM gold_daily_sales GROUP BY city ORDER BY revenue DESC;
