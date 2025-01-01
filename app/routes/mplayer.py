import json
import os
import random

from flask import Blueprint, render_template, request, redirect, send_from_directory, abort, jsonify
from urllib.parse import unquote

from app.config import Config
from app.support.user import check_auth
from app.support.mplayer_ext import Progress, threading_create_playlist, threading_update_playlist
from app.support.yt import check_playlist_accessibility

mplayer_bp = Blueprint('mplayer', __name__)

@mplayer_bp.route('/mplayer')
def mplayer():
    if not check_auth():
        abort(403)
    
    # load lists data
    lists_json_path = os.path.join(Config.MUSIC_DATA_PATH, "lists.json")
    if not os.path.isfile(lists_json_path):
        lists_info = []
    else:
        with open(lists_json_path, mode="rb") as file:
            lists_info: list[dict] = json.load(file)
    
    return render_template("mplayer.html", lists_info = lists_info)

@mplayer_bp.route('/mplayer_fetch_progress')
def mplayer_fetch_progress():
    if not check_auth():
        abort(403)
    
    xid = request.args.get('xid')
    if xid in (None, ""):
        return jsonify({"percentage": 0})
    
    return jsonify({"percentage": Progress.get_progress(xid)})

@mplayer_bp.route('/mplayer_create')
def create_list():
    if not check_auth():
        abort(403)
    if Config.YOUTUBE_API_KEY == "":
        return """
<h1>Youtube API Key not set</h1>
<meta http-equiv="refresh" content="3;url=/mplayer" />
        """

    yt_playlist_id = request.args.get('yt_playlist_id')
    if yt_playlist_id in (None, ""):
        return redirect('/')
    if not check_playlist_accessibility(f"https://www.youtube.com?list={yt_playlist_id}"):
        return "Playlist not found or private", 404
    
    xid = threading_create_playlist(yt_playlist_id)
    
    return render_template("mplayer_progress.html", 
                           fetch_progress_url = f"/mplayer_fetch_progress?xid={xid}", 
                           redir_href = "/mplayer")

@mplayer_bp.route('/mplayer_update')
def update_list():
    if not check_auth():
        abort(403)
    if Config.YOUTUBE_API_KEY == "":
        return """
<h1>Youtube API Key not set</h1>
<meta http-equiv="refresh" content="3;url=/mplayer" />
        """

    list_id = request.args.get('list_id')
    if list_id in (None, ""):
        return redirect('/')
    if not os.path.isdir(os.path.join(Config.MUSIC_DATA_PATH, list_id)):
        return redirect('/')
    
    to_remove = request.args.get('to_remove')
    if to_remove in (None, ""):
        to_remove = False
    else:
        to_remove = True

    xid = threading_update_playlist(list_id, to_remove)

    return render_template("mplayer_progress.html", 
                           fetch_progress_url = f"/mplayer_fetch_progress?xid={xid}", 
                           redir_href = f"/mplayer/{list_id}")

@mplayer_bp.route('/mplayer/<list_id>')
def playlist_page(list_id):
    if not check_auth():
        abort(403)
    
    # load list info
    with open(os.path.join(Config.MUSIC_DATA_PATH, list_id, "playlist.json"), "rb") as fp:
        list_info = json.load(fp)

    return render_template("mplayer_playlist.html", 
                           list_info = list_info, list_id = list_id, 
                           total = len(list_info["contents"]), enumerate = enumerate)

@mplayer_bp.route('/mplayer/<list_id>/play')
def play_id(list_id):
    if not check_auth():
        abort(403)
    
    # load list info
    with open(os.path.join(Config.MUSIC_DATA_PATH, list_id, "playlist.json"), "rb") as fp:
        list_info = json.load(fp)
    
    length = len(list_info["contents"])
    
    # create random sequence
    seq = [i for i in range(length)]
    random.shuffle(seq)

    folder = os.path.join(Config.MUSIC_DATA_PATH, list_id)
    if not os.path.isdir(folder):
        return "DIR not found: " + folder
    audio_files = [f"{i}.mp3" for i in range(length)]
    titles = [d["title"] for d in list_info["contents"]]
    return render_template("mplayer_player.html", list_id = list_id, list_name = list_info["name"], 
                           audio_files = audio_files, seq = seq, titles = titles)

@mplayer_bp.route('/mplayer/play_single_song')
def play_single_song():
    if not check_auth():
        abort(403)
    
    list_id = request.args.get('list_id')
    if list_id in (None, ""):
        return redirect('/')
    song_id = request.args.get('song_id')
    if song_id in (None, ""):
        return redirect('/')
    
    folder = os.path.join(Config.MUSIC_DATA_PATH, list_id)
    if not os.path.isdir(folder):
        return "DIR not found: " + folder
    audio_file = f"{song_id}.mp3"

    with open(os.path.join(folder, "playlist.json"), "rb") as fp:
        list_info = json.load(fp)

    return render_template("mplayer_player.html", 
                           list_id = list_id, 
                           list_name = "Single Song",
                           audio_files = [audio_file], 
                           seq = [0], 
                           titles = [list_info["contents"][int(song_id)]["title"]])

@mplayer_bp.route('/mplayer_rename_song', methods=['POST'])
def mplayer_rename_song():
    if not check_auth():
        abort(403)
    
    list_id = request.args.get('list_id')
    if list_id in (None, ""):
        return "wrong list_id", 400
    song_id = request.args.get('song_id')
    if song_id in (None, ""):
        return "wrong song_id", 400
    newname = request.args.get('newname')
    if newname in (None, ""):
        return "wrong newname", 400
    
    newname = unquote(newname)

    dir_path = os.path.join(Config.MUSIC_DATA_PATH, list_id)
    if not os.path.isdir(dir_path):
        return f"no list id: {list_id}", 400
    json_playlist_path = os.path.join(dir_path, "playlist.json")
    with open(json_playlist_path, "rb") as fp:
        list_info = json.load(fp)
    
    if int(song_id) >= len(list_info["contents"]):
        return f"no song id: {song_id}", 400
    list_info["contents"][int(song_id)]["title"] = newname

    with open(json_playlist_path, "w") as fp:
        json.dump(list_info, fp)

    return "rename successfully", 200

@mplayer_bp.route('/send_audio_file/<filename>')
def send_audio_file(filename):
    if not check_auth():
        abort(403)
    
    list_id = request.args.get('list_id')
    if list_id in (None, ""):
        return redirect('/')
    
    if not os.path.isfile(os.path.join(Config.MUSIC_DATA_PATH, list_id, filename)):
        return redirect('/')
    
    if Config.MUSIC_DATA_PATH.startswith(('./', '.\\')):
        path = os.path.join(os.getcwd(), Config.MUSIC_DATA_PATH[2:])
    else:
        path = Config.MUSIC_DATA_PATH

    return send_from_directory(os.path.join(path, list_id), filename)