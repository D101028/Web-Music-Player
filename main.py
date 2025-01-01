import os

from app import create_app
from app.config import Config

app = create_app()

def init_data():
    if not os.path.isdir(Config.MUSIC_DATA_PATH):
        os.mkdir(Config.MUSIC_DATA_PATH)
    if not os.path.isfile(os.path.join(Config.MUSIC_DATA_PATH, "lists.json")):
        with open(os.path.join(Config.MUSIC_DATA_PATH, "lists.json"), mode="w") as file:
            file.write("[]")
    if not os.path.isdir(Config.MUSIC_DATA_PATH):
        os.mkdir(Config.MUSIC_DATA_PATH)

if __name__ == '__main__':
    init_data()
    app.run(host=Config.HOST, port=Config.PORT, debug=True)
