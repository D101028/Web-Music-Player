import json
import requests

from googleapiclient.discovery import build, HttpError
import yt_dlp

from app.config import Config

class VideoInfo:
    def __init__(self, title: str, vid: str):
        self.title = title
        self.vid = vid

class PlaylistInfo:
    def __init__(self, name: str):
        self.name = name
        self.contents: list[VideoInfo] = []
        
    def dumps(self, filepath: str):
        info = {
            "name": self.name, 
            "contents": [
                {
                    "title": video.title, 
                    "vid": video.vid
                } for video in self.contents
            ]
        }
        with open(filepath, mode = "w") as fp:
            json.dump(info, fp, indent=4)
        

def get_yt_playlist_info(url_or_playlist_id: str, api_key: str = Config.YOUTUBE_API_KEY) -> PlaylistInfo | None:
    youtube = build('youtube', 'v3', developerKey=api_key)

    if '?' in url_or_playlist_id:
        # extract id
        args = url_or_playlist_id[url_or_playlist_id.index('?')+1:].split("&")
        for arg in args:
            if arg.startswith("list="):
                playlist_id = arg[5:]
                break
        else:
            raise ValueError("Invalid URL/VID")
    else:
        playlist_id = url_or_playlist_id

    # Get the name of the playlist
    playlist_request = youtube.playlists().list(
        part='snippet',
        id=playlist_id
    )
    playlist_response = playlist_request.execute()
    
    # Extract playlist name
    playlist_title = playlist_response['items'][0]['snippet']['title']

    info = PlaylistInfo(playlist_title)
    next_page_token = None

    while True:
        request = youtube.playlistItems().list(
            part='snippet',
            playlistId=playlist_id,
            # Retrieve up to 50 items at a time
            pageToken=next_page_token
        )
        response = request.execute()

        for item in response['items']:
            video_title = item['snippet']['title']
            info.contents.append(VideoInfo(video_title, item['snippet']['resourceId']['videoId']))

        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break

    return info

def yt_download_audio(vid: str, filename: str, path: str, ext: str = "mp3"):
    ydl_opts = {
        'format': 'bestaudio/best',  # Only download the best audio
        'outtmpl': f'{path}/{filename}.%(ext)s',  # Save the file to the specified path
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',  # Convert to audio
            'preferredcodec': ext,      # Format
            'preferredquality': '192',    # Bitrate
        }],
    }

    url = f"https://www.youtube.com/watch?v={vid}"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def check_playlist_accessibility(playlist_url):
    response = requests.get(playlist_url)
    if response.status_code == 200:
        if "This playlist is private" in response.text or "The playlist does not exist" in response.text:
            print("Playlist is not accessible.")
            return False
        else:
            print("Playlist is accessible.")
            return True
    else:
        print(f"Failed to fetch the playlist. Status code: {response.status_code}")
        return False

def check_playlist_accessibility_by_api(playlist_id, api_key: str = Config.YOUTUBE_API_KEY) -> bool:
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        response = youtube.playlists().list(
            part='id,snippet',
            id=playlist_id
        ).execute()
        
        if 'items' in response and len(response['items']) > 0:
            playlist = response['items'][0]
            title = playlist['snippet']['title']
            print(f"Playlist is accessible. Title: {title}")
            return True
        else:
            print("Playlist not found or not accessible.")
            return False
    except HttpError as e:
        print(f"An error occurred: {e}")
        return False
