"""Collect competitor content from TikHub.

  --stage search   TikTok keyword search, Instagram hashtag posts, YouTube search
  --stage details  YouTube video details + Instagram creator follower counts
                   (needs normalize.py to have run once, to know which items to fetch)
  --dry-run        print planned calls, estimated cost and current balance; fetch nothing
"""
import argparse
import concurrent.futures as cf
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ensure_dirs, load_brief  # noqa: E402
import tikhub  # noqa: E402


def save(path, data):
    json.dump(data, open(path, 'w', encoding='utf-8'), ensure_ascii=False)


def tiktok_job(b, i, kw, sort):
    n = 0
    for p in range(int(b.get('tiktok_pages', 6))):
        d = tikhub.get('/api/v1/tiktok/app/v3/fetch_video_search_result', dict(keyword=kw, count=20, offset=p * 20, sort_type=sort))
        save(os.path.join(b['_raw'], 'th', f'tt_{i}_s{sort}_p{p}.json'), d)
        dd = d.get('data') or {}
        items = dd.get('search_item_list') or []
        n += len(items)
        if not items or not dd.get('has_more'):
            break
    return f'TikTok「{kw}」sort{sort}: {n}'


def instagram_job(b, i, tag, feed):
    n, tok = 0, None
    for p in range(int(b.get('instagram_pages', 5))):
        params = dict(keyword=tag, feed_type=feed)
        if tok:
            params['pagination_token'] = tok
        d = tikhub.get('/api/v1/instagram/v2/fetch_hashtag_posts', params)
        save(os.path.join(b['_raw'], 'th', f'ig_{i}_{feed}_p{p}.json'), d)
        dd = d.get('data') or {}
        items = (dd.get('data') or {}).get('items') or []
        n += len(items)
        tok = dd.get('pagination_token')
        if not items or not tok:
            break
    return f'Instagram #{tag} {feed}: {n}'


def youtube_job(b, i, q):
    n, tok = 0, None
    order = 'this_month' if int(b.get('window_days', 90)) <= 31 else 'this_year'
    for p in range(int(b.get('youtube_pages', 3))):
        params = dict(search_query=q, order_by=order)
        if tok:
            params['continuation_token'] = tok
        d = tikhub.get('/api/v1/youtube/web/search_video', params)
        save(os.path.join(b['_raw'], 'th', f'yt_{i}_p{p}.json'), d)
        dd = d.get('data') or {}
        vids = dd.get('videos') or []
        n += len(vids)
        tok = dd.get('continuation_token')
        if not vids or not tok:
            break
    return f'YouTube「{q}」: {n}'


def yt_detail(b, vid):
    p = os.path.join(b['_raw'], 'ytinfo', f'{vid}.json')
    if os.path.exists(p) and os.path.getsize(p) > 200:
        return
    save(p, tikhub.get('/api/v1/youtube/web_v2/get_video_info', dict(video_id=vid, language_code='en')))


def ig_profile(b, h):
    p = os.path.join(b['_raw'], 'igprof', f'{h}.json')
    if os.path.exists(p) and os.path.getsize(p) > 200:
        return
    save(p, tikhub.get('/api/v1/instagram/v1/fetch_user_info_by_username', dict(username=h)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--brief', required=True)
    ap.add_argument('--stage', choices=['search', 'details'], required=True)
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--workers', type=int, default=10)
    a = ap.parse_args()
    b = load_brief(a.brief)
    ensure_dirs(b)

    if a.stage == 'search':
        tt, ig, yt = b.get('tiktok_keywords', []), b.get('instagram_hashtags', []), b.get('youtube_queries', [])
        planned = len(tt) * 2 * int(b.get('tiktok_pages', 6)) + len(ig) * 2 * int(b.get('instagram_pages', 5)) + len(yt) * int(b.get('youtube_pages', 3))
    else:
        cand = os.path.join(b['_raw'], 'yt_candidates.json')
        hand = os.path.join(b['_raw'], 'ig_handles.json')
        if not (os.path.exists(cand) and os.path.exists(hand)):
            sys.exit('先运行 normalize.py，生成 yt_candidates.json 和 ig_handles.json。')
        vids = [v['id'] for v in json.load(open(cand))]
        handles = json.load(open(hand))
        todo_v = [v for v in vids if not os.path.exists(os.path.join(b['_raw'], 'ytinfo', f'{v}.json'))]
        todo_h = [h for h in handles if not os.path.exists(os.path.join(b['_raw'], 'igprof', f'{h}.json'))]
        planned = len(todo_v) + len(todo_h)

    bal, err = tikhub.balance()
    est = planned * tikhub.PRICE_PER_CALL
    print(f'计划调用：最多 {planned} 次（翻页提前结束会更少），预估 ≤ ${est:.2f}；当前余额：{bal if bal is not None else "未知 " + str(err)}')
    if a.dry_run:
        return
    if bal is not None and bal < est:
        sys.exit('余额不足，先充值或减少关键词/页数。')

    with cf.ThreadPoolExecutor(max_workers=a.workers) as ex:
        if a.stage == 'search':
            jobs = [ex.submit(tiktok_job, b, i, kw, s) for i, kw in enumerate(tt) for s in (0, 1)]
            jobs += [ex.submit(instagram_job, b, i, t, f) for i, t in enumerate(ig) for f in ('top', 'recent')]
            jobs += [ex.submit(youtube_job, b, i, q) for i, q in enumerate(yt)]
            for j in cf.as_completed(jobs):
                print(j.result(), flush=True)
        else:
            list(ex.map(lambda v: yt_detail(b, v), todo_v))
            list(ex.map(lambda h: ig_profile(b, h), todo_h))
            print(f'YouTube 详情 {len(todo_v)} 条，IG 主页 {len(todo_h)} 个')
    bal2, _ = tikhub.balance()
    if bal is not None and bal2 is not None:
        print(f'本阶段花费 ${bal - bal2:.3f}，余额 ${bal2:.2f}')


if __name__ == '__main__':
    main()
