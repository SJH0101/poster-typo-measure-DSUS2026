"""탐색용 · 논문 수치 아님 — VLM 에 주는 «입력 형태» 에 따라 묶기가 어떻게 달라지나.

같은 판 30장(깨끗한 세트에서 층별로 고르게)에 세 조건으로 묻는다.

    (a) 원본 이미지만 — 블록 영역을 정규화 좌표로 직접 답한다 (딱지 없음)
    (b) 원본 이미지 + Surya 줄 상자 좌표 목록(텍스트) — 어느 줄끼리 묶이는지 번호로 답한다
    (c) 현행 — Surya 줄에 번호 딱지를 붙인 2배 이미지(SoM) + docs/clean_vlm_prompt.md

채점은 현행과 같다: 블록 IoU ≥ 0.5 1:1 매칭의 F1 · 과병합 · 과분할 (eval/group_score · eval/detector_score).
(a) 는 VLM 이 답한 좌표를 그대로 상자로 쓴다. 참값은 c_in 쌍을 합친 정의 (clean 본 수치와 같다).

이 결과로 상수 · 파이프라인 · 사전등록을 고치지 않는다. VLM 응답은 사람 상자를 본 적 없는
새 세션(서브에이전트)이 만들어야 한다 — CLAUDE.md 실험 7.

    python eval/explore_vlm_input_form.py prepare --manifest docs/clean_manifest.json \
        --lines ~/.typo-mcp/clean-lines.json --dir ~/.typo-mcp/clean --work ~/.typo-mcp/vlm_input --n 30
    python eval/explore_vlm_input_form.py score --work ~/.typo-mcp/vlm_input \
        --dir ~/.typo-mcp/clean --lines ~/.typo-mcp/clean-lines.json \
        --som-vlm boxes/clean_vlm_pass1.json --out docs/vlm_input_form_explore.json
"""
import argparse
import collections
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
import detector_score as DSc      # noqa: E402  iou · held · inside · match
import group_score as GS          # noqa: E402  묶음 → 상자 · c_in 합치기

STRATA = ('columns', 'xh')


def _p(x):
    return os.path.expanduser(x)


def sample(items, n, seed=30):
    """층((단 수, x높이))마다 고르게. 남는 수는 큰 층부터 하나씩."""
    st = collections.defaultdict(list)
    for it in items:
        st[tuple(it[k] for k in STRATA)].append(it)
    keys = sorted(st)
    base, rest = divmod(n, len(keys))
    order = sorted(keys, key=lambda k: -len(st[k]))
    take = {k: base + (1 if i < rest else 0) for i, k in enumerate(order)}
    rng = np.random.default_rng(seed)
    out = []
    for k in keys:
        pool = sorted(st[k], key=lambda it: it['seed'])
        idx = rng.choice(len(pool), size=min(take[k], len(pool)), replace=False)
        out += [pool[i] for i in sorted(idx)]
    return sorted(out, key=lambda it: it['seed'])


def prepare(a):
    M = json.load(open(a.manifest))['items']
    L = json.load(open(_p(a.lines)))['lines']
    picked = sample(M, a.n)
    work = _p(a.work)
    os.makedirs(work, exist_ok=True)
    rows = []
    for it in picked:
        k = str(it['seed'])
        rows.append(dict(seed=it['seed'], file=it['image'], columns=it['columns'], xh=it['xh'],
                         n_blocks=it['n_blocks'], size=L[k]['size'], 줄=len(L[k]['lines']),
                         image=os.path.join(_p(a.dir), it['image']),
                         som=os.path.join(_p(a.dir), 'som', f"{it['seed']}_som.png")))
    json.dump(dict(what='탐색용 · 논문 수치 아님', 층=list(STRATA), 판=len(rows), 목록=rows),
              open(os.path.join(work, 'sample.json'), 'w'), ensure_ascii=False, indent=1)
    # (b) 조건에 넣을 줄 상자 목록 — 판마다 번호와 픽셀 좌표
    lines_txt = {}
    for r in rows:
        k = str(r['seed'])
        lines_txt[r['file']] = [[i + 1] + [int(round(v)) for v in l[:4]] for i, l in enumerate(L[k]['lines'])]
    json.dump(dict(what='탐색용 — (b) 조건 프롬프트에 넣을 줄 상자', 형식='[번호, x1, y1, x2, y2] · 원본 픽셀',
                   판={r['file']: dict(size=r['size'], lines=lines_txt[r['file']]) for r in rows}),
              open(os.path.join(work, 'lines_for_b.json'), 'w'), ensure_ascii=False, indent=1)
    print('판', len(rows), '· 층', dict(collections.Counter((r['columns'], r['xh']) for r in rows)))
    print('→', os.path.join(work, 'sample.json'))
    print('→', os.path.join(work, 'lines_for_b.json'))


# ------------------------------------------------------------------ 채점
def iou(a, b):
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[2], b[2]), min(a[3], b[3])
    if x2 <= x1 or y2 <= y1:
        return 0.0
    inter = (x2 - x1) * (y2 - y1)
    ar = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ar if ar > 0 else 0.0


def count(T, P):
    mr, mp = DSc.match(T, P)
    over_m = sum(1 for pb in P if sum(1 for r in T if DSc.held(pb, r) >= DSc.INSIDE) >= 2)
    over_s = sum(1 for j, pb in enumerate(P) if j not in mp and any(DSc.inside(pb, r) >= DSc.INSIDE for r in T))
    return dict(참조=len(T), 출처=len(P), 맞음=len(mr), 과병합=over_m, 과분할=over_s)


def f1(c):
    r = c['맞음'] / c['참조'] if c['참조'] else 0.0
    p = c['맞음'] / c['출처'] if c['출처'] else 0.0
    return dict(재현=round(r, 4), 정밀=round(p, 4), F1=round(2 * r * p / (r + p), 4) if r + p else 0.0)


def truth_boxes(t, merge=True):
    tt = GS.merge_c_in(t) if merge else t
    return [tb['ink_box'] for tb in tt['blocks']]


def score(a):
    work = _p(a.work)
    S = json.load(open(os.path.join(work, 'sample.json')))['목록']
    L = json.load(open(_p(a.lines)))['lines']
    truths = {str(r['seed']): json.load(open(os.path.join(_p(a.dir), f"{r['seed']}.json"))) for r in S}
    ans = {}
    for cond, path in (('a', a.a), ('b', a.b)):
        if path and os.path.exists(path):
            d = json.load(open(path))
            ans[cond] = {p['file']: p for p in d['posters']}
            ans[cond + '_meta'] = {k: v for k, v in d.items() if k != 'posters'}
    som = json.load(open(a.som_vlm))
    ans['c'] = {p['file']: p for p in som['posters']}
    ans['c_meta'] = {k: v for k, v in som.items() if k != 'posters'}
    per, tot = {}, {}
    ious = collections.defaultdict(list)
    for cond in ('a', 'b', 'c'):
        if cond not in ans:
            continue
        rows, agg = [], collections.Counter()
        parse = collections.Counter()
        for r in S:
            k = str(r['seed'])
            t = truths[k]; T = truth_boxes(t)
            W, H = L[k]['size']
            key = r['file'] if cond != 'c' else f"{r['seed']}_som.png"
            e = ans[cond].get(key)
            if e is None:
                parse['없는 장'] += 1
                continue
            if cond == 'a':
                P = []
                for b in e.get('blocks', []):
                    try:
                        x1, y1, x2, y2 = [float(v) for v in b]
                    except Exception:
                        parse['bad'] += 1; continue
                    if max(x1, y1, x2, y2) <= 1.5:              # 정규화 좌표
                        x1, x2 = x1 * W, x2 * W
                        y1, y2 = y1 * H, y2 * H
                    P.append([min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)])
            else:
                asg, bad = GS.groups_vlm(L[k]['lines'], e)
                parse.update(bad)
                P = [b[1][:4] for b in GS.boxes_of(L[k]['lines'], asg)]
            c = count(T, P)
            for tb in T:
                ious[cond].append(max([iou(tb, pb) for pb in P], default=0.0))
            agg.update(c)
            rows.append(dict(seed=r['seed'], columns=r['columns'], xh=r['xh'], **c, **f1(c),
                             IoU중앙=round(float(np.median([max([iou(tb, pb) for pb in P], default=0.0)
                                                          for tb in T])), 3) if T else None))
        per[cond] = rows
        v = np.asarray(ious[cond], dtype=float)
        tot[cond] = dict(판=len(rows), **dict(agg), **f1(agg),
                         과병합_몫=round(agg['과병합'] / agg['출처'], 4) if agg['출처'] else None,
                         과분할_몫=round(agg['과분할'] / agg['출처'], 4) if agg['출처'] else None,
                         파싱=dict(parse),
                         정답블록_최대IoU=dict(n=len(v), 중앙=round(float(np.median(v)), 3),
                                          p25=round(float(np.percentile(v, 25)), 3),
                                          p75=round(float(np.percentile(v, 75)), 3),
                                          _0=int((v == 0).sum()),
                                          _0p5이상=int((v >= 0.5).sum()),
                                          _0p75이상=int((v >= 0.75).sum())) if len(v) else None)
    res = dict(what='탐색용 · 논문 수치 아님',
               무엇='VLM 입력 형태 세 가지((a) 원본만 · (b) 원본+줄 좌표 목록 · (c) 현행 SoM)의 묶기 비교',
               주의=['깨끗한 세트(합성)라 참값은 그린 좌표다. 사람 라벨이 아니다',
                    '(c) 는 2026-09-14 에 만든 boxes/clean_vlm_pass1.json 을 그대로 쓴다 — 다시 부르지 않았다',
                    '참값은 c_in 쌍을 합친 정의 (clean 본 수치와 같다)',
                    '이 결과로 상수 · 파이프라인 · 사전등록을 고치지 않는다'],
               지표='블록 IoU ≥ 0.5 1:1 매칭 · 과병합(참조 둘 이상을 덮음) · 과분할(참조 안에 들어가고 짝이 없음)',
               조건별=tot, 판별=per,
               응답={k: v for k, v in ans.items() if k.endswith('_meta')})
    json.dump(res, open(a.out, 'w'), ensure_ascii=False, indent=1)
    print(json.dumps(tot, ensure_ascii=False, indent=1))
    print('→', a.out)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    p1 = sub.add_parser('prepare')
    p1.add_argument('--manifest', required=True); p1.add_argument('--lines', required=True)
    p1.add_argument('--dir', required=True); p1.add_argument('--work', required=True)
    p1.add_argument('--n', type=int, default=30)
    p2 = sub.add_parser('score')
    p2.add_argument('--work', required=True); p2.add_argument('--dir', required=True)
    p2.add_argument('--lines', required=True); p2.add_argument('--som-vlm', required=True)
    p2.add_argument('--a'); p2.add_argument('--b'); p2.add_argument('--out', required=True)
    a = ap.parse_args()
    (prepare if a.cmd == 'prepare' else score)(a)


if __name__ == '__main__':
    main()
