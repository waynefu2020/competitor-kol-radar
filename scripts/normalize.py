"""Turn raw TikHub responses into one classified table: raw/posts.jsonl.

Also writes raw/yt_candidates.json and raw/ig_handles.json for the details stage,
and prints counts plus a random spot-check sample (review it before analysing).
Rows from raw/posts_extra.jsonl (e.g. manually collected domestic data) are merged in.
"""
import argparse
import collections
import datetime
import glob
import json
import os
import random
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_brief, read_jsonl, write_jsonl  # noqa: E402

PAID = re.compile(r'#ad\b|#ads\b|#sponsored|#spon\b|paid partnership|sponsored by|in partnership with|#partner\b|#advertisement|'
                  r'#werbung|#anzeige|#광고|#협찬광고|#publi\b|#adv\b|\bAD\b|\[ad\]|\(ad\)|#gesponsert', re.I)
GIFT = re.compile(r'#pr\b|\bpr\b|gifted|#gift\b|pr package|pr box|pr haul|sent me|sent by|c/o|thank you (so much )?@|thanks (to )?@|'
                  r'#협찬|협찬|提供|ご提供|いただきました|#presente|recebido|regalo de', re.I)
CODE = re.compile(r'code[: ]+[\"“”\']?[a-z0-9]{3,}|use (my )?code|[0-9]+ ?% ?off|discount|coupon|promo ?code|affiliate|쿠폰|クーポン|割引|descuento|cupom|rabatt', re.I)
RETAIL = re.compile(r'yesstyle|stylevana|amazon|amzn|geni\.us|shopee|lazada|sephora|ulta|shein|target|best ?buy|costco|walmart|tiktok ?shop|tiktokmadem|'
                    r'orange cart|yellow (basket|cart)|keranjang|carrito|link in (my )?bio|bio link|sjv\.io', re.I)
SHOP = re.compile(r'tiktok ?shop|tiktokmadem|orange cart|yellow (basket|cart)|keranjang|carrito', re.I)


def classify(text, paid_flag, shop_flag, disclosed):
    if paid_flag or PAID.search(text):
        return 'paid'
    if GIFT.search(text):
        return 'gifted'
    if shop_flag or CODE.search(text) or RETAIL.search(text):
        return 'affiliate'
    if disclosed:
        return 'collab'
    return 'organic'


def channel(text, shop_flag):
    if shop_flag or SHOP.search(text):
        return 'TikTok Shop'
    for name, rx in [('Amazon', r'amazon|amzn|geni\.us'), ('YesStyle/Stylevana', r'yesstyle|stylevana'), ('Shopee/Lazada', r'shopee|lazada'),
                     ('线下/大型零售', r'ulta|sephora|target|best ?buy|costco|walmart|shein'), ('Impact 联盟链接', r'sjv\.io|impact')]:
        if re.search(rx, text, re.I):
            return name
    if CODE.search(text):
        return '官网专属折扣码'
    return ''


def rel_days(s):
    m = re.match(r'(\d+)\s+(second|minute|hour|day|week|month|year)', s or '')
    if not m:
        return None
    return int(m.group(1)) * {'second': 0, 'minute': 0, 'hour': 0, 'day': 1, 'week': 7, 'month': 30, 'year': 365}[m.group(2)]


def num(s):
    m = re.search(r'([\d.,]+)\s*([KMB]?)', str(s or ''))
    if not m:
        return None
    return float(m.group(1).replace(',', '')) * {'K': 1e3, 'M': 1e6, 'B': 1e9, '': 1}[m.group(2)]


def to_int(x):
    try:
        return int(float(x))
    except (TypeError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--brief', required=True)
    ap.add_argument('--sample', type=int, default=20)
    a = ap.parse_args()
    b = load_brief(a.brief)
    R = b['_raw']
    brand, official, noise, sponsor = b['_brand_regex'], b['_official_regex'], b['_noise_regex'], b['_competitor_sponsor_regex']
    since, end = b['_since_ts'], b['_end_ts']
    posts, dropped = {}, collections.Counter()

    def add(p):
        p['ts'] = to_int(p.get('ts')) or 0
        if not p['id']:
            return
        # Fallback sources (yt-dlp search without cookies) carry no date: keep them, flagged, instead of silently dropping.
        if not p.get('ts_unknown') and not (since <= p['ts'] <= end):
            dropped['时间窗外'] += 1
            return
        if not brand.search(p['text']):
            dropped['未提及品牌'] += 1
            return
        if official and official.search(p.get('handle') or ''):
            dropped['官方/仿冒号'] += 1
            return
        if noise and noise.search(p['text']):
            dropped['同名噪音'] += 1
            return
        if sponsor and sponsor.search(p.get('clstext') or p['text']):
            dropped['竞品赞助'] += 1
            return
        key = (p['platform'], p['id'])
        old = posts.get(key)
        if old:
            for k, v in p.items():
                if old.get(k) in (None, '', 0) and v not in (None, ''):
                    old[k] = v
        else:
            posts[key] = p

    for f in glob.glob(os.path.join(R, 'th', 'tt_*.json')):
        for it in ((json.load(open(f)).get('data') or {}).get('search_item_list') or []):
            x = it.get('aweme_info') or {}
            if not x:
                continue
            st, au, ci = x.get('statistics') or {}, x.get('author') or {}, x.get('commerce_info') or {}
            tags = ' '.join('#' + t['hashtag_name'] for t in (x.get('text_extra') or []) if t.get('hashtag_name'))
            bct = ci.get('branded_content_type') or 0
            anchors = '|'.join(str(y.get('type')) for y in (x.get('anchors') or []))
            shop = bct in (7, 13) or bool(re.search(r'(^|\|)35($|\|)', anchors)) or bool(x.get('products_info'))
            add(dict(platform='TikTok', id=str(x.get('aweme_id')), handle=au.get('unique_id'), followers=au.get('follower_count'),
                     views=st.get('play_count'), likes=st.get('digg_count'), comments=st.get('comment_count'), ts=x.get('create_time'),
                     text=(x.get('desc') or '') + ' ' + tags, region=x.get('region'),
                     url=f"https://www.tiktok.com/@{au.get('unique_id')}/video/{x.get('aweme_id')}",
                     paidflag=bool(x.get('is_ads')), shop=shop, disclosed=bct not in (0, 7, 13)))

    for f in glob.glob(os.path.join(R, 'th', 'ig_*.json')):
        for it in (((json.load(open(f)).get('data') or {}).get('data') or {}).get('items') or []):
            add(dict(platform='Instagram', id=str(it.get('code') or it.get('pk')), handle=(it.get('user') or {}).get('username'),
                     followers=None, views=it.get('play_count') or it.get('ig_play_count') or it.get('view_count'),
                     likes=it.get('like_count'), comments=it.get('comment_count'), ts=it.get('taken_at'),
                     text=(it.get('caption') or {}).get('text') or '', url=f"https://www.instagram.com/p/{it.get('code')}/",
                     paidflag=bool(it.get('is_paid_partnership') or it.get('sponsor_tags')), shop=False, disclosed=False,
                     ptype=it.get('product_type')))

    yt = {}
    for f in glob.glob(os.path.join(R, 'th', 'yt_*.json')):
        for v in ((json.load(open(f)).get('data') or {}).get('videos') or []):
            days = rel_days(v.get('published_time'))
            if days is None or days > int(b.get('window_days', 90)) + 3:
                continue
            if not brand.search((v.get('title') or '') + ' ' + (v.get('description') or '')):
                continue
            if official and official.search(v.get('author') or ''):
                continue
            yt[v['video_id']] = dict(id=v['video_id'], title=v.get('title'), author=v.get('author'))

    for f in glob.glob(os.path.join(R, 'ytinfo', '*.json')):
        d = json.load(open(f)).get('data') or {}
        if not d.get('publish_date'):
            continue
        vid = os.path.basename(f)[:-5]
        desc = d.get('description') or ''
        # Creators list codes for many brands in descriptions; classify on brand-relevant lines only.
        rel = '\n'.join(l for l in desc.split('\n') if brand.search(l))
        add(dict(platform='YouTube', id=vid, handle=d.get('channel_handle') or d.get('author'), followers=num(d.get('subscriber_count_text')),
                 views=to_int(d.get('view_count')), likes=to_int(d.get('like_count')), comments=None,
                 ts=int(datetime.datetime.fromisoformat(d['publish_date']).timestamp()),
                 text=(d.get('title') or '') + ' ' + desc, clstext=(d.get('title') or '') + '\n' + rel,
                 url=f'https://youtu.be/{vid}', paidflag=False, shop=False, disclosed=False, title=d.get('title')))

    for p in read_jsonl(os.path.join(R, 'posts_extra.jsonl')):
        add(p)

    for p in posts.values():
        if p['platform'] == 'Instagram' and p.get('handle'):
            try:
                p['followers'] = json.load(open(os.path.join(R, 'igprof', p['handle'] + '.json')))['data']['data']['user']['edge_followed_by']['count']
            except Exception:
                pass
        t = p.get('clstext') or p['text']
        p['cat'] = classify(t, p.get('paidflag'), p.get('shop'), p.get('disclosed'))
        p['channel'] = channel(t, p.get('shop')) if p['cat'] != 'organic' else ''

    rows = list(posts.values())
    write_jsonl(os.path.join(R, 'posts.jsonl'), rows)
    json.dump(list(yt.values()), open(os.path.join(R, 'yt_candidates.json'), 'w'), ensure_ascii=False)
    handles = sorted({p['handle'] for p in rows if p['platform'] == 'Instagram' and p.get('handle')})
    json.dump(handles, open(os.path.join(R, 'ig_handles.json'), 'w'), ensure_ascii=False)

    print(f'时间窗 {b["_window"]}；剔除：{dict(dropped)}')
    for plat in ('TikTok', 'Instagram', 'YouTube', '小红书'):
        P = [p for p in rows if p['platform'] == plat]
        if not P:
            continue
        print(f'{plat}: {len(P)} 条 / {len({p["handle"] for p in P})} 位博主 / 有粉丝数 {sum(1 for p in P if p.get("followers"))} | '
              f'{dict(collections.Counter(p["cat"] for p in P))}')
    print(f'YouTube 待拉详情 {len(yt)} 条，IG 待查主页 {len(handles)} 个')
    fb = collections.Counter(p.get('source', 'tikhub') for p in rows)
    if len(fb) > 1 or 'tikhub' not in fb:
        print(f'数据来源：{dict(fb)}；其中无发布日期 {sum(1 for p in rows if p.get("ts_unknown"))} 条（未按时间窗过滤）')
    if a.sample and rows:
        print('\n—— 抽查样本（确认：在说这个品牌吗？分类对吗？）——')
        random.seed(7)
        for p in random.sample(rows, min(a.sample, len(rows))):
            snippet = re.sub(r'\s+', ' ', p.get('clstext') or p['text'])[:140]
            print(f"[{p['platform']}|{p['cat']}|{p.get('channel') or '-'}] @{p.get('handle')} {snippet}")


if __name__ == '__main__':
    main()
