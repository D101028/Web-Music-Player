
from flask import Blueprint, Response, abort, request, render_template, jsonify
from urllib.parse import unquote

from app.config import Config
from app.support.data_manage import list_id_exists, is_list_empty
from app.support.filter import browser_only, logged_in_only
from app.support.radio_ext import audio_stream_generator

radio_bp = Blueprint('radio', __name__)

@radio_bp.route('/radio')
@browser_only
@logged_in_only
def radio_index():
    return render_template("radio_index.html")

@radio_bp.route('/radio/play/<list_id>')
def radio_stream(list_id):
    """給遊戲或第三方播放器連接的 HTTP 直播串流"""
    # Check Access Validation
    if Config.RADIO_URL_UUID:
        recieved_uuid = request.args.get("uuid")
        if not recieved_uuid or recieved_uuid != Config.RADIO_URL_UUID:
            abort(403)

    # Check Playlist Existence
    if not list_id_exists(list_id) or is_list_empty(list_id):
        abort(404)

    response = Response(
        audio_stream_generator(list_id),
        mimetype='audio/mpeg'
    )
    
    # 這些標頭能防止遊戲快取音訊，並告訴遊戲「這是一個沒有終點的即時串流」
    response.headers.set('Cache-Control', 'no-cache, no-store, must-revalidate')
    response.headers.set('Pragma', 'no-cache')
    response.headers.set('Expires', '0')
    # response.headers.set('Connection', 'keep-alive')
    
    # 允許所有客戶端/遊戲引擎跨網域讀取
    response.headers.set('Access-Control-Allow-Origin', '*')
    
    # 移除或不設定 Content-Length，觸發 Chunked Transfer Encoding
    response.headers.remove('Content-Length') 
    
    return response

@radio_bp.route('/radio/copy_link/<list_id>', methods=['POST'])
@logged_in_only
def copy_link(list_id):
    # Check Playlist Existence
    if not list_id_exists(list_id) or is_list_empty(list_id):
        abort(404)

    if Config.RADIO_URL_UUID:
        return jsonify({"url-tail": f"/radio/play/{list_id}?uuid={Config.RADIO_URL_UUID}"})
    else:
        return jsonify({"url-tail": f"/radio/play/{list_id}"})
