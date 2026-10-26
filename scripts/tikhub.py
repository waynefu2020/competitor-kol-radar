import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = 'https://api.tikhub.io'
PRICE_PER_CALL = 0.0011  # observed average across TikTok/IG/YouTube endpoints


def api_key():
    k = os.environ.get('TIKHUB_API_KEY', '').strip()
    if not k:
        p = os.path.expanduser('~/.config/tikhub/key')
        if os.path.exists(p):
            k = open(p).read().strip()
    if not k:
        raise SystemExit('缺少 TikHub API Key：设置环境变量 TIKHUB_API_KEY，或写入 ~/.config/tikhub/key（权限 600）。'
                         '没有 Key 时改走免费兜底方案，见 references/fallback-agent-reach.md。')
    return k


def get(path, params=None, retries=3):
    url = BASE + path + ('?' + urllib.parse.urlencode(params) if params else '')
    # TikHub's edge rejects Python's default User-Agent with 403.
    req = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + api_key(), 'User-Agent': 'curl/8.7.1',
                                               'Accept': 'application/json'})
    err = ''
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            err = f'HTTP {e.code}'
            if e.code in (401, 402, 403):
                break
        except Exception as e:  # network hiccups, timeouts
            err = str(e)
        time.sleep(2 + attempt * 3)
    return {'error': err}


def balance():
    d = get('/api/v1/tikhub/user/get_user_info')
    u = d.get('user_data') or d.get('data') or {}
    return u.get('balance'), d.get('error')
