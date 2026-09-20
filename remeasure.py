"""코퍼스를 새 경로(Surya + measure/ground)로 다시 잰다 — 대상은 각 코퍼스 index.csv 의 코어.

    python remeasure.py                 네 코퍼스 전부
    python remeasure.py rose            하나만
    python remeasure.py --dry-run       재지 않고 대상 목록 · 장 수 · 지금 캐시와의 차만 찍는다

대상 (2026-09-15 부터). 각 코퍼스 폴더의 corpus/index.csv 에서 group = 코어 인 판이다. 분류 절차와 기준은
docs/CORPUS_SELECTION.md. 열쇠는 «폴더__파일» (surface.paths 와 같은 모양)이다. index.csv 코어 경로에 파일이
없으면 멈춘다 — 파일 이름으로 짝을 찾지 않는다.
그 전에는 보관본(~/.typo-mcp/old-20260824)의 열쇠를 썼다. 브로크만 · 호프만 · 루더는 그 목록이 코어와 같았고,
로제만 달랐다 (제외_판형 9장이 들고, 코어 1장이 빠짐).

측정 대상에서 빼는 판 — 코어 분류와 다른 기준이다. 코어는 저자 · 이미지 신뢰성 · 판형으로 가르고 내용은 보지 않는다.
글자가 없는 판은 잴 활자가 없으므로 측정 대상에서 뺀다. NO_TEXT 에 판마다 까닭과 함께 적는다.

규칙은 잰 코퍼스마다 나머지 셋을 참조로 넣어 뽑는다 (rules.derive — 참조는 설명력 scope 에만 쓰인다).
결과 요약은 docs/remeasure_log.json 에 코퍼스별로 남긴다 (다시 잰 코퍼스 항목만 바꾼다).
"""
import csv
import json
import os
import sys

import measure_corpus as MC
import rules
import surface

NEW = os.path.expanduser('~/.typo-mcp')
LOG = 'docs/remeasure_log.json'

# 측정 대상에서 빼는 판 (코어 분류 기준 밖, docs/CORPUS_SELECTION.md «측정 대상»)
NO_TEXT = {
    'rose': {'Sonstige__1961_[ohne Text].jpg': '글자가 없는 판 (제목 «[ohne Text]») — 잴 활자가 없다'},
}


def keys_of(c):
    """index.csv group = 코어 → ([(열쇠, 경로)], {뺀 열쇠: 까닭}). 코어 경로에 파일이 없거나 열쇠가 겹치면 멈춘다."""
    corpus = os.path.join(os.path.expanduser(surface.ROOTS[c]), 'corpus')
    rows = [r for r in csv.DictReader(open(os.path.join(corpus, 'index.csv'), encoding='utf-8-sig'))
            if r['group'] == '코어']
    items, skipped, missing = [], {}, []
    for r in rows:
        p = os.path.join(corpus, r['new_path'])
        k = os.path.basename(os.path.dirname(p)) + '__' + os.path.basename(p)
        if k in NO_TEXT.get(c, {}):
            skipped[k] = NO_TEXT[c][k]
            continue
        if not os.path.isfile(p):
            missing.append(r['new_path'])
            continue
        items.append((k, p))
    if missing:
        sys.exit(f'{c}: index.csv 코어 경로에 파일이 없다 — {missing}')
    if len({k for k, _ in items}) != len(items):
        sys.exit(f'{c}: 열쇠가 겹친다')
    unknown = set(NO_TEXT.get(c, {})) - set(skipped)
    if unknown:
        sys.exit(f'{c}: NO_TEXT 의 판이 코어에 없다 — {sorted(unknown)}')
    return sorted(items), skipped


def dry_run(which):
    for c in which:
        items, skipped = keys_of(c)
        target = {k for k, _ in items}
        p = os.path.join(NEW, c + '.json')
        cache = set(json.load(open(p))['raw']) if os.path.exists(p) else set()
        print(f'{c}: 코어 {len(items) + len(skipped)} · 측정에서 뺌 {len(skipped)} · 대상 {len(items)} · '
              f'지금 캐시 {len(cache)} · 같음 {target == cache} · 겹침 {len(target & cache)} · '
              f'대상에만 {len(target - cache)} · 캐시에만 {len(cache - target)}', flush=True)
        for k, why in skipped.items():
            print(f'   뺌: {k} — {why}')


def main(which):
    got, report = {}, {}
    for c in which:
        items, skipped = keys_of(c)
        print(f'{c}: {len(items)}장 (측정에서 뺌 {len(skipped)})', flush=True)
        raw, failed = MC.measure_items(items)
        got[c] = raw
        bs = [b for e in raw.values() for b in (e.get('blocks') or [])]
        report[c] = dict(판=len(items), 잰판=len(raw), 대상='corpus/index.csv group = 코어',
                         측정에서_뺌=skipped,
                         실패=[[os.path.basename(p), w] for p, w in failed],
                         덩어리=len(bs), 뒤집힌아래끝=sum(1 for b in bs if b['y2'] < b['y1']),
                         기울어짐=sum(1 for e in raw.values() if e.get('skewed')))
        print(f"  잰 판 {len(raw)} · 실패 {len(failed)} · 덩어리 {len(bs)} · "
              f"뒤집힌 아래끝 {report[c]['뒤집힌아래끝']} · 기울어짐 {report[c]['기울어짐']}", flush=True)
    for c, raw in got.items():
        refs = {o: (got[o] if o in got else json.load(open(os.path.join(NEW, o + '.json')))['raw'])
                for o in surface.ROOTS if o != c}
        r = rules.derive(raw, references=refs)
        MC.write(os.path.join(NEW, c + '.json'), raw, rules=r,
                 source=f'remeasure.py — {surface.ROOTS[c]}/corpus/index.csv 코어 {len(raw)}장')
        print(f'  → {NEW}/{c}.json', flush=True)
    prev = json.load(open(LOG)) if os.path.exists(LOG) else {}
    prev.update(report)
    json.dump(prev, open(LOG, 'w'), ensure_ascii=False, indent=1)
    print('끝', flush=True)


if __name__ == '__main__':
    args = sys.argv[1:]
    dry = '--dry-run' in args
    which = [a for a in args if a != '--dry-run'] or list(surface.ROOTS)
    bad = [a for a in which if a not in surface.ROOTS]
    if bad:
        sys.exit(f'모르는 코퍼스: {bad} (가능: {list(surface.ROOTS)})')
    (dry_run if dry else main)(which)
