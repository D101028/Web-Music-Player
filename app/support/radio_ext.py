import os
import random
import time

import av

from app.config import Config

def get_mp3_files(list_id: str):
    """獲取音樂資料夾中所有的 MP3 檔案路徑"""
    music_dir = os.path.join(Config.MUSIC_DATA_PATH, list_id)
    files = [os.path.join(music_dir, f) for f in os.listdir(music_dir) if f.endswith('.mp3')]
    random.shuffle(files) # randomly shuffle the sequence
    return files

def audio_stream_generator(list_id: str):
    """音訊串流產生器，會無限循環播放 MP3 檔案"""
    while True:
        mp3_files = get_mp3_files(list_id)
        if not mp3_files:
            time.sleep(1)
            continue
        
        for file_path in mp3_files:
            print(f"正在電台播放: {file_path}")
            try:
                # 使用 PyAV 開啟音訊檔案
                container = av.open(file_path)
                stream = container.streams.audio[0]
                
                start_time = time.time()
                bytes_sent = 0
                
                # 逐幀讀取音訊並轉回原始 MP3/AAC 數據或直接串流
                # 這裡為了簡單，我們直接精準控制時間來讀取並發送二進位包
                # 更進階的做法是解碼再重編碼，但直接讀取 packet 效能最好
                for packet in container.demux(stream):
                    if packet.size == 0:
                        continue
                        
                    # 獲取當前 packet 的數據
                    data = bytes(packet)
                    yield data
                    
                    # 精準控制播放速度（避免伺服器一次把檔案傳完）
                    # 根據 packet 的 pts (時間戳) 來計算應該延遲的時間
                    if packet.time_base and packet.pts:
                        current_play_time = float(packet.pts * packet.time_base)
                        elapsed_time = time.time() - start_time
                        sleep_time = current_play_time - elapsed_time
                        if sleep_time > 0:
                            time.sleep(sleep_time)
                            
                container.close()
            except Exception as e:
                print(f"播放檔案時發生錯誤 {file_path}: {e}")
                time.sleep(1)


