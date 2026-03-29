"""
ER Diagram for OLTP Sales System
This file contains an ASCII representation and SQL to visualize the ER diagram
"""

# ============================================
# ER DIAGRAM (ASCII Art)
# ============================================

ER_DIAGRAM = """
+-------------+        +-------------+        +-------------+
|  CUSTOMER   |        |   PRODUCT   |        |  LOCATION   |
+-------------+        +-------------+        +-------------+
| PK customer_id |     | PK product_id |     | PK location_id |
| first_name     |     | product_name  |     | location_name  |
| last_name      |     | category      |     | city           |
| email (U)      |     | brand         |     | address        |
| phone          |     | unit_price    |     | country        |
| created_at     |     | is_active     |     | is_active      |
| updated_at     |     | created_at    |     | created_at     |
+-------------+        | updated_at    |     | updated_at     |
        |              +-------------+        +-------------+
        |                      |                      |
        | 0..*                 | 1..*                 | 1..*
        |                      |                      |
        +----------------------+----------------------+
                               |
                               | (FK references)
                               v
                   +-----------------------+
                   |         SALES         |
                   +-----------------------+
                   | PK sale_id            |
                   | sale_timestamp        |
                   | quantity              |
                   | unit_price            |
                   | total_amount          |
                   | FK customer_id  ------+----> CUSTOMER.customer_id
                   | FK product_id   ------+----> PRODUCT.product_id
                   | FK location_id  ------+----> LOCATION.location_id
                   +-----------------------+

Relationship Cardinality:
- CUSTOMER 1 -- 0..* SALES   (One customer can make zero or many sales)
- PRODUCT  1 -- 1..* SALES   (One product can be in one or many sales)
- LOCATION 1 -- 1..* SALES   (One location can process one or many sales)

Indexes for Performance:
- SALES.product_id, location_id, sale_timestamp (Composite for Query 1)
- SALES.product_id, location_id (Composite for Query 2)

======================================================================
CUSTOMERS_DIM  --  6-Level Geographic Hierarchy (Oracle-style CREATE DIMENSION)
======================================================================

geog_rollup hierarchy path:
  customer -> city -> state -> country -> subregion -> region

+---------------------------+        +---------------------------+
|      DIM_COUNTRIES        |        |       CUSTOMERS_DIM       |
+---------------------------+        +---------------------------+
| PK country_id             |<-------| PK customer_key           |
|    country_name           | FK     |    cust_id (NK)           |
|    country_subregion      |        |    cust_first_name        |
|    country_region         |        |    cust_last_name         |
+---------------------------+        |    cust_gender            |
  LEVEL country                      |    cust_marital_status    |
  LEVEL subregion                    |    cust_year_of_birth     |
  LEVEL region                       |    cust_income_level      |
  ATTRIBUTE country                  |    cust_credit_limit      |
    DETERMINES (country_name)        |    cust_city              |
                                     |    cust_state_province    |
                                     |    FK country_id          |
                                     +---------------------------+
                                       LEVEL customer
                                       LEVEL city
                                       LEVEL state
                                       ATTRIBUTE customer
                                         DETERMINES (first_name,
                                           last_name, gender, ...)

VIEW vw_customers_geog_rollup:
  Flattens all 6 levels:  cust_id | city | state | country_name
                          | subregion | region
"""

# ============================================
# Mermaid Diagram (for markdown/web rendering)
# ============================================

MERMAID_DIAGRAM = """
```mermaid
erDiagram
    CUSTOMER ||--o{ SALES : makes
    PRODUCT ||--|{ SALES : "sold in"
    LOCATION ||--|{ SALES : "processes"
    DIM_COUNTRIES ||--|{ CUSTOMERS_DIM : "JOIN KEY country_id"

    CUSTOMER {
        int customer_id PK
        varchar first_name
        varchar last_name
        varchar email UK
        varchar phone
        timestamp created_at
        timestamp updated_at
    }

    PRODUCT {
        int product_id PK
        varchar product_name
        varchar category
        varchar brand
        decimal unit_price
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    LOCATION {
        int location_id PK
        varchar location_name
        varchar city
        varchar address
        varchar country
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    SALES {
        int sale_id PK
        timestamp sale_timestamp
        int quantity
        decimal unit_price
        decimal total_amount
        int customer_id FK
        int product_id FK
        int location_id FK
    }

    DIM_COUNTRIES {
        int country_id PK
        varchar country_name
        varchar country_subregion
        varchar country_region
    }

    CUSTOMERS_DIM {
        int customer_key PK
        int cust_id UK
        varchar cust_first_name
        varchar cust_last_name
        char cust_gender
        varchar cust_marital_status
        year cust_year_of_birth
        varchar cust_income_level
        decimal cust_credit_limit
        varchar cust_city
        varchar cust_state_province
        int country_id FK
    }
```
"""

def print_er_diagram():
    """Print the ER diagram to console"""
    print(ER_DIAGRAM)

def save_mermaid_diagram(filename="ER_DIAGRAM.md"):
    """Save Mermaid diagram to a markdown file"""
    with open(filename, 'w') as f:
        f.write("# OLTP Sales System - Entity Relationship Diagram\n\n")
        f.write(MERMAID_DIAGRAM)
        f.write("\n\n## Relationships\n\n")
        f.write("- **CUSTOMER to SALES**: One-to-Many (1:0..*)\n")
        f.write("  - A customer can make zero or many purchases\n")
        f.write("  - A sale is associated with one customer (optional)\n\n")
        f.write("- **PRODUCT to SALES**: One-to-Many (1:1..*)\n")
        f.write("  - A product can be sold many times\n")
        f.write("  - Each sale must reference one product\n\n")
        f.write("- **LOCATION to SALES**: One-to-Many (1:1..*)\n")
        f.write("  - A location can process many sales\n")
        f.write("  - Each sale occurs at one location\n\n")        f.write("## CUSTOMERS_DIM Geographic Hierarchy\n\n")
        f.write("Implements Oracle-style CREATE DIMENSION geog_rollup hierarchy:\n\n")
        f.write("```\n")
        f.write("customer -> city -> state -> country -> subregion -> region\n")
        f.write("```\n\n")
        f.write("- **DIM_COUNTRIES to CUSTOMERS_DIM**: One-to-Many (via JOIN KEY country_id)\n")
        f.write("  - DIM_COUNTRIES holds LEVEL country, subregion, region\n")
        f.write("  - CUSTOMERS_DIM holds LEVEL customer, city, state\n")
        f.write("  - ATTRIBUTE customer DETERMINES (first_name, last_name, gender, ...)\n")
        f.write("  - ATTRIBUTE country DETERMINES (country_name)\n\n")        f.write("## Key Attributes\n\n")
        f.write("- **PK**: Primary Key (Auto-increment)\n")
        f.write("- **FK**: Foreign Key (References parent table)\n")
        f.write("- **UK**: Unique Key (No duplicates allowed)\n")
        f.write("- **Timestamps**: Automatic tracking of record creation/updates\n")
    print(f"Mermaid ER diagram saved to {filename}")

if __name__ == "__main__":
    print_er_diagram()
    save_mermaid_diagram()
