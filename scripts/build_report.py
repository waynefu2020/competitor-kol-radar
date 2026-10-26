"""Merge analysis.json + narrative.json into <base>/<slug>-report.html.

Style resolution (first match wins):
  --style flag → narrative.style / brief.style (unless "auto") → purpose → category.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import SKILL_DIR, load_brief  # noqa: E402

REQUIRED = ['verdict', 'summary', 'actions']
GF = 'https://fonts.googleapis.com/css2?'
FONTS = {
    'consulting': GF + 'family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;700&display=swap',
    'wrapped': GF + 'family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,800&family=IBM+Plex+Mono:wght@400;500&family=Noto+Sans+SC:wght@400;500;700;900&display=swap',
    'brand': GF + 'family=Cormorant+Garamond:ital,wght@0,600;1,600&family=IBM+Plex+Mono:wght@400;500&family=Noto+Sans+SC:wght@400;500;700&family=Noto+Serif+SC:wght@600;900&display=swap',
    'terminal': GF + 'family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&family=Noto+Sans+SC:wght@400;500;700&display=swap',
    'notebook': GF + 'family=IBM+Plex+Mono:wght@400;500&family=Ma+Shan+Zheng&family=Noto+Sans+SC:wght@400;500;700&family=ZCOOL+KuaiLe&display=swap',
}
STYLE_NAMES = {'consulting': '咨询报告风', 'wrapped': '年度回顾风', 'brand': '品牌调性风', 'terminal': '暗黑科技风', 'notebook': '小红书手账风'}
PURPOSE = {'report': 'consulting', '汇报': 'consulting', 'boss': 'consulting', 'client': 'consulting',
           'social': 'wrapped', '社媒': 'wrapped', 'video': 'wrapped', '视频': 'wrapped', 'douyin': 'wrapped', 'tiktok': 'wrapped',
           'xhs': 'notebook', '小红书': 'notebook', 'rednote': 'notebook'}
CATEGORY = {'beauty': 'brand', 'fashion': 'brand', 'lifestyle': 'brand', 'food': 'brand', 'tech': 'terminal', 'app': 'terminal', 'saas': 'terminal'}


def resolve_style(cli, narrative, brief):
    for s in (cli, narrative.get('style'), brief.get('style')):
        if s and s != 'auto':
            if s not in FONTS:
                sys.exit(f'未知风格 {s}，可选：{", ".join(FONTS)}')
            return s, '指定'
    purpose = str(narrative.get('purpose') or brief.get('purpose') or '').lower()
    for k, s in PURPOSE.items():
        if k in purpose:
            return s, f'按用途「{purpose}」'
    cat = str(brief.get('category') or '').lower()
    if cat in CATEGORY:
        return CATEGORY[cat], f'按品类「{cat}」'
    return 'consulting', '默认'


def safe_json(obj):
    return json.dumps(obj, ensure_ascii=False).replace('</', '<\\/')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--brief', required=True)
    ap.add_argument('--style', choices=list(FONTS), help='覆盖自动选择的风格')
    ap.add_argument('--out', help='输出文件名（默认 <slug>-report.html，指定风格时为 <slug>-report-<style>.html）')
    a = ap.parse_args()
    b = load_brief(a.brief)
    analysis = json.load(open(os.path.join(b['_base'], 'analysis.json'), encoding='utf-8'))
    np = os.path.join(b['_base'], 'narrative.json')
    if not os.path.exists(np):
        sys.exit('缺少 narrative.json：按 references/report-spec.md 写好结论再生成报告。')
    narrative = json.load(open(np, encoding='utf-8'))
    missing = [k for k in REQUIRED if not narrative.get(k)]
    if missing:
        sys.exit(f'narrative.json 缺少字段：{missing}')
    style, why = resolve_style(a.style, narrative, b)
    tpl = open(os.path.join(SKILL_DIR, 'assets', 'report_template.html'), encoding='utf-8').read()
    title = (narrative.get('title') or f"{b['brand']}红人打法拆解").replace('<', '').replace('>', '')
    html = (tpl.replace('__TITLE__', title).replace('__STYLE__', style).replace('__FONTS__', FONTS[style])
               .replace('__DATA__', safe_json(analysis)).replace('__NARRATIVE__', safe_json(narrative)))
    slug = b.get('slug') or b['brand'].lower().replace(' ', '')
    name = a.out or (f'{slug}-report-{style}.html' if a.style else f'{slug}-report.html')
    out = os.path.join(b['_base'], name)
    open(out, 'w', encoding='utf-8').write(html)
    print(f'已生成 {out}（{len(html) // 1024} KB）· 风格：{STYLE_NAMES[style]}（{style}，{why}）')


if __name__ == '__main__':
    main()
