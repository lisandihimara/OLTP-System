import argparse
import mysql.connector
import config


def query_top_sales(product_name: str, city: str, country: str = None, limit: int = 10):
    cnx = mysql.connector.connect(
        host=config.DB_HOST,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DATABASE_NAME
    )
    cur = cnx.cursor()

    where_clauses = ['dp.product_name = %s', 'dl.city = %s']
    params = [product_name, city]
    if country:
        where_clauses.append('dl.country = %s')
        params.append(country)

    query = f"""
    SELECT
        dp.product_name,
        dl.city,
        dl.country,
        COUNT(*) AS num_transactions,
        SUM(f.total_amount) AS total_revenue,
        SUM(f.quantity) AS total_units,
        ROUND(AVG(f.total_amount), 2) AS avg_transaction_value,
        ROUND(AVG(f.quantity), 2) AS avg_quantity_per_transaction
    FROM fact_sales_dw f
    JOIN dim_product dp ON f.product_key = dp.product_key
    JOIN dim_location dl ON f.location_key = dl.location_key
    WHERE {' AND '.join(where_clauses)}
    GROUP BY dp.product_name, dl.city, dl.country
    ORDER BY total_revenue DESC
    LIMIT %s
    """

    params.append(limit)
    cur.execute(query, tuple(params))
    rows = cur.fetchall()

    if not rows:
        print('No sales data found for the given product/location filter.')
    else:
        print(f"Top {limit} sales summary for product '{product_name}' in {city}{f', {country}' if country else ''}:")
        print('-' * 90)
        print(f"{'Product':<30} {'City':<15} {'Country':<15} {'Tx':>4} {'Units':>8} {'Revenue':>12} {'Avg Tx':>10} {'Avg Qty':>10}")
        print('-' * 90)
        for product, city_name, country_name, tx, units, revenue, avg_tx, avg_qty in rows:
            print(f"{product:<30} {city_name:<15} {country_name:<15} {tx:>4} {units:>8} ${revenue:>11.2f} ${avg_tx:>9.2f} {avg_qty:>10.2f}")

    cur.close()
    cnx.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Top sales for a product within a given location using the data mart')
    parser.add_argument('--product', required=True, help='Product name to filter on')
    parser.add_argument('--city', required=True, help='City to filter on')
    parser.add_argument('--country', help='Country to filter on (optional)')
    parser.add_argument('--limit', type=int, default=10, help='Number of top results to return')
    args = parser.parse_args()

    query_top_sales(args.product, args.city, args.country, args.limit)
