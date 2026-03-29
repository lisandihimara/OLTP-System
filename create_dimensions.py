"""
Create Dimension Tables - ETL Process (Extract, Transform, Load)
Transforms OLTP data into dimensional models
"""

from sqlalchemy import text
from config import engine
from datetime import datetime, timedelta

def create_dim_date(connection):
    """
    Create DIM_DATE dimension from sales transactions
    Extracts unique dates and generates date attributes
    """
    print("\n=== Creating DIM_DATE ===")
    
    connection.execute(text("DELETE FROM dim_date"))
    
    result = connection.execute(text("""
        INSERT INTO dim_date (
            date_key,
            full_date,
            day_of_month,
            month_number,
            month_name,
            quarter_number,
            year_number,
            day_name,
            is_weekend
        )
        SELECT DISTINCT
            CAST(DATE_FORMAT(DATE(s.sale_timestamp), '%%Y%%m%%d') AS UNSIGNED) AS date_key,
            DATE(s.sale_timestamp) AS full_date,
            DAY(DATE(s.sale_timestamp)) AS day_of_month,
            MONTH(DATE(s.sale_timestamp)) AS month_number,
            MONTHNAME(DATE(s.sale_timestamp)) AS month_name,
            QUARTER(DATE(s.sale_timestamp)) AS quarter_number,
            YEAR(DATE(s.sale_timestamp)) AS year_number,
            DAYNAME(DATE(s.sale_timestamp)) AS day_name,
            CASE
                WHEN DAYOFWEEK(DATE(s.sale_timestamp)) IN (1, 7) THEN TRUE
                ELSE FALSE
            END AS is_weekend
        FROM sales s
        WHERE s.sale_timestamp IS NOT NULL
          AND CAST(DATE_FORMAT(DATE(s.sale_timestamp), '%%Y%%m%%d') AS UNSIGNED) <> 0
    """))
    
    count = result.rowcount
    print(f"✓ DIM_DATE: {count} rows created")
    return count


def create_dim_customer(connection):
    """
    Create DIM_CUSTOMER dimension from OLTP customer table
    Maps customer_id (natural key) to customer_key (surrogate key)
    """
    print("\n=== Creating DIM_CUSTOMER ===")
    
    connection.execute(text("DELETE FROM dim_customer"))
    
    result = connection.execute(text("""
        INSERT INTO dim_customer (customer_id_nk, full_name, email, phone, created_at)
        SELECT
            c.customer_id,
            CONCAT(c.first_name, ' ', c.last_name) AS full_name,
            c.email,
            c.phone,
            c.created_at
        FROM customer c
    """))
    
    count = result.rowcount
    print(f"✓ DIM_CUSTOMER: {count} rows created")
    return count


def create_dim_product(connection):
    """
    Create DIM_PRODUCT dimension from OLTP product table
    Captures product attributes at point in time
    """
    print("\n=== Creating DIM_PRODUCT ===")
    
    connection.execute(text("DELETE FROM dim_product"))
    
    result = connection.execute(text("""
        INSERT INTO dim_product (product_id_nk, product_name, category, brand, base_unit_price, is_active)
        SELECT
            p.product_id,
            p.product_name,
            p.category,
            p.brand,
            p.unit_price,
            p.is_active
        FROM product p
    """))
    
    count = result.rowcount
    print(f"✓ DIM_PRODUCT: {count} rows created")
    return count


def create_dim_location(connection):
    """
    Create DIM_LOCATION dimension from OLTP location table
    Includes geographic hierarchy information
    """
    print("\n=== Creating DIM_LOCATION ===")
    
    connection.execute(text("DELETE FROM dim_location"))
    
    result = connection.execute(text("""
        INSERT INTO dim_location (location_id_nk, location_name, city, address, country, is_active)
        SELECT
            l.location_id,
            l.location_name,
            l.city,
            l.address,
            l.country,
            l.is_active
        FROM location l
    """))
    
    count = result.rowcount
    print(f"✓ DIM_LOCATION: {count} rows created")
    return count


def create_fact_sales_dw(connection):
    """
    Create FACT_SALES_DW fact table from sales transactions
    Joins dimension tables to get surrogate keys
    Grain: One row per sales transaction
    """
    print("\n=== Creating FACT_SALES_DW ===")
    
    connection.execute(text("DELETE FROM fact_sales_dw"))
    
    result = connection.execute(text("""
        INSERT INTO fact_sales_dw (
            sale_id_nk,
            date_key,
            customer_key,
            product_key,
            location_key,
            quantity,
            unit_price,
            total_amount,
            sale_timestamp
        )
        SELECT
            s.sale_id,
            CAST(DATE_FORMAT(DATE(s.sale_timestamp), '%%Y%%m%%d') AS UNSIGNED) AS date_key,
            dc.customer_key,
            dp.product_key,
            dl.location_key,
            s.quantity,
            s.unit_price,
            s.total_amount,
            s.sale_timestamp
        FROM sales s
        LEFT JOIN dim_customer dc ON dc.customer_id_nk = s.customer_id
        JOIN dim_product dp ON dp.product_id_nk = s.product_id
        JOIN dim_location dl ON dl.location_id_nk = s.location_id
        WHERE s.sale_timestamp IS NOT NULL
          AND CAST(DATE_FORMAT(DATE(s.sale_timestamp), '%%Y%%m%%d') AS UNSIGNED) <> 0
    """))
    
    count = result.rowcount
    print(f"✓ FACT_SALES_DW: {count} rows created")
    return count


def create_all_dimensions():
    """
    Main function to create all dimensions in correct order
    Order matters due to foreign key constraints
    """
    try:
        with engine.begin() as connection:
            print("\n" + "="*60)
            print("DIMENSIONAL MODEL CREATION (ETL PROCESS)")
            print("="*60)
            
            # Create dimensions in order (no dependencies)
            total_rows = 0
            total_rows += create_dim_date(connection)
            total_rows += create_dim_customer(connection)
            total_rows += create_dim_product(connection)
            total_rows += create_dim_location(connection)
            
            # Create fact table (depends on dimensions)
            total_rows += create_fact_sales_dw(connection)
            
            # Print summary
            print("\n" + "="*60)
            print("SUMMARY")
            print("="*60)
            
            result = connection.execute(text("SELECT COUNT(*) FROM dim_date"))
            print(f"DIM_DATE:       {result.scalar()} rows")
            
            result = connection.execute(text("SELECT COUNT(*) FROM dim_customer"))
            print(f"DIM_CUSTOMER:   {result.scalar()} rows")
            
            result = connection.execute(text("SELECT COUNT(*) FROM dim_product"))
            print(f"DIM_PRODUCT:    {result.scalar()} rows")
            
            result = connection.execute(text("SELECT COUNT(*) FROM dim_location"))
            print(f"DIM_LOCATION:   {result.scalar()} rows")
            
            result = connection.execute(text("SELECT COUNT(*) FROM fact_sales_dw"))
            print(f"FACT_SALES_DW:  {result.scalar()} rows")
            
            print("\n✓ All dimensions created successfully!")
            print("="*60)
            
    except Exception as e:
        print(f"\n✗ Error creating dimensions: {e}")
        raise


if __name__ == "__main__":
    create_all_dimensions()
