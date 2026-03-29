-- ============================================
-- OLTP Sales System - Database Schema
-- ============================================
-- Purpose: Online Transaction Processing database
-- for managing customer sales across locations
-- ============================================

-- Create database
CREATE DATABASE IF NOT EXISTS oltp_sales_db;
USE oltp_sales_db;

-- ============================================
-- TABLE: CUSTOMER
-- ============================================
-- Stores customer information
CREATE TABLE IF NOT EXISTS customer (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_customer_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- TABLE: PRODUCT
-- ============================================
-- Stores product catalog
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- TABLE: LOCATION
-- ============================================
-- Stores sales location/store information
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- TABLE: SALES (Fact Table)
-- ============================================
-- Stores all sales transactions
CREATE TABLE IF NOT EXISTS sales (
    sale_id INT AUTO_INCREMENT PRIMARY KEY,
    sale_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10, 2) NOT NULL,
    total_amount DECIMAL(12, 2) NOT NULL,
    customer_id INT,
    product_id INT NOT NULL,
    location_id INT NOT NULL,
    
    -- Foreign key constraints
    CONSTRAINT fk_sales_customer FOREIGN KEY (customer_id) 
        REFERENCES customer(customer_id) ON DELETE RESTRICT,
    CONSTRAINT fk_sales_product FOREIGN KEY (product_id) 
        REFERENCES product(product_id) ON DELETE RESTRICT,
    CONSTRAINT fk_sales_location FOREIGN KEY (location_id) 
        REFERENCES location(location_id) ON DELETE RESTRICT,
    
    -- Performance indexes for OLTP queries
    INDEX idx_sales_timestamp (sale_timestamp),
    INDEX idx_sales_product (product_id),
    INDEX idx_sales_location (location_id),
    
    -- Composite indexes for specific query patterns
    INDEX idx_sales_product_location_time (product_id, location_id, sale_timestamp),
    INDEX idx_sales_product_location (product_id, location_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- DIMENSIONAL MODEL TABLES (STAR SCHEMA)
-- ============================================

-- Date dimension
CREATE TABLE IF NOT EXISTS dim_date (
    date_key INT PRIMARY KEY, -- YYYYMMDD
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Customer dimension
CREATE TABLE IF NOT EXISTS dim_customer (
    customer_key INT AUTO_INCREMENT PRIMARY KEY,
    customer_id_nk INT NOT NULL UNIQUE,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP NOT NULL,
    INDEX idx_dim_customer_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Product dimension
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Location dimension
CREATE TABLE IF NOT EXISTS dim_location (
    location_key INT AUTO_INCREMENT PRIMARY KEY,
    location_id_nk INT NOT NULL UNIQUE,
    location_name VARCHAR(100) NOT NULL,
    city VARCHAR(50) NOT NULL,
    address VARCHAR(200),
    country VARCHAR(50) NOT NULL,
    is_active BOOLEAN NOT NULL,
    INDEX idx_dim_location_city_country (city, country)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Warehouse fact table
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- VIEWS FOR COMMON QUERIES
-- ============================================

-- View: Sales with full details
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
JOIN location l ON s.location_id = l.location_id;

-- ============================================
-- USEFUL STATISTICS QUERIES
-- ============================================

-- Query 1: Sales for a given product by location over a period of time
-- Example usage (replace with actual values):
/*
SELECT 
    p.product_name,
    l.location_name,
    l.city,
    l.country,
    COUNT(*) AS number_of_sales,
    SUM(s.quantity) AS total_quantity_sold,
    SUM(s.total_amount) AS total_revenue,
    AVG(s.total_amount) AS avg_sale_amount,
    MIN(s.sale_timestamp) AS first_sale,
    MAX(s.sale_timestamp) AS last_sale
FROM sales s
JOIN product p ON s.product_id = p.product_id
JOIN location l ON s.location_id = l.location_id
WHERE p.product_id = 1  -- Replace with actual product_id
  AND l.location_id = 2  -- Replace with actual location_id
  AND s.sale_timestamp BETWEEN '2024-01-01' AND '2024-12-31'
GROUP BY p.product_name, l.location_name, l.city, l.country;
*/

-- Query 2: Maximum number of sales for a given product at a location
-- Example usage (replace with actual values):
/*
SELECT 
    p.product_name,
    l.location_name,
    DATE(s.sale_timestamp) AS sale_date,
    COUNT(*) AS number_of_sales,
    SUM(s.quantity) AS total_quantity
FROM sales s
JOIN product p ON s.product_id = p.product_id
JOIN location l ON s.location_id = l.location_id
WHERE p.product_id = 1  -- Replace with actual product_id
  AND l.location_id = 2  -- Replace with actual location_id
  AND s.sale_timestamp BETWEEN '2024-01-01' AND '2024-12-31'
GROUP BY p.product_name, l.location_name, DATE(s.sale_timestamp)
ORDER BY number_of_sales DESC
LIMIT 1;
*/

-- ============================================
-- CUSTOMERS DIMENSION (Geographic Hierarchy)
-- ============================================
-- Implements the equivalent of Oracle CREATE DIMENSION:
--
--   DIMENSION customers_dim
--     LEVEL customer  IS (customers.cust_id)
--     LEVEL city      IS (customers.cust_city)
--     LEVEL state     IS (customers.cust_state_province)
--     LEVEL country   IS (countries.country_id)
--     LEVEL subregion IS (countries.country_subregion)
--     LEVEL region    IS (countries.country_region)
--     HIERARCHY geog_rollup (
--       customer CHILD OF city CHILD OF state
--       CHILD OF country     -- JOIN KEY country_id
--       CHILD OF subregion CHILD OF region
--     )
--     ATTRIBUTE customer DETERMINES
--       (cust_first_name, cust_last_name, cust_gender,
--        cust_marital_status, cust_year_of_birth,
--        cust_income_level, cust_credit_limit)
--     ATTRIBUTE country DETERMINES (country_name)
-- ============================================

-- --------------------------------------------
-- Level 4-6 of hierarchy:  country → subregion → region
-- ATTRIBUTE country DETERMINES (country_name)
-- --------------------------------------------
CREATE TABLE IF NOT EXISTS dim_countries (
    country_id      INT AUTO_INCREMENT PRIMARY KEY,   -- LEVEL country
    country_name    VARCHAR(100) NOT NULL,            -- ATTRIBUTE country DETERMINES (country_name)
    country_subregion VARCHAR(100) NOT NULL,          -- LEVEL subregion
    country_region  VARCHAR(50)  NOT NULL,            -- LEVEL region

    INDEX idx_dim_countries_subregion (country_subregion),
    INDEX idx_dim_countries_region    (country_region)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='Geographic rollup levels: country -> subregion -> region';

-- --------------------------------------------
-- Level 1-3 of hierarchy:  customer → city → state
-- + JOIN KEY country_id → dim_countries (level 4)
-- ATTRIBUTE customer DETERMINES (first_name, last_name, ...)
-- --------------------------------------------
CREATE TABLE IF NOT EXISTS customers_dim (
    customer_key        INT AUTO_INCREMENT PRIMARY KEY,
    cust_id             INT NOT NULL UNIQUE,          -- LEVEL customer (natural key)

    -- ATTRIBUTE customer DETERMINES (...)
    cust_first_name     VARCHAR(50)  NOT NULL,
    cust_last_name      VARCHAR(50)  NOT NULL,
    cust_gender         CHAR(1)      DEFAULT NULL     COMMENT 'M / F / O',
    cust_marital_status VARCHAR(20)  DEFAULT NULL     COMMENT 'Single / Married / Divorced',
    cust_year_of_birth  YEAR         DEFAULT NULL,
    cust_income_level   VARCHAR(30)  DEFAULT NULL     COMMENT 'e.g. A: Below 30K',
    cust_credit_limit   DECIMAL(12,2) DEFAULT NULL,

    -- LEVEL city  (child of customer in geog_rollup)
    cust_city           VARCHAR(100) NOT NULL,

    -- LEVEL state (child of city in geog_rollup)
    cust_state_province VARCHAR(100) NOT NULL,

    -- JOIN KEY ... REFERENCES country
    country_id          INT NOT NULL,

    -- SCD Type 1 timestamps
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Enforce the JOIN KEY relationship (geog_rollup hierarchy link)
    CONSTRAINT fk_custdim_country
        FOREIGN KEY (country_id)
        REFERENCES dim_countries (country_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    -- Performance indexes matching hierarchy traversal
    INDEX idx_custdim_city          (cust_city),
    INDEX idx_custdim_state         (cust_state_province),
    INDEX idx_custdim_country       (country_id),
    INDEX idx_custdim_state_country (cust_state_province, country_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='customers_dim: 6-level geographic hierarchy customer->city->state->country->subregion->region';

-- ============================================
-- VIEW: Full geog_rollup hierarchy flattened
-- (equivalent to querying the dimension across
--  all 6 levels in one place)
-- ============================================
CREATE OR REPLACE VIEW vw_customers_geog_rollup AS
SELECT
    -- Level 1 - customer
    cd.cust_id,
    cd.cust_first_name,
    cd.cust_last_name,
    cd.cust_gender,
    cd.cust_marital_status,
    cd.cust_year_of_birth,
    cd.cust_income_level,
    cd.cust_credit_limit,
    -- Level 2
    cd.cust_city            AS city,
    -- Level 3
    cd.cust_state_province  AS state,
    -- Level 4
    co.country_id,
    co.country_name,
    -- Level 5
    co.country_subregion    AS subregion,
    -- Level 6
    co.country_region       AS region
FROM customers_dim  cd
JOIN dim_countries  co ON cd.country_id = co.country_id;
