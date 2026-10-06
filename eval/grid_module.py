"""가로 정렬 위치가 한 단위 u 의 정수배 간격으로 놓이는지 — 사전등록 docs/grid_module_preregister.json 그대로.

    python eval/grid_module.py --cache ~/.typo-mcp/brockmann.json \
        --posters docs/labeling/posters_for_labelers.json \
        --guides labels/guides/guides_labelerA_20260917-2016.json labels/guides/guides_labelerB_20260916-0201.json \
        --consensus docs/brockmann_consensus_refs.json --prereg docs/grid_module_preregister.json \
        --out docs/grid_module_result.json

사전등록이 정한 것만 구현한다. 새 지표를 더하지 않고 문턱을 두지 않는다.

  정렬 위치  블록 왼쪽 끝 x1 ÷ 판 폭 W 를 explore_typography_rules2.clusters(·, 0.01) 로 묶고
             묶음마다 중앙값 (결정 1). 단위는 판 폭 몫 (0~1).
  맞춤 점수  (u, x0) 를 훑어 «위치가 x0 + k·u 에서 허용 0.15·u 안에 드는 몫» 의 최댓값.
             u 는 0.07~0.50 간격 0.001, x0 는 관측 위치 각각 (결정 2).
  대조       위치 개수 m 을 유지하고 판별 최소~최대에서 균등 재추출. 두 값이 0.01 보다
             가까우면 다시 뽑는다. 2,000 벌, 대조에도 같은 (u, x0) 고르기 (결정 3).
  판정       판별 점수 중앙값이 대조 95% 구간 밖이면 «규칙 있음» (결정 4).
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
import brockmann_stage2_score as S2                 # noqa: E402  kept · refs_of · load_labelers
import explore_typography_rules2 as T2              # noqa: E402  clusters (C1 과 같은 군집 규칙)

THR = 0.01                         # 결정 1 — C1 의 군집 문턱 (판 폭 몫)
MIN_POS = 4                        # 결정 1 — 주 결과로 쓰는 위치 개수 바닥
ALSO_MIN = (3, 5)                  # 결정 1 — 보조
US = np.round(np.arange(0.07, 0.5 + 1e-9, 0.001), 3)   # 결정 2 — u 범위
TOL_U = 0.15                       # 결정 2 — 허용 = 0.15 × u
TRIALS = 2000                      # 결정 3
SEED = 20261006                    # 결정 3
REDRAW = 1000                      # 결정 3 — 최소 간격 재추출 한도


def _sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def _r(x, n=4):
    return None if x is None else round(float(x), n)


def positions(blocks, W):
    """결정 1 — C1 과 같은 군집 규칙. 판 폭 몫으로 돌려준다."""
    if not blocks:
        return []
    v = [b['x1'] / float(W) for b in blocks]
    return [float(np.median(c)) for c in T2.clusters(v, THR)]


def best_fit(pos):
    """결정 2 — (u, x0) 를 훑어 가장 높은 몫. (점수, 최적 u).

    u 와 x0 를 한꺼번에 센다. 동점이면 작은 u, 그 다음 앞선 x0 — 사전등록의 훑는 차례와 같다.
    """
    p = np.asarray(pos, dtype=float)
    u = US[:, None, None]                              # (u, x0, 위치)
    d = (p[None, None, :] - p[None, :, None]) / u      # x0 는 관측 위치 각각
    s = (np.abs(d - np.round(d)) * u <= TOL_U * u).mean(axis=2)
    i = int(np.argmax(s))                              # 평평하면 u 오름차순의 첫 자리
    return float(s.flat[i]), float(US[i // s.shape[1]])


def draw(m, lo, hi, rng):
    """결정 3 — 개수 m 유지, [lo, hi] 균등, 두 값이 THR 보다 가까우면 다시. (위치, 재추출 횟수)."""
    for k in range(REDRAW):
        v = np.sort(rng.uniform(lo, hi, m))
        if m < 2 or np.min(np.diff(v)) >= THR:
            return v, k
    return v, REDRAW


def summarize(P, rng, min_pos=MIN_POS):
    """P = [(key, 위치 목록)]. 사전등록 결정 2 · 3 · 4."""
    use = [(k, np.asarray(v, dtype=float)) for k, v in P if len(v) >= min_pos]
    if not use:
        return None
    real, us = [], []
    for _k, v in use:
        s, u = best_fit(v)
        real.append(s); us.append(u)
    med = float(np.median(real))
    spans = [(float(v.min()), float(v.max()), len(v)) for _k, v in use]
    meds, redraw = [], 0
    for _ in range(TRIALS):
        cur = []
        for lo, hi, m in spans:
            v, k = draw(m, lo, hi, rng); redraw += k
            cur.append(best_fit(v)[0])
        meds.append(float(np.median(cur)))
    lo_, hi_ = float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5))
    return dict(
        판=len(P), 쓴_판=len(use), 위치_개수=dict(sorted(collections.Counter(len(v) for _k, v in P).items())),
        점수_중앙=_r(med), 점수_분포=dict(p25=_r(np.percentile(real, 25)), p75=_r(np.percentile(real, 75)),
                                    최소=_r(min(real)), 최대=_r(max(real))),
        최적u_중앙=_r(np.median(us), 3), 최적u_도수=dict(sorted(collections.Counter(np.round(us, 2)).items())),
        대조=dict(평균=_r(np.mean(meds)), 구간=[_r(lo_), _r(hi_)]),
        판정=('규칙 있음' if (med < lo_ or med > hi_) else '구분되지 않음'),
        방향=('구간보다 높다' if med > hi_ else ('구간보다 낮다' if med < lo_ else '구간 안')),
        재추출_합=int(redraw))


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

    def meas(k):
        return positions(T2.blocks_pipeline(raw[k]), raw[k]['size'][0])

    def lab(ps):
        out = []
        for o in sorted(ps):
            if o not in ck or ck[o] not in raw or not S2.kept(ps[o]):
                continue
            R, _X = S2.refs_of(ps[o], 'main')
            bl = [dict(x1=float(b['box'][0])) for b in R]
            out.append((ck[o], positions(bl, raw[ck[o]]['size'][0])))
        return out

    sets = {'측정_브로크만_123': [(k, meas(k)) for k in sorted(raw) if T2.blocks_pipeline(raw[k])]}
    sets['라벨_라벨러A_50'] = lab(labs['라벨러A']['posters'])
    sets['라벨_라벨러B_50'] = lab(labs['라벨러B']['posters'])
    sets['라벨_합의_50 (보조)'] = lab(cons)

    res = dict(
        what=f'사전등록 {a.prereg} 의 결과', 사전등록_sha256=_sha(a.prereg),
        무엇='가로 정렬 위치가 한 단위 u 의 정수배 간격으로 놓이는지 · 개수를 유지한 무작위 대조',
        정의=dict(정렬위치='블록 x1 ÷ 판 폭 을 clusters(·, 0.01) 로 묶고 묶음 중앙값 (C1 과 같은 규칙)',
                쓴_판=f'정렬 위치 {MIN_POS}개 이상', u=f'{US[0]}~{US[-1]} 간격 0.001 (판 폭 몫)',
                허용=f'{TOL_U} × u', 시작점='관측된 정렬 위치 각각',
                판별통계='판별 점수의 중앙값', 대조='위치 개수 유지 · 판별 최소~최대 균등 · 최소 간격 0.01',
                시행=TRIALS, 씨앗=SEED, 판정='중앙값이 대조 95% 구간 밖이면 «규칙 있음»'),
        입력=dict(캐시=dict(파일='~' + os.path.expanduser(a.cache)[len(os.path.expanduser('~')):],
                         commit=cache.get('provenance', {}).get('commit'), n=cache.get('provenance', {}).get('n')),
                라벨=[dict(파일=g, sha256=_sha(g)) for g in a.guides],
                합의=dict(파일=a.consensus, sha256=_sha(a.consensus))),
        대상={})
    for name, P in sets.items():
        rng = np.random.default_rng(SEED)
        print(f'  {name} · 판 {len(P)}', flush=True)
        res['대상'][name] = dict(주_결과=summarize(P, rng))
        for mp in ALSO_MIN:
            rng2 = np.random.default_rng(SEED)
            res['대상'][name][f'보조_위치{mp}개이상'] = summarize(P, rng2, min_pos=mp)
    json.dump(res, open(a.out, 'w'), ensure_ascii=False, indent=1)
    print('→', a.out)


if __name__ == '__main__':
    main()
