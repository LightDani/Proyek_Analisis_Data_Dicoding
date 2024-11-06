import streamlit as st
import pandas as pd
import altair as alt

# Load and preprocess data
data = pd.read_csv("main_data.csv")


def preprocess_data(df):
    def fix_prefix(data):
        return data.astype(str).str.zfill(5)

    df["customer_zip_code_prefix"] = fix_prefix(df["customer_zip_code_prefix"])
    df["seller_zip_code_prefix"] = fix_prefix(df["seller_zip_code_prefix"])
    df["order_item_id"] = df["order_item_id"].astype(str)
    date_columns = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    for column in date_columns:
        df[column] = pd.to_datetime(df[column], errors="coerce")
    df.query("order_status == 'delivered'", inplace=True)


preprocess_data(data)

# Sidebar filter for years
with st.sidebar:
    st.header("Filters")
    years = st.multiselect(
        "Select Year(s)",
        options=data["order_purchase_year"].unique(),
        default=data["order_purchase_year"].unique(),
    )

# Filter data based on selected years
filtered_data = data[data["order_purchase_year"].isin(years)]

# Dashboard title and selected years
st.title("E-Commerce Sales Dashboard")
st.write(f"Dashboard for Years: {', '.join(map(str, sorted(years)))}")

# ---- KPI Row ----
total_revenue = filtered_data["total_revenue"].sum()
num_orders = filtered_data["order_id"].nunique()
average_order_value = total_revenue / num_orders if num_orders > 0 else 0
units_sold = filtered_data["order_item_id"].count()

# Display KPIs in a row with individual `with` statements
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Revenue", f"R${total_revenue / 1_000_000:.3f}M")
with col2:
    st.metric("Average Order Value", f"R${average_order_value:,.2f}")
with col3:
    st.metric("Number of Orders", f"{num_orders:,}")
with col4:
    st.metric("Units Sold", f"{units_sold:,}")

# ---- Top-Selling Product Categories Tabs ----
st.subheader("Top-Selling Product Categories")
tab1, tab2 = st.tabs(["By Units Sold", "By Revenue"])

with tab1:
    top_categories_units = (
        filtered_data.groupby("product_category_name_english")["order_item_id"]
        .count()
        .reset_index()
        .rename(columns={"order_item_id": "units_sold"})
        .sort_values(by="units_sold", ascending=False)
        .head(10)
    )

    bar_chart_units = (
        alt.Chart(top_categories_units)
        .mark_bar()
        .encode(
            x=alt.X("units_sold:Q", title="Units Sold"),
            y=alt.Y(
                "product_category_name_english:N", sort="-x", title="Product Category"
            ),
        )
    )
    st.altair_chart(bar_chart_units, use_container_width=True)

with tab2:
    top_categories_revenue = (
        filtered_data.groupby("product_category_name_english")["total_revenue"]
        .sum()
        .reset_index()
        .sort_values(by="total_revenue", ascending=False)
        .head(10)
    )

    bar_chart_revenue = (
        alt.Chart(top_categories_revenue)
        .mark_bar()
        .encode(
            x=alt.X("total_revenue:Q", title="Total Revenue"),
            y=alt.Y(
                "product_category_name_english:N", sort="-x", title="Product Category"
            ),
        )
    )
    st.altair_chart(bar_chart_revenue, use_container_width=True)

# ---- Top Revenue-Generating States Bar Chart ----
with st.container():
    st.subheader("Top Revenue-Generating States")
    top_states = (
        filtered_data.groupby("customer_state")["total_revenue"]
        .sum()
        .reset_index()
        .sort_values(by="total_revenue", ascending=False)
        .head(10)
    )

    state_chart = (
        alt.Chart(top_states)
        .mark_bar()
        .encode(
            x=alt.X("total_revenue:Q", title="Total Revenue"),
            y=alt.Y("customer_state:N", sort="-x", title="State"),
        )
    )
    st.altair_chart(state_chart, use_container_width=True)


# ---- Monthly Revenue and Order Trend ----
st.subheader("Monthly Trend")

# Extract year and month
filtered_data["year_month"] = filtered_data["order_purchase_timestamp"].dt.to_period(
    "M"
)

# Group by month and aggregate revenue and order count
monthly_trend = (
    filtered_data.groupby("year_month")
    .agg(total_revenue=("total_revenue", "sum"), order_count=("order_id", "nunique"))
    .reset_index()
)

# Convert year_month back to datetime for plotting
monthly_trend["year_month"] = monthly_trend["year_month"].dt.to_timestamp()

tab1, tab2 = st.tabs(["Revenue", "Order Count"])
# Left Chart: Revenue Over Time
with tab1:
    revenue_chart = (
        alt.Chart(monthly_trend)
        .mark_line(color="blue")
        .encode(
            x=alt.X("year_month:T", title="Month"),
            y=alt.Y("total_revenue:Q", title="Total Revenue"),
            tooltip=["year_month:T", "total_revenue:Q"],
        )
    )
    st.altair_chart(revenue_chart, use_container_width=True)

# Right Chart: Order Count Over Time
with tab2:
    order_chart = (
        alt.Chart(monthly_trend)
        .mark_line(color="orange")
        .encode(
            x=alt.X("year_month:T", title="Month"),
            y=alt.Y("order_count:Q", title="Order Count"),
            tooltip=["year_month:T", "order_count:Q"],
        )
    )
    st.altair_chart(order_chart, use_container_width=True)
