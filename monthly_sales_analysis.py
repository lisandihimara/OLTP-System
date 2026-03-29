"""
Monthly Sales Analysis for Specific Product
Using the Data Mart (Star Schema)
"""

import mysql.connector
import config

def analyze_monthly_sales_for_product(product_id=None):
    """
    Analyze monthly sales trends for a specific product using the data mart
    """
    cnx = mysql.connector.connect(
        host=config.DB_HOST,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DATABASE_NAME
    )
    cur = cnx.cursor()

    try:
        # If no product specified, show available products and pick first one
        if product_id is None:
            cur.execute('SELECT product_id_nk, product_name FROM dim_product LIMIT 5')
            products = cur.fetchall()
            print('Available products:')
            for p in products:
                print(f'  {p[0]}: {p[1]}')

            # Choose the first product for analysis
            product_id = products[0][0]
            product_name = products[0][1]
        else:
            # Get product name for the specified ID
            cur.execute('SELECT product_name FROM dim_product WHERE product_id_nk = %s', (product_id,))
            result = cur.fetchone()
            product_name = result[0] if result else f"Product ID {product_id}"

        print(f'\n=== MONTHLY SALES ANALYSIS ===')
        print(f'Product: {product_name} (ID: {product_id})')
        print('=' * 80)

        # Main query: Monthly sales for the specific product
        query = """
        SELECT
            dd.year_number,
            dd.month_number,
            dd.month_name,
            COUNT(f.sales_key) AS num_transactions,
            SUM(f.quantity) AS total_units_sold,
            SUM(f.total_amount) AS total_revenue,
            ROUND(AVG(f.total_amount), 2) AS avg_transaction_value,
            ROUND(AVG(f.quantity), 1) AS avg_quantity_per_transaction
        FROM fact_sales_dw f
        JOIN dim_date dd ON f.date_key = dd.date_key
        JOIN dim_product dp ON f.product_key = dp.product_key
        WHERE dp.product_id_nk = %s
        GROUP BY dd.year_number, dd.month_number, dd.month_name
        ORDER BY dd.year_number, dd.month_number
        """

        cur.execute(query, (product_id,))
        results = cur.fetchall()

        if not results:
            print(f"No sales data found for product {product_name}")
            return

        # Print header
        print(f"{'Year':<6} {'Month':<8} {'Trans':<8} {'Units':<8} {'Revenue':<12} {'Avg Trans':<12} {'Avg Qty':<10}")
        print('-' * 80)

        # Print results
        total_transactions = 0
        total_units = 0
        total_revenue = 0

        for row in results:
            year, month_num, month_name, transactions, units, revenue, avg_trans, avg_qty = row
            print(f"{year:<6} {month_name:<8} {transactions:<8} {units:<8} ${revenue:<11.2f} ${avg_trans:<11.2f} {avg_qty:<10.1f}")

            total_transactions += transactions
            total_units += units
            total_revenue += revenue

        # Print summary
        print('-' * 80)
        print(f"{'TOTAL':<22} {total_transactions:<8} {total_units:<8} ${total_revenue:<11.2f}")

        # Additional insights
        print(f"\n=== INSIGHTS FOR {product_name.upper()} ===")
        print(f"• Total periods with sales: {len(results)}")
        print(f"• Best performing month: {max(results, key=lambda x: x[5])[2]} {max(results, key=lambda x: x[5])[0]} (${max(results, key=lambda x: x[5])[5]:.2f})")
        print(f"• Average monthly revenue: ${total_revenue/len(results):.2f}")
        print(f"• Average monthly transactions: {total_transactions/len(results):.1f}")

    except Exception as e:
        print(f"Error analyzing sales: {e}")
    finally:
        cur.close()
        cnx.close()

if __name__ == "__main__":
    # Analyze sales for a specific product (or None to pick first available)
    analyze_monthly_sales_for_product()  # Will pick first product
    # analyze_monthly_sales_for_product(1)  # Would analyze product with ID 1