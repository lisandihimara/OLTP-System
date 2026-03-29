from datetime import datetime, timedelta

from flask import Flask, render_template, request
from sqlalchemy import text

from config import engine
from queries import (
    ensure_dimensional_model_ready,
    get_sales_by_product_location_time_dim,
    get_max_sales_for_product_location_dim,
)

app = Flask(__name__)


def load_products():
    with engine.connect() as connection:
        result = connection.execute(text(
            "SELECT product_id_nk, product_name FROM dim_product ORDER BY product_name"
        ))
        return [dict(zip(result.keys(), row)) for row in result.fetchall()]


def load_locations():
    with engine.connect() as connection:
        result = connection.execute(text(
            "SELECT location_id_nk, location_name, city, country FROM dim_location ORDER BY country, city"
        ))
        return [dict(zip(result.keys(), row)) for row in result.fetchall()]


@app.route('/', methods=['GET'])
def dashboard():
    ensure_dimensional_model_ready()

    products = load_products()
    locations = load_locations()

    selected_product = request.args.get('product_id', type=int)
    selected_location = request.args.get('location_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not end_date:
        end_date = datetime.today().date().isoformat()
    if not start_date:
        start_date = (datetime.today().date() - timedelta(days=30)).isoformat()

    summary = None
    peak_day = None
    error = None

    if selected_product and selected_location:
        try:
            summary = get_sales_by_product_location_time_dim(
                selected_product,
                selected_location,
                start_date,
                end_date,
            )
            peak_day = get_max_sales_for_product_location_dim(
                selected_product,
                selected_location,
                start_date,
                end_date,
            )
            if summary is None:
                error = 'No data found for this product, location, and date range.'
        except Exception as exc:
            error = f'Unable to load dashboard data: {exc}'

    return render_template(
        'dashboard.html',
        products=products,
        locations=locations,
        selected_product=selected_product,
        selected_location=selected_location,
        start_date=start_date,
        end_date=end_date,
        summary=summary,
        peak_day=peak_day,
        error=error,
    )


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8500)
