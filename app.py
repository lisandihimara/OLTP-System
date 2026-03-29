"""
Streamlit UI for the OLTP Sales System.

Run with:
    streamlit run app.py
"""
from datetime import datetime, timedelta

import streamlit as st
from sqlalchemy import text

from config import engine
from queries import (
    ensure_dimensional_model_ready,
    get_customers_by_region,
    get_customers_drilldown,
    get_max_sales_for_product_location,
    get_max_sales_for_product_location_dim,
    get_sales_by_product_location_time,
    get_sales_by_product_location_time_dim,
)


st.set_page_config(
    page_title="OLTP Sales UI",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_styles() -> None:
    """Apply a custom visual style so the app feels intentional and distinct."""
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

            html, body, [class*="css"], [data-testid="stAppViewContainer"] {
                font-family: 'Space Grotesk', sans-serif;
            }

            [data-testid="stAppViewContainer"] {
                background:
                    radial-gradient(circle at 10% 20%, rgba(24, 115, 255, 0.12), transparent 35%),
                    radial-gradient(circle at 90% 10%, rgba(255, 105, 95, 0.14), transparent 40%),
                    linear-gradient(180deg, #f8fafc 0%, #eef3f9 100%);
            }

            h1, h2, h3 {
                letter-spacing: 0.02em;
                color: #0f172a;
            }

            .metric-card {
                padding: 0.8rem;
                border-radius: 0.75rem;
                border: 1px solid rgba(15, 23, 42, 0.12);
                background: rgba(255, 255, 255, 0.82);
                box-shadow: 0 12px 24px rgba(15, 23, 42, 0.08);
            }

            .small-muted {
                font-family: 'IBM Plex Mono', monospace;
                color: #475569;
                font-size: 0.8rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _to_float(value, default: float = 0.0) -> float:
    """Safely coerce numeric-like values for display formatting."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value, default: int = 0) -> int:
    """Safely coerce integer-like values for display formatting."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def render_sales_detail(result: dict) -> None:
    """Render Query 1 details in readable UI blocks instead of raw JSON."""
    st.subheader("Details")
    left, right = st.columns(2)
    left.write(f"Product: {result['product_name']}")
    left.write(f"Category: {result['category']}")
    left.write(f"Brand: {result['brand']}")
    left.write(f"Product ID: {_to_int(result['product_id'])}")

    right.write(f"Location: {result['location_name']}")
    right.write(f"City: {result['city']}")
    right.write(f"Country: {result['country']}")
    right.write(f"Location ID: {_to_int(result['location_id'])}")

    summary_row = {
        "First Sale": str(result["first_sale_date"]),
        "Last Sale": str(result["last_sale_date"]),
        "Total Revenue": f"${_to_float(result['total_revenue']):,.2f}",
        "Average Sale": f"${_to_float(result['avg_sale_amount']):,.2f}",
    }
    st.dataframe([summary_row], use_container_width=True, hide_index=True)


def render_peak_day_detail(result: dict) -> None:
    """Render Query 2 details in readable UI blocks instead of raw JSON."""
    max_day = result.get("max_sales_day")
    stats = result.get("overall_stats")

    if max_day:
        st.subheader("Peak Day Detail")
        peak_row = {
            "Date": str(max_day["sale_date"]),
            "Product": max_day["product_name"],
            "Location": max_day["location_name"],
            "Number of Sales": _to_int(max_day["number_of_sales"]),
            "Total Quantity": _to_int(max_day["total_quantity"]),
            "Daily Revenue": f"${_to_float(max_day['daily_revenue']):,.2f}",
        }
        st.dataframe([peak_row], use_container_width=True, hide_index=True)

    if stats:
        st.subheader("Period Summary")
        stats_row = {
            "Total Sales": _to_int(stats["total_sales"]),
            "Days With Sales": _to_int(stats["days_with_sales"]),
            "Average Daily Sales": f"{_to_float(stats['avg_daily_sales']):.2f}",
            "Maximum Daily Sales": f"{_to_float(stats['max_daily_sales']):.0f}",
        }
        st.dataframe([stats_row], use_container_width=True, hide_index=True)


@st.cache_data(ttl=60)
def load_products() -> list[dict]:
    with engine.connect() as connection:
        result = connection.execute(text("""
            SELECT product_id, product_name, category, brand
            FROM product
            ORDER BY product_name
        """))
        return [dict(zip(result.keys(), row)) for row in result.fetchall()]


@st.cache_data(ttl=60)
def load_locations() -> list[dict]:
    with engine.connect() as connection:
        result = connection.execute(text("""
            SELECT location_id, location_name, city, country
            FROM location
            ORDER BY location_name
        """))
        return [dict(zip(result.keys(), row)) for row in result.fetchall()]


@st.cache_data(ttl=60)
def load_regions() -> list[str]:
    rows = get_customers_by_region()
    if not rows:
        return []
    return [row["region"] for row in rows]


@st.cache_data(ttl=60)
def load_countries() -> list[str]:
    with engine.connect() as connection:
        result = connection.execute(text("""
            SELECT DISTINCT country_name
            FROM vw_customers_geog_rollup
            ORDER BY country_name
        """))
        return [row[0] for row in result.fetchall()]


def render_metric_row(result: dict) -> None:
    c1, c2, c3 = st.columns(3)
    c1.metric("Sales Count", f"{result['number_of_sales']:,}")
    c2.metric("Quantity Sold", f"{result['total_quantity_sold']:,}")
    c3.metric("Total Revenue", f"${_to_float(result['total_revenue']):,.2f}")

    c4, c5, c6 = st.columns(3)
    c4.metric("Average Sale", f"${_to_float(result['avg_sale_amount']):,.2f}")
    c5.metric("Min Sale", f"${_to_float(result['min_sale_amount']):,.2f}")
    c6.metric("Max Sale", f"${_to_float(result['max_sale_amount']):,.2f}")

    st.caption(
        f"First sale: {result['first_sale_date']} | Last sale: {result['last_sale_date']}"
    )


def render_peak_day(result: dict) -> None:
    max_day = result.get("max_sales_day")
    stats = result.get("overall_stats")
    if not max_day:
        st.warning("No matching peak sales day found for this filter.")
        return

    st.subheader("Peak Sales Day")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Date", str(max_day["sale_date"]))
    c2.metric("Number of Sales", f"{max_day['number_of_sales']:,}")
    c3.metric("Total Quantity", f"{max_day['total_quantity']:,}")
    c4.metric("Daily Revenue", f"${_to_float(max_day['daily_revenue']):,.2f}")

    if stats:
        st.subheader("Period Statistics")
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Total Sales", f"{stats['total_sales']:,}")
        s2.metric("Days With Sales", f"{stats['days_with_sales']:,}")
        s3.metric("Avg Daily Sales", f"{_to_float(stats['avg_daily_sales']):.2f}")
        s4.metric("Max Daily Sales", f"{_to_float(stats['max_daily_sales']):.0f}")


def main() -> None:
    inject_styles()

    st.title("OLTP Sales System UI")
    st.markdown(
        "Interactive analytics for OLTP queries, dimensional query comparison, "
        "and customer geography rollups."
    )

    with st.sidebar:
        st.header("Query Controls")

        model = st.radio(
            "Data Source",
            options=["WITHOUT DIM (OLTP)", "WITH DIM (Star Schema)"],
            index=0,
        )

        if model == "WITH DIM (Star Schema)":
            if ensure_dimensional_model_ready():
                st.success("Dimensional model is ready.")
            else:
                st.error("Dimensional model is not ready. Run create_db.py and sample_data.py.")

        products = load_products()
        locations = load_locations()

        if not products or not locations:
            st.error("No products/locations found. Populate the database using sample_data.py.")
            st.stop()

        product_labels = {
            p["product_id"]: f"{p['product_name']} [{p['category']} | {p['brand']}]"
            for p in products
        }
        location_labels = {
            l["location_id"]: f"{l['location_name']} ({l['city']}, {l['country']})"
            for l in locations
        }

        product_id = st.selectbox(
            "Product",
            options=list(product_labels.keys()),
            format_func=lambda pid: product_labels[pid],
        )
        location_id = st.selectbox(
            "Location",
            options=list(location_labels.keys()),
            format_func=lambda lid: location_labels[lid],
        )

        today = datetime.now().date()
        two_years_ago = today - timedelta(days=730)
        start_date, end_date = st.date_input(
            "Date Range",
            value=(two_years_ago, today),
            min_value=today - timedelta(days=3650),
            max_value=today,
        )

        if start_date > end_date:
            st.error("Start date must be before end date.")
            st.stop()

        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

    tab1, tab2, tab3 = st.tabs([
        "Query 1: Product + Location + Time",
        "Query 2: Peak Sales Day",
        "Geography Rollup",
    ])

    with tab1:
        st.markdown("### Sales Summary")
        st.markdown(
            f"<p class='small-muted'>Model: {model} | Product ID: {product_id} | "
            f"Location ID: {location_id} | Period: {start_date_str} to {end_date_str}</p>",
            unsafe_allow_html=True,
        )

        if st.button("Run Query 1", type="primary"):
            with st.spinner("Running Query 1..."):
                if model == "WITH DIM (Star Schema)":
                    result = get_sales_by_product_location_time_dim(
                        product_id, location_id, start_date_str, end_date_str
                    )
                else:
                    result = get_sales_by_product_location_time(
                        product_id, location_id, start_date_str, end_date_str
                    )

            if result:
                st.success("Query completed.")
                render_metric_row(result)
                render_sales_detail(result)
            else:
                st.warning("No sales rows found for this filter.")

    with tab2:
        st.markdown("### Maximum Sales Over Time")
        st.markdown(
            f"<p class='small-muted'>Model: {model} | Product ID: {product_id} | "
            f"Location ID: {location_id} | Period: {start_date_str} to {end_date_str}</p>",
            unsafe_allow_html=True,
        )

        if st.button("Run Query 2", type="primary"):
            with st.spinner("Running Query 2..."):
                if model == "WITH DIM (Star Schema)":
                    result = get_max_sales_for_product_location_dim(
                        product_id, location_id, start_date_str, end_date_str
                    )
                else:
                    result = get_max_sales_for_product_location(
                        product_id, location_id, start_date_str, end_date_str
                    )

            if result:
                st.success("Query completed.")
                render_peak_day(result)
                render_peak_day_detail(result)
            else:
                st.warning("No sales rows found for this filter.")

    with tab3:
        st.markdown("### Customer Geography Hierarchy")
        region_options = ["All Regions"] + load_regions()
        selected_region = st.selectbox("Region Filter", options=region_options)

        if st.button("Run Geography Rollup", type="primary"):
            with st.spinner("Loading geography data..."):
                if selected_region == "All Regions":
                    rows = get_customers_by_region()
                else:
                    rows = get_customers_by_region(selected_region)

            if rows:
                st.dataframe(rows, use_container_width=True)
            else:
                st.warning("No geography rows found. Run customers_dim.py first.")

        countries: list[str] = []
        try:
            countries = load_countries()
        except Exception:
            st.info("Country list is unavailable until customers_dim.py is populated.")

        if countries:
            country = st.selectbox("Country Drill-down", options=countries)
            if st.button("Run Drill-down", type="primary"):
                with st.spinner("Loading customer drill-down..."):
                    details = get_customers_drilldown(country)

                if details:
                    st.dataframe(details, use_container_width=True)
                else:
                    st.warning("No customer rows found for that country.")


if __name__ == "__main__":
    main()