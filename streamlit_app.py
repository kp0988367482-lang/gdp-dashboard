import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="GHG Emissions Dashboard", layout="wide")

# Sidebar Filters
st.sidebar.header("Filter Options")
region = st.sidebar.selectbox("Select Region", ["All", "Asia", "Europe", "North America"])
year = st.sidebar.multiselect("Select Year", [2017, 2018, 2019, 2020, 2021, 2022])

# Load data
df = pd.read_csv("emissions_data.csv")

# Apply filters
if "All" not in region:
    df = df[df["Region"] == region]
if year:
    df = df[df["Year"].isin(year)]

# Charts
st.subheader("📊 Total Carbon Emissions by Year (Scope 1, 2, 3)")
chart1 = alt.Chart(df).mark_bar().encode(
    x="Year:O",
    y="Total_Emissions_MTCO2e:Q",
    color="Scope:N"
)
st.altair_chart(chart1, use_container_width=True)

st.subheader("📈 Emission Intensity (MTCO₂e / Usage)")
chart2 = alt.Chart(df).mark_line().encode(
    x="Year:O",
    y="Intensity_MTCO2e_per_usage:Q"
)
st.altair_chart(chart2, use_container_width=True)

# KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Emissions (MTCO₂e)", f"{df['Total_Emissions_MTCO2e'].sum():,.2f}")
col2.metric("Scope 1 & 2 (MTCO₂e)", f"{df['Scope12_Emissions'].sum():,.2f}")
col3.metric("Projected Year-End (MTCO₂e)", f"{df['Projected_Emissions'].sum():,.2f}", "-10%")
col4.metric("Carbon Intensity", f"{df['Intensity_MTCO2e_per_usage'].mean():.6f}")
