
from flask import session

from app.config import Config

def check_auth(username: str = Config.USERNAME) -> bool:
    if username == "": # no auth required
        return True
    return username == session.get("username")
