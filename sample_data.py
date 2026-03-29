"""
Generate and insert sample data for OLTP Sales System using SQLAlchemy
"""
from sqlalchemy import text
from faker import Faker
import random
from datetime import datetime, timedelta
from config import engine

fake = Faker()


def insert_customers(connection, num_customers=100):
    """Insert sample customers"""
    print(f"Inserting {num_customers} customers...")

    for _ in range(num_customers):
        first_name = fake.first_name()
        last_name = fake.last_name()
        email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}@{fake.free_email_domain()}"
        phone = fake.phone_number()[:20]

        connection.execute(text("""
            INSERT INTO customer (first_name, last_name, email, phone)
            VALUES (:first_name, :last_name, :email, :phone)
        """), {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'phone': phone
        })

    print(f"Inserted {num_customers} customers successfully!")


def insert_products(connection):
    """Insert sample products"""
    print("Inserting 20 products...")

    products = [
        ('iPhone 14 Pro', 'Electronics', 'Apple', 999.99),
        ('Samsung Galaxy S23', 'Electronics', 'Samsung', 899.99),
        ('MacBook Air M2', 'Electronics', 'Apple', 1199.99),
        ('Dell XPS 15', 'Electronics', 'Dell', 1499.99),
        ('Sony WH-1000XM5', 'Electronics', 'Sony', 399.99),

        ("Levi's 501 Jeans", 'Clothing', "Levi's", 69.99),
        ('Nike Air Max 90', 'Clothing', 'Nike', 129.99),
        ('Adidas Ultraboost', 'Clothing', 'Adidas', 179.99),
        ('North Face Jacket', 'Clothing', 'The North Face', 249.99),
        ('Patagonia Fleece', 'Clothing', 'Patagonia', 159.99),

        ('Dyson V15 Vacuum', 'Home & Garden', 'Dyson', 649.99),
        ('KitchenAid Mixer', 'Home & Garden', 'KitchenAid', 379.99),
        ('Nespresso Machine', 'Home & Garden', 'Nespresso', 199.99),
        ('Roomba i7+', 'Home & Garden', 'iRobot', 799.99),
        ('Air Purifier', 'Home & Garden', 'Levoit', 149.99),

        ('Peloton Bike', 'Sports', 'Peloton', 1495.00),
        ('Bowflex Dumbbells', 'Sports', 'Bowflex', 349.99),
        ('Yoga Mat Pro', 'Sports', 'Lululemon', 78.99),
        ('Garmin Forerunner', 'Sports', 'Garmin', 299.99),
        ('Fitbit Charge 5', 'Sports', 'Fitbit', 149.95),
    ]

    for product_name, category, brand, unit_price in products:
        connection.execute(text("""
            INSERT INTO product (product_name, category, brand, unit_price)
            VALUES (:product_name, :category, :brand, :unit_price)
        """), {
            'product_name': product_name,
            'category': category,
            'brand': brand,
            'unit_price': unit_price
        })

    print("Inserted 20 products successfully!")


def insert_locations(connection):
    """Insert sample locations"""
    print("Inserting 10 locations...")

    locations = [
        ('Downtown Flagship Store', 'New York', '123 5th Avenue', 'USA'),
        ('Westfield Mall', 'Los Angeles', '10250 Santa Monica Blvd', 'USA'),
        ('Oxford Street Store', 'London', '456 Oxford Street', 'UK'),
        ('Covent Garden', 'London', '789 Covent Garden', 'UK'),
        ('Toronto Eaton Centre', 'Toronto', '220 Yonge Street', 'Canada'),
        ('Berlin Alexanderplatz', 'Berlin', 'Alexanderplatz 1', 'Germany'),
        ('Munich City Center', 'Munich', 'Marienplatz 8', 'Germany'),
        ('Sydney CBD', 'Sydney', '500 George Street', 'Australia'),
        ('Melbourne Central', 'Melbourne', '211 La Trobe Street', 'Australia'),
        ('Chicago Magnificent Mile', 'Chicago', '835 N Michigan Ave', 'USA'),
    ]

    for location_name, city, address, country in locations:
        connection.execute(text("""
            INSERT INTO location (location_name, city, address, country)
            VALUES (:location_name, :city, :address, :country)
        """), {
            'location_name': location_name,
            'city': city,
            'address': address,
            'country': country
        })

    print("Inserted 10 locations successfully!")


def insert_sales(connection, num_sales=1000):
    """Insert sample sales transactions"""
    print(f"Inserting {num_sales} sales records...")

    result = connection.execute(text("SELECT product_id, unit_price FROM product"))
    products = result.fetchall()

    result = connection.execute(text("SELECT location_id FROM location"))
    locations = [row[0] for row in result.fetchall()]

    result = connection.execute(text("SELECT customer_id FROM customer"))
    customers = [row[0] for row in result.fetchall()]

    start_date = datetime.now() - timedelta(days=730)

    for _ in range(num_sales):
        random_days = random.randint(0, 730)
        random_hours = random.randint(0, 23)
        random_minutes = random.randint(0, 59)

        sale_timestamp = start_date + timedelta(
            days=random_days,
            hours=random_hours,
            minutes=random_minutes
        )

        product_id, base_price = random.choice(products)
        base_price = float(base_price)

        quantity = random.choices([1, 2, 3, 4, 5], weights=[50, 25, 15, 7, 3])[0]
        unit_price = round(base_price * random.uniform(0.8, 1.0), 2)
        total_amount = round(quantity * unit_price, 2)

        customer_id = random.choice(customers)
        location_id = random.choice(locations)

        connection.execute(text("""
            INSERT INTO sales
            (sale_timestamp, quantity, unit_price, total_amount, customer_id, product_id, location_id)
            VALUES (:sale_timestamp, :quantity, :unit_price, :total_amount, :customer_id, :product_id, :location_id)
        """), {
            'sale_timestamp': sale_timestamp,
            'quantity': quantity,
            'unit_price': unit_price,
            'total_amount': total_amount,
            'customer_id': customer_id,
            'product_id': product_id,
            'location_id': location_id
        })

    print(f"Inserted {num_sales} sales records successfully!")


def populate_dimensional_model(connection):
    """Populate star schema"""
    print("Building dimensional model (dim_* and fact_sales_dw)...")

    connection.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
    connection.execute(text("DELETE FROM fact_sales_dw"))
    connection.execute(text("DELETE FROM dim_customer"))
    connection.execute(text("DELETE FROM dim_product"))
    connection.execute(text("DELETE FROM dim_location"))
    connection.execute(text("DELETE FROM dim_date"))
    connection.execute(text("SET FOREIGN_KEY_CHECKS = 1"))

    result = connection.execute(text("""
        INSERT INTO dim_customer (customer_id_nk, full_name, email, phone, created_at)
        SELECT
            c.customer_id,
            CONCAT(c.first_name, ' ', c.last_name),
            c.email,
            c.phone,
            c.created_at
        FROM customer c
    """))
    print("dim_customer inserted:", result.rowcount)

    result = connection.execute(text("""
        INSERT INTO dim_product (product_id_nk, product_name, category, brand, base_unit_price, is_active)
        SELECT
            p.product_id,
            p.product_name,
            p.category,
            p.brand,
            p.unit_price,
            p.is_active
        FROM product p
    """))
    print("dim_product inserted:", result.rowcount)

    result = connection.execute(text("""
        INSERT INTO dim_location (location_id_nk, location_name, city, address, country, is_active)
        SELECT
            l.location_id,
            l.location_name,
            l.city,
            l.address,
            l.country,
            l.is_active
        FROM location l
    """))
    print("dim_location inserted:", result.rowcount)

    result = connection.execute(text("""
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
            CAST(DATE_FORMAT(DATE(s.sale_timestamp), '%%Y%%m%%d') AS UNSIGNED) AS date_key,
            DATE(s.sale_timestamp) AS full_date,
            DAY(DATE(s.sale_timestamp)) AS day_of_month,
            MONTH(DATE(s.sale_timestamp)) AS month_number,
            MONTHNAME(DATE(s.sale_timestamp)) AS month_name,
            QUARTER(DATE(s.sale_timestamp)) AS quarter_number,
            YEAR(DATE(s.sale_timestamp)) AS year_number,
            DAYNAME(DATE(s.sale_timestamp)) AS day_name,
            CASE
                WHEN DAYOFWEEK(DATE(s.sale_timestamp)) IN (1, 7) THEN TRUE
                ELSE FALSE
            END AS is_weekend
        FROM sales s
        WHERE s.sale_timestamp IS NOT NULL
          AND CAST(DATE_FORMAT(DATE(s.sale_timestamp), '%%Y%%m%%d') AS UNSIGNED) <> 0
    """))
    print("dim_date inserted:", result.rowcount)

    result = connection.execute(text("""
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
            CAST(DATE_FORMAT(DATE(s.sale_timestamp), '%%Y%%m%%d') AS UNSIGNED) AS date_key,
            dc.customer_key,
            dp.product_key,
            dl.location_key,
            s.quantity,
            s.unit_price,
            s.total_amount,
            s.sale_timestamp
        FROM sales s
        LEFT JOIN dim_customer dc
            ON dc.customer_id_nk = s.customer_id
        JOIN dim_product dp
            ON dp.product_id_nk = s.product_id
        JOIN dim_location dl
            ON dl.location_id_nk = s.location_id
        WHERE s.sale_timestamp IS NOT NULL
          AND CAST(DATE_FORMAT(DATE(s.sale_timestamp), '%%Y%%m%%d') AS UNSIGNED) <> 0
    """))
    print("fact_sales_dw inserted:", result.rowcount)

    print("Dimensional model populated successfully!")

def load_sample_data():
    """Main function to load all sample data"""
    try:
        with engine.begin() as connection:
            connection.execute(text("SET FOREIGN_KEY_CHECKS = 0"))

            connection.execute(text("DELETE FROM fact_sales_dw"))
            connection.execute(text("DELETE FROM dim_customer"))
            connection.execute(text("DELETE FROM dim_product"))
            connection.execute(text("DELETE FROM dim_location"))
            connection.execute(text("DELETE FROM dim_date"))

            connection.execute(text("DELETE FROM sales"))
            connection.execute(text("DELETE FROM customer"))
            connection.execute(text("DELETE FROM product"))
            connection.execute(text("DELETE FROM location"))

            result = connection.execute(text("SELECT DATABASE()"))
            print("Connected to DB:", result.scalar())

            connection.execute(text("SET FOREIGN_KEY_CHECKS = 1"))

            insert_customers(connection, 100)
            insert_products(connection)
            insert_locations(connection)
            insert_sales(connection, 1000)
            populate_dimensional_model(connection)

            print("\n✓ Sample data loaded successfully!")
            print("\nDatabase now contains:")

            result = connection.execute(text("SELECT COUNT(*) FROM customer"))
            print(f"  - {result.scalar()} customers")

            result = connection.execute(text("SELECT COUNT(*) FROM product"))
            print(f"  - {result.scalar()} products")

            result = connection.execute(text("SELECT COUNT(*) FROM location"))
            print(f"  - {result.scalar()} locations")

            result = connection.execute(text("SELECT COUNT(*) FROM sales"))
            print(f"  - {result.scalar()} sales transactions")

            result = connection.execute(text("SELECT COUNT(*) FROM dim_date"))
            print(f"  - {result.scalar()} dim_date rows")

            result = connection.execute(text("SELECT COUNT(*) FROM fact_sales_dw"))
            print(f"  - {result.scalar()} fact_sales_dw rows")

    except Exception as e:
        print(f"✗ Error loading sample data: {e}")
        raise


if __name__ == "__main__":
    load_sample_data()