import logging
import os

from waitress import serve

from app import create_app
from app.config import Config

app = create_app()

# Set maximum upload size
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1024 MB

def init_data():
    if not os.path.isdir(Config.MUSIC_DATA_PATH):
        os.mkdir(Config.MUSIC_DATA_PATH)
    if not os.path.isfile(os.path.join(Config.MUSIC_DATA_PATH, "lists.json")):
        with open(os.path.join(Config.MUSIC_DATA_PATH, "lists.json"), mode="w") as file:
            file.write("[]")
    if not os.path.isdir(Config.MUSIC_DATA_PATH):
        os.mkdir(Config.MUSIC_DATA_PATH)
    if not os.path.isdir(Config.COMPRESSED_DATA_PATH):
        os.mkdir(Config.COMPRESSED_DATA_PATH)

if __name__ == '__main__':
    init_data()
    logging.basicConfig(level=logging.INFO)
    logging.info(f">> Starting Server on {Config.HOST}:{Config.PORT} <<")
    serve(app, host=Config.HOST, port=Config.PORT)
