import mysql.connector
import config

cnx=mysql.connector.connect(host=config.DB_HOST,user=config.DB_USER,password=config.DB_PASSWORD,database=config.DATABASE_NAME)
cur=cnx.cursor()
cur.execute('SELECT COUNT(*) FROM sales')
print('sales',cur.fetchone()[0])
cur.execute('SELECT COUNT(*) FROM (SELECT DISTINCT DATE(sale_timestamp) AS d FROM sales) AS t')
print('distinct days',cur.fetchone()[0])
cur.execute('SELECT COUNT(*) FROM dim_date')
print('dim_date',cur.fetchone()[0])
cur.execute('SELECT COUNT(*) FROM fact_sales_dw')
print('fact',cur.fetchone()[0])
cur.execute('SELECT MIN(sale_timestamp), MAX(sale_timestamp) FROM sales')
print('minmax',cur.fetchone())
cur.execute('SELECT DATE_FORMAT(DATE(sale_timestamp), "%Y%m%d") FROM sales LIMIT 5')
print('sample datetime ->',cur.fetchall())
cur.close();cnx.close()