import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Configuration
st.set_page_config(page_title="Global GHG Emissions Explorer", layout="wide")

# 2. Data Loading with Robust Error Handling
@st.cache_data
def load_data():
    file_path = 'OECD.ENV.EPI,DSD_AIR_GHG@DF_AIR_GHG,+.A.GHG._T.KG_CO2E_PS.csv'
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        st.error(f"File not found: {file_path}")
        st.stop()

    # Convert TIME_PERIOD to numeric and drop invalid rows
    df['TIME_PERIOD'] = pd.to_numeric(df['TIME_PERIOD'], errors='coerce')
    df['Observation value'] = pd.to_numeric(df['Observation value'], errors='coerce')
    
    # Drop rows where critical plotting data is missing
    df = df.dropna(subset=['TIME_PERIOD', 'Observation value', 'Reference area'])
    return df

df = load_data()

# --- Check if Dataframe is Empty ---
if df.empty:
    st.error("The dataset is empty after cleaning. Please check if the CSV file contains valid numeric years in the 'TIME_PERIOD' column.")
    st.stop()

# --- Sidebar Filters ---
st.sidebar.header("Interactive Filters")

# Calculate min and max safely
min_data_year = int(df['TIME_PERIOD'].min())
max_data_year = int(df['TIME_PERIOD'].max())

# Determine a safe default starting year for the slider
# Ensures the default (2000) is actually within the data's range
default_start_year = max(min_data_year, 2000)

all_countries = sorted(df['Reference area'].unique().tolist())
selected_countries = st.sidebar.multiselect(
    "Select Countries",
    options=all_countries,
    default=all_countries[:3]
)

year_range = st.sidebar.slider(
    "Select Year Range",
    min_value=min_data_year,
    max_value=max_data_year,
    value=(default_start_year, max_data_year)
)

# Filtering data based on selection
filtered_df = df[
    (df['Reference area'].isin(selected_countries)) &
    (df['TIME_PERIOD'].between(year_range[0], year_range[1]))
]

# --- Visualizations ---
st.title("🌍 Global GHG Emissions Tracker")

if not filtered_df.empty:
    fig_line = px.line(
        filtered_df,
        x='TIME_PERIOD',
        y='Observation value',
        color='Reference area',
        template="plotly_white",
        labels={'TIME_PERIOD': 'Year', 'Observation value': 'Emissions'}
    )
    st.plotly_chart(fig_line, width="stretch")
else:
    st.warning("No data available for the selected filters.")
