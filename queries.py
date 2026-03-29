"""
Demonstration of the two required queries for OLTP Sales System using SQLAlchemy
"""
from sqlalchemy import text
from config import engine
from datetime import datetime, timedelta
from time import perf_counter
from create_db import create_database
from sample_data import populate_dimensional_model


DIMENSIONAL_TABLES = (
    'dim_date',
    'dim_customer',
    'dim_product',
    'dim_location',
    'fact_sales_dw',
    'dim_countries',
    'customers_dim',
)


def _table_exists(connection, table_name):
    """Return True when the requested table exists in the current database."""
    result = connection.execute(text("""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
          AND table_name = :table_name
    """), {'table_name': table_name})
    return bool(result.scalar())


def ensure_dimensional_model_ready():
    """Create and populate the dimensional model when it is missing or stale."""
    with engine.connect() as connection:
        missing_tables = [
            table_name for table_name in DIMENSIONAL_TABLES
            if not _table_exists(connection, table_name)
        ]

    if missing_tables:
        print("Dimensional tables missing. Creating dimensional schema objects...")
        create_database()

    with engine.connect() as connection:
        missing_tables = [
            table_name for table_name in DIMENSIONAL_TABLES
            if not _table_exists(connection, table_name)
        ]
        if missing_tables:
            print(
                "Dimensional schema is still incomplete. "
                f"Missing tables: {', '.join(missing_tables)}"
            )
            return False

        sales_count = connection.execute(text("SELECT COUNT(*) FROM sales")).scalar()
        if not sales_count:
            print("No OLTP sales data found. Run sample_data.py before dimensional queries.")
            return False

        fact_count = connection.execute(text("SELECT COUNT(*) FROM fact_sales_dw")).scalar()

    if fact_count != sales_count:
        print("Synchronizing dimensional model from OLTP sales data...")
        with engine.connect() as connection:
            connection = connection.execution_options(isolation_level="AUTOCOMMIT")
            populate_dimensional_model(connection)

    return True

def get_sales_by_product_location_time(product_id, location_id, start_date, end_date):
    """
    Query 1: Sales for a given product by location over a period of time
    
    Returns aggregated sales metrics for a specific product at a specific location
    within a date range.
    """
    try:
        with engine.connect() as connection:
            query = text("""
                SELECT 
                    p.product_id,
                    p.product_name,
                    p.category,
                    p.brand,
                    l.location_id,
                    l.location_name,
                    l.city,
                    l.country,
                    COUNT(*) AS number_of_sales,
                    SUM(s.quantity) AS total_quantity_sold,
                    SUM(s.total_amount) AS total_revenue,
                    AVG(s.total_amount) AS avg_sale_amount,
                    MIN(s.total_amount) AS min_sale_amount,
                    MAX(s.total_amount) AS max_sale_amount,
                    MIN(s.sale_timestamp) AS first_sale_date,
                    MAX(s.sale_timestamp) AS last_sale_date
                FROM sales s
                JOIN product p ON s.product_id = p.product_id
                JOIN location l ON s.location_id = l.location_id
                WHERE p.product_id = :product_id
                  AND l.location_id = :location_id
                  AND s.sale_timestamp BETWEEN :start_date AND :end_date
                GROUP BY 
                    p.product_id, p.product_name, p.category, p.brand,
                    l.location_id, l.location_name, l.city, l.country
            """)
            
            result = connection.execute(query, {
                'product_id': product_id,
                'location_id': location_id,
                'start_date': start_date,
                'end_date': end_date
            })
            
            row = result.fetchone()
            if row:
                columns = [key for key in result.keys()]
                return dict(zip(columns, row))
            
            return None
        
    except Exception as e:
        print(f"Error executing query: {e}")
        return None

def get_max_sales_for_product_location(product_id, location_id, start_date, end_date):
    """
    Query 2: Maximum number of sales for a given product over time for a given location
    
    Returns the date with the maximum number of sales for a product at a location,
    along with daily sales statistics.
    """
    try:
        with engine.connect() as connection:
            # Get daily sales aggregated
            query = text("""
                SELECT 
                    p.product_id,
                    p.product_name,
                    l.location_id,
                    l.location_name,
                    DATE(s.sale_timestamp) AS sale_date,
                    COUNT(*) AS number_of_sales,
                    SUM(s.quantity) AS total_quantity,
                    SUM(s.total_amount) AS daily_revenue
                FROM sales s
                JOIN product p ON s.product_id = p.product_id
                JOIN location l ON s.location_id = l.location_id
                WHERE p.product_id = :product_id
                  AND l.location_id = :location_id
                  AND s.sale_timestamp BETWEEN :start_date AND :end_date
                GROUP BY 
                    p.product_id, p.product_name,
                    l.location_id, l.location_name,
                    DATE(s.sale_timestamp)
                ORDER BY number_of_sales DESC, daily_revenue DESC
                LIMIT 1
            """)
            
            result = connection.execute(query, {
                'product_id': product_id,
                'location_id': location_id,
                'start_date': start_date,
                'end_date': end_date
            })
            max_day_row = result.fetchone()
            max_day = None
            if max_day_row:
                columns = [key for key in result.keys()]
                max_day = dict(zip(columns, max_day_row))
            
            # Also get overall statistics
            stats_query = text("""
                SELECT 
                    CAST(COUNT(*) AS SIGNED) AS total_sales,
                    CAST(COUNT(DISTINCT sale_date) AS SIGNED) AS days_with_sales,
                    AVG(daily_sales) AS avg_daily_sales,
                    MAX(daily_sales) AS max_daily_sales
                FROM (
                    SELECT DATE(sale_timestamp) AS sale_date, COUNT(*) AS daily_sales
                    FROM sales
                    WHERE product_id = :product_id
                      AND location_id = :location_id
                      AND sale_timestamp BETWEEN :start_date AND :end_date
                    GROUP BY DATE(sale_timestamp)
                ) AS daily_stats
            """)
            
            result = connection.execute(stats_query, {
                'product_id': product_id,
                'location_id': location_id,
                'start_date': start_date,
                'end_date': end_date
            })
            stats_row = result.fetchone()
            stats = None
            if stats_row:
                stats_columns = [key for key in result.keys()]
                stats = dict(zip(stats_columns, stats_row))
            
            return {
                'max_sales_day': max_day,
                'overall_stats': stats
            }
        
    except Exception as e:
        print(f"Error executing query: {e}")
        return None


def get_sales_by_product_location_time_dim(product_id, location_id, start_date, end_date):
    """
    Query 1 (Dimensional): Sales for a given product by location over a period of time.
    """
    try:
        with engine.connect() as connection:
            query = text("""
                SELECT
                    dp.product_id_nk AS product_id,
                    dp.product_name,
                    dp.category,
                    dp.brand,
                    dl.location_id_nk AS location_id,
                    dl.location_name,
                    dl.city,
                    dl.country,
                    COUNT(*) AS number_of_sales,
                    SUM(f.quantity) AS total_quantity_sold,
                    SUM(f.total_amount) AS total_revenue,
                    AVG(f.total_amount) AS avg_sale_amount,
                    MIN(f.total_amount) AS min_sale_amount,
                    MAX(f.total_amount) AS max_sale_amount,
                    MIN(f.sale_timestamp) AS first_sale_date,
                    MAX(f.sale_timestamp) AS last_sale_date
                FROM fact_sales_dw f
                JOIN dim_product dp ON f.product_key = dp.product_key
                JOIN dim_location dl ON f.location_key = dl.location_key
                JOIN dim_date dd ON f.date_key = dd.date_key
                WHERE dp.product_id_nk = :product_id
                  AND dl.location_id_nk = :location_id
                  AND dd.full_date BETWEEN :start_date AND :end_date
                GROUP BY
                    dp.product_id_nk, dp.product_name, dp.category, dp.brand,
                    dl.location_id_nk, dl.location_name, dl.city, dl.country
            """)

            result = connection.execute(query, {
                'product_id': product_id,
                'location_id': location_id,
                'start_date': start_date,
                'end_date': end_date
            })

            row = result.fetchone()
            if row:
                columns = [key for key in result.keys()]
                return dict(zip(columns, row))

            return None

    except Exception as e:
        print(f"Error executing dimensional query: {e}")
        return None


def get_max_sales_for_product_location_dim(product_id, location_id, start_date, end_date):
    """
    Query 2 (Dimensional): Peak sales day for a product at a location using star schema.
    """
    try:
        with engine.connect() as connection:
            query = text("""
                SELECT
                    dp.product_id_nk AS product_id,
                    dp.product_name,
                    dl.location_id_nk AS location_id,
                    dl.location_name,
                    dd.full_date AS sale_date,
                    COUNT(*) AS number_of_sales,
                    SUM(f.quantity) AS total_quantity,
                    SUM(f.total_amount) AS daily_revenue
                FROM fact_sales_dw f
                JOIN dim_product dp ON f.product_key = dp.product_key
                JOIN dim_location dl ON f.location_key = dl.location_key
                JOIN dim_date dd ON f.date_key = dd.date_key
                WHERE dp.product_id_nk = :product_id
                  AND dl.location_id_nk = :location_id
                  AND dd.full_date BETWEEN :start_date AND :end_date
                GROUP BY
                    dp.product_id_nk, dp.product_name,
                    dl.location_id_nk, dl.location_name,
                    dd.full_date
                ORDER BY number_of_sales DESC, daily_revenue DESC
                LIMIT 1
            """)

            result = connection.execute(query, {
                'product_id': product_id,
                'location_id': location_id,
                'start_date': start_date,
                'end_date': end_date
            })
            max_day_row = result.fetchone()
            max_day = None
            if max_day_row:
                columns = [key for key in result.keys()]
                max_day = dict(zip(columns, max_day_row))

            stats_query = text("""
                SELECT
                    CAST(COUNT(*) AS SIGNED) AS total_sales,
                    CAST(COUNT(DISTINCT sale_date) AS SIGNED) AS days_with_sales,
                    AVG(daily_sales) AS avg_daily_sales,
                    MAX(daily_sales) AS max_daily_sales
                FROM (
                    SELECT dd.full_date AS sale_date, COUNT(*) AS daily_sales
                    FROM fact_sales_dw f
                    JOIN dim_product dp ON f.product_key = dp.product_key
                    JOIN dim_location dl ON f.location_key = dl.location_key
                    JOIN dim_date dd ON f.date_key = dd.date_key
                    WHERE dp.product_id_nk = :product_id
                      AND dl.location_id_nk = :location_id
                      AND dd.full_date BETWEEN :start_date AND :end_date
                    GROUP BY dd.full_date
                ) AS daily_stats
            """)

            result = connection.execute(stats_query, {
                'product_id': product_id,
                'location_id': location_id,
                'start_date': start_date,
                'end_date': end_date
            })
            stats_row = result.fetchone()
            stats = None
            if stats_row:
                stats_columns = [key for key in result.keys()]
                stats = dict(zip(stats_columns, stats_row))

            return {
                'max_sales_day': max_day,
                'overall_stats': stats
            }

    except Exception as e:
        print(f"Error executing dimensional query: {e}")
        return None

def get_customers_by_region(region: str = None):
    """
    Geographic hierarchy query: rollup customer dimension to LEVEL region.
    If region is None, returns counts for all regions.
    """
    try:
        with engine.connect() as connection:
            if region:
                query = text("""
                    SELECT region, subregion, country_name, state, city,
                           cust_id,
                           CONCAT(cust_first_name, ' ', cust_last_name) AS customer_name,
                           cust_gender, cust_income_level, cust_credit_limit
                    FROM   vw_customers_geog_rollup
                    WHERE  region = :region
                    ORDER  BY subregion, country_name, state, city, cust_id
                """)
                result = connection.execute(query, {"region": region})
            else:
                query = text("""
                    SELECT region,
                           COUNT(DISTINCT country_name) AS countries,
                           COUNT(DISTINCT state)        AS states,
                           COUNT(*)                     AS customers,
                           AVG(cust_credit_limit)       AS avg_credit_limit
                    FROM   vw_customers_geog_rollup
                    GROUP  BY region
                    ORDER  BY region
                """)
                result = connection.execute(query)
            rows = result.fetchall()
            columns = list(result.keys())
            return [dict(zip(columns, r)) for r in rows]
    except Exception as e:
        print(f"Error executing geography hierarchy query: {e}")
        return None


def get_customers_drilldown(country_name: str):
    """
    Drill down from LEVEL country → individual customers (LEVEL customer).
    Returns all customer attributes for the specified country.
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT cust_id,
                       CONCAT(cust_first_name, ' ', cust_last_name) AS customer_name,
                       cust_gender, cust_marital_status, cust_year_of_birth,
                       cust_income_level, cust_credit_limit,
                       city, state, country_name, subregion, region
                FROM   vw_customers_geog_rollup
                WHERE  country_name = :country
                ORDER  BY state, city, cust_id
            """), {"country": country_name})
            rows = result.fetchall()
            columns = list(result.keys())
            return [dict(zip(columns, r)) for r in rows]
    except Exception as e:
        print(f"Error executing customer drill-down query: {e}")
        return None


def benchmark_query(query_func, *args, runs=5):
    """Measure average execution time in milliseconds for a query function."""
    durations = []
    last_result = None

    for _ in range(runs):
        start = perf_counter()
        last_result = query_func(*args)
        durations.append((perf_counter() - start) * 1000)

    return {
        'runs': runs,
        'avg_ms': sum(durations) / len(durations),
        'min_ms': min(durations),
        'max_ms': max(durations),
        'last_result': last_result,
    }


def print_performance_summary(oltp_q1_perf, oltp_q2_perf, dim_q1_perf=None, dim_q2_perf=None):
    """Print query timing comparison for WITHOUT DIM vs WITH DIM."""
    print("\n" + "=" * 80)
    print("QUERY PERFORMANCE")
    print("=" * 80)

    print("\nWITHOUT DIM")
    print(
        f"  Query 1 avg={oltp_q1_perf['avg_ms']:.3f} ms "
        f"min={oltp_q1_perf['min_ms']:.3f} ms max={oltp_q1_perf['max_ms']:.3f} ms"
    )
    print(
        f"  Query 2 avg={oltp_q2_perf['avg_ms']:.3f} ms "
        f"min={oltp_q2_perf['min_ms']:.3f} ms max={oltp_q2_perf['max_ms']:.3f} ms"
    )

    if dim_q1_perf and dim_q2_perf:
        print("\nWITH DIM")
        print(
            f"  Query 1 avg={dim_q1_perf['avg_ms']:.3f} ms "
            f"min={dim_q1_perf['min_ms']:.3f} ms max={dim_q1_perf['max_ms']:.3f} ms"
        )
        print(
            f"  Query 2 avg={dim_q2_perf['avg_ms']:.3f} ms "
            f"min={dim_q2_perf['min_ms']:.3f} ms max={dim_q2_perf['max_ms']:.3f} ms"
        )

        print("\nPERFORMANCE DELTA")
        print(
            f"  Query 1 dim/oltp ratio = {dim_q1_perf['avg_ms'] / oltp_q1_perf['avg_ms']:.2f}x"
        )
        print(
            f"  Query 2 dim/oltp ratio = {dim_q2_perf['avg_ms'] / oltp_q2_perf['avg_ms']:.2f}x"
        )


def print_model_comparison(result1, dim_result1, result2, dim_result2, region_summary, us_customers):
    """Print one integrated comparison across OLTP and one combined dimensional schema."""
    print("\n" + "=" * 80)
    print("COMPARISON: WITHOUT DIM vs WITH DIM")
    print("=" * 80)

    print("\n1. WITHOUT DIM (OLTP)")
    print("   Source tables: sales + product + location")
    print("   Best for: live transaction queries and operational reporting")
    if result1 and result2 and result2.get('max_sales_day'):
        print(
            "   This run: "
            f"sales={result1['number_of_sales']}, revenue=${result1['total_revenue']:,.2f}, "
            f"peak_day={result2['max_sales_day']['sale_date']}"
        )

    print("\n2. WITH DIM (Single Dimensional Schema)")
    print("   Source tables: fact_sales_dw + dim_date + dim_product + dim_location + customers_dim + dim_countries")
    print("   Best for: aggregated analytics plus customer geographic rollup/drill-down")
    if dim_result1 and dim_result2 and dim_result2.get('max_sales_day'):
        print(
            "   This run: "
            f"sales={dim_result1['number_of_sales']}, revenue=${dim_result1['total_revenue']:,.2f}, "
            f"peak_day={dim_result2['max_sales_day']['sale_date']}"
        )
    if region_summary:
        print(
            "   Geography: "
            f"regions={len(region_summary)}, total_customers={sum(r['customers'] for r in region_summary)}"
        )
    if us_customers:
        print(f"   Drill-down example: United States of America -> {len(us_customers)} customers")

    print("\nRESULT CHECK")
    if result1 and dim_result1:
        same_sales = result1['number_of_sales'] == dim_result1['number_of_sales']
        same_revenue = float(result1['total_revenue']) == float(dim_result1['total_revenue'])
        print(f"   Query 1 WITHOUT DIM vs WITH DIM: sales_match={same_sales}, revenue_match={same_revenue}")
    if result2 and dim_result2 and result2.get('max_sales_day') and dim_result2.get('max_sales_day'):
        same_peak_day = str(result2['max_sales_day']['sale_date']) == str(dim_result2['max_sales_day']['sale_date'])
        same_peak_count = result2['max_sales_day']['number_of_sales'] == dim_result2['max_sales_day']['number_of_sales']
        print(f"   Query 2 WITHOUT DIM vs WITH DIM: peak_day_match={same_peak_day}, peak_count_match={same_peak_count}")

    print("\nSUMMARY")
    print("   WITHOUT DIM = transaction-oriented normalized model")
    print("   WITH DIM    = one dimensional schema combining star analytics and customer geography hierarchy")


def demonstrate_queries():
    """Run demonstration queries with sample data"""
    print("=" * 80)
    print("OLTP Sales System - Query Demonstrations")
    print("=" * 80)
    
    # Get some sample product and location IDs
    try:
        with engine.connect() as connection:
            # Get a random product/location combination that actually has sales
            result = connection.execute(text("""
                SELECT 
                    p.product_id, 
                    p.product_name,
                    l.location_id,
                    l.location_name,
                    COUNT(*) as sales_count
                FROM sales s
                JOIN product p ON s.product_id = p.product_id
                JOIN location l ON s.location_id = l.location_id
                GROUP BY p.product_id, p.product_name, l.location_id, l.location_name
                HAVING sales_count >= 3
                ORDER BY RAND()
                LIMIT 1
            """))
            row = result.fetchone()
            
            if not row:
                print("No sales data found. Please run sample_data.py first.")
                return
                
            product = {'product_id': row[0], 'product_name': row[1]}
            location = {'location_id': row[2], 'location_name': row[3]}
        
        product_id = product['product_id']
        location_id = location['location_id']
        
        # Date range: last 2 years (matching the sample data)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=730)
        
        print(f"\nSample Query Parameters:")
        print(f"  Product: {product['product_name']} (ID: {product_id})")
        print(f"  Location: {location['location_name']} (ID: {location_id})")
        print(f"  Date Range: {start_date.date()} to {end_date.date()}")
        print()
        
        # ========================================
        # Query 1 Demonstration
        # ========================================
        print("\n" + "=" * 80)
        print("QUERY 1: Sales for product by location over time period")
        print("=" * 80)
        
        result1 = get_sales_by_product_location_time(
            product_id, 
            location_id, 
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )
        
        if result1:
            print(f"\nProduct: {result1['product_name']} ({result1['category']} - {result1['brand']})")
            print(f"Location: {result1['location_name']}, {result1['city']}, {result1['country']}")
            print(f"\nSales Metrics:")
            print(f"  Total Number of Sales: {result1['number_of_sales']}")
            print(f"  Total Quantity Sold: {result1['total_quantity_sold']}")
            print(f"  Total Revenue: ${result1['total_revenue']:,.2f}")
            print(f"  Average Sale Amount: ${result1['avg_sale_amount']:,.2f}")
            print(f"  Min Sale Amount: ${result1['min_sale_amount']:,.2f}")
            print(f"  Max Sale Amount: ${result1['max_sale_amount']:,.2f}")
            print(f"  First Sale: {result1['first_sale_date']}")
            print(f"  Last Sale: {result1['last_sale_date']}")
        else:
            print("No sales found for this product/location combination in the date range.")
        
        # ========================================
        # Query 2 Demonstration
        # ========================================
        print("\n" + "=" * 80)
        print("QUERY 2: Maximum number of sales for product at location")
        print("=" * 80)
        
        result2 = get_max_sales_for_product_location(
            product_id,
            location_id,
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )
        
        if result2 and result2['max_sales_day']:
            max_day = result2['max_sales_day']
            stats = result2['overall_stats']
            
            print(f"\nProduct: {max_day['product_name']}")
            print(f"Location: {max_day['location_name']}")
            print(f"\nPeak Sales Day:")
            print(f"  Date: {max_day['sale_date']}")
            print(f"  Number of Sales: {max_day['number_of_sales']}")
            print(f"  Total Quantity: {max_day['total_quantity']}")
            print(f"  Daily Revenue: ${max_day['daily_revenue']:,.2f}")
            
            print(f"\nOverall Statistics:")
            print(f"  Total Sales (Period): {stats['total_sales']}")
            print(f"  Days with Sales: {stats['days_with_sales']}")
            print(f"  Average Daily Sales: {stats['avg_daily_sales']:.2f}")
            print(f"  Maximum Daily Sales: {stats['max_daily_sales']}")
        else:
            print("No sales found for this product/location combination in the date range.")
        
        # ========================================
        # Query 1 (Dimensional) Demonstration
        # ========================================
        print("\n" + "=" * 80)
        print("QUERY 1 (DIM): Sales for product by location over time period")
        print("=" * 80)

        dimensional_model_ready = ensure_dimensional_model_ready()

        dim_result1 = None
        if dimensional_model_ready:
            dim_result1 = get_sales_by_product_location_time_dim(
                product_id,
                location_id,
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )

            if dim_result1:
                print(f"\nProduct: {dim_result1['product_name']} ({dim_result1['category']} - {dim_result1['brand']})")
                print(f"Location: {dim_result1['location_name']}, {dim_result1['city']}, {dim_result1['country']}")
                print(f"\nSales Metrics (Dimensional):")
                print(f"  Total Number of Sales: {dim_result1['number_of_sales']}")
                print(f"  Total Quantity Sold: {dim_result1['total_quantity_sold']}")
                print(f"  Total Revenue: ${dim_result1['total_revenue']:,.2f}")
                print(f"  Average Sale Amount: ${dim_result1['avg_sale_amount']:,.2f}")
                print(f"  Min Sale Amount: ${dim_result1['min_sale_amount']:,.2f}")
                print(f"  Max Sale Amount: ${dim_result1['max_sale_amount']:,.2f}")
                print(f"  First Sale: {dim_result1['first_sale_date']}")
                print(f"  Last Sale: {dim_result1['last_sale_date']}")
            else:
                print("No dimensional sales found for this product/location combination in the date range.")
        else:
            print("Dimensional query skipped because the warehouse layer is not ready.")

        # ========================================
        # Query 2 (Dimensional) Demonstration
        # ========================================
        print("\n" + "=" * 80)
        print("QUERY 2 (DIM): Maximum number of sales for product at location")
        print("=" * 80)

        dim_result2 = None
        if dimensional_model_ready:
            dim_result2 = get_max_sales_for_product_location_dim(
                product_id,
                location_id,
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )

            if dim_result2 and dim_result2['max_sales_day']:
                max_day = dim_result2['max_sales_day']
                stats = dim_result2['overall_stats']

                print(f"\nProduct: {max_day['product_name']}")
                print(f"Location: {max_day['location_name']}")
                print(f"\nPeak Sales Day (Dimensional):")
                print(f"  Date: {max_day['sale_date']}")
                print(f"  Number of Sales: {max_day['number_of_sales']}")
                print(f"  Total Quantity: {max_day['total_quantity']}")
                print(f"  Daily Revenue: ${max_day['daily_revenue']:,.2f}")

                print(f"\nOverall Statistics (Dimensional):")
                print(f"  Total Sales (Period): {stats['total_sales']}")
                print(f"  Days with Sales: {stats['days_with_sales']}")
                print(f"  Average Daily Sales: {stats['avg_daily_sales']:.2f}")
                print(f"  Maximum Daily Sales: {stats['max_daily_sales']}")
            else:
                print("No dimensional sales found for this product/location combination in the date range.")
        else:
            print("Dimensional query skipped because the warehouse layer is not ready.")

        # ========================================
        # CUSTOMERS_DIM Geography Hierarchy Demo
        # ========================================
        print("\n" + "=" * 80)
        print("CUSTOMERS_DIM: Geographic Hierarchy Rollup (6 levels)")
        print("=" * 80)

        region_summary = get_customers_by_region()
        if region_summary:
            print("\nRollup to LEVEL region:")
            for r in region_summary:
                print(f"  {r['region']:<15} | Countries: {r['countries']} "
                      f"| States: {r['states']} | Customers: {r['customers']} "
                      f"| Avg Credit: ${float(r['avg_credit_limit'] or 0):,.2f}")

        print("\nDrill-down into 'United States of America':")
        us_customers = get_customers_drilldown("United States of America")
        if us_customers:
            for c in us_customers:
                print(f"  ID:{c['cust_id']} | {c['customer_name']:<22} | "
                      f"{c['city']}, {c['state']} | {c['cust_income_level']}")
        else:
            print("  No customers found (run customers_dim.py to populate).")

        oltp_q1_perf = benchmark_query(
            get_sales_by_product_location_time,
            product_id,
            location_id,
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d'),
        )
        oltp_q2_perf = benchmark_query(
            get_max_sales_for_product_location,
            product_id,
            location_id,
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d'),
        )
        dim_q1_perf = None
        dim_q2_perf = None
        if dimensional_model_ready:
            dim_q1_perf = benchmark_query(
                get_sales_by_product_location_time_dim,
                product_id,
                location_id,
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d'),
            )
            dim_q2_perf = benchmark_query(
                get_max_sales_for_product_location_dim,
                product_id,
                location_id,
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d'),
            )

        print_performance_summary(
            oltp_q1_perf,
            oltp_q2_perf,
            dim_q1_perf,
            dim_q2_perf,
        )

        print_model_comparison(
            result1,
            dim_result1,
            result2,
            dim_result2,
            region_summary,
            us_customers,
        )

        print("\n" + "=" * 80)
        print("Query demonstrations completed!")
        print("=" * 80)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    demonstrate_queries()
