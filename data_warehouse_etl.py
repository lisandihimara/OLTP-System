"""
Data Warehouse Architecture with Staging Area and Sales Data Mart
Three-Layer Architecture:
  1. STAGING LAYER - Raw data extracted from OLTP (staging_*)
  2. INTEGRATION/CLEANSING - Data transformation and quality checks
  3. DATA MART LAYER - Star schema optimized for reporting (dim_* and fact_sales_dw)
"""

from sqlalchemy import text, func, literal_column
from config import engine
from datetime import datetime

def create_staging_layer(connection):
    """
    Create staging tables - exact replicas of OLTP source tables
    Used for raw data extraction before transformation
    """
    print("\n" + "="*70)
    print("STAGING LAYER CREATION")
    print("="*70)
    
    # Staging Customer
    print("\nCreating staging_customer...")
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS staging_customer (
            customer_id INT PRIMARY KEY,
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50) NOT NULL,
            email VARCHAR(100) NOT NULL,
            phone VARCHAR(20),
            created_at TIMESTAMP NULL,
            updated_at TIMESTAMP NULL,
            load_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'When record was loaded',
            source_system VARCHAR(50) DEFAULT 'OLTP',
            INDEX idx_staging_cust_email (email),
            INDEX idx_staging_cust_load (load_datetime)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        COMMENT='Staging: Raw customer data from OLTP'
    """))
    print("✓ staging_customer created")
    
    # Staging Product
    print("Creating staging_product...")
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS staging_product (
            product_id INT PRIMARY KEY,
            product_name VARCHAR(100) NOT NULL,
            category VARCHAR(50) NOT NULL,
            brand VARCHAR(50) NOT NULL,
            unit_price DECIMAL(10, 2) NOT NULL,
            is_active BOOLEAN,
            created_at TIMESTAMP NULL,
            updated_at TIMESTAMP NULL,
            load_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            source_system VARCHAR(50) DEFAULT 'OLTP',
            INDEX idx_staging_prod_cat (category),
            INDEX idx_staging_prod_load (load_datetime)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        COMMENT='Staging: Raw product data from OLTP'
    """))
    print("✓ staging_product created")
    
    # Staging Location
    print("Creating staging_location...")
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS staging_location (
            location_id INT PRIMARY KEY,
            location_name VARCHAR(100) NOT NULL,
            city VARCHAR(50) NOT NULL,
            address VARCHAR(200),
            country VARCHAR(50) NOT NULL,
            is_active BOOLEAN,
            created_at TIMESTAMP NULL,
            updated_at TIMESTAMP NULL,
            load_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            source_system VARCHAR(50) DEFAULT 'OLTP',
            INDEX idx_staging_loc_city (city),
            INDEX idx_staging_loc_load (load_datetime)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        COMMENT='Staging: Raw location data from OLTP'
    """))
    print("✓ staging_location created")
    
    # Staging Sales
    print("Creating staging_sales...")
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS staging_sales (
            sale_id INT PRIMARY KEY,
            sale_timestamp TIMESTAMP NOT NULL,
            quantity INT NOT NULL,
            unit_price DECIMAL(10, 2) NOT NULL,
            total_amount DECIMAL(12, 2) NOT NULL,
            customer_id INT,
            product_id INT NOT NULL,
            location_id INT NOT NULL,
            load_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            source_system VARCHAR(50) DEFAULT 'OLTP',
            is_processed BOOLEAN DEFAULT FALSE,
            error_message VARCHAR(500),
            INDEX idx_staging_sales_timestamp (sale_timestamp),
            INDEX idx_staging_sales_processed (is_processed),
            INDEX idx_staging_sales_load (load_datetime)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        COMMENT='Staging: Raw sales transactions from OLTP'
    """))
    print("✓ staging_sales created")
    
    print("\n✓ Staging layer created successfully!")


def load_staging_data(connection):
    """
    Extract data from OLTP to Staging Area
    First step of ETL: Extract
    """
    print("\n" + "="*70)
    print("EXTRACTING DATA TO STAGING LAYER (E of ETL)")
    print("="*70)
    
    # Load Staging Customer
    print("\nExtracting customer data...")
    connection.execute(text("DELETE FROM staging_customer"))
    result = connection.execute(text("""
        INSERT INTO staging_customer (customer_id, first_name, last_name, email, phone, created_at, updated_at, source_system)
        SELECT customer_id, first_name, last_name, email, phone, created_at, updated_at, 'OLTP'
        FROM customer
    """))
    print(f"✓ Loaded {result.rowcount} customer records")
    
    # Load Staging Product
    print("Extracting product data...")
    connection.execute(text("DELETE FROM staging_product"))
    result = connection.execute(text("""
        INSERT INTO staging_product (product_id, product_name, category, brand, unit_price, is_active, created_at, updated_at)
        SELECT product_id, product_name, category, brand, unit_price, is_active, created_at, updated_at
        FROM product
    """))
    print(f"✓ Loaded {result.rowcount} product records")
    
    # Load Staging Location
    print("Extracting location data...")
    connection.execute(text("DELETE FROM staging_location"))
    result = connection.execute(text("""
        INSERT INTO staging_location (location_id, location_name, city, address, country, is_active, created_at, updated_at)
        SELECT location_id, location_name, city, address, country, is_active, created_at, updated_at
        FROM location
    """))
    print(f"✓ Loaded {result.rowcount} location records")
    
    # Load Staging Sales
    print("Extracting sales data...")
    connection.execute(text("DELETE FROM staging_sales"))
    result = connection.execute(text("""
        INSERT INTO staging_sales (sale_id, sale_timestamp, quantity, unit_price, total_amount, customer_id, product_id, location_id)
        SELECT sale_id, sale_timestamp, quantity, unit_price, total_amount, customer_id, product_id, location_id
        FROM sales
    """))
    print(f"✓ Loaded {result.rowcount} sales records")
    
    print("\n✓ Data extraction to staging complete!")


def validate_staging_data(connection):
    """
    Data quality checks on staging area
    Identify problematic records before transformation
    """
    print("\n" + "="*70)
    print("DATA QUALITY VALIDATION")
    print("="*70)
    
    # Check for invalid dates
    print("\nValidating staging_sales...")
    result = connection.execute(text("""
        SELECT COUNT(*) FROM staging_sales
        WHERE sale_timestamp IS NULL
           OR CAST(DATE_FORMAT(DATE(sale_timestamp), :format_str) AS UNSIGNED) = 0
    """).bindparams(format_str='%Y%m%d'))
    invalid_dates = result.scalar()
    print(f"  Invalid date records: {invalid_dates}")

    # Debug: Check total count
    result = connection.execute(text("SELECT COUNT(*) FROM staging_sales"))
    total_count = result.scalar()
    print(f"  Total staging_sales records: {total_count}")

    # Check for missing customer references
    result = connection.execute(text("""
        SELECT COUNT(*) FROM staging_sales ss
        LEFT JOIN staging_customer sc ON ss.customer_id = sc.customer_id
        WHERE ss.customer_id IS NOT NULL AND sc.customer_id IS NULL
    """))
    orphan_customers = result.scalar()
    print(f"  Orphan customer references: {orphan_customers}")
    
    # Check for missing product references
    result = connection.execute(text("""
        SELECT COUNT(*) FROM staging_sales ss
        LEFT JOIN staging_product sp ON ss.product_id = sp.product_id
        WHERE sp.product_id IS NULL
    """))
    orphan_products = result.scalar()
    print(f"  Orphan product references: {orphan_products}")
    
    # Check for missing location references
    result = connection.execute(text("""
        SELECT COUNT(*) FROM staging_sales ss
        LEFT JOIN staging_location sl ON ss.location_id = sl.location_id
        WHERE sl.location_id IS NULL
    """))
    orphan_locations = result.scalar()
    print(f"  Orphan location references: {orphan_locations}")
    
    if invalid_dates + orphan_customers + orphan_products + orphan_locations == 0:
        print("\n✓ All data quality checks passed!")
    else:
        print("\n⚠ Data quality issues detected - review before transformation")


def load_data_mart(connection):
    """
    Load Data Mart from Staging Area (T of ETL - Transform)
    Transform raw data into star schema optimized for sales reporting
    """
    print("\n" + "="*70)
    print("LOADING DATA MART (T of ETL - Transform & Cleanse)")
    print("="*70)
    
    # Load DIM_DATE
    print("\nLoading DIM_DATE from staging_sales...")
    connection.execute(text("DELETE FROM dim_date"))
    result = connection.execute(text("""
        INSERT INTO dim_date (
            date_key, full_date, day_of_month, month_number, month_name,
            quarter_number, year_number, day_name, is_weekend
        )
        SELECT DISTINCT
            CAST(DATE_FORMAT(DATE(ss.sale_timestamp), :format_str) AS UNSIGNED),
            DATE(ss.sale_timestamp),
            DAY(DATE(ss.sale_timestamp)),
            MONTH(DATE(ss.sale_timestamp)),
            MONTHNAME(DATE(ss.sale_timestamp)),
            QUARTER(DATE(ss.sale_timestamp)),
            YEAR(DATE(ss.sale_timestamp)),
            DAYNAME(DATE(ss.sale_timestamp)),
            CASE WHEN DAYOFWEEK(DATE(ss.sale_timestamp)) IN (1,7) THEN TRUE ELSE FALSE END
        FROM staging_sales ss
        WHERE ss.sale_timestamp IS NOT NULL
          AND CAST(DATE_FORMAT(DATE(ss.sale_timestamp), :format_str) AS UNSIGNED) <> 0
    """).bindparams(format_str='%Y%m%d'))
    print(f"✓ DIM_DATE: {result.rowcount} rows loaded")
    
    # Load DIM_CUSTOMER
    print("Loading DIM_CUSTOMER from staging_customer...")
    connection.execute(text("DELETE FROM dim_customer"))
    result = connection.execute(text("""
        INSERT INTO dim_customer (customer_id_nk, full_name, email, phone, created_at)
        SELECT 
            sc.customer_id,
            CONCAT(sc.first_name, ' ', sc.last_name),
            sc.email,
            sc.phone,
            sc.created_at
        FROM staging_customer sc
    """))
    print(f"✓ DIM_CUSTOMER: {result.rowcount} rows loaded")
    
    # Load DIM_PRODUCT
    print("Loading DIM_PRODUCT from staging_product...")
    connection.execute(text("DELETE FROM dim_product"))
    result = connection.execute(text("""
        INSERT INTO dim_product (product_id_nk, product_name, category, brand, base_unit_price, is_active)
        SELECT 
            sp.product_id,
            sp.product_name,
            sp.category,
            sp.brand,
            sp.unit_price,
            sp.is_active
        FROM staging_product sp
    """))
    print(f"✓ DIM_PRODUCT: {result.rowcount} rows loaded")
    
    # Load DIM_LOCATION
    print("Loading DIM_LOCATION from staging_location...")
    connection.execute(text("DELETE FROM dim_location"))
    result = connection.execute(text("""
        INSERT INTO dim_location (location_id_nk, location_name, city, address, country, is_active)
        SELECT 
            sl.location_id,
            sl.location_name,
            sl.city,
            sl.address,
            sl.country,
            sl.is_active
        FROM staging_location sl
    """))
    print(f"✓ DIM_LOCATION: {result.rowcount} rows loaded")
    
    # Load FACT_SALES_DW
    print("Loading FACT_SALES_DW from staging_sales with dimension keys...")
    connection.execute(text("DELETE FROM fact_sales_dw"))
    result = connection.execute(text("""
        INSERT INTO fact_sales_dw (
            sale_id_nk, date_key, customer_key, product_key, location_key,
            quantity, unit_price, total_amount, sale_timestamp
        )
        SELECT
            ss.sale_id,
            CAST(DATE_FORMAT(DATE(ss.sale_timestamp), :format_str) AS UNSIGNED),
            dc.customer_key,
            dp.product_key,
            dl.location_key,
            ss.quantity,
            ss.unit_price,
            ss.total_amount,
            ss.sale_timestamp
        FROM staging_sales ss
        LEFT JOIN dim_customer dc ON dc.customer_id_nk = ss.customer_id
        JOIN dim_product dp ON dp.product_id_nk = ss.product_id
        JOIN dim_location dl ON dl.location_id_nk = ss.location_id
        WHERE ss.sale_timestamp IS NOT NULL
          AND CAST(DATE_FORMAT(DATE(ss.sale_timestamp), :format_str) AS UNSIGNED) <> 0
    """).bindparams(format_str='%Y%m%d'))
    print(f"✓ FACT_SALES_DW: {result.rowcount} rows loaded")
    
    print("\n✓ Data mart loading complete!")


def run_full_etl_pipeline():
    """
    Complete ETL Pipeline:
    1. Extract (OLTP → Staging)
    2. Validate (Quality checks on staging)
    3. Transform (Staging → Data Mart)
    4. Load (Data Mart ready for reporting)
    """
    try:
        with engine.begin() as connection:
            print("\n" + "="*70)
            print("DATA WAREHOUSE ETL PIPELINE")
            print("="*70)
            print("Architecture: OLTP → Staging → Data Mart (Star Schema)")
            
            # Step 1: Create staging layer
            create_staging_layer(connection)
            
            # Step 2: Extract data
            load_staging_data(connection)
            
            # Step 3: Validate data quality
            validate_staging_data(connection)
            
            # Step 4: Transform and load data mart
            load_data_mart(connection)
            
            # Summary
            print("\n" + "="*70)
            print("ETL PIPELINE SUMMARY")
            print("="*70)
            
            result = connection.execute(text("SELECT COUNT(*) FROM staging_customer"))
            print(f"\nSTAGING LAYER:")
            print(f"  staging_customer:   {result.scalar()} rows")
            
            result = connection.execute(text("SELECT COUNT(*) FROM staging_product"))
            print(f"  staging_product:    {result.scalar()} rows")
            
            result = connection.execute(text("SELECT COUNT(*) FROM staging_location"))
            print(f"  staging_location:   {result.scalar()} rows")
            
            result = connection.execute(text("SELECT COUNT(*) FROM staging_sales"))
            print(f"  staging_sales:      {result.scalar()} rows")
            
            result = connection.execute(text("SELECT COUNT(*) FROM dim_date"))
            print(f"\nDATA MART (STAR SCHEMA):")
            print(f"  dim_date:           {result.scalar()} rows")
            
            result = connection.execute(text("SELECT COUNT(*) FROM dim_customer"))
            print(f"  dim_customer:       {result.scalar()} rows")
            
            result = connection.execute(text("SELECT COUNT(*) FROM dim_product"))
            print(f"  dim_product:        {result.scalar()} rows")
            
            result = connection.execute(text("SELECT COUNT(*) FROM dim_location"))
            print(f"  dim_location:       {result.scalar()} rows")
            
            result = connection.execute(text("SELECT COUNT(*) FROM fact_sales_dw"))
            print(f"  fact_sales_dw:      {result.scalar()} rows (FACTS)")
            
            print("\n" + "="*70)
            print("✓ ETL PIPELINE COMPLETED SUCCESSFULLY!")
            print("="*70)
            
    except Exception as e:
        print(f"\n✗ Error in ETL pipeline: {e}")
        raise


if __name__ == "__main__":
    run_full_etl_pipeline()
