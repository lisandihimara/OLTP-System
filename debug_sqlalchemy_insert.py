from sqlalchemy import text
from config import engine

with engine.begin() as conn:
    conn.execute(text('DELETE FROM dim_date'))
    # perform the same insert expression
    conn.execute(text('''
        INSERT INTO dim_date (
            date_key,
            full_date,
            day_of_month,
            month_number,
            month_name,
            quarter_number,
            year_number,
            day_name,
            is_weekend
        )
        SELECT DISTINCT
            CAST(DATE_FORMAT(DATE(s.sale_timestamp), '%Y%m%d') AS UNSIGNED) AS date_key,
            DATE(s.sale_timestamp) AS full_date,
            DAY(DATE(s.sale_timestamp)) AS day_of_month,
            MONTH(DATE(s.sale_timestamp)) AS month_number,
            MONTHNAME(DATE(s.sale_timestamp)) AS month_name,
            QUARTER(DATE(s.sale_timestamp)) AS quarter_number,
            YEAR(DATE(s.sale_timestamp)) AS year_number,
            DAYNAME(DATE(s.sale_timestamp)) AS day_name,
            CASE WHEN DAYOFWEEK(DATE(s.sale_timestamp)) IN (1, 7) THEN TRUE ELSE FALSE END AS is_weekend
        FROM sales s
        WHERE s.sale_timestamp IS NOT NULL
          AND CAST(DATE_FORMAT(DATE(s.sale_timestamp), '%Y%m%d') AS UNSIGNED) <> 0
    '''))

    result = conn.execute(text('SELECT COUNT(*) FROM dim_date')).scalar()
    print('dim_date after sqlalchemy insert', result)

    conn.execute(text('DELETE FROM fact_sales_dw'))
    conn.execute(text('''
        INSERT INTO fact_sales_dw (
            sale_id_nk,
            date_key,
            customer_key,
            product_key,
            location_key,
            quantity,
            unit_price,
            total_amount,
            sale_timestamp
        )
        SELECT
            s.sale_id,
            CAST(DATE_FORMAT(DATE(s.sale_timestamp), '%Y%m%d') AS UNSIGNED) AS date_key,
            dc.customer_key,
            dp.product_key,
            dl.location_key,
            s.quantity,
            s.unit_price,
            s.total_amount,
            s.sale_timestamp
        FROM sales s
        LEFT JOIN dim_customer dc ON dc.customer_id_nk = s.customer_id
        JOIN dim_product dp ON dp.product_id_nk = s.product_id
        JOIN dim_location dl ON dl.location_id_nk = s.location_id
        WHERE s.sale_timestamp IS NOT NULL
          AND CAST(DATE_FORMAT(DATE(s.sale_timestamp), '%Y%m%d') AS UNSIGNED) <> 0
    '''))

    result2 = conn.execute(text('SELECT COUNT(*) FROM fact_sales_dw')).scalar()
    print('fact_sales_dw after sqlalchemy insert', result2)
