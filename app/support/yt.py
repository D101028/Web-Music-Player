import json
import os
import requests
import shutil
from subprocess import Popen

from yt_dlp import YoutubeDL

from app.config import Config

class VideoInfo:
    def __init__(self, title: str, vid: str):
        self.title = title
        self.vid = vid
    
    def __str__(self):
        return f"<VideoInfo {self.vid} {self.title}>"

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

# def yt_download_audio(vid: str, filename: str, path: str, ext: str = "mp3"):
#     ydl_opts = {
#         'format': 'bestaudio/best',  # Only download the best audio
#         'outtmpl': f'{path}/{filename}.%(ext)s',  # Save the file to the specified path
#         'postprocessors': [{
#             'key': 'FFmpegExtractAudio',  # Convert to audio
#             'preferredcodec': ext,      # Format
#             'preferredquality': '192',    # Bitrate
#         }],
#     }

#     url = f"https://www.youtube.com/watch?v={vid}"

#     with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#         ydl.download([url])

def yt_download_audio(vid: str, basename: str, dest: str, ext: str = "mp3"):
    # Create temp directory
    temp_dir = os.path.join(dest, ".temp")
    if os.path.isfile(temp_dir):
        os.remove(temp_dir)
    elif os.path.isdir(temp_dir):
        shutil.rmtree(temp_dir)
    os.mkdir(temp_dir)

    # Fetch audio file
    url = f"https://www.youtube.com/watch?v={vid}"
    cmd = ["yt-dlp", 
           "-f", "bestaudio", 
           "--ffmpeg-location", f'"{Config.FFMPEG_LOCATION}"', 
           "--extract-audio", 
           "-o", "temp", 
           f'{url}']
    process = Popen(cmd, cwd=temp_dir)
    status = process.wait()
    if status:
        raise Exception("yt-dlp download error")
    
    # Get filename
    file = None
    for root, dirs, files in os.walk(temp_dir):
        for f in files:
            file = f
    if file is None:
        raise Exception("yt-dlp downloaded file not found")

    # Convert to target form
    input_path = os.path.abspath(os.path.join(temp_dir, file))
    output_path = os.path.abspath(os.path.join(dest, f"{basename}.{ext}"))
    cmd = ["/bin/ffmpeg", "-i", f'"{input_path}"', "-y", f'"{output_path}"']
    process = Popen(cmd, cwd=dest)
    status = process.wait()
    if status:
        raise Exception("ffmpeg convert error")

    # Remove temp dir
    shutil.rmtree(temp_dir)

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
