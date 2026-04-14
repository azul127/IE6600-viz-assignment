import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Configuration
st.set_page_config(page_title="Global GHG Emissions Explorer", layout="wide")

# 2. Data Loading with Specific Filtering
@st.cache_data
def load_data():
    file_path = 'OECD.ENV.EPI,DSD_AIR_GHG@DF_AIR_GHG,+.A.GHG._T.KG_CO2E_PS.csv'
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        st.error(f"File not found: {file_path}")
        st.stop()

    # --- CRITICAL FIX: Filtering to avoid vertical overlapping lines ---
    # We filter by 'Pollutant' to ensure we only show Total Greenhouse Gases
    # and not individual gases like CO2 or Methane simultaneously.
    if 'Pollutant' in df.columns:
        df = df[df['Pollutant'] == 'Greenhouse gases']
    
    # Ensuring Measure is consistent (Total emissions excluding LULUCF)
    if 'Measure' in df.columns:
        df = df[df['Measure'].str.contains('Total emissions', na=False)]

    # Convert numeric columns
    df['TIME_PERIOD'] = pd.to_numeric(df['TIME_PERIOD'], errors='coerce')
    df['OBS_VALUE'] = pd.to_numeric(df['OBS_VALUE'], errors='coerce')
    
    # Drop invalid rows and SORT by year to ensure lines connect correctly
    df = df.dropna(subset=['TIME_PERIOD', 'OBS_VALUE', 'Reference area'])
    df = df.sort_values(by=['Reference area', 'TIME_PERIOD'])
    
    return df

df = load_data()

# Safety check for empty dataframe
if df.empty:
    st.error("Data processing error: No valid records found. Check your CSV filters.")
    st.stop()

# --- Sidebar Filters ---
st.sidebar.header("Dashboard Filters")

min_year = int(df['TIME_PERIOD'].min())
max_year = int(df['TIME_PERIOD'].max())
all_countries = sorted(df['Reference area'].unique().tolist())

# Dynamic Default Selection
potential_defaults = ['United Kingdom', 'United States', 'China', 'Australia', 'Germany']
default_selection = [c for c in all_countries if any(d in c for d in potential_defaults)]
if not default_selection:
    default_selection = all_countries[:3]

selected_countries = st.sidebar.multiselect(
    "Select Countries/Regions",
    options=all_countries,
    default=default_selection
)

year_range = st.sidebar.slider(
    "Select Year Range",
    min_value=min_year,
    max_value=max_year,
    value=(max(min_year, 2000), max_year)
)

# Apply filters
filtered_df = df[
    (df['Reference area'].isin(selected_countries)) &
    (df['TIME_PERIOD'].between(year_range[0], year_range[1]))
]

# --- Main Dashboard ---
st.title("🌍 Global Greenhouse Gas (GHG) Emissions Explorer")
st.markdown("This dashboard explores GHG emissions per capita (kg CO2e) based on OECD Inventory data.")

# Visualization 1: Time Series (Line Chart)
st.subheader("1. Historical Emissions Trend")
if not filtered_df.empty:
    fig_line = px.line(
        filtered_df,
        x='TIME_PERIOD',
        y='OBS_VALUE',
        color='Reference area',
        labels={'TIME_PERIOD': 'Year', 'OBS_VALUE': 'Emissions (kg CO2e)'},
        markers=True,
        template="plotly_white"
    )
    # Fix for tooltip and line clarity
    fig_line.update_layout(hovermode="x unified")
    st.plotly_chart(fig_line, width="stretch")
else:
    st.info("Select countries in the sidebar to visualize trends.")

# Visualization 2: Comparison (Bar Chart)
st.subheader(f"2. Snapshot Comparison for {year_range[1]}")
df_snapshot = df[
    (df['TIME_PERIOD'] == year_range[1]) & 
    (df['Reference area'].isin(selected_countries))
]

if not df_snapshot.empty:
    fig_bar = px.bar(
        df_snapshot.sort_values('OBS_VALUE', ascending=False),
        x='Reference area',
        y='OBS_VALUE',
        color='OBS_VALUE',
        color_continuous_scale='Viridis',
        labels={'OBS_VALUE': 'Emissions', 'Reference area': 'Country'}
    )
    st.plotly_chart(fig_bar, width="stretch")

# --- Mandatory Write-up Section ---
st.divider()
st.header("Project Write-up")

with st.expander("Design Rationale & Development Process", expanded=True):
    st.subheader("1. Question Answered")
    st.write("Which major economies have effectively reduced their per-capita greenhouse gas emissions over the last two decades, and how do they compare in the most recent recorded year?")

    st.subheader("2. Design Decisions")
    st.markdown("""
    * **Visual Encodings**: 
        * **Line Charts** are used to show temporal trends, making it easy to spot historical peaks and declines.
        * **Bar Charts** are used for cross-sectional comparisons, providing a clear ranking of emissions at a specific point in time.
    * **Interaction**: 
        * **Multiselect**: Allows users to filter out clutter and focus on specific regional comparisons.
        * **Year Slider**: Enables focused exploration of specific historical periods.
    * **Fixing Data Overlap**: The dataset was filtered to show only 'Total Greenhouse Gases' to prevent multiple pollutant types from overlapping on the same year.
    """)

    st.subheader("3. Development Commentary")
    st.write("Total development time: Approximately 5-6 hours. The most time-consuming part was identifying and filtering redundant pollutant categories in the OECD dataset that were causing visual artifacts in the line chart.")
