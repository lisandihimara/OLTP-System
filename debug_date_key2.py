import mysql.connector
import config

cnx = mysql.connector.connect(host=config.DB_HOST, user=config.DB_USER, password=config.DB_PASSWORD, database=config.DATABASE_NAME)
cur = cnx.cursor()
cur.execute("SELECT CAST(DATE_FORMAT(sale_date, '%Y%m%d') AS UNSIGNED) AS date_key, sale_date FROM (SELECT DISTINCT DATE(sale_timestamp) AS sale_date FROM sales WHERE sale_timestamp IS NOT NULL AND DATE(sale_timestamp) != '0000-00-00') dates")
rows = cur.fetchall()
print('total dates', len(rows))
zero = [r for r in rows if r[0]==0]
if zero:
    print('found zero', zero[:10])
else:
    print('no zero date_key')

keys = [r[0] for r in rows]
dups = [k for k in set(keys) if keys.count(k) > 1]
print('duplicate keys', dups[:10], 'count', len(dups))

cur.close()
cnx.close()