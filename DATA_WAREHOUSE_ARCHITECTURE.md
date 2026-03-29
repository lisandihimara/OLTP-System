# Data Warehouse Architecture for Sales Data Mart

## 3-Layer Data Warehouse Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    OLTP SYSTEM (Source)                      │
│         customer | product | location | sales               │
└─────────────────────────────────────────────────────────────┘
                              ↓
                    (E) EXTRACT
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              STAGING LAYER (Raw Data)                        │
│   staging_customer | staging_product | staging_location    │
│   staging_sales (with load_datetime, source tracking)      │
│                                                              │
│   Purpose: Raw replica of source, history, quality checks   │
└─────────────────────────────────────────────────────────────┘
                              ↓
                   (T) TRANSFORM & CLEANSE
                   (Quality Validation)
                              ↓
┌─────────────────────────────────────────────────────────────┐
│          DATA MART - STAR SCHEMA (Sales)                     │
│                                                              │
│   DIMENSIONS:                 FACT TABLE:                    │
│   • dim_date                  • fact_sales_dw               │
│   • dim_customer              (1 row per sales transaction) │
│   • dim_product                                              │
│   • dim_location              Grain: Sales Transaction       │
│                                                              │
│   Purpose: Optimized for reporting & analytics              │
└─────────────────────────────────────────────────────────────┘
                              ↓
                   (L) LOAD
                              ↓
┌─────────────────────────────────────────────────────────────┐
│          BI TOOLS & REPORTING                                │
│     (Tableau, Power BI, SQL Analytics, Dashboards)         │
└─────────────────────────────────────────────────────────────┘
```

---

## Why This Architecture?

### **Staging Layer Benefits:**
- ✅ Decouples source (OLTP) from transformation logic
- ✅ Captures raw data for audit/compliance
- ✅ Allows data quality checks before transformation
- ✅ Supports incremental loads and delta detection
- ✅ Historical tracking with `load_datetime`

### **Star Schema (Data Mart) Benefits:**
- ✅ Simplified queries for business users
- ✅ Optimized for analytical queries (vs normalized OLTP)
- ✅ Fast aggregations (pre-joined dimensions)
- ✅ Easy to understand business metrics
- ✅ Scalable for large fact tables

### **Choice: Star Schema vs Snowflake**
We chose **STAR SCHEMA** because:
- Sales data mart is a single business process (sales)
- Simple queries for reporting (fewer joins)
- Better performance for BI tools
- Snowflake is better for complex cross-domain analysis

---

## ETL Process (Extract, Transform, Load)

### **Step 1: Extract (OLTP → Staging)**
```
customer       → staging_customer
product        → staging_product
location       → staging_location
sales          → staging_sales
```
- Exact copy of source data
- Adds `load_datetime` and `source_system` tracking

### **Step 2: Validate (Quality Checks)**
Checks performed on staging data:
- Invalid dates (NULL, 0000-00-00)
- Orphan records (missing customer/product/location)
- Data type validations
- Business rule validations

### **Step 3: Transform (Staging → Data Mart)**
```
Staging Customer  ─┐
Staging Product   ├──→ Dimensional Model Creation
Staging Location  ┤
                  │
Staging Sales ────┴──→ Fact Table (with dimension keys)
```

**Transformations:**
- Concatenate customer names
- Generate date dimensions (day, month, quarter, year)
- Join sales with dimensions to get surrogate keys
- Calculate derived measures if needed

### **Step 4: Load (Ready for Reporting)**
Data mart tables are now:
- ✅ Consistent (all sources integrated)
- ✅ Trusted (quality validated)
- ✅ Optimized (star schema indexed)
- ✅ Timely (loaded regularly via ETL)

---

## Database Objects

### **Staging Tables** (schema.sql or create_db.py)
```sql
staging_customer   -- Raw customer data with load tracking
staging_product    -- Raw product data with load tracking
staging_location   -- Raw location data with load tracking
staging_sales      -- Raw sales with is_processed flag
```

### **Data Mart Tables** (already created)
```sql
dim_date       -- Time dimension (YYYYMMDD key)
dim_customer   -- Customer dimension (with customer_key surrogate)
dim_product    -- Product dimension (with product_key surrogate)
dim_location   -- Location dimension (with location_key surrogate)
fact_sales_dw  -- Sales fact table (1 row per transaction)
```

---

## Running the ETL Pipeline

### **Full Pipeline (E→T→L)**
```bash
python data_warehouse_etl.py
```

This runs:
1. Create staging tables
2. Extract data from OLTP
3. Validate data quality
4. Load data mart dimensions and facts
5. Print summary

### **Output Example**
```
======================================================================
DATA WAREHOUSE ETL PIPELINE
======================================================================
Architecture: OLTP → Staging → Data Mart (Star Schema)

======================================================================
STAGING LAYER CREATION
======================================================================
Creating staging_customer...
✓ staging_customer created
...

======================================================================
EXTRACTING DATA TO STAGING LAYER (E of ETL)
======================================================================
Extracting customer data...
✓ Loaded 100 customer records
...

======================================================================
DATA QUALITY VALIDATION
======================================================================
Validating staging_sales...
  Invalid date records: 0
  Orphan customer references: 0
...
✓ All data quality checks passed!

======================================================================
LOADING DATA MART (T of ETL - Transform & Cleanse)
======================================================================
...

======================================================================
ETL PIPELINE SUMMARY
======================================================================
STAGING LAYER:
  staging_customer:   100 rows
  staging_product:    20 rows
  staging_location:   10 rows
  staging_sales:      1000 rows

DATA MART (STAR SCHEMA):
  dim_date:           548 rows
  dim_customer:       100 rows
  dim_product:        20 rows
  dim_location:       10 rows
  fact_sales_dw:      1000 rows (FACTS)

======================================================================
✓ ETL PIPELINE COMPLETED SUCCESSFULLY!
======================================================================
```

---

## Example Reporting Queries

### **Total Sales by Customer**
```sql
SELECT 
    dc.full_name,
    COUNT(f.sales_key) AS num_transactions,
    SUM(f.total_amount) AS total_revenue,
    AVG(f.total_amount) AS avg_transaction_value
FROM fact_sales_dw f
JOIN dim_customer dc ON f.customer_key = dc.customer_key
GROUP BY dc.full_name
ORDER BY total_revenue DESC;
```

### **Sales by Month and Product**
```sql
SELECT 
    dd.year_number,
    dd.month_name,
    dp.product_name,
    SUM(f.quantity) AS units_sold,
    SUM(f.total_amount) AS revenue
FROM fact_sales_dw f
JOIN dim_date dd ON f.date_key = dd.date_key
JOIN dim_product dp ON f.product_key = dp.product_key
GROUP BY dd.year_number, dd.month_number, dd.month_name, dp.product_name
ORDER BY dd.year_number, dd.month_number;
```

### **Sales by Location**
```sql
SELECT 
    dl.country,
    dl.city,
    COUNT(*) AS transactions,
    SUM(f.total_amount) AS total_sales
FROM fact_sales_dw f
JOIN dim_location dl ON f.location_key = dl.location_key
GROUP BY dl.country, dl.city
ORDER BY total_sales DESC;
```

---

## Advantages of This Architecture

| Aspect | Benefit |
|--------|---------|
| **Separation** | Source system not impacted by analytics queries |
| **Quality** | Data validated in staging before analytics |
| **Performance** | Star schema optimized for BI queries |
| **History** | Staging keeps audit trail of extractions |
| **Scalability** | Staging act as buffer for large data volumes |
| **Flexibility** | Multiple data marts can source from staging |
| **Maintainability** | Clear ETL flow, easy to troubleshoot |

---

## Next Steps

1. Run `python data_warehouse_etl.py` to populate the data warehouse
2. Create BI dashboards using dim/fact tables
3. Schedule ETL as recurring job (daily/hourly)
4. Add more dimensions (time, geography hierarchies)
5. Implement slowly changing dimensions (SCD) for historical tracking
6. Add data quality monitoring and alerting
