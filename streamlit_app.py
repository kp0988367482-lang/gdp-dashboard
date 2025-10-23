import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="GHG Emissions Dashboard", layout="wide")
st.title("🌍 GHG Emissions Dashboard")

# ---------- Data input ----------
st.sidebar.header("Data")
uploaded = st.sidebar.file_uploader("Upload CSV", type=["csv"])
if uploaded:
    df_raw = pd.read_csv(uploaded)
else:
    st.sidebar.info("Using bundled sample: emissions_data.csv")
    df_raw = pd.read_csv("emissions_data.csv")

# Normalize columns
df_raw.columns = [c.strip().replace("\n", " ") for c in df_raw.columns]

# Try to find expected columns (case-insensitive contains)
def find(colnames, candidates):
    cols = []
    for c in candidates:
        for real in df_raw.columns:
            if c.lower() == real.lower() or c.lower() in real.lower():
                cols.append(real)
                break
    return cols[0] if cols else None

COL_YEAR   = find(df_raw.columns, ["Year"])
COL_REGION = find(df_raw.columns, ["Region"])
COL_S1     = find(df_raw.columns, ["Scope1", "Scope 1"])
COL_S2     = find(df_raw.columns, ["Scope2", "Scope 2"])
COL_S3     = find(df_raw.columns, ["Scope3", "Scope 3"])
COL_USAGE  = find(df_raw.columns, ["Usage", "kWh", "MWh"])

needed = [COL_YEAR, COL_S1, COL_S2, COL_S3]
if any(c is None for c in needed):
    st.error("CSV must include columns for Year, Scope1, Scope2, Scope3 (case-insensitive).")
    st.stop()

# Ensure numerics
for c in [COL_S1, COL_S2, COL_S3, COL_USAGE]:
    if c and c in df_raw.columns:
        df_raw[c] = pd.to_numeric(df_raw[c], errors="coerce")

# ---------- Sidebar filters ----------
st.sidebar.header("Filter Options")
region_options = ["All"] + (sorted(df_raw[COL_REGION].dropna().unique()) if COL_REGION else [])
region = st.sidebar.selectbox("Select Region", region_options)

year_values = sorted(df_raw[COL_YEAR].dropna().unique().tolist())
sel_years = st.sidebar.multiselect("Select Year", year_values, default=year_values)

df = df_raw.copy()
if region != "All" and COL_REGION:
    df = df[df[COL_REGION] == region]
if sel_years:
    df = df[df[COL_YEAR].isin(sel_years)]

# ---------- Aggregations ----------
df["Total_Emissions_MTCO2e"] = df[[COL_S1, COL_S2, COL_S3]].sum(axis=1)
if COL_USAGE:
    df["Intensity_MTCO2e_per_usage"] = df["Total_Emissions_MTCO2e"] / df[COL_USAGE].replace({0: pd.NA})

# Yearly totals (for charts/KPIs)
grp_year = df.groupby(COL_YEAR, as_index=False).agg(
    Scope1=(COL_S1, "sum"),
    Scope2=(COL_S2, "sum"),
    Scope3=(COL_S3, "sum"),
    Total=("Total_Emissions_MTCO2e", "sum"),
    Usage=(COL_USAGE, "sum") if COL_USAGE else ("Total_Emissions_MTCO2e", "size")
)
if COL_USAGE:
    grp_year["Intensity"] = grp_year["Total"] / grp_year["Usage"].replace({0: pd.NA})

# ---------- KPIs ----------
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Emissions (tCO₂e)", f"{grp_year['Total'].sum():,.2f}")
k2.metric("Scope 1 (tCO₂e)", f"{grp_year['Scope1'].sum():,.2f}")
k3.metric("Scope 2 (tCO₂e)", f"{grp_year['Scope2'].sum():,.2f}")
if COL_USAGE and grp_year["Usage"].sum():
    k4.metric("Carbon Intensity (tCO₂e/unit)", f"{(grp_year['Total'].sum()/grp_year['Usage'].sum()):.6f}")
else:
    k4.metric("Carbon Intensity (tCO₂e/unit)", "n/a")

# ---------- Charts ----------
st.subheader("📊 Total Carbon Emissions by Year — Stacked (Scope 1/2/3)")
stack_df = grp_year.melt(id_vars=[COL_YEAR], value_vars=["Scope1", "Scope2", "Scope3"],
                         var_name="Scope", value_name="Emissions")
chart1 = alt.Chart(stack_df).mark_bar().encode(
    x=alt.X(f"{COL_YEAR}:O", title="Year"),
    y=alt.Y("Emissions:Q", title="tCO₂e"),
    color=alt.Color("Scope:N", legend=alt.Legend(title="Scope"))
).properties(height=320)
st.altair_chart(chart1, use_container_width=True)

if COL_USAGE:
    st.subheader("📈 Emission Intensity (tCO₂e / Usage)")
    chart2 = alt.Chart(grp_year).mark_line(point=True).encode(
        x=alt.X(f"{COL_YEAR}:O", title="Year"),
        y=alt.Y("Intensity:Q", title="tCO₂e / unit")
    ).properties(height=300)
    st.altair_chart(chart2, use_container_width=True)

st.subheader("📋 Data (filtered)")
st.dataframe(df)

