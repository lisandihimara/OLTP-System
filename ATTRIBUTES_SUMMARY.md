# OLTP Database - Table Attributes Summary

## Overview
This document details all attributes for the OLTP (Online Transaction Processing) database designed to efficiently handle sales transactions and support analytical queries.

---

## 1. CUSTOMER Table

**Purpose**: Store customer information for transaction processing

| Attribute | Data Type | Constraints | Description |
|-----------|-----------|-------------|-------------|
| customer_id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique identifier for each customer |
| first_name | VARCHAR(50) | NOT NULL | Customer's first name |
| last_name | VARCHAR(50) | NOT NULL | Customer's last name |
| email | VARCHAR(100) | NOT NULL, UNIQUE | Customer's email address (unique) |
| phone | VARCHAR(20) | NULL | Customer's contact number |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | Last update timestamp |

**Indexes**:
- PRIMARY KEY on `customer_id`
- UNIQUE INDEX on `email`

---

## 2. PRODUCT Table

**Purpose**: Store product catalog information

| Attribute | Data Type | Constraints | Description |
|-----------|-----------|-------------|-------------|
| product_id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique identifier for each product |
| product_name | VARCHAR(100) | NOT NULL | Name of the product |
| category | VARCHAR(50) | NOT NULL | Product category (Electronics, Clothing, etc.) |
| brand | VARCHAR(50) | NOT NULL | Brand/manufacturer name |
| unit_price | DECIMAL(10,2) | NOT NULL | Current selling price per unit |
| is_active | BOOLEAN | DEFAULT TRUE | Product availability status |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | Last update timestamp |

**Indexes**:
- PRIMARY KEY on `product_id`
- INDEX on `category` for filtering
- INDEX on `is_active` for active product queries

---

## 3. LOCATION Table

**Purpose**: Store sales location/store information

| Attribute | Data Type | Constraints | Description |
|-----------|-----------|-------------|-------------|
| location_id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique identifier for each location |
| location_name | VARCHAR(100) | NOT NULL | Name of the store/location |
| city | VARCHAR(50) | NOT NULL | City where location is situated |
| address | VARCHAR(200) | NULL | Complete street address |
| country | VARCHAR(50) | NOT NULL | Country code or name |
| is_active | BOOLEAN | DEFAULT TRUE | Location operational status |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | Last update timestamp |

**Indexes**:
- PRIMARY KEY on `location_id`
- INDEX on `city` for location-based queries
- INDEX on `country` for regional analysis

---

## 4. SALES Table (Fact Table)

**Purpose**: Store all sales transactions - the core OLTP table

| Attribute | Data Type | Constraints | Description |
|-----------|-----------|-------------|-------------|
| sale_id | INT | PRIMARY KEY, AUTO_INCREMENT | Unique identifier for each sale transaction |
| sale_timestamp | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Date and time of the sale |
| quantity | INT | NOT NULL, CHECK (quantity > 0) | Number of units sold |
| unit_price | DECIMAL(10,2) | NOT NULL | Price per unit at time of sale |
| total_amount | DECIMAL(12,2) | NOT NULL | Total transaction amount (quantity × unit_price) |
| customer_id | INT | FOREIGN KEY | Reference to CUSTOMER table |
| product_id | INT | FOREIGN KEY, NOT NULL | Reference to PRODUCT table |
| location_id | INT | FOREIGN KEY, NOT NULL | Reference to LOCATION table |

**Indexes** (Critical for OLTP Performance):
- PRIMARY KEY on `sale_id`
- INDEX on `product_id` (for product-based queries)
- INDEX on `location_id` (for location-based queries)
- INDEX on `sale_timestamp` (for time-based queries)
- COMPOSITE INDEX on `(product_id, location_id, sale_timestamp)` (for Query 1)
- COMPOSITE INDEX on `(product_id, location_id)` (for Query 2)
- FOREIGN KEY on `customer_id` → CUSTOMER(customer_id)
- FOREIGN KEY on `product_id` → PRODUCT(product_id)
- FOREIGN KEY on `location_id` → LOCATION(location_id)

---

## Query Support

### Query 1: Sales for a given product by location over a period of time
**Supported by**:
- Composite index: `(product_id, location_id, sale_timestamp)`
- Individual columns: `product_id`, `location_id`, `sale_timestamp`

### Query 2: Maximum number of sales for a given product over time for a given location
**Supported by**:
- Composite index: `(product_id, location_id)`
- Sale timestamp for time-based aggregation

---

## OLTP Design Principles Applied

1. **Normalization**: All tables are in 3NF to minimize redundancy
2. **Referential Integrity**: Foreign keys ensure data consistency
3. **Audit Trail**: `created_at` and `updated_at` timestamps on all tables
4. **Data Quality**: NOT NULL constraints on critical fields
5. **Performance**: Strategic indexes on columns used in WHERE/JOIN clauses
6. **Flexibility**: `is_active` flags for soft deletes
7. **Scalability**: Auto-increment primary keys for easy insertion
8. **Transaction Support**: Design supports ACID properties

---

## 5. DIM_DATE Table

**Purpose**: Date dimension for time-based analytics in the star schema

| Attribute | Data Type | Constraints | Description |
|-----------|-----------|-------------|-------------|
| date_key | INT | PRIMARY KEY (YYYYMMDD) | Surrogate/intelligent key for date |
| full_date | DATE | NOT NULL, UNIQUE | Calendar date |
| day_of_month | TINYINT | NOT NULL | Day number in month |
| month_number | TINYINT | NOT NULL | Month number (1-12) |
| month_name | VARCHAR(20) | NOT NULL | Month name |
| quarter_number | TINYINT | NOT NULL | Quarter number (1-4) |
| year_number | SMALLINT | NOT NULL | Year |
| day_name | VARCHAR(20) | NOT NULL | Day of week name |
| is_weekend | BOOLEAN | NOT NULL | Weekend indicator |

---

## 6. DIM_CUSTOMER Table

**Purpose**: Customer analytics dimension mapped from CUSTOMER

| Attribute | Data Type | Constraints | Description |
|-----------|-----------|-------------|-------------|
| customer_key | INT | PRIMARY KEY, AUTO_INCREMENT | Surrogate key |
| customer_id_nk | INT | NOT NULL, UNIQUE | Natural key from CUSTOMER.customer_id |
| full_name | VARCHAR(120) | NOT NULL | Combined customer first + last name |
| email | VARCHAR(100) | NOT NULL | Customer email |
| phone | VARCHAR(20) | NULL | Customer phone |
| created_at | TIMESTAMP | NOT NULL | Original customer creation timestamp |

---

## 7. DIM_PRODUCT Table

**Purpose**: Product analytics dimension mapped from PRODUCT

| Attribute | Data Type | Constraints | Description |
|-----------|-----------|-------------|-------------|
| product_key | INT | PRIMARY KEY, AUTO_INCREMENT | Surrogate key |
| product_id_nk | INT | NOT NULL, UNIQUE | Natural key from PRODUCT.product_id |
| product_name | VARCHAR(100) | NOT NULL | Product name |
| category | VARCHAR(50) | NOT NULL | Product category |
| brand | VARCHAR(50) | NOT NULL | Product brand |
| base_unit_price | DECIMAL(10,2) | NOT NULL | Product list/base price |
| is_active | BOOLEAN | NOT NULL | Product availability flag |

---

## 8. DIM_LOCATION Table

**Purpose**: Location analytics dimension mapped from LOCATION

| Attribute | Data Type | Constraints | Description |
|-----------|-----------|-------------|-------------|
| location_key | INT | PRIMARY KEY, AUTO_INCREMENT | Surrogate key |
| location_id_nk | INT | NOT NULL, UNIQUE | Natural key from LOCATION.location_id |
| location_name | VARCHAR(100) | NOT NULL | Store/location name |
| city | VARCHAR(50) | NOT NULL | City |
| address | VARCHAR(200) | NULL | Street address |
| country | VARCHAR(50) | NOT NULL | Country |
| is_active | BOOLEAN | NOT NULL | Operational status |

---

## 9. FACT_SALES_DW Table

**Purpose**: Analytical fact table linked to star-schema dimensions

| Attribute | Data Type | Constraints | Description |
|-----------|-----------|-------------|-------------|
| sales_key | BIGINT | PRIMARY KEY, AUTO_INCREMENT | Warehouse surrogate key |
| sale_id_nk | INT | NOT NULL, UNIQUE | Natural key from SALES.sale_id |
| date_key | INT | FOREIGN KEY, NOT NULL | Reference to DIM_DATE |
| customer_key | INT | FOREIGN KEY | Reference to DIM_CUSTOMER |
| product_key | INT | FOREIGN KEY, NOT NULL | Reference to DIM_PRODUCT |
| location_key | INT | FOREIGN KEY, NOT NULL | Reference to DIM_LOCATION |
| quantity | INT | NOT NULL | Quantity sold |
| unit_price | DECIMAL(10,2) | NOT NULL | Unit price at sale time |
| total_amount | DECIMAL(12,2) | NOT NULL | Transaction amount |
| sale_timestamp | TIMESTAMP | NOT NULL | Original sale timestamp |

---

## 10. DIM_COUNTRIES Table

**Purpose**: Geographic lookup for LEVEL country → subregion → region in the customers_dim hierarchy

| Attribute | Data Type | Constraints | Description |
|-----------|-----------|-------------|-------------|
| country_id | INT | PRIMARY KEY, AUTO_INCREMENT | Surrogate key (LEVEL country) |
| country_name | VARCHAR(100) | NOT NULL | Country name — *ATTRIBUTE country DETERMINES (country_name)* |
| country_subregion | VARCHAR(100) | NOT NULL | UN subregion (LEVEL subregion) |
| country_region | VARCHAR(50) | NOT NULL | Continental region (LEVEL region) |

**Indexes**:
- PRIMARY KEY on `country_id`
- INDEX on `country_subregion`
- INDEX on `country_region`

---

## 11. CUSTOMERS_DIM Table

**Purpose**: Customer geographic dimension implementing a 6-level Oracle-style hierarchy

Equivalent Oracle syntax:
```sql
CREATE DIMENSION customers_dim
   LEVEL customer   IS (customers.cust_id)
   LEVEL city       IS (customers.cust_city)
   LEVEL state      IS (customers.cust_state_province)
   LEVEL country    IS (countries.country_id)
   LEVEL subregion  IS (countries.country_subregion)
   LEVEL region     IS (countries.country_region)
   HIERARCHY geog_rollup (
      customer CHILD OF city CHILD OF state CHILD OF country
      JOIN KEY (customers.country_id) REFERENCES country
      CHILD OF subregion CHILD OF region
   )
   ATTRIBUTE customer DETERMINES
      (cust_first_name, cust_last_name, cust_gender,
       cust_marital_status, cust_year_of_birth,
       cust_income_level, cust_credit_limit)
   ATTRIBUTE country DETERMINES (countries.country_name)
;
```

| Attribute | Data Type | Constraints | Description |
|-----------|-----------|-------------|-------------|
| customer_key | INT | PRIMARY KEY, AUTO_INCREMENT | Surrogate key |
| cust_id | INT | NOT NULL, UNIQUE | Natural key (LEVEL customer) |
| cust_first_name | VARCHAR(50) | NOT NULL | First name — *ATTRIBUTE customer DETERMINES* |
| cust_last_name | VARCHAR(50) | NOT NULL | Last name — *ATTRIBUTE customer DETERMINES* |
| cust_gender | CHAR(1) | NULL | Gender (M/F/O) — *ATTRIBUTE customer DETERMINES* |
| cust_marital_status | VARCHAR(20) | NULL | Marital status — *ATTRIBUTE customer DETERMINES* |
| cust_year_of_birth | YEAR | NULL | Birth year — *ATTRIBUTE customer DETERMINES* |
| cust_income_level | VARCHAR(30) | NULL | Income band — *ATTRIBUTE customer DETERMINES* |
| cust_credit_limit | DECIMAL(12,2) | NULL | Credit limit — *ATTRIBUTE customer DETERMINES* |
| cust_city | VARCHAR(100) | NOT NULL | City (LEVEL city) |
| cust_state_province | VARCHAR(100) | NOT NULL | State/province (LEVEL state) |
| country_id | INT | FOREIGN KEY, NOT NULL | JOIN KEY → DIM_COUNTRIES (LEVEL country) |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Insert timestamp |
| updated_at | TIMESTAMP | ON UPDATE CURRENT_TIMESTAMP | Last update timestamp |

**Indexes**:
- PRIMARY KEY on `customer_key`
- UNIQUE INDEX on `cust_id`
- INDEX on `cust_city`
- INDEX on `cust_state_province`
- INDEX on `country_id`
- COMPOSITE INDEX on `(cust_state_province, country_id)` for hierarchy traversal
- FOREIGN KEY `country_id` → DIM_COUNTRIES(country_id)

**View**: `vw_customers_geog_rollup` flattens all 6 levels in a single query:
```
cust_id | city | state | country_name | subregion | region
```

**geog_rollup Hierarchy Path**:
```
customer → city → state → country → subregion → region
(customers_dim)     FK country_id   (dim_countries)
```
