"""
Check what sales data actually exists
"""
from sqlalchemy import text
from config import engine
from datetime import datetime, timedelta

with engine.connect() as connection:
    # Show date range of sales
    result = connection.execute(text("""
        SELECT 
            MIN(sale_timestamp) as first_sale,
            MAX(sale_timestamp) as last_sale,
            COUNT(*) as total_sales
        FROM sales
    """))
    row = result.fetchone()
    print("=" * 80)
    print("SALES DATA SUMMARY")
    print("=" * 80)
    print(f"First Sale: {row[0]}")
    print(f"Last Sale: {row[1]}")
    print(f"Total Sales: {row[2]}")
    
    # Show product/location combinations with sales
    print("\n" + "=" * 80)
    print("TOP 10 PRODUCT/LOCATION COMBINATIONS WITH MOST SALES")
    print("=" * 80)
    
    result = connection.execute(text("""
        SELECT 
            p.product_id,
            p.product_name,
            l.location_id,
            l.location_name,
            COUNT(*) as sales_count,
            SUM(s.total_amount) as revenue
        FROM sales s
        JOIN product p ON s.product_id = p.product_id
        JOIN location l ON s.location_id = l.location_id
        GROUP BY p.product_id, p.product_name, l.location_id, l.location_name
        ORDER BY sales_count DESC
        LIMIT 10
    """))
    
    for row in result:
        print(f"\nProduct: {row[1]} (ID: {row[0]})")
        print(f"Location: {row[3]} (ID: {row[2]})")
        print(f"Sales: {row[4]}, Revenue: ${row[5]:,.2f}")

    # -------------------------------------------------------
    # CUSTOMERS_DIM geographic hierarchy tables
    # -------------------------------------------------------
    print("\n" + "=" * 80)
    print("CUSTOMERS_DIM HIERARCHY SUMMARY")
    print("=" * 80)

    result = connection.execute(text("SELECT COUNT(*) FROM dim_countries"))
    print(f"dim_countries rows : {result.scalar()}")

    result = connection.execute(text("SELECT COUNT(*) FROM customers_dim"))
    print(f"customers_dim rows : {result.scalar()}")

    print("\n--- Region rollup (vw_customers_geog_rollup) ---")
    result = connection.execute(text("""
        SELECT region,
               COUNT(DISTINCT country_name) AS countries,
               COUNT(*) AS customers
        FROM   vw_customers_geog_rollup
        GROUP  BY region
        ORDER  BY region
    """))
    for row in result:
        print(f"  {row[0]:<15} | Countries: {row[1]} | Customers: {row[2]}")
