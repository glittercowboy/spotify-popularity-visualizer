# TÂCHES Spotify Popularity Visualizer

Interactive dashboard to visualize Spotify popularity trends for TÂCHES's tracks over time.

## Features

- Real-time popularity trend visualization
- Interactive date range selection
- Multi-track comparison
- Track statistics (average, min, max, standard deviation)
- Recent changes tracking with visual indicators
- Responsive design for all screen sizes

## Setup

1. Create a Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On macOS
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy your .env file from the tracker project (containing Airtable credentials)

4. Run the app:
```bash
streamlit run app.py
```

## Usage

1. Select date range using the date pickers
2. Choose tracks to display using the multi-select dropdown
3. Hover over the graph to see detailed values
4. View track statistics and recent changes below the graph

## Data Updates

The data is automatically updated daily by the companion tracking script. The visualization will reflect these changes in real-time when you refresh the page.
