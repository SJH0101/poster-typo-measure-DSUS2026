"""순서 4 · 병행 상수의 합성 스윕 — docs/constants_preregister.json (수정 4 · 5 · 8).

    python eval/constants_sweep4.py --dir ~/.typo-mcp/synth_sweep --manifest docs/synth_sweep_manifest.json \
        --lines ~/.typo-mcp/synth_sweep_lines --prereg docs/constants_preregister.json --out docs/constants_sweep4.json

세트: 조정 세트 (합성 스윕 공용 세트, 13셀 × seed 7201~7230). 한 번에 한 상수, 나머지는 현재 값.
코드의 상수는 바꾸지 않는다 — 실행 중에만 measure/ink.py 소스 사본과 모듈 값을 갈아 끼운다.
재기: detect_surya.boxes_norm → measure.ground.entry (photo 없음), 줄은 사람 확인 뒤 뽑은 Surya 줄.

결정 (수정 5): 지표 곡선 = 13셀 단순 평균, 평평 = 최고 − δ 안의 연속 격자 점 (최고가 여럿이면 가장 작은 격자 점을 품는 구간),
현재 값이 모든 결정 지표의 평평 구간 안이면 유지, 아니면 교집합의 가운데 (짝수면 낮은 쪽), 교집합이 없으면 멈춘다.
정밀도 (수정 8): 모든 상수에 재현율과 함께 적고, 정밀도 < 현재 값 정밀도 − δ 인 격자 점을 표시한다 (판정은 바꾸지 않는다).
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'eval'))
import detect_surya as DS          # noqa: E402
import detector_score as DSc       # noqa: E402
import measure_corpus as MC        # noqa: E402
import synth_score as SS           # noqa: E402
from measure import ground as G    # noqa: E402
from measure import ink, region    # noqa: E402

INK_SRC = open(os.path.join(ROOT, 'measure/ink.py'), encoding='utf-8').read()
INK_KEYS = ('lines', 'split_marks', 'baseline', 'descender', 'polarity', 'threshold',
            'FRAG_WIDE', 'FRAG_COVER', 'INK_FRAC', 'BASE_OFFSET', 'MARK_SMALL', 'MARK_GAP_RATIO',
            'MARK_GAP_MIN', 'MARK_GAP_RATIO_XH', 'MARK_GAP_E', 'ASC_RATIO')
INK_NOW = {k: getattr(ink, k) for k in INK_KEYS}
DS_NOW = {k: getattr(DS, k) for k in ('X_OVER', 'MIN_AREA', 'H_RATIO', 'Y_GAP')}
PAD_NOW = region.PAD
SAMPLE_MIN = 30          # 수정 9 의 3 — 결정 지표 표본이 이보다 적으면 판정하지 않는다
KINDS3 = (('베이스라인', '베이스라인'), ('x높이선', 'x높이선'), ('상단 잉크선', '캡선'))


def _loc(path, needle, n=1):
    """file:line 표기를 문자열 검색으로 만든다 — 줄 번호를 손으로 적지 않는다."""
    for i, line in enumerate(open(os.path.join(ROOT, path), encoding='utf-8'), 1):
        if needle in line:
            n -= 1
            if n == 0:
                return f'{path}:{i}'
    return path


def _src_num(needle, group=1, path='measure/ink.py'):
    """코드에서 숫자를 읽는다 (정규식 첫 묶음)."""
    m = re.search(needle, open(os.path.join(ROOT, path), encoding='utf-8').read())
    return float(m.group(group)) if m else None


def _tilde(q):
    """기록 경로의 홈을 ~ 로 접는다."""
    h = os.path.expanduser('~')
    return '~' + q[len(h):] if q.startswith(h) else q


def _sha(p):
    return hashlib.sha256(open(os.path.expanduser(p), 'rb').read()).hexdigest()


def ink_variant(repl=None, record_g1=False):
    """measure/ink.py 소스 사본 — 문자열 치환만 한다. record_g1 이면 G1 되돌림 여부를 _G1 에 적는다."""
    src = INK_SRC
    for a, b in (repl or []):
        assert src.count(a) == 1, a
        src = src.replace(a, b)
    if record_g1:
        a = "        low = [t for t, b in comps if b >= s + raw and t <= cen]\n        if low:\n            xh = max(low)\n"
        assert src.count(a) == 1
        src = src.replace(a, a.replace("        if low:\n", "        _G1.append(not low)\n        if low:\n"))
        b = "    if prof.max() == 0:\n"
        src = src.replace(b, "    if prof.max() == 0:\n        _G1.append(None)\n", 1)
        c = "    raw = min(max(base - BASE_OFFSET - s, 1), len(prof) - 1)\n    w = prof[:raw + 1]\n    if w.sum() > 0:\n"
        assert src.count(c) == 1
        src = src.replace(c, c.replace("    if w.sum() > 0:\n", "    if w.sum() <= 0:\n        _G1.append(None)\n    if w.sum() > 0:\n"))
    ns = dict(_G1=[])
    exec(compile(src, 'ink_variant', 'exec'), ns)
    return ns


def install(ns=None, ds=None, pad=None):
    for k in INK_KEYS:
        setattr(ink, k, (ns[k] if ns else INK_NOW[k]))
    for k, v in DS_NOW.items():
        setattr(DS, k, (ds.get(k, v) if ds else v))
    region.PAD = PAD_NOW if pad is None else pad


def measure(item):
    bx = DS.boxes_norm(item['lines']['lines'], item['lines']['size'])
    if not bx:
        return dict(blocks=[])
    try:
        return G.entry(item['image'], bx, coords='norm', photo=False)[0]
    except Exception:
        return dict(blocks=[])


def line_stats(t, m):
    d = SS.direct_lines(t, m)
    out = {}
    for name, fld in KINDS3:
        v = d[fld]
        out[name] = dict(참값=v['n_truth'], 측정=v['n_meas'], 짝=len(v['pairs']), 맞음=sum(q['hit'] for q in v['pairs']),
                         행일치=sum(abs(q['err']) <= 0.5 for q in v['pairs']))
    return out


def block_stats(t, m):
    T = [tb['ink_box'] for tb in t['blocks']]
    P = [[b['x1'], b['y1'], b['x2'], b['y2']] for b in m['blocks']]
    mr, mp = DSc.match(T, P)
    ious = [DSc.iou(T[i], P[j]) for i, j in mr.items()]
    merged = sum(1 for p in P if sum(1 for r in T if DSc.held(p, r) >= DSc.INSIDE) >= 2)
    split = sum(1 for j, p in enumerate(P) if j not in mp and any(DSc.inside(p, r) >= DSc.INSIDE for r in T))
    return dict(참조=len(T), 출처=len(P), 맞음=len(mr), iou합=float(sum(ious)), 과병합=merged, 과분할=split)


def g1_stats(t, m, g1):
    """G1 되돌림이 쓰인 줄만: x높이선 참값과 같은 행 몫. g1[i] = 측정 줄 i 의 되돌림 여부."""
    T = []
    for tb in t['blocks']:
        lead = SS._lead_of(tb)
        for ln in tb['lines']:
            T.append(dict(y=ln['xtop_y'], lead=lead, x1=ln['x1'], x2=ln['x2']))
    P, flag = [], []
    k = 0
    for b in m['blocks']:
        for v in b['xtops']:
            P.append((v, b['x1'], b['x2'])); flag.append(g1[k] if k < len(g1) else None); k += 1
    cand = sorted((abs(p[0] - tl['y']), i, j) for i, tl in enumerate(T) for j, p in enumerate(P)
                  if abs(p[0] - tl['y']) <= SS.MATCH_WIN * tl['lead'] and min(tl['x2'], p[2]) - max(tl['x1'], p[1]) > 0)
    mi, mj, n, ok = set(), set(), 0, 0
    for _d, i, j in cand:
        if i in mi or j in mj:
            continue
        mi.add(i); mj.add(j)
        if flag[j]:
            n += 1; ok += abs(P[j][0] - T[i]['y']) <= 0.5
    return dict(되돌림_짝=n, 행일치=ok)


def flat(points, vals, delta):
    ok = [i for i, v in enumerate(vals) if v is not None]
    if not ok:
        return None
    best = max(vals[i] for i in ok)
    i0 = next(i for i in ok if vals[i] == best)
    lo = hi = i0
    while lo - 1 >= 0 and vals[lo - 1] is not None and vals[lo - 1] >= best - delta - 1e-12:
        lo -= 1
    while hi + 1 < len(vals) and vals[hi + 1] is not None and vals[hi + 1] >= best - delta - 1e-12:
        hi += 1
    return dict(최고=round(best, 4), 최고_격자=points[i0], 구간=[points[lo], points[hi]], 격자점=points[lo:hi + 1])


def decide(points, curves, cur, delta):
    flats = {k: flat(points, v, delta) for k, v in curves.items()}
    sets = [set(f['격자점']) for f in flats.values() if f]
    inter = sorted(set.intersection(*sets)) if sets else []
    inside = all(f and cur in f['격자점'] for f in flats.values())
    if inside:
        v = dict(판정='유지', 값=cur)
    elif inter:
        v = dict(판정='바꿀 값', 값=inter[(len(inter) - 1) // 2])
    else:
        v = dict(판정='멈춤', 값=None, 까닭='결정 지표 평평 구간의 교집합이 없다')
    return flats, inter, inside, v


def specs():
    """(이름, 위치, 현재 값, 격자, 설치 함수, 지표 갈래)"""
    S = []
    S.append(dict(이름='lines(… body_h=)', 위치=[_loc('measure/ink.py', 'def lines(')],
                  현재=int(_src_num(r'def lines\(.*body_h=(\d+)')), 격자=[2, 3, 4, 5, 6], 갈래='line',
                  결정=['베이스라인'], 설치=lambda v: install(ink_variant([("def lines(g, th, x0, x1, min_h=2, body_h=4, mask=None):",
                                                                          f"def lines(g, th, x0, x1, min_h=2, body_h={v}, mask=None):")]))))
    S.append(dict(이름='split_marks() · 되돌림 어깨', 위치=[_loc('measure/ink.py', 'prof >= 0.5 * prof.max()')],
                  현재=_src_num(r'prof >= ([\d.]+) \* prof\.max\(\)'), 격자=[0.3, 0.4, 0.5, 0.6, 0.7], 갈래='g1',
                  결정=['되돌림_행일치'], 설치=lambda v: install(ink_variant([("xh = s + int(np.argmax(prof >= 0.5 * prof.max()))",
                                                                            f"xh = s + int(np.argmax(prof >= {v} * prof.max()))")], record_g1=True))))
    S.append(dict(이름='region.PAD', 위치=[_loc('measure/region.py', 'PAD = ')], 현재=PAD_NOW, 격자=[1, 2, 3, 4, 5, 6], 갈래='line+block',
                  결정=['베이스라인', '상단 잉크선', '블록'], 설치=lambda v: install(pad=v)))
    S.append(dict(이름='FRAG_WIDE', 위치=[_loc('measure/ink.py', 'FRAG_WIDE = ')], 현재=INK_NOW['FRAG_WIDE'], 격자=[0.2, 0.3, 0.4, 0.5, 0.6], 갈래='line',
                  결정=['베이스라인', 'x높이선', '상단 잉크선'], 설치=lambda v: install(ink_variant([("FRAG_WIDE = 0.40", f"FRAG_WIDE = {v}")]))))
    S.append(dict(이름='FRAG_COVER', 위치=[_loc('measure/ink.py', 'FRAG_COVER = ')], 현재=INK_NOW['FRAG_COVER'], 격자=[0.175, 0.2625, 0.35, 0.4375, 0.525], 갈래='line',
                  결정=['베이스라인', 'x높이선', '상단 잉크선'], 설치=lambda v: install(ink_variant([("FRAG_COVER = 0.35", f"FRAG_COVER = {v}")]))))
    S.append(dict(이름='polarity() 꼬리 백분위 (아래 p, 위 100 − p)', 위치=[_loc('measure/ink.py', 'np.percentile(g, (')],
                  현재=int(_src_num(r'np\.percentile\(g, \((\d+), 50')), 격자=[2, 4, 5, 6, 8], 갈래='line',
                  결정=['베이스라인', 'x높이선', '상단 잉크선'],
                  설치=lambda v: install(ink_variant([("lo, med, hi = np.percentile(g, (5, 50, 95))", f"lo, med, hi = np.percentile(g, ({v}, 50, {100 - v}))")]))))
    S.append(dict(이름='lines() · peak 백분위', 위치=[_loc('measure/ink.py', 'peak = np.percentile(')],
                  현재=_src_num(r'peak = np\.percentile\(ink\[ink > 0\], ([\d.]+)\)'), 격자=[85, 87.5, 90, 92.5, 95], 갈래='line',
                  결정=['베이스라인', 'x높이선', '상단 잉크선'],
                  설치=lambda v: install(ink_variant([("peak = np.percentile(ink[ink > 0], 90)", f"peak = np.percentile(ink[ink > 0], {v})")]))))
    S.append(dict(이름='lines() · on 백분위', 위치=[_loc('measure/ink.py', 'on = ink > max(np.percentile(')],
                  현재=int(_src_num(r'on = ink > max\(np\.percentile\(ink, (\d+)\)')), 격자=[2, 4, 5, 6, 8], 갈래='line',
                  결정=['베이스라인', 'x높이선', '상단 잉크선'],
                  설치=lambda v: install(ink_variant([("on = ink > max(np.percentile(ink, 5), INK_FRAC * peak)", f"on = ink > max(np.percentile(ink, {v}), INK_FRAC * peak)")]))))
    # «현재» 는 코드에서 읽는다 (DS_NOW) — 박아 두면 상수를 고친 뒤 옛 값 기준으로 판정하게 된다
    for key, grid in (('X_OVER', [0.075, 0.1125, 0.15, 0.1875, 0.225]),
                      ('MIN_AREA', [100, 150, 200, 250, 300])):
        cur = DS_NOW[key]
        S.append(dict(이름=f'detect_surya.{key}', 위치=[_loc('detect_surya.py', f'{key} = ')], 현재=cur, 격자=grid, 갈래='block',
                      결정=['블록'], 설치=(lambda v, k=key: install(ds={k: v}))))
    for key, idx, grid in (('H_RATIO', 0, [0.6, 0.675, 0.75, 0.825, 0.9]), ('H_RATIO', 1, [1.7, 2.55, 3.4, 4.25, 5.1]),
                           ('Y_GAP', 0, [-0.6, -0.5, -0.4, -0.3, -0.2]), ('Y_GAP', 1, [0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.6])):
        cur = DS_NOW[key][idx]
        S.append(dict(이름=f'detect_surya.{key} {"하한" if idx == 0 else "상한"}', 위치=[_loc('detect_surya.py', f'{key} = ')], 현재=cur, 격자=grid, 갈래='block',
                      결정=['블록'], 설치=(lambda v, k=key, i=idx: install(ds={k: (tuple(v if j == i else DS_NOW[k][j] for j in (0, 1)))}))))
    return S


def main(argv=None):
    ap = argparse.ArgumentParser(description='순서 4 · 병행 상수 합성 스윕')
    ap.add_argument('--dir', required=True); ap.add_argument('--manifest', required=True)
    ap.add_argument('--lines', required=True); ap.add_argument('--prereg', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--only', nargs='*')
    a = ap.parse_args(argv)
    P = json.load(open(a.prereg)); delta = P['공통 규칙']['합성 스윕']['δ']
    D = os.path.expanduser(a.dir); M = json.load(open(a.manifest))
    LW = os.path.expanduser(a.lines); LM = json.load(open(os.path.join(LW, 'manifest.json'))); LL = json.load(open(os.path.join(LW, 'lines.json')))
    by = {(it['cell'], it['seed']): it for it in M['items']}
    items = []
    for li in LM['items']:
        it = by[(li['cell'], li['poster_seed'])]
        p = os.path.join(D, it['image'])
        if _sha(p) != it['image_sha256'] or LL['lines'][f"{li['seed']:03d}"]['sha256'] != it['image_sha256']:
            sys.exit(f'manifest 와 다른 이미지 또는 줄: {p}')
        items.append(dict(cell=it['cell'], seed=it['seed'], image=p, truth=json.load(open(p[:-4] + '.json')), lines=LL['lines'][f"{li['seed']:03d}"]))
    cells = list(M['cells'])
    res = {}
    t0 = time.time()
    for sp in specs():
        if a.only and sp['이름'] not in a.only:
            continue
        per = {}
        for v in sp['격자']:
            ns_g1 = None
            if sp['갈래'] == 'g1':
                ns_g1 = ink_variant([("xh = s + int(np.argmax(prof >= 0.5 * prof.max()))",
                                      f"xh = s + int(np.argmax(prof >= {v} * prof.max()))")], record_g1=True)
                install(ns_g1)
            else:
                sp['설치'](v)
            acc = {c: dict(line={n: dict(참값=0, 측정=0, 짝=0, 맞음=0, 행일치=0) for n, _f in KINDS3},
                           block=dict(참조=0, 출처=0, 맞음=0, iou합=0.0, 과병합=0, 과분할=0), g1=dict(되돌림_짝=0, 행일치=0)) for c in cells}
            for x in items:
                if ns_g1 is not None:
                    ns_g1['_G1'].clear()
                m = measure(x)
                A = acc[x['cell']]
                if sp['갈래'] in ('line', 'line+block'):
                    ls = line_stats(x['truth'], m)
                    for n, _f in KINDS3:
                        for k2 in A['line'][n]:
                            A['line'][n][k2] += ls[n][k2]
                if sp['갈래'] in ('block', 'line+block'):
                    bs = block_stats(x['truth'], m)
                    for k2 in A['block']:
                        A['block'][k2] += bs[k2]
                if sp['갈래'] == 'g1':
                    gs = g1_stats(x['truth'], m, list(ns_g1['_G1']))
                    for k2 in A['g1']:
                        A['g1'][k2] += gs[k2]
            per[str(v)] = {c: dict(line={n: dict(A['line'][n]) for n, _f in KINDS3}, block=dict(A['block']), g1=dict(A['g1'])) for c, A in acc.items()}
            print(f"  {sp['이름']} {v}  {time.time() - t0:.0f}s", flush=True)
        install()
        # 곡선 (13셀 단순 평균)
        pts = [str(v) for v in sp['격자']]
        rate = lambda d, a_, b_: (d[a_] / d[b_] if d[b_] else None)
        curves, prec = {}, {}
        mean = lambda vs: (float(np.mean([v for v in vs if v is not None])) if any(v is not None for v in vs) else None)
        for n, _f in KINDS3:
            curves[n] = [mean([rate(per[p_][c]['line'][n], '맞음', '참값') for c in cells]) for p_ in pts]
            prec[n] = [mean([rate(per[p_][c]['line'][n], '맞음', '측정') for c in cells]) for p_ in pts]
        curves['블록'] = [mean([rate(per[p_][c]['block'], '맞음', '참조') for c in cells]) for p_ in pts]
        prec['블록'] = [mean([rate(per[p_][c]['block'], '맞음', '출처') for c in cells]) for p_ in pts]
        curves['되돌림_행일치'] = [mean([rate(per[p_][c]['g1'], '행일치', '되돌림_짝') for c in cells]) for p_ in pts]
        extra = dict(과병합=[int(sum(per[p_][c]['block']['과병합'] for c in cells)) for p_ in pts],
                     과분할=[int(sum(per[p_][c]['block']['과분할'] for c in cells)) for p_ in pts],
                     합_과병합_과분할=[int(sum(per[p_][c]['block']['과병합'] + per[p_][c]['block']['과분할'] for c in cells)) for p_ in pts],
                     평균_IoU=[mean([rate(per[p_][c]['block'], 'iou합', '맞음') for c in cells]) for p_ in pts],
                     되돌림_짝=[int(sum(per[p_][c]['g1']['되돌림_짝'] for c in cells)) for p_ in pts],
                     평균_IoU_주=  '짝지은 블록만')
        dec_curves = {k: [None if v is None else round(v, 4) for v in curves[k]] for k in sp['결정']}
        n_sample = {}
        for k in sp['결정']:
            if k == '블록':
                n_sample[k] = int(min(sum(per[p_][c]['block']['참조'] for c in cells) for p_ in pts))
            elif k == '되돌림_행일치':
                n_sample[k] = int(min(sum(per[p_][c]['g1']['되돌림_짝'] for c in cells) for p_ in pts))
            else:
                n_sample[k] = int(min(sum(per[p_][c]['line'][k]['참값'] for c in cells) for p_ in pts))
        flats, inter, inside, verdict = decide(sp['격자'], dec_curves, sp['현재'], delta)
        thin = [k for k, n in n_sample.items() if n < SAMPLE_MIN]
        blockish = sp['이름'].startswith('detect_surya.')
        cost = extra['합_과병합_과분할']
        flat_single_edge = {k: f['구간'] for k, f in flats.items()
                            if f and len(f['격자점']) == 1 and f['격자점'][0] in (sp['격자'][0], sp['격자'][-1])}
        no_effect = all(len(set(v)) == 1 for v in dec_curves.values()) and (not blockish or len(set(cost)) == 1)
        if thin:
            verdict = dict(판정='표본 부족 — 유지', 값=sp['현재'], 까닭=f'결정 지표 표본 < {SAMPLE_MIN} ({n_sample})')
        elif blockish:
            fl = flats['블록']
            best = min(cost[sp['격자'].index(g)] for g in fl['격자점'])
            tied = [g for g in fl['격자점'] if cost[sp['격자'].index(g)] == best]
            if sp['현재'] in tied:      # 수정 10 의 1 — 동점이면 현재 값 유지
                verdict = dict(판정=('유지 (효과 없음)' if len(tied) > 1 else '유지'), 값=sp['현재'],
                               규칙='재현율 평평 구간 안 과병합 + 과분할 최소 (수정 9 의 2), 동점이면 현재 값 유지 (수정 10 의 1)',
                               합=best, 동점_격자=tied)
            else:
                verdict = dict(판정='바꿀 값', 값=tied[0], 규칙='재현율 평평 구간 안 과병합 + 과분할 최소 (수정 9 의 2)', 합=best, 동점_격자=tied)
        elif no_effect:
            verdict = dict(판정='유지 (효과 없음)', 값=sp['현재'], 까닭='격자 전체에서 결정 지표가 같다 (수정 10 의 1 · 3)')
        # 수정 10 의 2 — 선택된 점이 격자의 끝이면 넓혀 다시 돌린다
        if verdict.get('값') is not None and verdict['값'] in (sp['격자'][0], sp['격자'][-1]) and '효과 없음' not in verdict['판정'] and not thin:
            verdict = dict(판정='격자 끝점 — 넓혀 다시 돌려야 함', 값=None, 앞선_판정=verdict, 격자=sp['격자'])
        elif flat_single_edge and verdict.get('값') is not None:
            verdict['평평_구간_끝점'] = flat_single_edge
        ci = sp['격자'].index(sp['현재'])
        flags = {k: [sp['격자'][i] for i, v in enumerate(prec[k])
                     if prec[k][ci] is not None and v is not None and prec[k][ci] - v > delta + 1e-12] for k in prec}
        res[sp['이름']] = dict(위치=sp['위치'], 현재=sp['현재'], 격자=sp['격자'], 갈래=sp['갈래'], 결정_지표=sp['결정'],
                              곡선_재현율={k: [None if v is None else round(v, 4) for v in curves[k]] for k in curves},
                              곡선_정밀도={k: [None if v is None else round(v, 4) for v in prec[k]] for k in prec}, 참고=extra,
                              평평_구간=flats, 교집합=inter, 현재값_평평구간_안=inside, 표본=n_sample, 판정=verdict,
                              정밀도_δ이상_떨어진_격자={k: v for k, v in flags.items() if v}, 셀별=per)
        print(sp['이름'], verdict, '· 정밀도 표시', {k: v for k, v in flags.items() if v}, flush=True)
    out = dict(무엇='순서 4 · 병행 상수 합성 스윕 — constants_preregister 수정 4 · 5 · 8. 결과 보고까지만 (코드 상수는 바꾸지 않음)',
               사전등록=a.prereg, 사전등록_sha256=_sha(a.prereg), manifest=a.manifest, manifest_sha256=_sha(a.manifest),
               줄=dict(폴더=_tilde(a.lines), lines_sha256=_sha(os.path.join(LW, 'lines.json')), provenance=LL.get('provenance')),
               정의=dict(세트='조정 세트 13셀 × seed 7201~7230', δ=delta, 곡선='13셀 단순 평균',
                       재현율='맞음 ÷ 참값 (선: direct_lines 허용 안 짝 ÷ 참값 선, 블록: IoU ≥ 0.5 1:1 ÷ 참값 블록)',
                       정밀도='맞음 ÷ 측정 (선: 측정 선, 블록: 출처 블록)',
                       되돌림_행일치='G1 되돌림이 쓰인 측정 줄의 x높이선 짝 가운데 |오차| ≤ 0.5 몫',
                       정밀도_표시='정밀도 < 현재 값 정밀도 − δ 인 격자 점 (수정 8, 판정은 바꾸지 않음)',
                       블록_판정='재현율 평평 구간 안에서 과병합 + 과분할 이 가장 작은 격자 점 (수정 9 의 2)',
                       표본_부족=f'결정 지표 표본 < {SAMPLE_MIN} 이면 판정하지 않고 현재 값 유지 (수정 9 의 3)',
                       격자_끝점='평평 구간이 격자 끝점에서 끝나면 넓혀 다시 돌린다 (수정 9 의 1, 최대 2회)'),
               상수=res, 최종_판정={k: dict(현재=v['현재'], 판정=v['판정']['판정'], 값=v['판정'].get('값')) for k, v in res.items()},
               provenance=MC.provenance('eval/constants_sweep4.py', len(items)))
    json.dump(out, open(a.out, 'w'), ensure_ascii=False, indent=1)
    print('→', a.out)


if __name__ == '__main__':
    main()
