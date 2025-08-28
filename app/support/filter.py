from functools import wraps
from flask import request, abort

from .user import check_auth

def browser_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_agent = request.headers.get('User-Agent', '').lower()

        # 常見瀏覽器關鍵字白名單
        browser_keywords = ['mozilla', 'chrome', 'safari', 'firefox', 'edge', 'opera']

        # 常見爬蟲或自動工具黑名單
        blocked_keywords = ['bot', 'spider', 'crawl', 'wget', 'curl', 'python', 'scrapy', 'aiohttp']

        # 沒有 UA 直接拒絕
        if not user_agent:
            abort(403)
            # abort(403, 'User-Agent missing')

        # 黑名單關鍵字
        if any(bad in user_agent for bad in blocked_keywords):
            abort(403)
            # abort(403, 'Blocked user agent')

        # 必須有白名單關鍵字之一
        if not any(browser in user_agent for browser in browser_keywords):
            abort(403)
            # abort(403, 'Not a browser')

        return f(*args, **kwargs)
    return decorated_function

def logged_in_only(f):
    @wraps(f)
    def inner(*args, **kwargs):
        if not check_auth():
            abort(403)
        return f(*args, **kwargs)
    return inner

