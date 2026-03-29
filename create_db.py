"""
Create OLTP Sales Database and Tables using SQLAlchemy
"""
from sqlalchemy import text
from config import engine_without_db, engine, DATABASE_NAME

def create_database():
    """Create the database and tables"""
    try:
        # Create database
        print(f"Creating database: {DATABASE_NAME}")
        with engine_without_db.connect() as connection:
            connection.execution_options(isolation_level="AUTOCOMMIT")
            connection.execute(text(f"CREATE DATABASE IF NOT EXISTS {DATABASE_NAME}"))
            print(f"Database {DATABASE_NAME} is ready")
        
        # Connect to the database
        with engine.connect() as connection:
            connection.execution_options(isolation_level="AUTOCOMMIT")
            
            # Create CUSTOMER table
            print("Creating tables...")
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS customer (
                    customer_id INT AUTO_INCREMENT PRIMARY KEY,
                    first_name VARCHAR(50) NOT NULL,
                    last_name VARCHAR(50) NOT NULL,
                    email VARCHAR(100) NOT NULL UNIQUE,
                    phone VARCHAR(20),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_customer_email (email)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """))
            print("Table CUSTOMER created successfully!")
            
            # Create PRODUCT table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS product (
                    product_id INT AUTO_INCREMENT PRIMARY KEY,
                    product_name VARCHAR(100) NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    brand VARCHAR(50) NOT NULL,
                    unit_price DECIMAL(10, 2) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_product_category (category),
                    INDEX idx_product_active (is_active)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """))
            print("Table PRODUCT created successfully!")
            
            # Create LOCATION table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS location (
                    location_id INT AUTO_INCREMENT PRIMARY KEY,
                    location_name VARCHAR(100) NOT NULL,
                    city VARCHAR(50) NOT NULL,
                    address VARCHAR(200),
                    country VARCHAR(50) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_location_city (city),
                    INDEX idx_location_country (country)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """))
            print("Table LOCATION created successfully!")
            
            # Create SALES table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS sales (
                    sale_id INT AUTO_INCREMENT PRIMARY KEY,
                    sale_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    quantity INT NOT NULL CHECK (quantity > 0),
                    unit_price DECIMAL(10, 2) NOT NULL,
                    total_amount DECIMAL(12, 2) NOT NULL,
                    customer_id INT,
                    product_id INT NOT NULL,
                    location_id INT NOT NULL,
                    CONSTRAINT fk_sales_customer FOREIGN KEY (customer_id) 
                        REFERENCES customer(customer_id) ON DELETE RESTRICT,
                    CONSTRAINT fk_sales_product FOREIGN KEY (product_id) 
                        REFERENCES product(product_id) ON DELETE RESTRICT,
                    CONSTRAINT fk_sales_location FOREIGN KEY (location_id) 
                        REFERENCES location(location_id) ON DELETE RESTRICT,
                    INDEX idx_sales_timestamp (sale_timestamp),
                    INDEX idx_sales_product (product_id),
                    INDEX idx_sales_location (location_id),
                    INDEX idx_sales_product_location_time (product_id, location_id, sale_timestamp),
                    INDEX idx_sales_product_location (product_id, location_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """))
            print("Table SALES created successfully!")

            # Create DIM_DATE table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS dim_date (
                    date_key INT PRIMARY KEY,
                    full_date DATE NOT NULL UNIQUE,
                    day_of_month TINYINT NOT NULL,
                    month_number TINYINT NOT NULL,
                    month_name VARCHAR(20) NOT NULL,
                    quarter_number TINYINT NOT NULL,
                    year_number SMALLINT NOT NULL,
                    day_name VARCHAR(20) NOT NULL,
                    is_weekend BOOLEAN NOT NULL,
                    INDEX idx_dim_date_full_date (full_date),
                    INDEX idx_dim_date_year_month (year_number, month_number)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """))
            print("Table DIM_DATE created successfully!")

            # Create DIM_CUSTOMER table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS dim_customer (
                    customer_key INT AUTO_INCREMENT PRIMARY KEY,
                    customer_id_nk INT NOT NULL UNIQUE,
                    full_name VARCHAR(120) NOT NULL,
                    email VARCHAR(100) NOT NULL,
                    phone VARCHAR(20),
                    created_at TIMESTAMP NOT NULL,
                    INDEX idx_dim_customer_email (email)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """))
            print("Table DIM_CUSTOMER created successfully!")

            # Create DIM_PRODUCT table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS dim_product (
                    product_key INT AUTO_INCREMENT PRIMARY KEY,
                    product_id_nk INT NOT NULL UNIQUE,
                    product_name VARCHAR(100) NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    brand VARCHAR(50) NOT NULL,
                    base_unit_price DECIMAL(10, 2) NOT NULL,
                    is_active BOOLEAN NOT NULL,
                    INDEX idx_dim_product_category (category),
                    INDEX idx_dim_product_brand (brand)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """))
            print("Table DIM_PRODUCT created successfully!")

            # Create DIM_LOCATION table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS dim_location (
                    location_key INT AUTO_INCREMENT PRIMARY KEY,
                    location_id_nk INT NOT NULL UNIQUE,
                    location_name VARCHAR(100) NOT NULL,
                    city VARCHAR(50) NOT NULL,
                    address VARCHAR(200),
                    country VARCHAR(50) NOT NULL,
                    is_active BOOLEAN NOT NULL,
                    INDEX idx_dim_location_city_country (city, country)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """))
            print("Table DIM_LOCATION created successfully!")

            # Create FACT_SALES_DW table
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS fact_sales_dw (
                    sales_key BIGINT AUTO_INCREMENT PRIMARY KEY,
                    sale_id_nk INT NOT NULL UNIQUE,
                    date_key INT NOT NULL,
                    customer_key INT,
                    product_key INT NOT NULL,
                    location_key INT NOT NULL,
                    quantity INT NOT NULL,
                    unit_price DECIMAL(10, 2) NOT NULL,
                    total_amount DECIMAL(12, 2) NOT NULL,
                    sale_timestamp TIMESTAMP NOT NULL,
                    CONSTRAINT fk_fact_date FOREIGN KEY (date_key)
                        REFERENCES dim_date(date_key) ON DELETE RESTRICT,
                    CONSTRAINT fk_fact_customer FOREIGN KEY (customer_key)
                        REFERENCES dim_customer(customer_key) ON DELETE RESTRICT,
                    CONSTRAINT fk_fact_product FOREIGN KEY (product_key)
                        REFERENCES dim_product(product_key) ON DELETE RESTRICT,
                    CONSTRAINT fk_fact_location FOREIGN KEY (location_key)
                        REFERENCES dim_location(location_key) ON DELETE RESTRICT,
                    INDEX idx_fact_product_location_date (product_key, location_key, date_key),
                    INDEX idx_fact_sale_timestamp (sale_timestamp)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """))
            print("Table FACT_SALES_DW created successfully!")
            
            # Create view
            connection.execute(text("""
                CREATE OR REPLACE VIEW vw_sales_details AS
                SELECT 
                    s.sale_id,
                    s.sale_timestamp,
                    s.quantity,
                    s.unit_price,
                    s.total_amount,
                    c.customer_id,
                    CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
                    c.email AS customer_email,
                    p.product_id,
                    p.product_name,
                    p.category AS product_category,
                    p.brand AS product_brand,
                    l.location_id,
                    l.location_name,
                    l.city,
                    l.country
                FROM sales s
                LEFT JOIN customer c ON s.customer_id = c.customer_id
                JOIN product p ON s.product_id = p.product_id
                JOIN location l ON s.location_id = l.location_id
            """))
            print("View vw_sales_details created successfully!")

            # --------------------------------------------------------
            # CUSTOMERS DIMENSION  (6-level geographic hierarchy)
            # Implements Oracle-style CREATE DIMENSION customers_dim
            # --------------------------------------------------------

            # Level country → subregion → region
            # ATTRIBUTE country DETERMINES (country_name)
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS dim_countries (
                    country_id        INT AUTO_INCREMENT PRIMARY KEY,
                    country_name      VARCHAR(100) NOT NULL,
                    country_subregion VARCHAR(100) NOT NULL,
                    country_region    VARCHAR(50)  NOT NULL,
                    INDEX idx_dim_countries_subregion (country_subregion),
                    INDEX idx_dim_countries_region    (country_region)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                  COMMENT='LEVEL country->subregion->region | ATTRIBUTE country DETERMINES (country_name)'
            """))
            print("Table DIM_COUNTRIES created successfully!")

            # Level customer → city → state  +  JOIN KEY country_id
            # ATTRIBUTE customer DETERMINES (first_name, last_name, ...)
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS customers_dim (
                    customer_key        INT AUTO_INCREMENT PRIMARY KEY,
                    cust_id             INT NOT NULL UNIQUE,
                    cust_first_name     VARCHAR(50)   NOT NULL,
                    cust_last_name      VARCHAR(50)   NOT NULL,
                    cust_gender         CHAR(1)       DEFAULT NULL,
                    cust_marital_status VARCHAR(20)   DEFAULT NULL,
                    cust_year_of_birth  YEAR          DEFAULT NULL,
                    cust_income_level   VARCHAR(30)   DEFAULT NULL,
                    cust_credit_limit   DECIMAL(12,2) DEFAULT NULL,
                    cust_city           VARCHAR(100)  NOT NULL,
                    cust_state_province VARCHAR(100)  NOT NULL,
                    country_id          INT NOT NULL,
                    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    CONSTRAINT fk_custdim_country
                        FOREIGN KEY (country_id) REFERENCES dim_countries(country_id)
                        ON DELETE RESTRICT ON UPDATE CASCADE,
                    INDEX idx_custdim_city          (cust_city),
                    INDEX idx_custdim_state         (cust_state_province),
                    INDEX idx_custdim_country       (country_id),
                    INDEX idx_custdim_state_country (cust_state_province, country_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                  COMMENT='LEVEL customer->city->state  JOIN KEY country_id->dim_countries'
            """))
            print("Table CUSTOMERS_DIM created successfully!")

            # Flattened view across all 6 hierarchy levels
            connection.execute(text("""
                CREATE OR REPLACE VIEW vw_customers_geog_rollup AS
                SELECT
                    cd.cust_id,
                    cd.cust_first_name,
                    cd.cust_last_name,
                    cd.cust_gender,
                    cd.cust_marital_status,
                    cd.cust_year_of_birth,
                    cd.cust_income_level,
                    cd.cust_credit_limit,
                    cd.cust_city            AS city,
                    cd.cust_state_province  AS state,
                    co.country_id,
                    co.country_name,
                    co.country_subregion    AS subregion,
                    co.country_region       AS region
                FROM customers_dim  cd
                JOIN dim_countries  co ON cd.country_id = co.country_id
            """))
            print("View vw_customers_geog_rollup created successfully!")

            print("\n✓ All tables created successfully!")
        
    except Exception as e:
        print(f"✗ Error creating database: {e}")
        raise


def create_dimensions():
    """Create explicit dimension tables for star schema"""
    try:
        with engine.connect() as connection:
            connection.execution_options(isolation_level="AUTOCOMMIT")
            
            print("\n=== CREATING DIMENSION TABLES ===\n")
            
            # DIM_DATE - Time dimension
            print("Creating DIM_DATE...")
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS dim_date (
                    date_key INT PRIMARY KEY COMMENT 'YYYYMMDD format',
                    full_date DATE NOT NULL UNIQUE,
                    day_of_month TINYINT NOT NULL,
                    month_number TINYINT NOT NULL,
                    month_name VARCHAR(20) NOT NULL,
                    quarter_number TINYINT NOT NULL,
                    year_number SMALLINT NOT NULL,
                    day_name VARCHAR(20) NOT NULL,
                    is_weekend BOOLEAN NOT NULL,
                    INDEX idx_dim_date_full_date (full_date),
                    INDEX idx_dim_date_year_month (year_number, month_number)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                COMMENT='Time dimension table - grain: day'
            """))
            print("✓ DIM_DATE created")
            
            # DIM_CUSTOMER - Customer dimension
            print("Creating DIM_CUSTOMER...")
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS dim_customer (
                    customer_key INT AUTO_INCREMENT PRIMARY KEY,
                    customer_id_nk INT NOT NULL UNIQUE COMMENT 'Natural key from source',
                    full_name VARCHAR(120) NOT NULL,
                    email VARCHAR(100) NOT NULL,
                    phone VARCHAR(20),
                    created_at TIMESTAMP NOT NULL,
                    INDEX idx_dim_customer_email (email),
                    INDEX idx_dim_customer_nk (customer_id_nk)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                COMMENT='Customer dimension - includes customer attributes'
            """))
            print("✓ DIM_CUSTOMER created")
            
            # DIM_PRODUCT - Product dimension
            print("Creating DIM_PRODUCT...")
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS dim_product (
                    product_key INT AUTO_INCREMENT PRIMARY KEY,
                    product_id_nk INT NOT NULL UNIQUE COMMENT 'Natural key from source',
                    product_name VARCHAR(100) NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    brand VARCHAR(50) NOT NULL,
                    base_unit_price DECIMAL(10, 2) NOT NULL,
                    is_active BOOLEAN NOT NULL,
                    INDEX idx_dim_product_category (category),
                    INDEX idx_dim_product_brand (brand),
                    INDEX idx_dim_product_nk (product_id_nk)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                COMMENT='Product dimension - includes product attributes'
            """))
            print("✓ DIM_PRODUCT created")
            
            # DIM_LOCATION - Location dimension
            print("Creating DIM_LOCATION...")
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS dim_location (
                    location_key INT AUTO_INCREMENT PRIMARY KEY,
                    location_id_nk INT NOT NULL UNIQUE COMMENT 'Natural key from source',
                    location_name VARCHAR(100) NOT NULL,
                    city VARCHAR(50) NOT NULL,
                    address VARCHAR(200),
                    country VARCHAR(50) NOT NULL,
                    is_active BOOLEAN NOT NULL,
                    INDEX idx_dim_location_city_country (city, country),
                    INDEX idx_dim_location_nk (location_id_nk)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                COMMENT='Location dimension - includes location attributes'
            """))
            print("✓ DIM_LOCATION created")
            
            # FACT_SALES_DW - Fact table
            print("Creating FACT_SALES_DW...")
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS fact_sales_dw (
                    sales_key BIGINT AUTO_INCREMENT PRIMARY KEY,
                    sale_id_nk INT NOT NULL UNIQUE COMMENT 'Natural key from source',
                    date_key INT NOT NULL,
                    customer_key INT,
                    product_key INT NOT NULL,
                    location_key INT NOT NULL,
                    quantity INT NOT NULL,
                    unit_price DECIMAL(10, 2) NOT NULL,
                    total_amount DECIMAL(12, 2) NOT NULL,
                    sale_timestamp TIMESTAMP NOT NULL,
                    CONSTRAINT fk_fact_date FOREIGN KEY (date_key)
                        REFERENCES dim_date(date_key) ON DELETE RESTRICT,
                    CONSTRAINT fk_fact_customer FOREIGN KEY (customer_key)
                        REFERENCES dim_customer(customer_key) ON DELETE RESTRICT,
                    CONSTRAINT fk_fact_product FOREIGN KEY (product_key)
                        REFERENCES dim_product(product_key) ON DELETE RESTRICT,
                    CONSTRAINT fk_fact_location FOREIGN KEY (location_key)
                        REFERENCES dim_location(location_key) ON DELETE RESTRICT,
                    INDEX idx_fact_product_location_date (product_key, location_key, date_key),
                    INDEX idx_fact_sale_timestamp (sale_timestamp),
                    INDEX idx_fact_date_key (date_key),
                    INDEX idx_fact_customer_key (customer_key)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                COMMENT='Fact table for sales - grain: each sales transaction'
            """))
            print("✓ FACT_SALES_DW created")
            
            print("\n✓ All dimension tables created successfully!")
        
    except Exception as e:
        print(f"✗ Error creating dimensions: {e}")
        raise


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--dimensions-only":
        # Create only dimension tables
        create_dimensions()
    else:
        # Create full database with all tables
        create_database()
        print("\nTo create dimensions separately, run: python create_db.py --dimensions-only")
