"""
customers_dim.py
================
Implements the CUSTOMERS_DIM geographic hierarchy for the OLTP Sales System.

Equivalent Oracle OLAP concept:
---------------------------------
CREATE DIMENSION customers_dim
   LEVEL customer   IS (customers.cust_id)
   LEVEL city       IS (customers.cust_city)
   LEVEL state      IS (customers.cust_state_province)
   LEVEL country    IS (countries.country_id)
   LEVEL subregion  IS (countries.country_subregion)
   LEVEL region     IS (countries.country_region)
   HIERARCHY geog_rollup (
      customer  CHILD OF city  CHILD OF state  CHILD OF country
      JOIN KEY (customers.country_id) REFERENCES country
      CHILD OF subregion  CHILD OF region
   )
   ATTRIBUTE customer DETERMINES
      (cust_first_name, cust_last_name, cust_gender,
       cust_marital_status, cust_year_of_birth,
       cust_income_level, cust_credit_limit)
   ATTRIBUTE country DETERMINES (countries.country_name)
;

MySQL Implementation:
---------------------
  dim_countries  → holds levels: country, subregion, region
                   + ATTRIBUTE country DETERMINES (country_name)
  customers_dim  → holds levels: customer, city, state
                   + JOIN KEY country_id → dim_countries
                   + ATTRIBUTE customer DETERMINES (first_name, ...)
  vw_customers_geog_rollup → flattened view of all 6 levels
"""

from sqlalchemy import text
from config import engine


# ===========================================================
# DDL:  Create the two dimension tables
# ===========================================================

CREATE_DIM_COUNTRIES = """
CREATE TABLE IF NOT EXISTS dim_countries (
    country_id        INT AUTO_INCREMENT PRIMARY KEY,
    country_name      VARCHAR(100) NOT NULL,
    country_subregion VARCHAR(100) NOT NULL,
    country_region    VARCHAR(50)  NOT NULL,
    INDEX idx_dim_countries_subregion (country_subregion),
    INDEX idx_dim_countries_region    (country_region)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='LEVEL country -> subregion -> region  |  ATTRIBUTE country DETERMINES (country_name)';
"""

CREATE_CUSTOMERS_DIM = """
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
  COMMENT='LEVEL customer->city->state  JOIN KEY country_id->dim_countries';
"""

CREATE_VIEW_GEOG_ROLLUP = """
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
JOIN dim_countries  co ON cd.country_id = co.country_id;
"""


# ===========================================================
# Sample data: dim_countries
#   (LEVEL country / subregion / region)
#   + ATTRIBUTE country DETERMINES (country_name)
# ===========================================================
SAMPLE_COUNTRIES = [
    # (country_name,                    country_subregion,          country_region)
    ("United States of America",        "Northern America",          "Americas"),
    ("United Kingdom",                  "Northern Europe",           "Europe"),
    ("Canada",                          "Northern America",          "Americas"),
    ("Germany",                         "Western Europe",            "Europe"),
    ("Australia",                       "Australia and New Zealand", "Oceania"),
    ("India",                           "Southern Asia",             "Asia"),
    ("China",                           "Eastern Asia",              "Asia"),
    ("Brazil",                          "South America",             "Americas"),
    ("France",                          "Western Europe",            "Europe"),
    ("Japan",                           "Eastern Asia",              "Asia"),
]

# ===========================================================
# Sample data: customers_dim
#   (LEVEL customer / city / state  +  attributes)
#   city & state come from the store location the customer
#   belongs to; country_id is the JOIN KEY reference
# ===========================================================
SAMPLE_CUSTOMERS = [
    # cust_id, first, last, gender, marital, birth_year,
    #   income_level, credit_limit, city, state, country_id
    (1001, "James",   "Carter",    "M", "Married",  1985, "L: 300,000 and above", 15000.00,
     "New York",    "New York",          1),   # USA
    (1002, "Emma",    "Williams",  "F", "Single",   1993, "F: 110,000 - 129,999", 8000.00,
     "Los Angeles", "California",        1),   # USA
    (1003, "Oliver",  "Thompson",  "M", "Single",   1990, "G: 130,000 - 149,999", 9500.00,
     "London",      "England",           2),   # UK
    (1004, "Sophia",  "Brown",     "F", "Married",  1978, "K: 250,000 - 299,999", 12000.00,
     "Toronto",     "Ontario",           3),   # Canada
    (1005, "Liam",    "Müller",    "M", "Divorced", 1982, "H: 150,000 - 169,999", 10000.00,
     "Berlin",      "Berlin",            4),   # Germany
    (1006, "Ava",     "Johnson",   "F", "Single",   1997, "C: 50,000 - 69,999",   5000.00,
     "Sydney",      "New South Wales",   5),   # Australia
    (1007, "Noah",    "Sharma",    "M", "Married",  1980, "J: 190,000 - 249,999", 11000.00,
     "Mumbai",      "Maharashtra",       6),   # India
    (1008, "Isabella","Wang",      "F", "Single",   1995, "D: 70,000 - 89,999",   6500.00,
     "Shanghai",    "Shanghai",          7),   # China
    (1009, "Lucas",   "Silva",     "M", "Married",  1976, "L: 300,000 and above", 14000.00,
     "São Paulo",   "São Paulo",         8),   # Brazil
    (1010, "Mia",     "Dupont",    "F", "Single",   1991, "E: 90,000 - 109,999",  7200.00,
     "Paris",       "Île-de-France",     9),   # France
    (1011, "Ethan",   "Tanaka",    "M", "Married",  1983, "I: 170,000 - 189,999", 10500.00,
     "Tokyo",       "Tokyo",            10),   # Japan
    (1012, "Amelia",  "Davis",     "F", "Single",   1999, "B: 30,000 - 49,999",   4000.00,
     "Chicago",     "Illinois",          1),   # USA
]


# ===========================================================
# Functions
# ===========================================================

def create_dimension_tables():
    """Create dim_countries, customers_dim, and the rollup view."""
    with engine.connect() as conn:
        conn.execute(text(CREATE_DIM_COUNTRIES))
        conn.execute(text(CREATE_CUSTOMERS_DIM))
        conn.execute(text(CREATE_VIEW_GEOG_ROLLUP))
        conn.commit()
    print("  [OK] dim_countries  table created")
    print("  [OK] customers_dim  table created")
    print("  [OK] vw_customers_geog_rollup view created")


def populate_dim_countries():
    """
    Insert ATTRIBUTE country DETERMINES (country_name) rows.
    Level: country -> subregion -> region
    """
    insert_sql = text("""
        INSERT INTO dim_countries (country_name, country_subregion, country_region)
        VALUES (:name, :subregion, :region)
        ON DUPLICATE KEY UPDATE country_name = VALUES(country_name)
    """)
    with engine.connect() as conn:
        for name, subregion, region in SAMPLE_COUNTRIES:
            conn.execute(insert_sql, {"name": name, "subregion": subregion, "region": region})
        conn.commit()
    print(f"  [OK] Inserted {len(SAMPLE_COUNTRIES)} rows into dim_countries")


def populate_customers_dim():
    """
    Insert customer dimension rows.
    Level hierarchy: customer -> city -> state -> country (via JOIN KEY country_id)
    ATTRIBUTE customer DETERMINES (first_name, last_name, gender, ...)
    """
    insert_sql = text("""
        INSERT INTO customers_dim
            (cust_id, cust_first_name, cust_last_name, cust_gender,
             cust_marital_status, cust_year_of_birth,
             cust_income_level, cust_credit_limit,
             cust_city, cust_state_province, country_id)
        VALUES
            (:cust_id, :first, :last, :gender,
             :marital, :birth_year,
             :income, :credit,
             :city, :state, :country_id)
        ON DUPLICATE KEY UPDATE
            cust_first_name     = VALUES(cust_first_name),
            cust_last_name      = VALUES(cust_last_name),
            cust_gender         = VALUES(cust_gender),
            cust_marital_status = VALUES(cust_marital_status),
            cust_year_of_birth  = VALUES(cust_year_of_birth),
            cust_income_level   = VALUES(cust_income_level),
            cust_credit_limit   = VALUES(cust_credit_limit),
            cust_city           = VALUES(cust_city),
            cust_state_province = VALUES(cust_state_province),
            country_id          = VALUES(country_id)
    """)
    with engine.connect() as conn:
        for row in SAMPLE_CUSTOMERS:
            (cust_id, first, last, gender, marital, birth_year,
             income, credit, city, state, country_id) = row
            conn.execute(insert_sql, {
                "cust_id": cust_id, "first": first, "last": last,
                "gender": gender, "marital": marital, "birth_year": birth_year,
                "income": income, "credit": credit,
                "city": city, "state": state, "country_id": country_id,
            })
        conn.commit()
    print(f"  [OK] Inserted {len(SAMPLE_CUSTOMERS)} rows into customers_dim")


# ===========================================================
# Hierarchy / drill-down queries
# ===========================================================

def query_all_levels():
    """
    Full geog_rollup hierarchy:
      customer -> city -> state -> country -> subregion -> region
    Uses vw_customers_geog_rollup (all 6 levels flattened).
    """
    print("\n--- geog_rollup: All 6 hierarchy levels ---")
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT cust_id,
                   CONCAT(cust_first_name, ' ', cust_last_name) AS customer,
                   city, state, country_name, subregion, region
            FROM   vw_customers_geog_rollup
            ORDER  BY region, subregion, country_name, state, city, cust_id
        """)).fetchall()
    for r in rows:
        print(f"  [{r.region}] [{r.subregion}] [{r.country_name}] "
              f"[{r.state}] [{r.city}] -> {r.cust_id}: {r.customer}")


def rollup_by_region():
    """
    Drill-up to LEVEL region: count customers per region.
    """
    print("\n--- Rollup to LEVEL region ---")
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT region, COUNT(*) AS customer_count
            FROM   vw_customers_geog_rollup
            GROUP  BY region
            ORDER  BY region
        """)).fetchall()
    for r in rows:
        print(f"  Region: {r.region:<12} | Customers: {r.customer_count}")


def rollup_by_subregion():
    """
    Drill-up to LEVEL subregion: count customers per subregion.
    """
    print("\n--- Rollup to LEVEL subregion ---")
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT subregion, region, COUNT(*) AS customer_count
            FROM   vw_customers_geog_rollup
            GROUP  BY subregion, region
            ORDER  BY region, subregion
        """)).fetchall()
    for r in rows:
        print(f"  [{r.region}] {r.subregion:<30} | Customers: {r.customer_count}")


def rollup_by_country():
    """
    Drill-down to LEVEL country + ATTRIBUTE country DETERMINES (country_name).
    Also shows avg credit limit per country.
    """
    print("\n--- Rollup to LEVEL country (with attributes) ---")
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT country_name, subregion, region,
                   COUNT(*)              AS customer_count,
                   AVG(cust_credit_limit) AS avg_credit_limit
            FROM   vw_customers_geog_rollup
            GROUP  BY country_name, subregion, region
            ORDER  BY region, subregion, country_name
        """)).fetchall()
    for r in rows:
        print(f"  {r.country_name:<35} | Customers: {r.customer_count} "
              f"| Avg Credit: ${r.avg_credit_limit:,.2f}")


def drilldown_to_customer(country_name: str):
    """
    Drill down from country level all the way to individual customers.
    Shows ATTRIBUTE customer DETERMINES (gender, income_level, credit_limit).
    """
    print(f"\n--- Drill-down into country='{country_name}' ---")
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT cust_id,
                   CONCAT(cust_first_name, ' ', cust_last_name) AS full_name,
                   cust_gender         AS gender,
                   cust_marital_status AS marital_status,
                   cust_year_of_birth  AS birth_year,
                   cust_income_level   AS income_level,
                   cust_credit_limit   AS credit_limit,
                   city, state
            FROM   vw_customers_geog_rollup
            WHERE  country_name = :country
            ORDER  BY state, city, cust_id
        """), {"country": country_name}).fetchall()
    if not rows:
        print(f"  No customers found for country '{country_name}'")
        return
    for r in rows:
        print(f"  ID:{r.cust_id} | {r.full_name:<22} | {r.gender} | "
              f"{r.marital_status:<10} | Born:{r.birth_year} | "
              f"{r.income_level:<25} | Credit:${r.credit_limit:,.2f} "
              f"| {r.city}, {r.state}")


# ===========================================================
# Main
# ===========================================================

if __name__ == "__main__":
    print("=" * 60)
    print(" CUSTOMERS_DIM  –  6-Level Geographic Hierarchy")
    print("=" * 60)

    print("\n[1] Creating dimension tables and view...")
    create_dimension_tables()

    print("\n[2] Populating dim_countries (LEVEL country->subregion->region)...")
    populate_dim_countries()

    print("\n[3] Populating customers_dim (LEVEL customer->city->state + JOIN KEY country_id)...")
    populate_customers_dim()

    # ---- Hierarchy queries ----
    query_all_levels()
    rollup_by_region()
    rollup_by_subregion()
    rollup_by_country()
    drilldown_to_customer("United States of America")

    print("\n" + "=" * 60)
    print(" Done. customers_dim hierarchy is fully operational.")
    print("=" * 60)
