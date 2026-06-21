import os

from app.config import Config

def get_list_path(list_id: str, check: bool = False):
    path = os.path.join(Config.MUSIC_DATA_PATH, list_id)
    if check:
        if not os.path.isdir(path):
            raise Exception(f"Playlist {list_id} Does Not Exist")
    return path

def list_id_exists(list_id: str):
    return os.path.isdir(get_list_path(list_id))

def is_list_empty(list_id: str):
    for _, files, dirs in os.walk(get_list_path(list_id, True)):
        for file in files:
            if file.endswith(".mp3"):
                return True
        return False
