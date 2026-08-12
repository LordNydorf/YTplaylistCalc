import json
import os
import re
import isodate
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def extract_playlist_id(url_or_id):
    if not url_or_id:
        return None
    url_or_id = url_or_id.strip()
    match = re.search(r"[?&]list=([a-zA-Z0-9_-]+)", url_or_id)
    if match:
        return match.group(1)
    if re.match(r"^[a-zA-Z0-9_-]{10,}$", url_or_id):
        return url_or_id
    return None

def format_duration(seconds):
    seconds = max(0, int(seconds))
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    mins, secs = divmod(rem, 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0 or days > 0:
        parts.append(f"{hours}h")
    if mins > 0 or hours > 0 or days > 0:
        parts.append(f"{mins}m")
    parts.append(f"{secs}s")
    
    verbose_parts = []
    if days > 0:
        verbose_parts.append(f"{days} {'day' if days == 1 else 'days'}")
    if hours > 0:
        verbose_parts.append(f"{hours} {'hour' if hours == 1 else 'hours'}")
    if mins > 0:
        verbose_parts.append(f"{mins} {'minute' if mins == 1 else 'minutes'}")
    if secs > 0 or not verbose_parts:
        verbose_parts.append(f"{secs} {'second' if secs == 1 else 'seconds'}")
        
    return {
        "text": " ".join(parts),
        "verbose": ", ".join(verbose_parts),
        "days": days,
        "hours": hours,
        "minutes": mins,
        "seconds": secs,
        "totalSeconds": seconds
    }

def format_time_saved(original_seconds, speed_seconds):
    saved = max(0, int(original_seconds - speed_seconds))
    if saved == 0:
        return "0m"
    hours, rem = divmod(saved, 3600)
    mins, _ = divmod(rem, 60)
    if hours > 0:
        return f"{hours}h {mins}m saved"
    return f"{mins}m saved"

def fetch_playlist_data(playlist_id):
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key:
        return {'error': 'YouTube API key is missing. Please configure YOUTUBE_API_KEY in your Netlify environment variables.'}

    # 1. Metadata
    playlist_meta_url = f'https://www.googleapis.com/youtube/v3/playlists?part=snippet,contentDetails&id={playlist_id}&key={api_key}'
    try:
        p_res = requests.get(playlist_meta_url, timeout=10)
        p_data = p_res.json()
    except Exception as e:
        return {'error': f'Network error contacting YouTube API: {str(e)}'}

    if 'error' in p_data:
        return {'error': p_data['error'].get('message', 'Invalid playlist ID or API error.')}

    if not p_data.get('items'):
        return {'error': 'Playlist not found. Make sure the playlist is public or unlisted.'}

    playlist_item = p_data['items'][0]
    p_snippet = playlist_item.get('snippet', {})
    p_thumbnails = p_snippet.get('thumbnails', {})
    thumb_url = (
        p_thumbnails.get('maxres', {}).get('url') or
        p_thumbnails.get('high', {}).get('url') or
        p_thumbnails.get('medium', {}).get('url') or
        p_thumbnails.get('default', {}).get('url') or
        ''
    )

    playlist_info = {
        'id': playlist_id,
        'title': p_snippet.get('title', 'YouTube Playlist'),
        'channelTitle': p_snippet.get('channelTitle', 'Unknown Creator'),
        'channelId': p_snippet.get('channelId', ''),
        'description': p_snippet.get('description', ''),
        'publishedAt': p_snippet.get('publishedAt', ''),
        'thumbnail': thumb_url,
        'itemCount': playlist_item.get('contentDetails', {}).get('itemCount', 0)
    }

    # 2. Items
    items_base_url = f'https://www.googleapis.com/youtube/v3/playlistItems?part=snippet,contentDetails&playlistId={playlist_id}&maxResults=50&key={api_key}'
    video_entries = []
    next_page_token = None
    max_pages = 10

    page = 0
    while page < max_pages:
        page += 1
        url = items_base_url
        if next_page_token:
            url += f'&pageToken={next_page_token}'

        try:
            r = requests.get(url, timeout=10)
            data = r.json()
        except Exception as e:
            return {'error': f'Error fetching playlist items: {str(e)}'}

        if 'error' in data:
            return {'error': data['error'].get('message', 'Error fetching playlist items.')}

        items = data.get('items', [])
        if not items and page == 1:
            return {'error': 'This playlist is empty or contains no accessible videos.'}

        for item in items:
            c_details = item.get('contentDetails', {})
            video_id = c_details.get('videoId')
            snippet = item.get('snippet', {})
            title = snippet.get('title', 'Unavailable video')
            
            if title in ['Private video', 'Deleted video'] or not video_id:
                continue

            v_thumbs = snippet.get('thumbnails', {})
            v_thumb = (
                v_thumbs.get('medium', {}).get('url') or
                v_thumbs.get('default', {}).get('url') or
                ''
            )

            video_entries.append({
                'id': video_id,
                'title': title,
                'thumbnail': v_thumb,
                'channelTitle': snippet.get('videoOwnerChannelTitle', p_snippet.get('channelTitle', '')),
                'position': len(video_entries) + 1
            })

        next_page_token = data.get('nextPageToken')
        if not next_page_token:
            break

    if not video_entries:
        return {'error': 'No accessible videos found in this playlist.'}

    # 3. Video Durations
    video_map = {}
    for i in range(0, len(video_entries), 50):
        chunk = video_entries[i:i+50]
        chunk_ids = [v['id'] for v in chunk]
        v_url = f'https://www.googleapis.com/youtube/v3/videos?part=contentDetails,snippet&id={",".join(chunk_ids)}&key={api_key}'
        try:
            v_res = requests.get(v_url, timeout=10)
            v_data = v_res.json()
        except Exception as e:
            return {'error': f'Error fetching video details: {str(e)}'}

        for v_item in v_data.get('items', []):
            vid = v_item.get('id')
            dur_iso = v_item.get('contentDetails', {}).get('duration', 'PT0S')
            try:
                dur_secs = int(isodate.parse_duration(dur_iso).total_seconds())
            except Exception:
                dur_secs = 0
            
            video_map[vid] = {
                'durationSeconds': dur_secs,
                'durationFormatted': format_duration(dur_secs)['text']
            }

    valid_videos = []
    total_seconds = 0
    shortest_video = None
    longest_video = None

    for v in video_entries:
        details = video_map.get(v['id'])
        if not details:
            continue
        v['durationSeconds'] = details['durationSeconds']
        v['duration'] = details['durationFormatted']
        valid_videos.append(v)
        total_seconds += v['durationSeconds']

        if v['durationSeconds'] > 0:
            if shortest_video is None or v['durationSeconds'] < shortest_video['durationSeconds']:
                shortest_video = v
            if longest_video is None or v['durationSeconds'] > longest_video['durationSeconds']:
                longest_video = v

    if not valid_videos:
        return {'error': 'Could not extract valid duration data for videos in this playlist.'}

    playlist_info['videoCount'] = len(valid_videos)
    if not playlist_info['thumbnail'] and valid_videos:
        playlist_info['thumbnail'] = valid_videos[0]['thumbnail']

    speed_factors = [1.0, 1.25, 1.5, 1.75, 2.0]
    speeds = {}
    for sf in speed_factors:
        adj_secs = int(total_seconds / sf)
        speeds[str(sf)] = {
            'speed': sf,
            'seconds': adj_secs,
            'formatted': format_duration(adj_secs),
            'timeSaved': format_time_saved(total_seconds, adj_secs)
        }

    avg_secs = int(total_seconds / len(valid_videos)) if valid_videos else 0

    return {
        'playlist': playlist_info,
        'totalSeconds': total_seconds,
        'formatted': format_duration(total_seconds),
        'speeds': speeds,
        'stats': {
            'avgSeconds': avg_secs,
            'avgFormatted': format_duration(avg_secs)['text'],
            'shortest': {
                'title': shortest_video['title'] if shortest_video else 'N/A',
                'duration': shortest_video['duration'] if shortest_video else '0s',
                'seconds': shortest_video['durationSeconds'] if shortest_video else 0
            } if shortest_video else None,
            'longest': {
                'title': longest_video['title'] if longest_video else 'N/A',
                'duration': longest_video['duration'] if longest_video else '0s',
                'seconds': longest_video['durationSeconds'] if longest_video else 0
            } if longest_video else None,
        },
        'videos': valid_videos
    }

def handler(event, context):
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "POST, OPTIONS, GET"
    }

    http_method = event.get('httpMethod', 'GET').upper()

    if http_method == 'OPTIONS':
        return {"statusCode": 204, "headers": headers, "body": ""}

    if http_method != 'POST':
        return {"statusCode": 405, "headers": headers, "body": json.dumps({"error": "Method Not Allowed. Use POST."})}

    try:
        body = event.get('body', '{}')
        if isinstance(body, str):
            data = json.loads(body) if body else {}
        else:
            data = body or {}
    except Exception:
        data = {}

    playlist_url = data.get('url', '').strip()
    if not playlist_url:
        return {"statusCode": 400, "headers": headers, "body": json.dumps({"error": "Please enter a YouTube playlist URL or ID."})}

    playlist_id = extract_playlist_id(playlist_url)
    if not playlist_id:
        return {"statusCode": 400, "headers": headers, "body": json.dumps({"error": "Invalid YouTube playlist URL or ID."})}

    result = fetch_playlist_data(playlist_id)
    if 'error' in result:
        return {"statusCode": 400, "headers": headers, "body": json.dumps(result)}

    result['totalDuration'] = result['formatted']['verbose']
    return {
        "statusCode": 200,
        "headers": headers,
        "body": json.dumps(result)
    }
