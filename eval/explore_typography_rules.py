"""탐색용 · 논문 수치 아님 — 포스터에서 조판 규칙을 뽑는다. 두 입력으로 같은 계산을 돌린다.

    (가) 파이프라인 측정  : ~/.typo-mcp/{브로크만 · 호프만(corpus) · 로제 · 루더}.json 의 blocks
    (나) 합의 라벨        : docs/brockmann_consensus_refs.json 의 블록 (브로크만 50장만)

재는 것 — 블록 안 행간 · 베이스라인 구조 (격자를 가정하지 않는다) · 정렬 위치와 여백, 그리고 (가)(나) 대조.
상수도 파이프라인도 이 결과로 고치지 않는다. 사전등록 없이 도는 탐색이다 (CLAUDE.md 실험 1).

    python eval/explore_typography_rules.py --cache 브로크만=~/.typo-mcp/brockmann.json … \
        --consensus docs/brockmann_consensus_refs.json --out docs/typography_rules_explore.json
"""
import argparse
import collections
import json
import os

import numpy as np

NEAR = 0.15          # 정수에서 이만큼 안이면 «정수배» 로 센다
GRID = (3.0, 80.5, 0.5)   # 격자 후보 g 를 훑는 범위 (px)
SHARE_OK, SHARE_PART = 0.9, 0.6   # 격자 판정 문턱 (설명됨 · 부분)
SAME_LEAD = 0.1      # 판 행간과 이만큼 안이면 «그 행간으로 설명되는 블록»
CLUS_W = 0.01        # x시작 군집을 가르는 틈 (판 너비 몫, 최소 3px)


def q(v, r=3):
    v = [float(x) for x in v]
    return (dict(n=len(v), 중앙=round(float(np.median(v)), r), p25=round(float(np.percentile(v, 25)), r),
                 p75=round(float(np.percentile(v, 75)), r)) if v else dict(n=0))


def near_int(x, tol=NEAR):
    return abs(x - round(x)) <= tol


def blocks_pipeline(e):
    out = []
    for b in e.get('blocks') or []:
        out.append(dict(bases=sorted(int(v) for v in b['bases']), xh=float(b['xh']),
                        x1=b['x1'], x2=b['x2'], y1=b['y1'], y2=b['y2']))
    return out


def blocks_label(p):
    """라벨 블록. 표시(flag)가 붙은 블록과 베이스라인이 없는 줄은 뺀다."""
    out = []
    for b in p['blocks']:
        if b.get('flag'):
            continue
        num = lambda v: isinstance(v, (int, float))
        bs = sorted(l['base'] for l in b['lines'] if num(l.get('base')))
        xh = [l['base'] - l['xh'] for l in b['lines'] if num(l.get('xh')) and num(l.get('base'))]
        if not bs:
            continue
        out.append(dict(bases=bs, xh=(float(np.median(xh)) if xh else None),
                        x1=b['box'][0], x2=b['box'][2], y1=b['box'][1], y2=b['box'][3]))
    return out


def poster_stats(blocks, size):
    """판 한 장의 값. 격자를 가정하지 않고, 이웃 간격이 어떤 값의 정수배로 얼마나 설명되는지 훑는다."""
    W, H = size
    gaps_px, gaps_xh, blk_med, blk_iqr, ratio_int = [], [], [], [], []
    for b in blocks:
        g = [b['bases'][i + 1] - b['bases'][i] for i in range(len(b['bases']) - 1)]
        if not g:
            continue
        gaps_px += g
        if b['xh']:
            gaps_xh += [x / b['xh'] for x in g]
        blk_med.append(float(np.median(g)))
        blk_iqr.append(float(np.percentile(g, 75) - np.percentile(g, 25)))
        mn = min(g)
        ratio_int += [near_int(x / mn) for x in g if mn > 0]
    lead = float(np.median(blk_med)) if blk_med else None
    same = (sum(1 for m in blk_med if abs(m - lead) <= SAME_LEAD * lead) / len(blk_med)) if blk_med else None
    ys = sorted({y for b in blocks for y in b['bases']})
    ng = [ys[i + 1] - ys[i] for i in range(len(ys) - 1)]
    best = None
    for cand in np.arange(*GRID):
        if not ng:
            break
        share = float(np.mean([near_int(x / cand) for x in ng]))
        resid = float(np.median([abs(x / cand - round(x / cand)) * cand for x in ng]))
        if best is None or (share, -resid) > (best['몫'], -best['잔차']):
            best = dict(g=float(cand), 몫=round(share, 4), 잔차=round(resid, 3))
    cls = None
    if best:
        cls = '설명됨' if best['몫'] >= SHARE_OK else ('부분' if best['몫'] >= SHARE_PART else '안 됨')
    share_pairs = tot_pairs = 0                      # 가로로 떨어진 두 블록이 베이스라인을 나눠 쓰는가
    for i in range(len(blocks)):
        for j in range(i + 1, len(blocks)):
            a, c = blocks[i], blocks[j]
            if min(a['x2'], c['x2']) - max(a['x1'], c['x1']) > 0:
                continue                             # 가로로 겹치면 좌우로 나란하지 않다
            if min(a['y2'], c['y2']) - max(a['y1'], c['y1']) <= 0:
                continue                             # 세로로 겹치는 구간이 없으면 견줄 수 없다
            tot_pairs += 1
            m = sum(1 for y in a['bases'] if any(abs(y - z) <= 1 for z in c['bases']))
            share_pairs += (m / min(len(a['bases']), len(c['bases'])) >= 0.5)
    xs = sorted(b['x1'] for b in blocks)
    clus = []
    for x in xs:
        if clus and x - clus[-1][-1] <= max(3, CLUS_W * W):
            clus[-1].append(x)
        else:
            clus.append([x])
    marg = (dict(왼=round(min(b['x1'] for b in blocks) / W, 4), 오른=round((W - max(b['x2'] for b in blocks)) / W, 4),
                 위=round(min(b['y1'] for b in blocks) / H, 4), 아래=round((H - max(b['y2'] for b in blocks)) / H, 4))
            if blocks else None)
    return dict(간격_px=gaps_px, 간격_xh=gaps_xh, 블록_중앙=blk_med, 블록_사분위폭=blk_iqr,
                정수비=ratio_int, 판_행간=lead, 판행간으로_설명되는_블록몫=(None if same is None else round(same, 4)),
                베이스라인=ys, 이웃간격=ng, 격자=best, 판정=cls,
                좌우_쌍=tot_pairs, 좌우_공유=share_pairs,
                정렬_군집=len(clus), 정렬_위치=[int(np.median(c)) for c in clus], 여백=marg)


def collect(rows):
    g_px = [x for r in rows for x in r['간격_px']]
    g_xh = [x for r in rows for x in r['간격_xh']]
    return dict(판=len(rows), 블록=sum(len(r['블록_중앙']) for r in rows),
                간격_px=q(g_px, 1), 간격_xh=q(g_xh),
                블록_중앙=q([x for r in rows for x in r['블록_중앙']], 1),
                블록_사분위폭=q([x for r in rows for x in r['블록_사분위폭']], 1),
                간격_최빈_px=collections.Counter(int(round(x)) for x in g_px).most_common(3),
                정수배_몫=(round(float(np.mean([b for r in rows for b in r['정수비']])), 4)
                        if any(r['정수비'] for r in rows) else None),
                판행간_설명몫=q([r['판행간으로_설명되는_블록몫'] for r in rows if r['판행간으로_설명되는_블록몫'] is not None]),
                격자_g=q([r['격자']['g'] for r in rows if r['격자']], 1),
                격자_몫=q([r['격자']['몫'] for r in rows if r['격자']]),
                격자_잔차=q([r['격자']['잔차'] for r in rows if r['격자']], 2),
                판정=dict(collections.Counter(r['판정'] for r in rows)),
                좌우_쌍=sum(r['좌우_쌍'] for r in rows), 좌우_공유=sum(r['좌우_공유'] for r in rows),
                정렬_군집=q([r['정렬_군집'] for r in rows], 1),
                여백=dict((k, q([r['여백'][k] for r in rows if r['여백']])) for k in ('왼', '오른', '위', '아래')))


def missed(poster, m):
    """합의 라벨 줄 가운데 측정 베이스라인과 짝 짓지 못한 줄 수 (사전등록 선 짝 정의: 창 0.5·행간 · 허용 0.2·행간)."""
    num = lambda v: isinstance(v, (int, float))
    T = []
    for b in poster['blocks']:
        if b.get('flag'):
            continue
        bs = [l['base'] for l in b['lines'] if num(l.get('base'))]
        if len(bs) > 1:
            L = float(np.median(np.diff(sorted(bs))))
        else:
            xh = [l['base'] - l['xh'] for l in b['lines'] if num(l.get('xh')) and num(l.get('base'))]
            L = 2.0 * (xh[0] if xh else 10.0)
        for l in b['lines']:
            if num(l.get('base')):
                T.append(dict(y=l['base'], lead=L, x1=b['box'][0], x2=b['box'][2]))
    P = [(v, mb['x1'], mb['x2']) for mb in (m.get('blocks') or []) for v in mb['bases']]
    cand = sorted((abs(p[0] - t['y']), i, j) for i, t in enumerate(T) for j, p in enumerate(P)
                  if abs(p[0] - t['y']) <= 0.5 * t['lead'] and min(t['x2'], p[2]) - max(t['x1'], p[1]) > 0)
    mi, mj, hit = set(), set(), {}
    for _d, i, j in cand:
        if i in mi or j in mj:
            continue
        mi.add(i); mj.add(j)
        hit[i] = abs(P[j][0] - T[i]['y']) <= 0.2 * T[i]['lead']
    return dict(줄=len(T), 미검출=sum(1 for i in range(len(T)) if not hit.get(i)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cache', action='append', required=True, help='이름=경로')
    ap.add_argument('--consensus', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    caches = {}
    for s in a.cache:
        name, path = s.split('=', 1)
        caches[name] = json.load(open(os.path.expanduser(path)))
    out = {'가': {}, '나': {}, '대조': {}}
    per = {}
    for c, cj in caches.items():
        rows = []
        for k, e in cj['raw'].items():
            b = blocks_pipeline(e)
            if not b:
                continue
            r = poster_stats(b, e['size']); r['key'] = k; rows.append(r)
        out['가'][c] = collect(rows); per[c] = {r['key']: r for r in rows}
    BR = next(c for c in caches if '브로크만' in c or 'brockmann' in c)
    raw = caches[BR]['raw']
    C = json.load(open(a.consensus))
    lab_rows, miss = [], {}
    for p in C['posters']:
        key = f"{p['folder']}__{p['file']}"
        e = raw.get(key)
        if not e:
            continue
        miss[p['order']] = missed(p, e)['미검출']
        b = blocks_label(p)
        if not b:
            continue
        r = poster_stats(b, e['size']); r['key'] = key; r['order'] = p['order']; lab_rows.append(r)
    out['나'][BR + '_50'] = collect(lab_rows)
    out['가'][BR + '_50'] = collect([per[BR][r['key']] for r in lab_rows if r['key'] in per[BR]])
    diffs = []
    for lr in lab_rows:
        pr = per[BR].get(lr['key'])
        if not pr:
            continue
        diffs.append(dict(order=lr['order'], 미검출=miss.get(lr['order']),
                          판행간_차=(None if (pr['판_행간'] is None or lr['판_행간'] is None)
                                  else round(pr['판_행간'] - lr['판_행간'], 2)),
                          격자_차=(None if not (pr['격자'] and lr['격자']) else round(pr['격자']['g'] - lr['격자']['g'], 2)),
                          격자몫_차=(None if not (pr['격자'] and lr['격자']) else round(pr['격자']['몫'] - lr['격자']['몫'], 3)),
                          군집_차=pr['정렬_군집'] - lr['정렬_군집'],
                          여백왼_차=(None if not (pr['여백'] and lr['여백']) else round(pr['여백']['왼'] - lr['여백']['왼'], 4)),
                          판정_가=pr['판정'], 판정_나=lr['판정']))
    KEYS = ('판행간_차', '격자_차', '격자몫_차', '군집_차', '여백왼_차')
    f = lambda rows, k: q([r[k] for r in rows if r[k] is not None], 2)
    hi = [d for d in diffs if (d['미검출'] or 0) >= 4]
    lo = [d for d in diffs if (d['미검출'] or 0) < 4]
    out['대조'] = dict(판=len(diffs), 전체={k: f(diffs, k) for k in KEYS},
                     미검출_4이상=dict(판=len(hi), **{k: f(hi, k) for k in KEYS}),
                     미검출_4미만=dict(판=len(lo), **{k: f(lo, k) for k in KEYS}),
                     판정_짝=dict(collections.Counter(f"{d['판정_가']} / {d['판정_나']}" for d in diffs)),
                     판별=sorted(diffs, key=lambda d: -(d['미검출'] or 0)))
    res = dict(what='탐색용 · 논문 수치 아님',
               무엇='포스터 조판 규칙 뽑기 — (가) 파이프라인 측정 · (나) 합의 라벨. 상수 · 파이프라인을 고치는 데 쓰지 않는다',
               입력=dict(캐시={k: dict(commit=v['provenance'].get('commit'), n=v['provenance'].get('n'))
                            for k, v in caches.items()}, 합의=a.consensus),
               문턱=dict(정수_허용=NEAR, 격자_훑기=list(GRID), 설명됨=SHARE_OK, 부분=SHARE_PART,
                       판행간_같음=SAME_LEAD, 군집_틈=CLUS_W),
               결과=out,
               판별_가={c: {k: dict(판_행간=r['판_행간'], 격자=r['격자'], 판정=r['판정'],
                                  정렬_군집=r['정렬_군집'], 정렬_위치=r['정렬_위치'], 여백=r['여백'])
                          for k, r in v.items()} for c, v in per.items()},
               판별_나={r['key']: dict(order=r['order'], 판_행간=r['판_행간'], 격자=r['격자'], 판정=r['판정'],
                                    정렬_군집=r['정렬_군집'], 정렬_위치=r['정렬_위치'], 여백=r['여백'])
                      for r in lab_rows})
    json.dump(res, open(a.out, 'w'), ensure_ascii=False, indent=1)
    print('→', a.out)


if __name__ == '__main__':
    main()
