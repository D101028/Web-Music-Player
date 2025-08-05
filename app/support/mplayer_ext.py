import json
import os
import random
import shutil
import time
from datetime import datetime
from werkzeug.datastructures import FileStorage
from threading import Thread

from app.config import Config
from app.support.yt import get_yt_playlist_info, yt_download_audio, PlaylistInfo, VideoInfo

class Progress:
    progress = {}

    @classmethod
    def init_progress(cls, total: int | None = None, done: int = 0) -> str:
        xid = ""
        for _ in range(5):
            xid += random.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
        xid += datetime.now().strftime("%Y%m%d%H%M%S")
        cls.progress[xid] = {"total": total, "done": done}
        return xid
    
    @classmethod
    def get_progress(cls, xid: str) -> int:
        progress = cls.progress[xid]
        if progress.get("total") is None:
            return 0
        result = int(progress["done"] / progress["total"] * 100)
        return result

    @classmethod
    def del_progress(cls, xid: str):
        del cls.progress[xid]
        return 

def search_video_from_playlist_json(j: dict, vid: str, to_replace = False) -> int | None:
    for index, content in enumerate(j["contents"]):
        if content is None:
            continue
        if content["vid"] == vid:
            if to_replace:
                j["contents"][index] = None
            return index
    return None

def create_playlist(yt_playlist_id: str, xid: str | None = None):

    total = 1

    # load lists data
    lists_json_path = os.path.join(Config.MUSIC_DATA_PATH, "lists.json")
    if not os.path.isfile(lists_json_path):
        lists_info = []
    else:
        with open(lists_json_path, mode="rb") as file:
            lists_info: list[dict] = json.load(file)
    
    # prepare for new playlist
    pl_dirname = str(len(lists_info))
    pl_dirpath = os.path.join(Config.MUSIC_DATA_PATH, pl_dirname)
    os.mkdir(pl_dirpath)

    # get playlist info
    info = get_yt_playlist_info(yt_playlist_id)
    if info is None:
        raise ValueError("couldn't extract YT playlist id")
    
    total += len(info.contents)
    if xid is not None:
        Progress.progress[xid]["total"] = total
        Progress.progress[xid]["done"] += 1

    # update lists data
    lists_info.append({"list-name": info.name, "pid": yt_playlist_id})
    with open(lists_json_path, mode="w") as fp:
        json.dump(lists_info, fp, indent=4)

    # create/download playlist data
    for i, video_info in enumerate(info.contents):
        basename = str(i)
        yt_download_audio(video_info.vid, basename, pl_dirpath)
        if xid is not None:
            Progress.progress[xid]["done"] += 1
    info.dumps(os.path.join(pl_dirpath, "playlist.json"))

    Progress.progress[xid]["done"] = total

def update_playlist(list_id: str, to_remove = False, xid: str | None = None):
    """
    1. load playlist info
    2. compare the info with old info, if not exist, download
    3. if not to remove, copy the rest info
    """
    list_id = int(list_id)

    total = 1

    # load lists data
    lists_json_path = os.path.join(Config.MUSIC_DATA_PATH, "lists.json")
    if not os.path.isfile(lists_json_path):
        return 1
        # raise ValueError("wrong list_id")
    else:
        with open(lists_json_path, mode="rb") as file:
            lists_info: list[dict] = json.load(file)

    if len(lists_info) <= list_id:
        return 1
        # raise IndexError(f"list_id out of range: {list_id}")

    if lists_info[list_id]["pid"] is None: # created by upload
        if xid is not None:
            Progress.progress[xid]["total"] = 1
            Progress.progress[xid]["done"] = 1
        return 0

    # get playlist info
    info = get_yt_playlist_info(lists_info[list_id]["pid"])
    if info is None:
        return 1
        # raise ValueError("incorrect yt_url")
    
    total += len(info.contents)
    
    # load old playlist info
    playlist_json_path = os.path.join(Config.MUSIC_DATA_PATH, str(list_id), "playlist.json")
    with open(playlist_json_path, "rb") as file:
        old_info: dict = json.load(file)
    
    total += len(old_info["contents"])
    total += 1 # for last
    # set progress data
    if xid is not None:
        Progress.progress[xid]["total"] = total
        Progress.progress[xid]["done"] += 1

    # update
    new_info: PlaylistInfo = PlaylistInfo(info.name)
    target_path = os.path.join(Config.MUSIC_DATA_PATH, str(list_id))
    renamed_path = os.path.join(Config.MUSIC_DATA_PATH, str(list_id)+"_temp")
    os.rename(target_path, renamed_path)
    os.mkdir(target_path)
    new_index = 0
    for video_info in info.contents:
        old_index = search_video_from_playlist_json(old_info, video_info.vid)
        if old_index is None:
            to_continue = False
            try:
                yt_download_audio(video_info.vid, str(new_index), target_path)
            except:
                to_continue = True
            # update progress
            if xid is not None:
                Progress.progress[xid]["done"] += 1
            if to_continue:
                continue
        else:
            os.rename(os.path.join(renamed_path, f"{old_index}.mp3"), 
                      os.path.join(target_path, f"{new_index}.mp3"))
            old_info["contents"][old_index] = None
            # update progress
            if xid is not None:
                Progress.progress[xid]["done"] += 2
        new_info.contents.append(video_info)
        new_index += 1

    if not to_remove:
        for old_index, v_info in enumerate(old_info["contents"]):
            if v_info is None:
                continue
            video_info = VideoInfo(title = v_info["title"], vid = v_info["vid"])
            os.rename(os.path.join(renamed_path, f"{old_index}.mp3"), 
                      os.path.join(target_path, f"{new_index}.mp3"))
            new_info.contents.append(video_info)
            new_index += 1
            # update progress
            if xid is not None:
                Progress.progress[xid]["done"] += 1
    else:
        # update progress
        if xid is not None:
            Progress.progress[xid]["done"] = Progress.progress[xid]["total"] - 1

    # save changes to json
    if new_info.name != lists_info[list_id]["list-name"]:
        lists_info[list_id]["list-name"] = new_info.name
        with open(lists_json_path, "w") as file:
            json.dump(lists_info, file, indent=4)
    new_info.dumps(playlist_json_path)

    shutil.rmtree(renamed_path)

    # update progress
    if xid is not None:
        Progress.progress[xid]["done"] = Progress.progress[xid]["total"]
    return 0

def remove_playlist(list_id: int):
    # load lists data
    lists_json_path = os.path.join(Config.MUSIC_DATA_PATH, "lists.json")
    if not os.path.isfile(lists_json_path):
        return 1
        # raise ValueError("wrong list_id")
    else:
        with open(lists_json_path, mode="rb") as file:
            lists_info: list[dict] = json.load(file)

    # remove playlist
    playlist_path = os.path.join(Config.MUSIC_DATA_PATH, str(list_id))
    shutil.rmtree(playlist_path)

    # resort playlists
    for i in range(list_id+1, len(lists_info)):
        os.rename(os.path.join(Config.MUSIC_DATA_PATH, str(i)), 
                  os.path.join(Config.MUSIC_DATA_PATH, str(i-1)))
    lists_info.pop(list_id)
    with open(lists_json_path, "w") as fp:
        json.dump(lists_info, fp, indent=4)

    return 0

def create_playlist_by_upload(files: list[FileStorage], playlist_name: str, xid: str | None = None):
    lists_json_path = os.path.join(Config.MUSIC_DATA_PATH, "lists.json")
    with open(lists_json_path, "r") as fp:
        lists_json = json.load(fp)
    
    upload_folder = os.path.join(Config.MUSIC_DATA_PATH, str(len(lists_json)))
    if not os.path.isdir(upload_folder):
        os.mkdir(upload_folder)

    playlist_info = {
        "name": playlist_name, 
        "contents": []
    }

    if xid is not None:
        Progress.progress[xid]["total"] = len(files) + 2
        Progress.progress[xid]["done"] = 1

    skipped = 0
    for index, file in enumerate(files):
        if file.filename == '':
            skipped += 1
            if xid is not None:
                Progress.progress[xid]["done"] += 1
            continue  # 跳過沒有檔名的檔案
        save_path = os.path.join(upload_folder, f"{index-skipped}.mp3")
        file.save(save_path)

        playlist_info["contents"].append({
            "title": ".".join(file.filename.split(".")[:-1]), 
            "vid": None
        })
        if xid is not None:
            Progress.progress[xid]["done"] += 1
    
    with open(lists_json_path, "w") as fp:
        lists_json.append({
            "list-name": playlist_name, 
            "pid": None
        })
        json.dump(lists_json, fp, indent=4)
    
    with open(os.path.join(upload_folder, "playlist.json"), mode="w") as fp:
        json.dump(playlist_info, fp, indent=4)
    
    if xid is not None:
        Progress.progress[xid]["done"] = Progress.progress[xid]["total"]

    return 0

def threading_create_playlist(yt_playlist_id: str):
    xid = Progress.init_progress()
    t = Thread(target=create_playlist, args=(yt_playlist_id, xid))
    t.start()
    def del_pro():
        t.join()
        time.sleep(60)
        Progress.del_progress(xid)
    t2 = Thread(target=del_pro)
    t2.start()
    return xid

def threading_update_playlist(list_id: str, to_remove: bool):
    xid = Progress.init_progress()
    t = Thread(target=update_playlist, args=(list_id, to_remove, xid))
    t.start()
    def del_pro():
        t.join()
        time.sleep(60)
        Progress.del_progress(xid)
    t2 = Thread(target=del_pro)
    t2.start()
    return xid

def threading_create_playlist_by_upload(files: list[FileStorage], playlist_name: str):
    xid = Progress.init_progress()
    t = Thread(target=create_playlist_by_upload, args=(files, playlist_name, xid))
    t.start()
    def del_pro():
        t.join()
        time.sleep(60)
        Progress.del_progress(xid)
    t2 = Thread(target=del_pro)
    t2.start()
    return xid

