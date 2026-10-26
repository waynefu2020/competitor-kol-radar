"""Compute KPIs, archetype and benchmark position from raw/posts.jsonl.

Writes <base>/analysis.json and <base>/<brand>_内容清单.csv.
--save-benchmark appends/updates this brand in references/benchmarks.json.
"""
import argparse
import collections
import csv
import datetime
import json
import os
import re
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import SKILL_DIR, load_brief, read_jsonl  # noqa: E402
from lexicons import POINTS, THEMES  # noqa: E402

PLATS = ['TikTok', 'Instagram', 'YouTube']
CATS = ['organic', 'gifted', 'affiliate', 'paid', 'collab']
CN = {'organic': '自然内容', 'gifted': '寄样(PR)', 'affiliate': '联盟带货', 'paid': '付费合作', 'collab': '品牌合作(未注明)'}
TIERS = ['纳米 <1万', '小 1-10万', '中 10-50万', '大 50-100万', '头部 100万+', '未知']


def tier(f):
    if not f:
        return '未知'
    for lim, name in [(1e4, TIERS[0]), (1e5, TIERS[1]), (5e5, TIERS[2]), (1e6, TIERS[3])]:
        if f < lim:
            return name
    return TIERS[4]


def lang(t):
    for code, rx in [('ko', r'[가-힯]'), ('ja', r'[぀-ヿ]'), ('th', r'[฀-๿]'), ('ru', r'[Ѐ-ӿ]'),
                     ('hi', r'[ऀ-ॿ]'), ('zh', r'[一-鿿]'), ('vi', r'[ăđơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ]')]:
        if re.search(rx, t, re.I):
            return code
    low = t.lower()
    for code, rx in [('es', r'\b(el|los|las|que|para|con|más|reuniones|maquillaje)\b'), ('pt', r'\b(você|não|ainda|maquiagem)\b'),
                     ('fr', r'\b(je|les|avec|une|très|maquillage)\b'), ('de', r'\b(und|ich|nicht|mit|das)\b'), ('it', r'\b(della|che|questa|trucco)\b'),
                     ('id/ms', r'\b(yang|bisa|banget|sangat|tak)\b')]:
        if re.search(rx, low):
            return code
    return 'en'


def med(xs):
    xs = [x for x in xs if isinstance(x, (int, float))]
    return [statistics.median(xs) if xs else None, len(xs)]


def counts(texts, dic):
    c = collections.Counter()
    for t in texts:
        for k, rx in dic.items():
            if re.search(rx, t, re.I):
                c[k] += 1
    return dict(c)


def brand_led(p):
    return p['cat'] in ('paid', 'collab', 'gifted') or (p['cat'] == 'affiliate' and p.get('channel') == '官网专属折扣码')


def archetype(k):
    r, org, comm_aff = k.get('brandled_vs_organic_views'), k['organic_share'], k.get('affiliate_of_commercial')
    if r is not None and r >= 5:
        return '买量型', f'TikTok 品牌主导内容的播放中位数是自然内容的 {r:.0f} 倍，声量主要靠投放买来。'
    if org >= 0.6 and (r is None or r <= 1):
        return '自来水型', f'{org:.0%} 的内容是用户自发内容，且自然内容播放不低于品牌主导内容，声量主要靠用户自传播。'
    if comm_aff is not None and comm_aff >= 0.5:
        return '联盟铺量型', f'商业内容里 {comm_aff:.0%} 是联盟带货，靠分佣让大量中小博主铺量。'
    return '混合型', '付费、寄样、联盟和自然内容都有一定比重，没有单一驱动力。'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--brief', required=True)
    ap.add_argument('--save-benchmark', action='store_true')
    a = ap.parse_args()
    b = load_brief(a.brief)
    posts = read_jsonl(os.path.join(b['_raw'], 'posts.jsonl'))
    if not posts:
        sys.exit('raw/posts.jsonl 为空：先运行 collect.py 和 normalize.py。')
    cat = b.get('category', 'general')
    themes, points, products = THEMES.get(cat, THEMES['general']), POINTS.get(cat, POINTS['general']), b.get('products') or {}

    plat = {}
    for pn in PLATS:
        P = [p for p in posts if p['platform'] == pn]
        if not P:
            continue
        comm = [p for p in P if p['cat'] != 'organic']
        first = {}
        for p in P:
            first.setdefault(p['handle'], p)
        crC = {p['handle']: p.get('followers') for p in comm}
        crO = {p['handle']: p.get('followers') for p in P if p['cat'] == 'organic'}
        texts = [p['text'] for p in P]
        plat[pn] = dict(
            total=len(P), creators=len(first),
            bycat={c: sum(1 for p in P if p['cat'] == c) for c in CATS},
            creators_bycat={c: len({p['handle'] for p in P if p['cat'] == c}) for c in CATS},
            views={c: med([p.get('views') for p in P if p['cat'] == c]) for c in CATS},
            views_brandled=med([p.get('views') for p in P if brand_led(p)]),
            fmed_comm=med(list(crC.values()))[0], fmed_org=med(list(crO.values()))[0],
            tiers_comm={t: sum(1 for f in crC.values() if tier(f) == t) for t in TIERS},
            tiers_org={t: sum(1 for f in crO.values() if tier(f) == t) for t in TIERS},
            products=counts(texts, products), themes=counts(texts, themes), points=counts(texts, points),
            langs=collections.Counter(lang(p.get('title') or p['text']) for p in P).most_common(8),
            channels=collections.Counter(p['channel'] for p in P if p.get('channel')).most_common(),
            per_creator_commercial=round(len(comm) / max(1, len(crC)), 2),
        )

    allc = collections.Counter(p['cat'] for p in posts)
    n = len(posts)
    tt = plat.get('TikTok') or {}
    org_v = (tt.get('views') or {}).get('organic', [None])[0]
    bl_v = (tt.get('views_brandled') or [None])[0]
    comm_n = n - allc['organic']
    kpi = dict(
        total=n, creators=len({(p['platform'], p['handle']) for p in posts}),
        organic_share=allc['organic'] / n, paid_share=allc['paid'] / n, gifted_share=allc['gifted'] / n,
        affiliate_share=allc['affiliate'] / n, collab_share=allc['collab'] / n, bycat=dict(allc),
        brandled_vs_organic_views=(bl_v / org_v) if (bl_v and org_v) else None,
        affiliate_of_commercial=(allc['affiliate'] / comm_n) if comm_n else None,
        commercial_follower_median=med([p.get('followers') for p in posts if p['cat'] != 'organic'])[0],
    )
    traffic = None
    swp = os.path.join(b['_raw'], 'sales', 'similarweb.json')
    if os.path.exists(swp):
        sw = json.load(open(swp))
        sw = sw.get('data', sw)
        ts = sw.get('trafficSources') or {}
        traffic = dict(sources=ts, monthly=sw.get('monthlyVisits'), visits=[v.get('visits') for v in sw.get('visitsHistory') or []],
                       countries=[[c.get('countryName'), c.get('share')] for c in (sw.get('topCountries') or [])[:6]])
        kpi['social_traffic_share'] = (ts.get('socialOrganic') or 0) + (ts.get('socialPaid') or 0)
    kpi['archetype'], kpi['archetype_reason'] = archetype(kpi)

    bench_path = os.path.join(SKILL_DIR, 'references', 'benchmarks.json')
    bench = [x for x in (json.load(open(bench_path)) if os.path.exists(bench_path) else []) if x.get('brand') != b['brand']]
    me = dict(brand=b['brand'], category=cat, window=b['_window'], archetype=kpi['archetype'], organic_share=round(kpi['organic_share'], 3),
              paid_share=round(kpi['paid_share'], 3), gifted_share=round(kpi['gifted_share'], 3), affiliate_share=round(kpi['affiliate_share'], 3),
              brandled_vs_organic_views=round(kpi['brandled_vs_organic_views'], 2) if kpi['brandled_vs_organic_views'] else None,
              commercial_follower_median=kpi['commercial_follower_median'], social_traffic_share=round(kpi.get('social_traffic_share'), 3) if kpi.get('social_traffic_share') is not None else None)

    rows = [dict(p=p['platform'], h=p.get('handle'), f=int(p['followers']) if p.get('followers') else None, tier=tier(p.get('followers')),
                 c=p['cat'], ch=p.get('channel') or '', v=p.get('views') if isinstance(p.get('views'), (int, float)) else None,
                 l=p.get('likes') if isinstance(p.get('likes'), (int, float)) else None, lang=lang(p.get('title') or p['text']), u=p.get('url'),
                 t=re.sub(r'\s+', ' ', p.get('title') or p['text'])[:140], ts=p['ts']) for p in posts]

    out = dict(brand=b['brand'], category=cat, window=b['_window'], decision_question=b.get('decision_question', ''),
               plat=plat, kpi=kpi, me=me, benchmarks=bench, traffic=traffic, rows=rows, tiers=TIERS,
               themes=list(themes), points=list(points), products=list(products))
    json.dump(out, open(os.path.join(b['_base'], 'analysis.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)

    csv_path = os.path.join(b['_base'], f"{b['brand']}_内容清单.csv")
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['平台', '博主', '粉丝数', '量级', '类型', '转化渠道', '播放量', '点赞', '语言', '发布日期', '链接', '内容摘要'])
        for r in sorted(rows, key=lambda r: (r['p'], -(r['v'] or 0))):
            w.writerow([r['p'], r['h'], r['f'] or '', r['tier'], CN[r['c']], r['ch'], r['v'] or '', r['l'] or '', r['lang'],
                        datetime.date.fromtimestamp(r['ts']).isoformat() if r['ts'] else '', r['u'], r['t']])

    if a.save_benchmark:
        json.dump(bench + [me], open(bench_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

    print(f"打法画像：{kpi['archetype']} —— {kpi['archetype_reason']}")
    print(f"共 {n} 条 / {kpi['creators']} 位博主 | 自然 {kpi['organic_share']:.0%} · 寄样 {kpi['gifted_share']:.0%} · 联盟 {kpi['affiliate_share']:.0%} · "
          f"付费 {kpi['paid_share']:.1%} · 品牌合作 {kpi['collab_share']:.0%}")
    for pn, d in plat.items():
        v = d['views']
        print(f"{pn}: {d['total']} 条 / {d['creators']} 人 | 播放中位数 自然 {v['organic'][0]} · 联盟 {v['affiliate'][0]} · 品牌主导 {d['views_brandled'][0]} "
              f"| 商业博主粉丝中位数 {d['fmed_comm']} | 渠道 {d['channels'][:4]}")
    print(f'对标库 {len(bench)} 个品牌；输出 analysis.json 与 {os.path.basename(csv_path)}')


if __name__ == '__main__':
    main()
