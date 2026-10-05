"""판을 N 등분한 격자와 블록 모서리의 일치율 — 사전등록 docs/grid_ndiv_preregister.json 그대로.

    python eval/grid_ndiv.py --cache ~/.typo-mcp/brockmann.json --posters docs/labeling/posters_for_labelers.json \
        --guides labels/guides/guides_labelerA_20260917-2016.json labels/guides/guides_labelerB_20260916-0201.json \
        --consensus docs/brockmann_consensus_refs.json --prereg docs/grid_ndiv_preregister.json \
        --out docs/grid_ndiv_result.json

사전등록이 정한 것만 구현한다. 새 지표를 더하지 않고 문턱을 두지 않는다.

  모서리   블록 상자의 네 변. 세로 칸 선에 y1 · y2, 가로 칸 선에 x1 · x2 를 견준다 (결정 3).
  칸 선     세로 y = i·H/N, 가로 x = i·W/N, i = 0…N — 판 테두리를 넣는다 (결정 5).
  맞음     가장 가까운 칸 선과의 거리 ≤ 0.15 × (L/N) (결정 4 · 5).
  대조     (i) 모서리를 U[0, L] 에서 다시 뽑기 · (ii) 블록 크기를 유지하고 위치만 균등 재배치 (주 대조, 결정 6).
  최적 N   판마다 가장 높은 N (동점이면 작은 N) 을 골라 그 일치율의 중앙값. 대조에도 같은 절차 (결정 7).
"""
import argparse
import collections
import hashlib
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
import brockmann_stage2_score as S2        # noqa: E402  load_labelers · load_consensus · kept · refs_of

NS = list(range(20, 141))          # 결정 1 — N 간격 1
TOL = 0.15                         # 결정 4 — 칸 폭의 0.15
TRIALS = 2000                      # 결정 6
SEED = 20261005                    # 결정 6
SINSILLA = '1960_Musica viva - Donnerstag, 10. März 1960 - Tonhalle Grosser S.jpg'   # 결정 9


def _sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def _r(x, n=4):
    return None if x is None else round(float(x), n)


def hit_share(vals, L, n):
    """모서리 좌표 vals 가 L 을 n 등분한 칸 선에 ±TOL 칸 안에 드는 몫."""
    if not len(vals):
        return None
    step = L / n
    d = np.abs(vals / step - np.round(vals / step))      # 칸 단위 거리
    return float(np.mean(d <= TOL))


def poster_edges(blocks):
    """(세로 칸 선에 견줄 값, 가로 칸 선에 견줄 값) = (y1·y2, x1·x2)."""
    v = np.array([v for b in blocks for v in (b['y1'], b['y2'])], dtype=float)
    h = np.array([v for b in blocks for v in (b['x1'], b['x2'])], dtype=float)
    return v, h


def curve(posters, key='실제'):
    """N 마다 판을 합친 일치율 (모서리를 모두 모아 센다) 과 판별 일치율."""
    out, per = {}, collections.defaultdict(dict)
    for n in NS:
        hv = hh = tv = th = 0
        for p in posters:
            v, h = p['edges']
            for vals, L, cnt in ((v, p['H'], 'v'), (h, p['W'], 'h')):
                if not len(vals):
                    continue
                step = L / n
                d = np.abs(vals / step - np.round(vals / step))
                k = int(np.sum(d <= TOL))
                if cnt == 'v':
                    hv += k; tv += len(vals)
                else:
                    hh += k; th += len(vals)
            per[p['key']][n] = _share(p, n)
        out[n] = dict(세로=_r(hv / tv) if tv else None, 가로=_r(hh / th) if th else None,
                      합침=_r((hv + hh) / (tv + th)) if (tv + th) else None)
    return out, per


def _share(p, n):
    v, h = p['edges']
    hit = tot = 0
    for vals, L in ((v, p['H']), (h, p['W'])):
        if not len(vals):
            continue
        step = L / n
        d = np.abs(vals / step - np.round(vals / step))
        hit += int(np.sum(d <= TOL)); tot += len(vals)
    return (hit / tot) if tot else None


def best_n(p):
    """판 하나의 최적 N (동점이면 작은 N) 과 그 일치율."""
    best, bv = None, -1.0
    for n in NS:
        s = _share(p, n)
        if s is not None and s > bv + 1e-12:
            best, bv = n, s
    return best, (bv if best is not None else None)


def rand_posters(posters, rng, mode):
    """대조 한 벌. (i) 모서리 균등 · (ii) 블록 크기 유지하고 위치만 균등."""
    out = []
    for p in posters:
        W, H = p['W'], p['H']
        if mode == 'i':
            nb = len(p['blocks'])
            v = rng.uniform(0, H, 2 * nb); h = rng.uniform(0, W, 2 * nb)
        else:
            v, h = [], []
            for b in p['blocks']:
                w, ht = b['x2'] - b['x1'], b['y2'] - b['y1']
                x1 = float(np.floor(rng.uniform(0, max(W - w, 0) + 1e-9)))
                y1 = float(np.floor(rng.uniform(0, max(H - ht, 0) + 1e-9)))
                v += [y1, y1 + ht]; h += [x1, x1 + w]
            v = np.array(v, dtype=float); h = np.array(h, dtype=float)
        out.append(dict(key=p['key'], W=W, H=H, blocks=p['blocks'], edges=(np.asarray(v), np.asarray(h))))
    return out


def control(posters, mode, rng):
    """대조 TRIALS 벌 — N 별 합침 일치율과 최적 N 중앙값의 분포."""
    curves = {n: [] for n in NS}
    bests = []
    for _ in range(TRIALS):
        R = rand_posters(posters, rng, mode)
        hv = {n: [0, 0] for n in NS}
        for p in R:
            for n in NS:
                v, h = p['edges']
                for vals, L in ((v, p['H']), (h, p['W'])):
                    if not len(vals):
                        continue
                    step = L / n
                    d = np.abs(vals / step - np.round(vals / step))
                    hv[n][0] += int(np.sum(d <= TOL)); hv[n][1] += len(vals)
        for n in NS:
            curves[n].append(hv[n][0] / hv[n][1] if hv[n][1] else np.nan)
        bv = [best_n(p)[1] for p in R]
        bests.append(float(np.median([x for x in bv if x is not None])))
    q = lambda a: dict(평균=_r(np.mean(a)), 구간=[_r(np.percentile(a, 2.5)), _r(np.percentile(a, 97.5))])
    return {n: q(curves[n]) for n in NS}, q(bests)


def build(blocks_of, size_of, keys):
    out = []
    for k in keys:
        b = blocks_of(k)
        if not b:
            continue
        W, H = size_of(k)
        out.append(dict(key=k, W=float(W), H=float(H), blocks=b, edges=poster_edges(b)))
    return out


def summarize(posters, rng):
    cur, per = curve(posters)
    bests = {p['key']: best_n(p) for p in posters}
    bv = [v for _n, v in bests.values() if v is not None]
    ns = [n for n, _v in bests.values() if n is not None]
    ci, cii = control(posters, 'i', rng), control(posters, 'ii', rng)
    real_b = float(np.median(bv)) if bv else None
    lo, hi = cii[1]['구간']
    return dict(
        판=len(posters), 블록=sum(len(p['blocks']) for p in posters),
        모서리=int(sum(len(p['edges'][0]) + len(p['edges'][1]) for p in posters)),
        N별=dict(실제={str(n): cur[n] for n in NS},
               대조_i={str(n): ci[0][n] for n in NS}, 대조_ii={str(n): cii[0][n] for n in NS}),
        N별_요약=dict(실제_합침_최소=_r(min(cur[n]['합침'] for n in NS)), 실제_합침_최대=_r(max(cur[n]['합침'] for n in NS)),
                   대조_ii_평균_최소=_r(min(cii[0][n]['평균'] for n in NS)), 대조_ii_평균_최대=_r(max(cii[0][n]['평균'] for n in NS)),
                   구간_밖_N=[n for n in NS if cur[n]['합침'] is not None
                            and not (cii[0][n]['구간'][0] <= cur[n]['합침'] <= cii[0][n]['구간'][1])]),
        최적N=dict(일치율_중앙=_r(real_b), 대조_i=ci[1], 대조_ii=cii[1],
                 판정=('우연 이상' if real_b is not None and not (lo <= real_b <= hi) else '구분되지 않음'),
                 N_도수=dict(sorted(collections.Counter(ns).items())),
                 N_중앙=_r(np.median(ns)) if ns else None,
                 N_60_5이내_판=int(sum(1 for n in ns if 55 <= n <= 65))),
        판별={k: dict(최적N=v[0], 일치율=_r(v[1]), N60=_r(per[k][60]), N30=_r(per[k][30])) for k, v in bests.items()})


def sinsilla(sets, file_name):
    """결정 9 — 신실라 대조. 60 등분 칸으로 환산한 칸 수와 모서리 어긋남."""
    out = {}
    for name, posters in sets.items():
        p = next((q for q in posters if q['key'].endswith(file_name) or file_name in q['key']), None)
        if p is None:
            out[name] = '그 판이 이 대상에 없다'; continue
        W, H = p['W'], p['H']
        sx, sy = W / 60.0, H / 60.0
        rows, dv, dh = [], [], []
        for b in sorted(p['blocks'], key=lambda b: (b['y1'], b['x1'])):
            cx1, cx2 = b['x1'] / sx, b['x2'] / sx
            cy1, cy2 = b['y1'] / sy, b['y2'] / sy
            rows.append(dict(상자=[_r(b['x1'], 1), _r(b['y1'], 1), _r(b['x2'], 1), _r(b['y2'], 1)],
                             칸=[_r(cx1, 2), _r(cy1, 2), _r(cx2, 2), _r(cy2, 2)],
                             칸수_반올림=[int(round(cx2 - cx1)), int(round(cy2 - cy1))]))
            dh += [abs(v - round(v)) for v in (cx1, cx2)]
            dv += [abs(v - round(v)) for v in (cy1, cy2)]
            b['_칸'] = rows[-1]['칸수_반올림']
        d = dv + dh
        leads = [float(np.median(np.diff(sorted(b['bases'])))) for b in p['blocks']
                 if b.get('bases') and len(b['bases']) >= 2]
        out[name] = dict(판=p['key'], 크기=[_r(W, 1), _r(H, 1)], 블록=len(p['blocks']),
                         칸_높이=_r(sy, 2), 칸_폭=_r(sx, 2),
                         모서리_어긋남_칸=dict(중앙=_r(np.median(d)), 최대=_r(max(d)), p90=_r(np.percentile(d, 90))),
                         모서리_어긋남_px_세로=dict(중앙=_r(np.median(dv) * sy), 최대=_r(max(dv) * sy)) if dv else None,
                         블록안_줄간격_중앙=_r(np.median(leads)) if leads else None,
                         블록별=rows)
    return out


def main():
    ap = argparse.ArgumentParser()
    for k in ('--cache', '--posters', '--consensus', '--prereg', '--out'):
        ap.add_argument(k, required=True)
    ap.add_argument('--guides', nargs='+', required=True)
    a = ap.parse_args()
    cache = json.load(open(os.path.expanduser(a.cache)))
    raw = cache['raw']
    Pl = {it['order']: it for it in json.load(open(a.posters))['main']}
    labs = S2.load_labelers(a.guides)
    cons = S2.load_consensus(a.consensus)
    ck = {o: f"{it['folder']}__{it['file']}" for o, it in Pl.items()}
    size_cache = lambda k: raw[k]['size']

    def blocks_meas(k):
        return [dict(x1=float(b['x1']), y1=float(b['y1']), x2=float(b['x2']), y2=float(b['y2']),
                     bases=sorted(float(v) for v in b['bases'])) for b in (raw[k].get('blocks') or [])]

    def blocks_lab(ps):
        def f(o):
            p = ps.get(o)
            if p is None or not S2.kept(p):
                return []
            R, _X = S2.refs_of(p, 'main')
            return [dict(x1=float(b['box'][0]), y1=float(b['box'][1]), x2=float(b['box'][2]), y2=float(b['box'][3]),
                         bases=sorted(float(l['base']) for l in b['lines'] if S2._num(l['base'])))
                    for b in R]
        return f

    sets = {}
    sets['측정_브로크만_123'] = build(blocks_meas, size_cache, sorted(raw))
    for name, ps in (('라벨_라벨러A_50', labs['라벨러A']['posters']), ('라벨_라벨러B_50', labs['라벨러B']['posters']),
                     ('라벨_합의_50 (보조)', cons)):
        keys = [o for o in sorted(ps) if o in ck and ck[o] in raw]
        bl = blocks_lab(ps)
        sets[name] = build(lambda o, bl=bl: bl(o), lambda o: size_cache(ck[o]), keys)
        for p in sets[name]:
            p['key'] = ck[p['key']]

    res = dict(what=f'사전등록 {a.prereg} 의 결과', 사전등록_sha256=_sha(a.prereg),
               무엇='판을 N 등분한 격자와 블록 모서리의 일치율 (N = 20~140) · 무작위 대조 둘',
               정의=dict(N=f'{NS[0]}~{NS[-1]} (간격 1)', 허용=f'칸 폭의 {TOL}', 모서리='블록 상자 네 변 (세로 칸 선에 y1·y2, 가로 칸 선에 x1·x2)',
                       칸선='i·L/N, i = 0…N (판 테두리 포함)', 대조_i='모서리를 U[0, L] 에서 다시 뽑는다',
                       대조_ii='블록 크기를 유지하고 왼쪽 위 좌표만 균등 재배치 (주 대조)',
                       시행=TRIALS, 씨앗=SEED, 최적N='판마다 가장 높은 N (동점이면 작은 N), 대조에도 같은 절차',
                       판정='실제 값이 대조 (ii) 95% 구간 밖일 때만 «우연 이상»'),
               입력=dict(캐시=dict(파일='~' + os.path.expanduser(a.cache)[len(os.path.expanduser('~')):],
                                commit=cache.get('provenance', {}).get('commit'), n=cache.get('provenance', {}).get('n')),
                       라벨=[dict(파일=g, sha256=_sha(g)) for g in a.guides],
                       합의=dict(파일=a.consensus, sha256=_sha(a.consensus))),
               대상={})
    for name, posters in sets.items():
        rng = np.random.default_rng(SEED)
        print(f'  {name} · 판 {len(posters)}', flush=True)
        res['대상'][name] = summarize(posters, rng)
    res['신실라_2021_대조'] = sinsilla(sets, SINSILLA)
    json.dump(res, open(a.out, 'w'), ensure_ascii=False, indent=1)
    print('→', a.out)


if __name__ == '__main__':
    main()
