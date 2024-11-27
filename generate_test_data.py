import os
from datetime import datetime, timedelta
from pyairtable import Table
import random

# Test data configuration
TRACKS = [
    {
        'name': 'Disappear',
        'album': 'Disappear',
        'release_date': '2022-05-20',
        'duration': '4:43',
        'base_popularity': 44,
        'uri': 'spotify:track:test1'
    },
    {
        'name': 'Heart of Gold - PIANIKA Remix',
        'album': 'Heart of Gold Remixes',
        'release_date': '2023-01-15',
        'duration': '3:55',
        'base_popularity': 38,
        'uri': 'spotify:track:test2'
    },
    {
        'name': 'So Proud of You',
        'album': 'So Proud of You',
        'release_date': '2023-08-01',
        'duration': '4:12',
        'base_popularity': 52,
        'uri': 'spotify:track:test3'
    }
]

def generate_popularity_trend(base_popularity, days, has_spike=False, spike_day=None):
    """Generate a realistic popularity trend with optional spike"""
    trend = []
    current = base_popularity
    
    for day in range(days):
        if has_spike and day == spike_day:
            # Create a sudden spike
            current += random.randint(15, 25)
        else:
            # Normal daily fluctuation
            change = random.uniform(-2, 2)
            current += change
        
        # Ensure popularity stays within bounds
        current = max(0, min(100, current))
        trend.append(round(current))
    
    return trend

def main():
    """Generate test data for visualization"""
    print("Generating test data...")
    
    # Initialize Airtable with placeholder credentials
    table = Table(
        "your_token_here",
        "your_base_id_here",
        "your_table_name_here"
    )
    
    # Generate 30 days of data
    days = 30
    end_date = datetime.now()
    
    for track in TRACKS:
        print(f"Generating data for {track['name']}...")
        
        # Generate popularity trend
        has_spike = random.choice([True, False])
        spike_day = random.randint(5, 25) if has_spike else None
        trend = generate_popularity_trend(track['base_popularity'], days, has_spike, spike_day)
        
        # Create records for each day
        for day in range(days):
            date = end_date - timedelta(days=days-day-1)
            record = {
                'Date': date.strftime('%Y-%m-%d'),
                'Track': track['name'],
                'Album': track['album'],
                'SPI': trend[day],
                'URI': track['uri'],
                'Release Date': track['release_date'],
                'Duration': track['duration']
            }
            
            # Print instead of creating records
            print(f"Would create record: {record}")
    
    print("\nTest data generated successfully!")
    print(f"Created {days} days of data for {len(TRACKS)} tracks")
    print("\nTo restore your Airtable to its original state, simply run your regular tracking script")

if __name__ == "__main__":
    main()
