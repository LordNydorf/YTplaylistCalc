from flask import Flask, request, jsonify, render_template
import requests
import isodate
from datetime import timedelta
import re

app = Flask(__name__)

# Function to extract playlist ID from URL
def extract_playlist_id(url):
    match = re.search(r"list=([a-zA-Z0-9_-]+)", url)
    if match:
        return match.group(1)
    else:
        return None

# Function to fetch video durations from YouTube API with pagination
def fetch_video_durations(playlist_id):
    api_key = 'YOUR_API_KEY'  # Replace with your actual YouTube API key
    base_url = f'https://www.googleapis.com/youtube/v3/playlistItems?part=contentDetails&playlistId={playlist_id}&maxResults=50&key={api_key}'
    
    video_durations = []
    next_page_token = None

    while True:
        url = base_url
        if next_page_token:
            url += f"&pageToken={next_page_token}"
        
        response = requests.get(url)
        data = response.json()

        # Check for API error (e.g., invalid playlist ID)
        if 'error' in data:
            error_message = data['error']['message']
            return {'error': f"Invalid playlist ID or the playlist is not accessible. Error: {error_message}"}

        # Check if the playlist contains items
        if 'items' not in data or len(data['items']) == 0:
            return None  # Return None if no videos are found

        # Get video IDs from the playlist
        video_ids = [item['contentDetails']['videoId'] for item in data['items']]
        
        # Fetch video durations based on video IDs
        if video_ids:
            video_url = f'https://www.googleapis.com/youtube/v3/videos?part=contentDetails&id={",".join(video_ids)}&key={api_key}'
            video_response = requests.get(video_url)
            video_data = video_response.json()

            # Handle API error while fetching video details
            if 'error' in video_data:
                error_message = video_data['error']['message']
                return {'error': f"Error fetching video details: {error_message}"}

            for item in video_data['items']:
                duration_str = item['contentDetails']['duration']
                duration = isodate.parse_duration(duration_str)
                video_durations.append(duration)

        # Check if there are more pages
        next_page_token = data.get('nextPageToken')
        if not next_page_token:
            break

    return video_durations

# Function to calculate total duration of videos in a playlist
def get_total_duration(playlist_id):
    try:
        video_durations = fetch_video_durations(playlist_id)

        # Handle invalid playlist error
        if isinstance(video_durations, dict) and 'error' in video_durations:
            return video_durations  # Return the error message

        # Handle empty playlist case
        if video_durations is None:
            return {'error': 'The playlist has no items or contains unaccessible videos.'}

        total_duration = sum(video_durations, timedelta())
        return {'totalDuration': str(total_duration)}  # Return total duration as a string
    except Exception as e:
        return {'error': str(e)}  # Return error if something goes wrong

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_playlist_duration', methods=['POST'])
def get_playlist_duration():
    data = request.get_json()
    playlist_url = data.get('url')
    
    # Extract the playlist ID from the URL
    playlist_id = extract_playlist_id(playlist_url)
    if not playlist_id:
        return jsonify({'error': 'Invalid playlist URL'}), 400  # Return error for invalid URL

    # Get total duration
    total_duration_data = get_total_duration(playlist_id)

    # Check if there's an error
    if isinstance(total_duration_data, dict) and 'error' in total_duration_data:
        return jsonify(total_duration_data), 400  # Return error
    else:
        return jsonify(total_duration_data)  # Return total duration

if __name__ == '__main__':
    app.run(debug=True)
