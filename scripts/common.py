import datetime
import json
import os
import re

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_brief(path):
    b = json.load(open(path, encoding='utf-8'))
    base = os.path.dirname(os.path.abspath(path))
    end = datetime.date.fromisoformat(b['end_date']) if b.get('end_date') else datetime.date.today()
    since = end - datetime.timedelta(days=int(b.get('window_days', 90)))
    b['_base'] = base
    b['_raw'] = os.path.join(base, 'raw')
    b['_since_ts'] = int(datetime.datetime.combine(since, datetime.time()).timestamp())
    b['_end_ts'] = int(datetime.datetime.combine(end, datetime.time(23, 59)).timestamp())
    b['_window'] = f'{since.isoformat()} → {end.isoformat()}'
    for k in ('brand_regex', 'official_regex', 'noise_regex', 'competitor_sponsor_regex'):
        b[f'_{k}'] = re.compile(b[k], re.I) if b.get(k) else None
    return b


def ensure_dirs(b):
    for d in ('th', 'ytinfo', 'igprof', 'sales'):
        os.makedirs(os.path.join(b['_raw'], d), exist_ok=True)


def read_jsonl(path):
    if not os.path.exists(path):
        return []
    return [json.loads(l) for l in open(path, encoding='utf-8') if l.strip()]


def write_jsonl(path, rows):
    with open(path, 'w', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
