import json
import requests

import yt_dlp
from googleapiclient.discovery import build, HttpError
from yt_dlp import YoutubeDL

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

def get_yt_playlist_info(url_or_playlist_id: str) -> PlaylistInfo | None:
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

    url = f"https://www.youtube.com/playlist?list={playlist_id}"

    ydl_opts = {
        'extract_flat': True,  # 僅擷取清單資訊而不下載影片
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    
    if info is None:
        return None

    contents = []
    for i, video in enumerate(info['entries'], start=1):
        contents.append(VideoInfo(video['title'], video['id']))

    playlist_info = PlaylistInfo(info['title'])
    playlist_info.contents = contents

    return playlist_info

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
