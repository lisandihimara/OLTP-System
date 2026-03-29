# OLTP Sales System

A complete Online Transaction Processing (OLTP) database system for managing customer sales across multiple locations, now extended with a dimensional (star schema) layer for analytics.

## 📋 Project Overview

This project implements a normalized OLTP database design with four core tables:
- **CUSTOMER**: Customer information
- **PRODUCT**: Product catalog
- **LOCATION**: Store/sales locations
- **SALES**: Transaction records (fact table)

It also includes a warehouse-oriented star schema:
- **DIM_DATE**: Calendar attributes for time analysis
- **DIM_CUSTOMER**: Customer analytics dimension
- **DIM_PRODUCT**: Product analytics dimension
- **DIM_LOCATION**: Location analytics dimension
- **FACT_SALES_DW**: Analytical sales fact table keyed by dimensions

And a 6-level geographic dimension modelled after Oracle's `CREATE DIMENSION` syntax:
- **DIM_COUNTRIES**: Geographic lookup — LEVEL country → subregion → region
- **CUSTOMERS_DIM**: Customer dimension — LEVEL customer → city → state → (JOIN KEY) country
- **VW_CUSTOMERS_GEOG_ROLLUP**: Flattened view of all 6 hierarchy levels

## 🎯 Supported Queries

The database is optimized to efficiently answer:

1. **Sales for a given product by location over a period of time**
   - Filter by product, location, and date range
   - Returns aggregated sales metrics

2. **Maximum number of sales for a given product over time for a given location**
   - Identifies peak sales periods
   - Supports inventory and demand planning

## 🗄️ Database Schema

```
CUSTOMER (customer_id, first_name, last_name, email, phone, created_at, updated_at)
PRODUCT (product_id, product_name, category, brand, unit_price, is_active, created_at, updated_at)
LOCATION (location_id, location_name, city, address, country, is_active, created_at, updated_at)
SALES (sale_id, sale_timestamp, quantity, unit_price, total_amount, customer_id, product_id, location_id)

DIM_DATE (date_key, full_date, day_of_month, month_number, month_name, quarter_number, year_number, day_name, is_weekend)
DIM_CUSTOMER (customer_key, customer_id_nk, full_name, email, phone, created_at)
DIM_PRODUCT (product_key, product_id_nk, product_name, category, brand, base_unit_price, is_active)
DIM_LOCATION (location_key, location_id_nk, location_name, city, address, country, is_active)
FACT_SALES_DW (sales_key, sale_id_nk, date_key, customer_key, product_key, location_key, quantity, unit_price, total_amount, sale_timestamp)

DIM_COUNTRIES (country_id, country_name, country_subregion, country_region)
CUSTOMERS_DIM (customer_key, cust_id, cust_first_name, cust_last_name, cust_gender, cust_marital_status, cust_year_of_birth, cust_income_level, cust_credit_limit, cust_city, cust_state_province, country_id)
```

See [ATTRIBUTES_SUMMARY.md](ATTRIBUTES_SUMMARY.md) for detailed attribute specifications.

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- MySQL Server 5.7+ or 8.0+
- pip (Python package manager)

### Installation

1. **Install Python dependencies**
```powershell
pip install -r requirements.txt
```

2. **Configure database connection**
Edit `config.py` and update your MySQL credentials:
```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_password_here',  # UPDATE THIS
    'port': 3306
}
```

3. **Test database connection**
```powershell
python test_connection.py
```

4. **Create database and tables**
```powershell
python create_db.py
```

5. **Load sample data**
```powershell
python sample_data.py
```

6. **Populate the geographic dimension (required before queries)**
```powershell
python customers_dim.py
```
This creates and fills `dim_countries` and `customers_dim` with the 6-level geographic hierarchy. `queries.py` expects these tables to exist — it does **not** run `customers_dim.py` automatically.

7. **Run sample queries**
```powershell
python queries.py
```

## 📁 File Structure

```
oltp_sales_system/
├── README.md                    # This file
├── ATTRIBUTES_SUMMARY.md        # Detailed table attributes
├── QUICKSTART.md                # Step-by-step setup guide
├── requirements.txt             # Python dependencies
├── config.py                    # Database configuration
├── schema.sql                   # SQL schema definition
├── test_connection.py           # Database connection test
├── create_db.py                 # Database setup script
├── sample_data.py               # Sample data generator
├── queries.py                   # Query demonstrations
├── app.py                       # Streamlit web UI for interactive queries
├── customers_dim.py             # 6-level geographic hierarchy dimension
├── check_data.py                # Data verification script
└── er_diagram.py                # ER diagram (ASCII + Mermaid)
```

## Web UI

You can run an interactive web interface for the same OLTP + dimensional queries:

```powershell
streamlit run app.py
```

The UI includes:
- Query 1: sales by product, location, and date range
- Query 2: peak sales day with period statistics
- Geography rollup/drill-down from `customers_dim`
- Toggle between `WITHOUT DIM` and `WITH DIM` query paths
- Daily trend charts for sales count and revenue
- Region distribution bar chart for customer rollup

## 💻 Usage Examples

### Query 1: Sales by Product, Location, and Time Period

```python
from queries import get_sales_by_product_location_time

results = get_sales_by_product_location_time(
    product_id=1,
    location_id=2,
    start_date='2024-01-01',
    end_date='2024-12-31'
)
```

### Query 2: Maximum Sales for Product at Location

```python
from queries import get_max_sales_for_product_location

results = get_max_sales_for_product_location(
    product_id=1,
    location_id=2,
    start_date='2024-01-01',
    end_date='2024-12-31'
)
```

### Query 3: Geographic Hierarchy Rollup (customers_dim)

```python
from queries import get_customers_by_region, get_customers_drilldown

# Rollup to region level
region_summary = get_customers_by_region()

# Drill down into a single country
us_customers = get_customers_drilldown("United States of America")
```

### Populate the geographic dimension

Run this **before** `queries.py`. It creates and seeds `dim_countries`, `customers_dim`, and `vw_customers_geog_rollup`:

```powershell
python customers_dim.py
```

## ⚡ Query Performance Comparison: Without vs With Dimension

`queries.py` automatically benchmarks every query **5 runs** and prints timing statistics plus a side-by-side comparison.

### How it works

| Step | Detail |
|------|--------|
| Benchmark function | `benchmark_query(fn, *args, runs=5)` — measures avg / min / max execution time in milliseconds using `time.perf_counter` |
| OLTP queries | Run directly against the normalized `sales + product + location` tables |
| Dimensional queries | Run against the pre-joined star schema `fact_sales_dw + dim_date + dim_product + dim_location` |

### Output printed by `queries.py`

```
================================================================================
QUERY PERFORMANCE
================================================================================

WITHOUT DIM
  Query 1 avg=X.XXX ms  min=X.XXX ms  max=X.XXX ms
  Query 2 avg=X.XXX ms  min=X.XXX ms  max=X.XXX ms

WITH DIM
  Query 1 avg=X.XXX ms  min=X.XXX ms  max=X.XXX ms
  Query 2 avg=X.XXX ms  min=X.XXX ms  max=X.XXX ms

PERFORMANCE DELTA
  Query 1 dim/oltp ratio = X.XXx
  Query 2 dim/oltp ratio = X.XXx
```

A ratio **< 1.0x** means the dimensional query is faster; **> 1.0x** means the OLTP query is faster.

### Comparison summary also printed

```
================================================================================
COMPARISON: WITHOUT DIM vs WITH DIM
================================================================================

1. WITHOUT DIM (OLTP)
   Source tables: sales + product + location
   Best for: live transaction queries and operational reporting

2. WITH DIM (Single Dimensional Schema)
   Source tables: fact_sales_dw + dim_date + dim_product + dim_location
                  + customers_dim + dim_countries
   Best for: aggregated analytics plus customer geographic rollup/drill-down

RESULT CHECK
   Query 1 WITHOUT DIM vs WITH DIM: sales_match=True, revenue_match=True
   Query 2 WITHOUT DIM vs WITH DIM: peak_day_match=True, peak_count_match=True

SUMMARY
   WITHOUT DIM = transaction-oriented normalized model
   WITH DIM    = one dimensional schema combining star analytics and customer geography hierarchy
```

### When dimensional queries are skipped

If `dim_q1_perf` / `dim_q2_perf` are `None` it means the dimensional tables were not ready (missing or empty). Run the setup steps in order to enable the WITH DIM columns:

```powershell
python create_db.py
python sample_data.py
python customers_dim.py
python queries.py      # now prints both WITHOUT DIM and WITH DIM timings
```

---

## 🔧 OLTP Design Features

- ✅ **ACID Compliance**: Full transaction support
- ✅ **Normalized Design**: 3NF schema minimizes data redundancy
- ✅ **Referential Integrity**: Foreign key constraints
- ✅ **Optimized Indexes**: Strategic indexing for query performance
- ✅ **Audit Trail**: Timestamp tracking on all tables
- ✅ **Data Quality**: NOT NULL and CHECK constraints
- ✅ **Scalability**: Auto-increment primary keys

## 📊 Sample Data

The `sample_data.py` script generates:
- 100 customers
- 20 products across 4 categories
- 10 locations across 5 countries
- 1,000 sales transactions
- Dimension rows derived from OLTP source tables
- 1,000 `fact_sales_dw` rows mapped to dimensional keys

The `customers_dim.py` script populates:
- 10 countries across 4 regions (Americas, Asia, Europe, Oceania)
- 12 sample customers mapped across all 6 geographic hierarchy levels

## 🔍 Performance Optimization

Key indexes for OLTP performance:

```sql
-- For Query 1: Product sales by location over time
INDEX idx_sales_product_location_time (product_id, location_id, sale_timestamp)

-- For Query 2: Maximum sales analysis
INDEX idx_sales_product_location (product_id, location_id)

-- General performance
INDEX idx_sales_timestamp (sale_timestamp)
```

## 📝 Notes

- All timestamps are stored in UTC
- Prices are stored with 2 decimal precision
- Email addresses must be unique per customer
- Foreign keys use ON DELETE RESTRICT to prevent orphaned records

## 🤝 Contributing

This is an educational project for OLTP database design. Feel free to extend with additional features:
- Payment processing
- Inventory management
- Customer loyalty programs
- Multi-currency support

## 📄 License

Educational use only.
