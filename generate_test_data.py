import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pyairtable import Table
import random

# Load environment variables
load_dotenv()

# Test data configuration
TRACKS = [
    {
        'name': 'Disappear',
        'album': 'Disappear',
        'release_date': '2022-05-20',
        'duration': '4:43',
        'base_popularity': 44,
        'spotify_uri': 'spotify:track:test1'
    },
    {
        'name': 'Heart of Gold - PIANIKA Remix',
        'album': 'Heart of Gold (PIANIKA Remix)',
        'release_date': '2024-04-05',
        'duration': '3:51',
        'base_popularity': 36,
        'spotify_uri': 'spotify:track:test2'
    },
    {
        'name': 'So Proud of You',
        'album': 'So Proud of You',
        'release_date': '2024-10-18',
        'duration': '4:24',
        'base_popularity': 35,
        'spotify_uri': 'spotify:track:test3'
    }
]

def generate_popularity_trend(base_popularity, days, has_spike=False, spike_day=None):
    """Generate a realistic popularity trend with optional spike"""
    trend = []
    current = base_popularity
    
    for day in range(days):
        if has_spike and day == spike_day:
            # Create a spike in popularity (e.g., after a playlist addition)
            current += random.randint(10, 15)
        
        # Add some random daily variation
        change = random.randint(-2, 2)
        # Gradually return to base popularity after spike
        if current > base_popularity:
            change -= 1
        elif current < base_popularity:
            change += 1
            
        current = max(0, min(100, current + change))  # Keep within 0-100
        trend.append(current)
    
    return trend

def main():
    # Initialize Airtable
    table = Table(
        os.getenv('AIRTABLE_ACCESS_TOKEN'),
        os.getenv('AIRTABLE_BASE_ID'),
        os.getenv('AIRTABLE_TABLE_NAME')
    )
    
    # Generate 30 days of data
    days = 30
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days-1)
    
    print("Generating test data...")
    
    # Clear existing records (optional)
    existing_records = table.all()
    for record in existing_records:
        table.delete(record['id'])
    
    # Generate data for each track
    for track in TRACKS:
        print(f"Generating data for {track['name']}...")
        
        # Create popularity trend with a spike for some tracks
        has_spike = random.choice([True, False])
        spike_day = random.randint(5, 25) if has_spike else None
        popularity_trend = generate_popularity_trend(
            track['base_popularity'],
            days,
            has_spike,
            spike_day
        )
        
        # Create daily records
        current_date = start_date
        for popularity in popularity_trend:
            record = {
                'Date': current_date.strftime('%Y-%m-%d'),
                'Track': track['name'],
                'Album': track['album'],
                'SPI': popularity,
                'Spotify URI': track['spotify_uri'],
                'Duration': track['duration'],
                'Release Date': track['release_date']
            }
            table.create(record)
            current_date += timedelta(days=1)
    
    print("\nTest data generated successfully!")
    print(f"Created {days} days of data for {len(TRACKS)} tracks")
    print("You can now run the visualization app to see the results")
    print("\nTo restore your Airtable to its original state, simply run your regular tracking script")

if __name__ == "__main__":
    main()
