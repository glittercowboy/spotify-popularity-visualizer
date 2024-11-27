import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from datetime import datetime
from pyairtable import Table
import time

def get_spotify_client():
    """Initialize Spotify client with credentials"""
    client_credentials_manager = SpotifyClientCredentials(
        client_id=os.environ['SPOTIFY_CLIENT_ID'],
        client_secret=os.environ['SPOTIFY_CLIENT_SECRET']
    )
    return spotipy.Spotify(client_credentials_manager=client_credentials_manager)

def get_all_artist_tracks(sp, artist_id):
    """Get all tracks by the artist, including features and remixes"""
    all_tracks = []
    print(f"Fetching tracks for artist ID: {artist_id}")
    
    # Get artist's albums
    albums = []
    results = sp.artist_albums(artist_id, album_type='album,single,appears_on')
    albums.extend(results['items'])
    while results['next']:
        results = sp.next(results)
        albums.extend(results['items'])
    
    print(f"Found {len(albums)} albums/singles")

    # Get tracks from each album
    for album in albums:
        print(f"Processing album: {album['name']}")
        results = sp.album_tracks(album['id'])
        for track in results['tracks']['items']:
            # Check if artist is in the track
            if any(artist['id'] == artist_id for artist in track['artists']):
                track_info = sp.track(track['id'])
                track_data = {
                    'id': track_info['id'],
                    'name': track_info['name'],
                    'album': album['name'],
                    'release_date': album['release_date'],
                    'popularity': track_info['popularity'],
                    'duration_ms': track_info['duration_ms'],
                    'uri': track_info['uri']
                }
                all_tracks.append(track_data)
                print(f"Added track: {track_data['name']} (Popularity: {track_data['popularity']})")
    
    return all_tracks

def get_last_popularity(table, track_uri):
    """Get the last recorded popularity for a track"""
    records = table.all(formula=f"{{URI}} = '{track_uri}'", sort=['-Date'])
    return records[0]['fields']['SPI'] if records else None

def format_duration(ms):
    """Convert milliseconds to MM:SS format"""
    seconds = ms // 1000
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    return f"{minutes}:{remaining_seconds:02d}"

def main():
    print("Starting Spotify popularity tracking...")
    
    # Initialize clients
    print("Initializing Spotify client...")
    sp = get_spotify_client()
    
    print("Initializing Airtable client...")
    table = Table(
        os.environ['AIRTABLE_ACCESS_TOKEN'],
        os.environ['AIRTABLE_BASE_ID'],
        os.environ['AIRTABLE_TABLE_NAME']
    )
    
    # Get all tracks
    artist_id = os.environ['SPOTIFY_ARTIST_ID']  # TÂCHES Spotify ID
    print(f"\nFetching tracks for artist ID: {artist_id}")
    tracks = get_all_artist_tracks(sp, artist_id)
    
    # Current date for logging
    current_date = datetime.now().strftime('%Y-%m-%d')
    print(f"\nProcessing tracks for date: {current_date}")
    
    # Process each track
    logged_tracks = []
    changes = 0
    
    for track in tracks:
        print(f"\nChecking track: {track['name']}")
        # Get last recorded popularity
        last_popularity = get_last_popularity(table, track['uri'])
        
        # Only log if popularity has changed or no previous record exists
        if last_popularity is None:
            print(f"No previous record found for {track['name']}")
        elif last_popularity != track['popularity']:
            print(f"Popularity changed from {last_popularity} to {track['popularity']}")
        else:
            print(f"No popularity change for {track['name']}")
            continue
            
        # Create record
        record = {
            'Date': current_date,
            'Track': track['name'],
            'Album': track['album'],
            'SPI': track['popularity'],
            'URI': track['uri'],
            'Release Date': track['release_date'],
            'Duration': format_duration(track['duration_ms'])
        }
        
        # Add to Airtable
        try:
            table.create(record)
            logged_tracks.append(track)
            changes += 1
            print(f"✅ Successfully logged {track['name']} - SPI: {track['popularity']}")
            time.sleep(0.2)  # Rate limiting
        except Exception as e:
            print(f"❌ Error logging {track['name']}: {str(e)}")
    
    # Display results
    print(f"\n📊 Summary:")
    print(f"Tracked {len(tracks)} songs, logged {changes} popularity changes:")
    if changes > 0:
        print("\nTracks with popularity changes:")
        for track in logged_tracks:
            print(f"• {track['name']} ({track['album']}) - {track['popularity']}/100 - {format_duration(track['duration_ms'])} - Released: {track['release_date']}")
    else:
        print("No popularity changes detected today.")

if __name__ == "__main__":
    main()