import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from datetime import datetime
from pyairtable import Api
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
    all_tracks = {}  # Using dict to avoid duplicates
    print(f"🔍 Fetching albums for artist ID: {artist_id}")
    
    # Get artist's albums
    albums = []
    results = sp.artist_albums(artist_id, album_type='album,single,appears_on', limit=50)
    albums.extend(results['items'])
    while results['next']:
        results = sp.next(results)
        albums.extend(results['items'])
    
    print(f"📀 Found {len(albums)} albums/singles to process")
    
    # Get tracks from each album
    total_albums = len(albums)
    for idx, album in enumerate(albums, 1):
        print(f"[{idx}/{total_albums}] Processing: {album['name']}")
        try:
            results = sp.album_tracks(album['id'], limit=50)
            tracks = results['items']
            
            # Get remaining tracks if album has more
            while results['next']:
                results = sp.next(results)
                tracks.extend(results['items'])
            
            # Process each track
            for track in tracks:
                # Skip if we already have this track
                if track['id'] in all_tracks:
                    continue
                    
                # Include tracks where artist is primary, featured, or remixer
                is_primary = track['artists'][0]['id'] == artist_id
                is_featured = any(artist['id'] == artist_id for artist in track['artists'])
                is_remix = 'TÂCHES' in track['name'] or 'Taches' in track['name'] or 'taches' in track['name']
                
                if is_primary or (is_featured and not album['name'].startswith('Zootopia')) or is_remix:
                    try:
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
                        all_tracks[track['id']] = track_data
                        print(f"  ✅ Added: {track_data['name']} (Popularity: {track_data['popularity']})")
                    except Exception as e:
                        print(f"  ❌ Error processing track {track['id']}: {str(e)}")
                        continue
        except Exception as e:
            print(f"  ❌ Error processing album {album['name']}: {str(e)}")
            continue
    
    return list(all_tracks.values())

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
    start_time = time.time()
    print("🎵 Starting Spotify popularity tracking...")
    
    # Initialize clients
    print("🔑 Initializing Spotify client...")
    sp = get_spotify_client()
    
    print("🔑 Initializing Airtable client...")
    api = Api(os.environ['AIRTABLE_ACCESS_TOKEN'])
    table = api.table(os.environ['AIRTABLE_BASE_ID'], os.environ['AIRTABLE_TABLE_NAME'])
    
    # Get all tracks
    artist_id = os.environ['SPOTIFY_ARTIST_ID']  # TÂCHES Spotify ID
    tracks = get_all_artist_tracks(sp, artist_id)
    
    # Current date for logging
    current_date = datetime.now().strftime('%Y-%m-%d')
    print(f"\n📊 Processing {len(tracks)} tracks for date: {current_date}")
    
    # Process each track
    logged_tracks = []
    changes = 0
    
    for track in tracks:
        # Get last recorded popularity
        last_popularity = get_last_popularity(table, track['uri'])
        
        # Only log if popularity has changed or no previous record exists
        if last_popularity is None:
            print(f"📝 First record for: {track['name']}")
        elif last_popularity != track['popularity']:
            print(f"📈 Popularity changed for {track['name']}: {last_popularity} → {track['popularity']}")
        else:
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
            print(f"✅ Logged: {track['name']}")
            time.sleep(0.2)  # Rate limiting
        except Exception as e:
            print(f"❌ Error logging {track['name']}: {str(e)}")
    
    # Display results
    end_time = time.time()
    duration = round(end_time - start_time, 2)
    print(f"\n📊 Summary (completed in {duration}s):")
    print(f"Processed {len(tracks)} tracks, logged {changes} popularity changes:")
    if changes > 0:
        print("\nTracks with popularity changes:")
        for track in logged_tracks:
            print(f"• {track['name']} ({track['album']}) - {track['popularity']}/100")
    else:
        print("No popularity changes detected today.")

if __name__ == "__main__":
    main()
