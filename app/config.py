import argparse
import configparser

# Initialize the parser
parser = argparse.ArgumentParser(description="A script that uses command-line arguments.")

# Add arguments
parser.add_argument("-c", "--config", type=str, help="Path to the configuration file")

# Parse the arguments
args = parser.parse_args()

# Access the argument
if args.config:
    config_path = args.config
else:
    config_path = "config.conf"

# Create a ConfigParser object
config = configparser.ConfigParser()

# Read the configuration file
config.read(config_path)

# Accessing the data
default_section = config["DEFAULT"]

class Config:
    HOST: str
    PROT: str
    USERNAME: str
    PASSWORD: str
    MUSIC_DATA_PATH: str
    FFMPEG_LOCATION: str
    COMPRESSED_DATA_PATH: str

    # Flask configuration
    _HOST = default_section.get("HOST")
    _PORT = default_section.get("PORT")

    # Authentication
    _USERNAME = default_section.get("USERNAME")
    _PASSWORD = default_section.get("PASSWORD")

    # Music data path
    _MUSIC_DATA_PATH = default_section.get("MUSIC_DATA_PATH")
    _COMPRESSED_DATA_PATH = default_section.get("COMPRESSED_DATA_PATH")

    # FFmpeg location
    _FFMPEG_LOCATION = default_section.get("FFMPEG_LOCATION")

    # Set default values
    if not _HOST:
        HOST = "localhost"
    else:
        HOST = _HOST
    if not _PORT:
        PORT = "5000"
    else:
        PORT = _PORT
    if not _USERNAME:
        USERNAME = ""
    else:
        USERNAME = _USERNAME
    if not _PASSWORD:
        PASSWORD = ""
    else:
        PASSWORD = _PASSWORD
    if not _MUSIC_DATA_PATH:
        MUSIC_DATA_PATH = "./data"
    else:
        MUSIC_DATA_PATH = _MUSIC_DATA_PATH
    if not _FFMPEG_LOCATION:
        FFMPEG_LOCATION = "/usr/bin"
    else:
        FFMPEG_LOCATION = _FFMPEG_LOCATION
    if not _COMPRESSED_DATA_PATH:
        COMPRESSED_DATA_PATH = "./.compressed"
    else:
        COMPRESSED_DATA_PATH = _COMPRESSED_DATA_PATH
