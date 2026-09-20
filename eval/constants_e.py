"""e (가장자리 번짐 행 수) — docs/constants_preregister.json «대상 상수» › e (순서 1, 라벨 없는 실물 관찰).

**폐기 — constants_preregister 수정 4 (c3fe03b) 로 e 측정을 없앴다. 사용 안 함.** 결과 파일 docs/constants_e.json 도
쓰지 않는다 (수정 4 전에 한 번 실행된 기록으로만 둔다). eval/refs.json · eval/run_all.py 에 넣지 않는다.

    python eval/constants_e.py --lines ~/.typo-mcp/unlabeled222 --prereg docs/constants_preregister.json \
        --out docs/constants_e.json

판: 라벨 없는 실물 222장 (브로크만 71 · 호프만 108 · 로제 16 · 루더 27), Surya 줄 (eval/group_score.py detect --order columns).
사전등록 계획: 창 = Surya 줄 상자 + PAD, 극성 맞춤, 섞임 공간 = 인코딩값 공간. 열마다 세로 밝기 프로파일에서 가장자리 =
배경 평탄 구간과 잉크 평탄 구간 (각각 연속 2행 이상) 사이의 전이. u = (v − 배경 수준) ÷ (잉크 수준 − 배경 수준),
배경 수준 = 창 밝기 중앙값, 잉크 수준 = «잉크 문턱 행과 같은 분위». 폭 = u 가 0.1 을 지나는 자리와 0.9 를 지나는 자리
사이의 행 수 (이웃 행 사이 선형 보간). 위 · 아래 가장자리를 모두 센다. e = ⌈모든 폭의 중앙값⌉.

실행 전에 정한 해석 (사전등록에 적혀 있지 않거나 가리키는 곳이 없어진 자리):
  - PAD = measure/region.py PAD, 창 자르기는 region.measure 와 같은 꼴 (정수 내림 뒤 ± PAD, 판 안으로).
  - 극성 맞춤 = measure/ink.polarity.
  - 잉크 수준: 최종 사전등록의 잉크 문턱 행 (합성 스윕) 에는 분위가 없다. e 행을 처음 쓴 커밋 486e6da 의 잉크 문턱 행 초안
    «ink = 창 밝기의 q 분위, q = f ÷ 2 — f = 창 밝기를 Otsu 두 무리로 나눈 어두운 무리의 화소 몫» 을 쓰고,
    섞임 공간 결정 (인코딩값 공간) 에 따라 Otsu 는 인코딩값 (0~255, 256칸) 에서 나눈다.
  - 평탄 구간: 배경 = u ≤ 0.1 인 행이 연속 2행 이상, 잉크 = u ≥ 0.9 인 행이 연속 2행 이상.
    열 안에서 이런 구간을 위에서부터 늘어놓아 배경 → 잉크 로 이웃하면 위 가장자리, 잉크 → 배경 이면 아래 가장자리.
  - 교차 자리: 위 가장자리는 배경 구간 끝 행부터 아래로 처음 u 가 0.1 을 넘는 자리, 잉크 구간 첫 행 앞에서 마지막으로 u 가
    0.9 에 이르는 자리. 아래 가장자리는 거꾸로. 폭 = 두 자리 사이 행 수 (선형 보간). 폭이 음수면 세지 않고 기록.
  - 잉크 수준 − 배경 수준 의 절댓값이 1 (인코딩값) 미만인 창은 세지 않고 기록.
결과 보고까지만 한다 — e 를 쓰는 식은 이 스크립트가 바꾸지 않는다.
"""
import argparse
import hashlib
import json
import math
import os
import sys
from collections import Counter, defaultdict
from multiprocessing import Pool

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'eval'))
import measure_corpus as MC        # noqa: E402  provenance
from measure import ink, region    # noqa: E402

LO, HI = 0.1, 0.9
RUN = 2
CORPUS = {'brockmann': '브로크만', 'corpus': '호프만', 'rose': '로제', 'ruder': '루더'}


def _sha(p):
    return hashlib.sha256(open(os.path.expanduser(p), 'rb').read()).hexdigest()


def otsu_dark_fraction(v):
    h = np.bincount(np.clip(np.rint(v), 0, 255).astype(int).ravel(), minlength=256).astype(float)
    n = h.sum(); x = np.arange(256)
    w0 = np.cumsum(h); w1 = n - w0
    m0 = np.cumsum(h * x); mt = m0[-1]
    with np.errstate(divide='ignore', invalid='ignore'):
        sb = (mt * w0 - m0 * n) ** 2 / (w0 * w1)
    sb[(w0 == 0) | (w1 == 0)] = -1
    t = int(np.argmax(sb))
    return w0[t] / n


def runs(flag):
    out = []; s = None
    for i, f in enumerate(flag):
        if f and s is None:
            s = i
        if not f and s is not None:
            if i - s >= RUN:
                out.append((s, i - 1))
            s = None
    if s is not None and len(flag) - s >= RUN:
        out.append((s, len(flag) - 1))
    return out


def cross(u, i, tau):
    return i + (tau - u[i]) / (u[i + 1] - u[i])


def column_edges(u):
    """[(종류, 폭)] 과 음수 폭 수."""
    R = sorted([(s, e, 'bg') for s, e in runs(u <= LO)] + [(s, e, 'ink') for s, e in runs(u >= HI)])
    out, neg = [], 0
    for (s0, e0, a), (s1, e1, b) in zip(R, R[1:]):
        if a == b:
            continue
        if a == 'bg':          # 위 가장자리: 배경 → 잉크
            i0 = next((i for i in range(e0, s1) if u[i] <= LO < u[i + 1]), None)
            i1 = next((i for i in range(s1 - 1, e0 - 1, -1) if u[i] < HI <= u[i + 1]), None)
            if i0 is None or i1 is None:
                continue
            w = cross(u, i1, HI) - cross(u, i0, LO); kind = '위'
        else:                  # 아래 가장자리: 잉크 → 배경
            i0 = next((i for i in range(e0, s1) if u[i] >= HI > u[i + 1]), None)
            i1 = next((i for i in range(s1 - 1, e0 - 1, -1) if u[i] > LO >= u[i + 1]), None)
            if i0 is None or i1 is None:
                continue
            w = cross(u, i1, LO) - cross(u, i0, HI); kind = '아래'
        if w < 0:
            neg += 1; continue
        out.append((kind, float(w)))
    return out, neg


def poster(job):
    it, lines = job
    g = np.asarray(Image.open(os.path.expanduser(it['image'])).convert('L')).astype(float)
    H, W = g.shape
    widths, c = [], Counter()
    for x1, y1, x2, y2 in lines:
        x1 = max(0, int(x1) - region.PAD); y1 = max(0, int(y1) - region.PAD)
        x2 = min(W, int(x2) + region.PAD); y2 = min(H, int(y2) + region.PAD)
        c['창'] += 1
        if x2 - x1 < 4 or y2 - y1 < 4:
            c['창_너무_작음'] += 1; continue
        sub = ink.polarity(g[y1:y2, x1:x2])
        bg = float(np.median(sub))
        q = otsu_dark_fraction(sub) / 2
        lvl = float(np.quantile(sub, q))
        if abs(lvl - bg) < 1:
            c['창_대비_없음'] += 1; continue
        u = (sub - bg) / (lvl - bg)
        for j in range(u.shape[1]):
            es, neg = column_edges(u[:, j])
            c['음수_폭'] += neg
            widths += [(k, w) for k, w in es]
    return it['corpus'], it['key'], widths, dict(c)


def stats(v):
    if not v:
        return dict(n=0)
    return dict(n=len(v), 중앙값=round(float(np.median(v)), 4), 사분위=[round(float(np.percentile(v, 25)), 4), round(float(np.percentile(v, 75)), 4)])


def main(argv=None):
    ap = argparse.ArgumentParser(description='e 측정 (constants_preregister 순서 1)')
    ap.add_argument('--lines', required=True, help='줄 폴더 (manifest.json · lines.json)')
    ap.add_argument('--prereg', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--workers', type=int, default=8)
    a = ap.parse_args(argv)
    LW = os.path.expanduser(a.lines)
    M = json.load(open(os.path.join(LW, 'manifest.json'))); LL = json.load(open(os.path.join(LW, 'lines.json')))
    jobs = []
    for it in M['items']:
        k = f"{it['seed']:03d}"
        if _sha(os.path.expanduser(it['image'])) != it['image_sha256'] or LL['lines'][k]['sha256'] != it['image_sha256']:
            sys.exit(f'manifest 와 다른 이미지 또는 줄: {it["image"]}')
        jobs.append((it, LL['lines'][k]['lines']))
    with Pool(a.workers) as pool:
        res = pool.map(poster, jobs, chunksize=1)
    allw, byc, byk, n_post, cnt = [], defaultdict(list), defaultdict(list), defaultdict(int), Counter()
    posters_with = defaultdict(int)
    for corp, key, ws, c in res:
        cnt.update(c); n_post[corp] += 1; posters_with[corp] += bool(ws)
        for kind, w in ws:
            allw.append(w); byc[corp].append(w); byk[kind].append(w)
    med = float(np.median(allw))
    out = dict(
        무엇='e (가장자리 번짐 행 수) — 라벨 없는 실물 222장, constants_preregister 순서 1. 결과 보고까지만',
        사전등록=a.prereg, 사전등록_sha256=_sha(a.prereg),
        줄=dict(폴더=a.lines, manifest_sha256=_sha(os.path.join(LW, 'manifest.json')), lines_sha256=_sha(os.path.join(LW, 'lines.json')),
               provenance=LL.get('provenance'), 환경=M.get('환경')),
        정의=dict(창=f'Surya 줄 상자 + PAD {region.PAD} (region.measure 와 같은 자르기)', 극성='measure/ink.polarity', 섞임_공간='인코딩값 공간',
                배경_수준='창 밝기 중앙값 (극성 맞춘 뒤)',
                잉크_수준='창 밝기의 q 분위, q = f ÷ 2, f = 창 인코딩값 Otsu (256칸) 어두운 무리 화소 몫 — 최종 사전등록에 분위가 없어 e 행을 처음 쓴 커밋 486e6da 의 잉크 문턱 행 초안을 따름',
                평탄='배경 u ≤ 0.1 · 잉크 u ≥ 0.9 가 연속 2행 이상', 폭='u 0.1 교차와 0.9 교차 사이 행 수 (선형 보간), 위 · 아래 가장자리',
                e='⌈모든 폭의 중앙값⌉'),
        판=sum(n_post.values()), 가장자리_있는_판=sum(posters_with.values()), 가장자리=len(allw), 창_기록=dict(cnt),
        전체=dict(**stats(allw), 판=sum(n_post.values())),
        위아래=dict((k, stats(v)) for k, v in sorted(byk.items())),
        작가별={CORPUS.get(c, c): dict(**stats(byc[c]), 판=n_post[c], 가장자리_있는_판=posters_with[c]) for c in CORPUS if c in n_post},
        e=int(math.ceil(med)),
        provenance=MC.provenance('eval/constants_e.py', sum(n_post.values())))
    json.dump(out, open(a.out, 'w'), ensure_ascii=False, indent=1)
    print('e =', out['e'], '· 중앙값', round(med, 4), '· 가장자리', len(allw), '→', a.out)


if __name__ == '__main__':
    main()
