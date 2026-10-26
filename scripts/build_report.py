"""Merge analysis.json + narrative.json into <base>/<slug>-report.html."""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import SKILL_DIR, load_brief  # noqa: E402

REQUIRED = ['verdict', 'summary', 'actions']


def safe_json(obj):
    return json.dumps(obj, ensure_ascii=False).replace('</', '<\\/')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--brief', required=True)
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
    tpl = open(os.path.join(SKILL_DIR, 'assets', 'report_template.html'), encoding='utf-8').read()
    title = narrative.get('title') or f"{b['brand']}红人打法拆解"
    html = (tpl.replace('__TITLE__', title.replace('<', '').replace('>', ''))
               .replace('__DATA__', safe_json(analysis))
               .replace('__NARRATIVE__', safe_json(narrative)))
    out = os.path.join(b['_base'], f"{b.get('slug') or b['brand'].lower().replace(' ', '')}-report.html")
    open(out, 'w', encoding='utf-8').write(html)
    print(f'已生成 {out}（{len(html) // 1024} KB）')


if __name__ == '__main__':
    main()
