import mysql.connector
import config
cnx = mysql.connector.connect(host=config.DB_HOST, user=config.DB_USER, password=config.DB_PASSWORD, database=config.DATABASE_NAME)
cur = cnx.cursor()
cur.execute('DELETE FROM dim_date')
cur.execute('INSERT INTO dim_date (date_key, full_date, day_of_month, month_number, month_name, quarter_number, year_number, day_name, is_weekend) SELECT DISTINCT CAST(DATE_FORMAT(DATE(s.sale_timestamp), "%Y%m%d") AS UNSIGNED), DATE(s.sale_timestamp), DAY(DATE(s.sale_timestamp)), MONTH(DATE(s.sale_timestamp)), MONTHNAME(DATE(s.sale_timestamp)), QUARTER(DATE(s.sale_timestamp)), YEAR(DATE(s.sale_timestamp)), DAYNAME(DATE(s.sale_timestamp)), CASE WHEN DAYOFWEEK(DATE(s.sale_timestamp)) IN (1,7) THEN TRUE ELSE FALSE END FROM sales s WHERE s.sale_timestamp IS NOT NULL AND CAST(DATE_FORMAT(DATE(s.sale_timestamp), "%Y%m%d") AS UNSIGNED) <> 0')
cur.execute('SELECT COUNT(*) FROM dim_date')
print('inserted', cur.fetchone()[0])
cur.close(); cnx.close()