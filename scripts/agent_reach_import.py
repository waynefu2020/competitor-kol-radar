"""Free fallback when there is no TikHub key: pull data with the Agent Reach toolchain
(yt-dlp, xhs-cli) and append it to raw/posts_extra.jsonl, which normalize.py merges.

  youtube  QUERY...          yt-dlp YouTube search (no date/subscribers unless --cookies-from-browser)
  tiktok   --urls FILE       yt-dlp metadata for TikTok video URLs found via web search (no follower counts)
  xhs      QUERY...          xhs-cli Xiaohongshu search (needs `xhs login` once)

Every row records its source so the report can state which numbers are partial.
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ensure_dirs, load_brief, read_jsonl, write_jsonl  # noqa: E402


def run(cmd, timeout=180):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout, r.stderr
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return '', str(e)


def cn_num(s):
    if s is None:
        return None
    m = re.match(r'([\d.]+)\s*(万|w|k|千)?', str(s).strip(), re.I)
    if not m:
        return None
    return int(float(m.group(1)) * {'万': 1e4, 'w': 1e4, 'k': 1e3, '千': 1e3}.get((m.group(2) or '').lower(), 1))


def xhs_time(text, now):
    """Turn Xiaohongshu relative/short dates ('3天前', '昨天 12:00', '10-21', '2025-09-12') into a timestamp."""
    t = (text or '').strip()
    if not t:
        return None
    for pat, unit in [(r'(\d+)\s*分钟前', 'minutes'), (r'(\d+)\s*小时前', 'hours'), (r'(\d+)\s*天前', 'days')]:
        m = re.search(pat, t)
        if m:
            return int((now - datetime.timedelta(**{unit: int(m.group(1))})).timestamp())
    if t.startswith('刚刚') or t.startswith('今天'):
        return int(now.timestamp())
    if t.startswith('昨天'):
        return int((now - datetime.timedelta(days=1)).timestamp())
    m = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', t)
    if m:
        return int(datetime.datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))).timestamp())
    m = re.search(r'(\d{1,2})-(\d{1,2})', t)
    if m:
        d = datetime.datetime(now.year, int(m.group(1)), int(m.group(2)))
        if d > now:
            d = d.replace(year=now.year - 1)
        return int(d.timestamp())
    return None


def youtube(b, queries, pages, browser):
    rows = []
    for q in queries:
        url = 'https://www.youtube.com/results?' + urllib.parse.urlencode({'search_query': q, 'sp': 'CAI='})
        out, err = run(['yt-dlp', '--no-update', '--flat-playlist', '--playlist-end', str(20 * pages), '-J', url])
        if not out:
            print(f'YouTube「{q}」失败：{err.strip()[-200:]}')
            continue
        entries = json.loads(out).get('entries') or []
        print(f'YouTube「{q}」：{len(entries)} 条')
        for e in entries:
            row = dict(platform='YouTube', id=e.get('id'), handle=e.get('channel') or e.get('uploader'), followers=None,
                       views=e.get('view_count'), likes=None, comments=None, ts=None, ts_unknown=True,
                       text=(e.get('title') or '') + ' ' + (e.get('description') or ''), title=e.get('title'),
                       url=f"https://youtu.be/{e.get('id')}", paidflag=False, shop=False, disclosed=False, source='agent-reach:yt-dlp')
            if browser:
                d_out, _ = run(['yt-dlp', '--no-update', '-j', '--skip-download', '--cookies-from-browser', browser, row['url']], timeout=120)
                if d_out:
                    d = json.loads(d_out)
                    desc = d.get('description') or ''
                    row.update(followers=d.get('channel_follower_count'), likes=d.get('like_count'), comments=d.get('comment_count'),
                               ts=d.get('timestamp'), ts_unknown=d.get('timestamp') is None, text=(d.get('title') or '') + ' ' + desc,
                               handle=d.get('channel') or row['handle'])
            rows.append(row)
    return rows


def tiktok(b, url_file):
    urls = [u.strip() for u in open(url_file, encoding='utf-8') if re.search(r'tiktok\.com/@[^/]+/video/\d+', u)]
    rows = []
    for u in dict.fromkeys(urls):
        out, err = run(['yt-dlp', '--no-update', '-j', '--skip-download', u], timeout=90)
        if not out:
            print(f'TikTok 解析失败 {u}：{err.strip()[-120:]}')
            continue
        d = json.loads(out)
        rows.append(dict(platform='TikTok', id=str(d.get('id')), handle=d.get('uploader') or d.get('channel'), followers=d.get('channel_follower_count'),
                         views=d.get('view_count'), likes=d.get('like_count'), comments=d.get('comment_count'), ts=d.get('timestamp'),
                         text=(d.get('description') or '') + ' ' + ' '.join('#' + t for t in (d.get('tags') or [])), url=u,
                         paidflag=False, shop=False, disclosed=False, source='agent-reach:yt-dlp'))
    print(f'TikTok：解析 {len(rows)}/{len(set(urls))} 条')
    return rows


def xhs(b, queries, pages):
    now = datetime.datetime.now()
    rows = []
    for q in queries:
        for sort in ('popular', 'latest'):
            for page in range(1, pages + 1):
                out, err = run(['xhs', 'search', q, '--sort', sort, '--page', str(page), '--json'])
                try:
                    items = (json.loads(out).get('data') or {}).get('items') or []
                except json.JSONDecodeError:
                    print(f'小红书「{q}」{sort} p{page} 失败：{(err or out).strip()[-160:]}（未登录先运行 xhs login）')
                    break
                for it in items:
                    nc = it.get('note_card') or {}
                    if not nc:
                        continue
                    ii, u = nc.get('interact_info') or {}, nc.get('user') or {}
                    pub = next((c.get('text') for c in (nc.get('corner_tag_info') or []) if c.get('type') == 'publish_time'), None)
                    ts = xhs_time(pub, now)
                    rows.append(dict(platform='小红书', id=it.get('id'), handle=u.get('nickname') or u.get('nick_name'), followers=None,
                                     views=None, likes=cn_num(ii.get('liked_count')), saves=cn_num(ii.get('collected_count')),
                                     comments=cn_num(ii.get('comment_count')), ts=ts, ts_unknown=ts is None, text=nc.get('display_title') or '',
                                     title=nc.get('display_title'), note_type=nc.get('type'),
                                     url=f"https://www.xiaohongshu.com/explore/{it.get('id')}?xsec_token={urllib.parse.quote(it.get('xsec_token') or '')}",
                                     paidflag=False, shop=False, disclosed=False, source='agent-reach:xhs-cli'))
                print(f'小红书「{q}」{sort} p{page}：{len(items)} 条')
                if not items:
                    break
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--brief', required=True)
    sub = ap.add_subparsers(dest='cmd', required=True)
    y = sub.add_parser('youtube'); y.add_argument('queries', nargs='+'); y.add_argument('--pages', type=int, default=2)
    y.add_argument('--cookies-from-browser', default='', help='chrome / safari / firefox：补齐发布日期、订阅数（会读取该浏览器的 YouTube 登录 Cookie）')
    t = sub.add_parser('tiktok'); t.add_argument('--urls', required=True, help='每行一个 TikTok 视频链接（来自网页搜索）')
    x = sub.add_parser('xhs'); x.add_argument('queries', nargs='+'); x.add_argument('--pages', type=int, default=2)
    a = ap.parse_args()
    b = load_brief(a.brief)
    ensure_dirs(b)
    if a.cmd == 'youtube':
        new = youtube(b, a.queries, a.pages, a.cookies_from_browser)
    elif a.cmd == 'tiktok':
        new = tiktok(b, a.urls)
    else:
        new = xhs(b, a.queries, a.pages)
    path = os.path.join(b['_raw'], 'posts_extra.jsonl')
    merged = {(r['platform'], r['id']): r for r in read_jsonl(path)}
    for r in new:
        if r.get('id'):
            merged[(r['platform'], r['id'])] = r
    write_jsonl(path, list(merged.values()))
    print(f'已写入 {path}，共 {len(merged)} 条（本次新增/更新 {len(new)} 条）。接着运行 normalize.py。')


if __name__ == '__main__':
    main()
