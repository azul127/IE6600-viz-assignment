import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Configuration
st.set_page_config(page_title="Global GHG Emissions Explorer", layout="wide")

# 2. Data Loading with Correct Column Mapping
@st.cache_data
def load_data():
    file_path = 'OECD.ENV.EPI,DSD_AIR_GHG@DF_AIR_GHG,+.A.GHG._T.KG_CO2E_PS.csv'
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        st.error(f"File not found: {file_path}")
        st.stop()

    # The CSV contains data in 'TIME_PERIOD' and 'OBS_VALUE'
    # 'Time period' and 'Observation value' columns appear to be empty in the source
    df['TIME_PERIOD'] = pd.to_numeric(df['TIME_PERIOD'], errors='coerce')
    df['OBS_VALUE'] = pd.to_numeric(df['OBS_VALUE'], errors='coerce')
    
    # Drop rows where critical plotting data is missing
    # We use 'Reference area' for the country names
    df = df.dropna(subset=['TIME_PERIOD', 'OBS_VALUE', 'Reference area'])
    return df

df = load_data()

# Check if Dataframe is empty
if df.empty:
    st.error("Data processing error: No valid numeric data found in 'TIME_PERIOD' or 'OBS_VALUE'.")
    st.stop()

# --- Sidebar Filters ---
st.sidebar.header("Interactive Filters")

min_data_year = int(df['TIME_PERIOD'].min())
max_data_year = int(df['TIME_PERIOD'].max())

# Find available countries
all_countries = sorted(df['Reference area'].unique().tolist())

# Default selections
potential_defaults = ['United Kingdom', 'United States', 'Australia', 'China']
default_options = [c for c in all_countries if any(d in c for d in potential_defaults)]
if not default_options:
    default_options = all_countries[:3]

selected_countries = st.sidebar.multiselect(
    "Select Countries to Compare",
    options=all_countries,
    default=default_options
)

year_range = st.sidebar.slider(
    "Select Year Range",
    min_value=min_data_year,
    max_value=max_data_year,
    value=(max(min_data_year, 2000), max_data_year)
)

# Filtering
filtered_df = df[
    (df['Reference area'].isin(selected_countries)) &
    (df['TIME_PERIOD'].between(year_range[0], year_range[1]))
]

# --- Main Dashboard ---
st.title("🌍 Global Greenhouse Gas (GHG) Emissions Tracker")
st.markdown("Exploring historical trends in GHG emissions per person (kg CO2e) across different regions.")

# Visualization 1: Line Chart
st.subheader("1. Emissions Trend Over Time")
if not filtered_df.empty:
    fig_line = px.line(
        filtered_df,
        x='TIME_PERIOD',
        y='OBS_VALUE',
        color='Reference area',
        labels={
            'TIME_PERIOD': 'Year',
            'OBS_VALUE': 'Emissions (kg CO2e per person)'
        },
        markers=True,
        template="plotly_white"
    )
    fig_line.update_layout(hovermode="x unified")
    st.plotly_chart(fig_line, width="stretch")
else:
    st.warning("Please select countries in the sidebar to display the chart.")

# Visualization 2: Bar Chart
st.subheader(f"2. Comparison for the Year {year_range[1]}")
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
        color_continuous_scale='Reds',
        labels={'OBS_VALUE': 'Emissions', 'Reference area': 'Country'}
    )
    st.plotly_chart(fig_bar, width="stretch")

# --- Write-up Section ---
st.divider()
st.header("Project Write-up")

with st.expander("Design Rationale & Development Commentary"):
    st.subheader("Question Answered")
    st.write("How do per-capita greenhouse gas emissions vary across different nations, and which regions have successfully reduced their carbon footprint over the last two decades?")

    st.subheader("Design Decisions")
    st.markdown("""
    * **Visual Encodings**: 
        * **Line Charts** emphasize the temporal change, allowing users to see if a country's emissions are peaking or declining.
        * **Bar Charts** provide an immediate ranking of the selected nations for a specific point in time.
