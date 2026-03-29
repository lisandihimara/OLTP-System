import mysql.connector
import config

cnx = mysql.connector.connect(host=config.DB_HOST, user=config.DB_USER, password=config.DB_PASSWORD, database=config.DATABASE_NAME)
cur = cnx.cursor()
cur.execute("SELECT DISTINCT DATE(sale_timestamp) AS sale_date, CAST(DATE_FORMAT(DATE(sale_timestamp), '%Y%m%d') AS UNSIGNED) AS date_key FROM sales WHERE sale_timestamp IS NOT NULL ORDER BY sale_date LIMIT 20")
print('sample rows:', cur.fetchall())
cur.execute("SELECT COUNT(*) FROM sales WHERE sale_timestamp IS NULL")
print('null count', cur.fetchone()[0])
cur.execute("SELECT COUNT(*) FROM sales WHERE DATE(sale_timestamp) = '0000-00-00'")
print('zero-date count', cur.fetchone()[0])
cur.execute("SELECT COUNT(*) FROM sales WHERE DATE(sale_timestamp) IS NULL")
print('date null count', cur.fetchone()[0])
cur.close()
cnx.close()