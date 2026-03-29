import mysql.connector
from config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DATABASE_NAME

DB_CONFIG = {
    'user': DB_USER,
    'password': DB_PASSWORD,
    'host': DB_HOST,
    'port': DB_PORT,
    'database': DATABASE_NAME
}

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()

# Test the validation query
cursor.execute("""
    SELECT COUNT(*) FROM staging_sales
    WHERE sale_timestamp IS NULL
       OR CAST(DATE_FORMAT(DATE(sale_timestamp), '%Y%m%d') AS UNSIGNED) = 0
""")
invalid_count = cursor.fetchone()[0]
print(f"Invalid date records: {invalid_count}")

# Test individual conditions
cursor.execute("SELECT COUNT(*) FROM staging_sales WHERE sale_timestamp IS NULL")
null_count = cursor.fetchone()[0]
print(f"NULL timestamps: {null_count}")

cursor.execute("SELECT COUNT(*) FROM staging_sales WHERE CAST(DATE_FORMAT(DATE(sale_timestamp), '%Y%m%d') AS UNSIGNED) = 0")
zero_count = cursor.fetchone()[0]
print(f"Zero date keys: {zero_count}")

# Check some actual values
cursor.execute("SELECT sale_timestamp, DATE_FORMAT(DATE(sale_timestamp), '%Y%m%d'), CAST(DATE_FORMAT(DATE(sale_timestamp), '%Y%m%d') AS UNSIGNED) FROM staging_sales LIMIT 5")
results = cursor.fetchall()
print("\nSample validation results:")
for row in results:
    print(f"  Timestamp: {row[0]}, Format: {row[1]}, Cast: {row[2]}")

cursor.close()
conn.close()