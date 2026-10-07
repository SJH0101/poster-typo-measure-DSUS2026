"""탐색용 · 논문 수치 아님 · **사전등록 없음** — 신실라(2021) 대조 포스터의 블록 모서리가
60등분 칸 선에 얼마나 붙는지, 대조 둘로 견준다.

    python eval/sinsilla_grid.py --caches 규칙기반=~/.typo-mcp/brockmann.json \
        VLM_회차1=~/.typo-mcp/vlm-pass1/brockmann.json VLM_회차2=~/.typo-mcp/vlm-pass2/brockmann.json \
        --posters docs/labeling/posters_for_labelers.json \
        --guides labels/guides/guides_labelerA_20260917-2016.json labels/guides/guides_labelerB_20260916-0201.json \
        --out docs/sinsilla_grid_result.json

**이 분석은 결과를 본 뒤에 만들었다 — 사전등록이 없다.** 23.6 절의 값을 보고 «대조를 하나 더
두면 무엇이 보이나» 를 물은 것이므로, 판정하는 수로 쓰지 않고 표로만 적는다.

  칸      신실라(2021)의 60×60 — 세로 칸 y = i·H/60, 가로 칸 x = i·W/60.
  거리    모서리 좌표와 가장 가까운 칸 선의 거리, 칸 단위 (|v/step − round(v/step)|).
  통계    블록 네 모서리를 모두 모은 거리의 **중앙값**.
  대조 A  블록 크기를 유지하고 **블록마다 따로** 왼쪽 위 좌표를 균등 재추출
          (eval/grid_ndiv.py 의 대조 (ii) 와 같은 방식, 씨앗 20261005). 줄 맞춘 구조가 흩어진다.
  대조 B  블록들의 **상대 배치를 그대로 두고** 배치 전체를 가로 · 세로로 각각 [0, 1칸) 에서
          균등하게 평행 이동 (씨앗 20261007). 구조는 지키고 «칸에 대한 위상» 만 무작위로 둔다.
  백분위  실제 값이 대조 B 2,000벌의 중앙값 분포에서 몇 백분위인지 — 분포에서 실제 값 이하인 벌의 몫.
"""
import argparse
import hashlib
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
import brockmann_stage2_score as S2          # noqa: E402  load_labelers · kept · refs_of

KEY = 'Musica_Viva__1960_Musica viva - Donnerstag, 10. März 1960 - Tonhalle Grosser S.jpg'
N = 60                 # 신실라(2021) 의 60×60
TRIALS = 2000
SEED_A = 20261005      # 대조 A — grid_ndiv 와 같은 씨앗
SEED_B = 20261007      # 대조 B — 이 분석에서 처음 쓰는 씨앗
MARGIN = 0.5           # «오른쪽 단 범위 안» 판정의 여유 (칸)


def _sha(p):
    return hashlib.sha256(open(os.path.expanduser(p), 'rb').read()).hexdigest()


def _r(x, n=4):
    return None if x is None else round(float(x), n)


def dist(v, L):
    """칸 단위 거리."""
    s = L / N
    return abs(v / s - round(v / s))


def dists(boxes, W, H):
    out = []
    for b in boxes:
        out += [dist(b[0], W), dist(b[2], W), dist(b[1], H), dist(b[3], H)]
    return out


def ctrl_a(boxes, W, H, rng):
    """대조 A — 블록 크기 유지, 블록마다 따로 균등 재추출."""
    meds = []
    for _ in range(TRIALS):
        d = []
        for b in boxes:
            w, h = b[2] - b[0], b[3] - b[1]
            x1 = float(np.floor(rng.uniform(0, max(W - w, 0) + 1e-9)))
            y1 = float(np.floor(rng.uniform(0, max(H - h, 0) + 1e-9)))
            d += [dist(x1, W), dist(x1 + w, W), dist(y1, H), dist(y1 + h, H)]
        meds.append(float(np.median(d)))
    return np.asarray(meds)


def ctrl_b(boxes, W, H, rng):
    """대조 B — 상대 배치 유지, 전체를 [0, 1칸) 안에서 평행 이동."""
    sx, sy = W / N, H / N
    meds = []
    for _ in range(TRIALS):
        dx, dy = rng.uniform(0, sx), rng.uniform(0, sy)
        d = dists([(b[0] + dx, b[1] + dy, b[2] + dx, b[3] + dy) for b in boxes], W, H)
        meds.append(float(np.median(d)))
    return np.asarray(meds)


def ci(a):
    return dict(평균=_r(a.mean()), 구간=[_r(np.percentile(a, 2.5)), _r(np.percentile(a, 97.5))])


def main():
    ap = argparse.ArgumentParser()
    for k in ('--posters', '--out'):
        ap.add_argument(k, required=True)
    ap.add_argument('--caches', nargs='+', required=True)
    ap.add_argument('--guides', nargs='+', required=True)
    a = ap.parse_args()

    caches = {}
    for s in a.caches:
        k, v = s.split('=', 1)
        caches[k] = (os.path.expanduser(v), json.load(open(os.path.expanduser(v)))['raw'])
    base_raw = caches['규칙기반'][1]
    W, H = base_raw[KEY]['size']
    sx, sy = W / N, H / N
    # 신실라 «오른쪽 단» 의 자리 = 규칙 기반 가장 큰 블록
    col = max(base_raw[KEY]['blocks'], key=lambda b: (b['x2'] - b['x1']) * (b['y2'] - b['y1']))
    L0, R0 = col['x1'] / sx, col['x2'] / sx

    sets = {}
    for nm, (_p, raw) in caches.items():
        sets[nm] = [(b['x1'], b['y1'], b['x2'], b['y2']) for b in raw[KEY]['blocks']]
    labs = S2.load_labelers(a.guides)
    Pl = {it['order']: it for it in json.load(open(a.posters))['main']}
    order = next(o for o, it in Pl.items() if f"{it['folder']}__{it['file']}" == KEY)
    for nm in S2.LABELERS:
        p = labs[nm]['posters'].get(order)
        if p is not None and S2.kept(p):
            sets[f'라벨 {nm}'] = [tuple(b['box']) for b in S2.refs_of(p, 'main')[0]]

    out = dict(
        what='탐색용 · 논문 수치 아님 · **사전등록 없음** (결과를 본 뒤 만든 분석)',
        무엇='신실라(2021) 대조 포스터의 블록 모서리가 60등분 칸 선에 붙는 정도 — 대조 둘로 견준다',
        사전등록='없다. 23.6 절의 값을 본 뒤 «대조를 하나 더 두면 무엇이 보이나» 를 물은 것이므로 판정하는 수로 쓰지 않는다',
        판=KEY, 크기=[W, H], 칸=dict(N=N, 가로=_r(sx, 2), 세로=_r(sy, 2)),
        오른쪽_단=dict(자리='규칙 기반 가장 큰 블록의 칸 x 범위', 칸_x=[_r(L0, 2), _r(R0, 2)],
                   폭_칸=_r(R0 - L0, 2), 여유=MARGIN),
        정의=dict(거리='모서리와 가장 가까운 칸 선의 거리 (칸 단위)', 통계='네 모서리를 모두 모은 거리의 중앙값',
                대조_A=f'블록 크기 유지 · 블록마다 따로 균등 재추출 (grid_ndiv 의 (ii) 와 같은 방식) · 씨앗 {SEED_A}',
                대조_B=f'상대 배치 유지 · 배치 전체를 가로 · 세로로 각각 [0, 1칸) 평행 이동 · 씨앗 {SEED_B}',
                백분위='대조 B 분포에서 실제 값 이하인 벌의 몫', 시행=TRIALS),
        입력=dict(캐시={k: dict(파일='~' + v[0][len(os.path.expanduser('~')):], sha256=None) for k, v in caches.items()},
                라벨=[dict(파일=g, sha256=_sha(g)) for g in a.guides]),
        대상={})
    for nm, boxes in sets.items():
        bl = sorted(boxes, key=lambda b: (b[1], b[0]))
        rows = []
        for b in bl:
            x1c, x2c = b[0] / sx, b[2] / sx
            d = dict(x1=_r(dist(b[0], W), 3), y1=_r(dist(b[1], H), 3),
                     x2=_r(dist(b[2], W), 3), y2=_r(dist(b[3], H), 3))
            rows.append(dict(상자=[_r(v, 1) for v in b],
                             칸=[_r(b[0] / sx, 2), _r(b[1] / sy, 2), _r(b[2] / sx, 2), _r(b[3] / sy, 2)],
                             칸수=[int(round((b[2] - b[0]) / sx)), int(round((b[3] - b[1]) / sy))],
                             거리=d, 거리_최대=_r(max(d.values()), 3),
                             오른쪽_단_안=bool(x1c >= L0 - MARGIN and x2c <= R0 + MARGIN)))
        dd = dists(bl, W, H)
        real = float(np.median(dd))
        A = ctrl_a(bl, W, H, np.random.default_rng(SEED_A))
        Bc = ctrl_b(bl, W, H, np.random.default_rng(SEED_B))
        pct = float(np.mean(Bc <= real))
        cA, cB = ci(A), ci(Bc)
        out['대상'][nm] = dict(
            블록=len(bl), 모서리=len(dd), 거리_중앙=_r(real), 거리_최대=_r(max(dd), 3),
            오른쪽_단_안_블록=sum(r['오른쪽_단_안'] for r in rows),
            대조_A=dict(**cA, 판정=('구간 밖' if real < cA['구간'][0] or real > cA['구간'][1] else '구간 안')),
            대조_B=dict(**cB, 백분위=_r(pct), 판정=('구간 밖' if real < cB['구간'][0] or real > cB['구간'][1] else '구간 안')),
            블록별=rows)
        print(f'  {nm:12} 블록 {len(bl)} · 중앙 {real:.4f} · A {cA["구간"]} · B {cB["구간"]} · 백분위 {pct:.4f}')
    json.dump(out, open(a.out, 'w'), ensure_ascii=False, indent=1)
    print('→', a.out)


if __name__ == '__main__':
    main()
