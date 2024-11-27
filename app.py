import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from pyairtable import Table

# Use Streamlit secrets
table = Table(
    st.secrets["AIRTABLE_ACCESS_TOKEN"],
    st.secrets["AIRTABLE_BASE_ID"],
    st.secrets["AIRTABLE_TABLE_NAME"]
)

# Set page config
st.set_page_config(
    page_title="TÂCHES Spotify Popularity Index",
    page_icon="📊",
    layout="wide"
)

def load_data():
    """Load and process data from Airtable"""
    records = table.all()
    
    # Convert records to DataFrame
    data = []
    for record in records:
        fields = record['fields']
        data.append({
            'Date': fields['Date'],
            'Track': fields['Track'],
            'Album': fields.get('Album', ''),
            'SPI': fields['SPI'],
            'Release Date': fields.get('Release Date', ''),
            'Duration': fields.get('Duration', '')
        })
    
    df = pd.DataFrame(data)
    
    # Convert dates
    df['Date'] = pd.to_datetime(df['Date'])
    df['Release Date'] = pd.to_datetime(df['Release Date'])
    
    # Group by Date and Track, taking the last entry for each day
    df = df.sort_values('Date').groupby(['Date', 'Track']).last().reset_index()
    
    return df

# Load data
df = load_data()

# Title
st.title("TÂCHES Spotify Popularity Index 📊")

# Date range selector
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input(
        "Start Date",
        value=df['Date'].min(),
        min_value=df['Date'].min().date(),
        max_value=df['Date'].max().date()
    )
with col2:
    end_date = st.date_input(
        "End Date",
        value=df['Date'].max(),
        min_value=df['Date'].min().date(),
        max_value=df['Date'].max().date()
    )

# Filter data by date range
mask = (df['Date'].dt.date >= start_date) & (df['Date'].dt.date <= end_date)
filtered_df = df.loc[mask]

# Get unique tracks
tracks = sorted(df['Track'].unique())

# Track selector
selected_tracks = st.multiselect(
    "Select Tracks to Display",
    tracks,
    default=tracks[:5]  # Default to top 5 tracks
)

# Filter by selected tracks
if selected_tracks:
    filtered_df = filtered_df[filtered_df['Track'].isin(selected_tracks)]

# Create main popularity trend chart
fig = px.line(
    filtered_df,
    x='Date',
    y='SPI',
    color='Track',
    title='Spotify Popularity Index Over Time',
    labels={'SPI': 'Popularity Score', 'Date': 'Date'},
    line_shape='linear'
)

# Customize layout
fig.update_layout(
    hovermode='x unified',
    legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01
    ),
    plot_bgcolor='white'
)

# Add gridlines
fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')

# Display the chart
st.plotly_chart(fig, use_container_width=True)

# Statistics section
st.header("Track Statistics")

# Calculate statistics for selected tracks
if selected_tracks:
    stats_df = filtered_df.groupby('Track').agg({
        'SPI': ['mean', 'min', 'max', 'std']
    }).round(2)
    
    stats_df.columns = ['Average', 'Minimum', 'Maximum', 'Std Dev']
    stats_df = stats_df.reset_index()
    
    # Display statistics
    st.dataframe(
        stats_df,
        column_config={
            "Track": "Track Name",
            "Average": "Average Popularity",
            "Minimum": "Lowest Score",
            "Maximum": "Highest Score",
            "Std Dev": "Standard Deviation"
        },
        hide_index=True
    )

# Recent changes section
st.header("Recent Changes")

# Get the most recent date in the data
most_recent = df['Date'].max()
previous_date = df['Date'].unique()[-2] if len(df['Date'].unique()) > 1 else most_recent

# Get records for the last two dates
recent_df = df[df['Date'].isin([most_recent, previous_date])]
changes = []

for track in recent_df['Track'].unique():
    track_data = recent_df[recent_df['Track'] == track].sort_values('Date')
    if len(track_data) > 1:
        old_spi = track_data.iloc[0]['SPI']
        new_spi = track_data.iloc[1]['SPI']
        change = new_spi - old_spi
        if change != 0:
            changes.append({
                'Track': track,
                'Old SPI': old_spi,
                'New SPI': new_spi,
                'Change': change
            })

if changes:
    changes_df = pd.DataFrame(changes)
    changes_df = changes_df.sort_values('Change', ascending=False)
    
    # Display changes with colored arrows
    for _, row in changes_df.iterrows():
        change = row['Change']
        arrow = "↑" if change > 0 else "↓"
        color = "green" if change > 0 else "red"
        st.markdown(
            f"**{row['Track']}**: {row['Old SPI']} → {row['New SPI']} "
            f"({arrow} {abs(change)}) ::{color}[{arrow}]"
        )
else:
    st.write("No changes in the last update.")
