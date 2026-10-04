"""탐색용 · 논문 수치 아님 — VLM 이 베이스라인 y 좌표를 얼마나 정확히 내는가 (브로크만 라벨 10장).

    (a) 포스터 원본 이미지만 — 글줄마다 베이스라인 y 와 글줄 왼끝 · 오른끝 x 를 원본 픽셀로 답한다
    (b) Surya 줄에 번호 딱지를 붙인 2배 이미지 (group_score.draw_som, 현행 VLM 패스와 같은 그림) —
        번호마다 베이스라인 y 를 그 2배 이미지의 픽셀로 답한다 (채점 때 ÷ 2)
    (c) 참고 — 현행 파이프라인 캐시의 베이스라인

정답은 사람 합의 라벨. 짝짓기 · 창 · 허용은 brockmann_stage2_score 의 선 채점과 같다
(창 0.5·행간 · 허용 0.2·행간 · 가로 겹침 · 가까운 순 1:1). 제외 · 판독 불가 블록 안의 답은 뺀다.
VLM 응답은 사람 상자를 본 적 없는 새 세션(서브에이전트)이 만든다 — CLAUDE.md 실험 7.
이 결과로 상수 · 파이프라인 · 사전등록을 고치지 않는다.

    python eval/explore_vlm_baseline.py prepare --work ~/.typo-mcp/brockmann50 --cache ~/.typo-mcp/brockmann.json \
        --consensus docs/brockmann_consensus_refs.json --posters docs/labeling/posters_for_labelers.json \
        --out-dir ~/.typo-mcp/vlm_baseline --sample docs/vlm_baseline_sample.json --n 10
    python eval/explore_vlm_baseline.py score --out-dir ~/.typo-mcp/vlm_baseline --sample docs/vlm_baseline_sample.json \
        --cache ~/.typo-mcp/brockmann.json --consensus docs/brockmann_consensus_refs.json \
        --a boxes/vlm_baseline_a1.json boxes/vlm_baseline_a2.json --b boxes/vlm_baseline_b1.json boxes/vlm_baseline_b2.json \
        --out docs/vlm_baseline_explore.json

사전등록 docs/vlm_baseline_all50_preregister.json — 50장 전부 · 갈린 줄 · 세 참조 (새 인자 없이 돌리면 위와 같다):

    python eval/explore_vlm_baseline.py prepare --all --split-lines --prereg docs/vlm_baseline_all50_preregister.json \
        --work ~/.typo-mcp/brockmann50 --cache ~/.typo-mcp/brockmann.json --consensus docs/brockmann_consensus_refs.json \
        --posters docs/labeling/posters_for_labelers.json --out-dir ~/.typo-mcp/vlm_baseline_all50 \
        --sample docs/vlm_baseline_all50_sample.json
    python eval/explore_vlm_baseline.py score --split-lines --prereg docs/vlm_baseline_all50_preregister.json \
        --guides labels/guides/guides_labelerA_20260917-2016.json labels/guides/guides_labelerB_20260916-0201.json \
        --work ~/.typo-mcp/brockmann50 --out-dir ~/.typo-mcp/vlm_baseline_all50 --sample docs/vlm_baseline_all50_sample.json \
        --cache ~/.typo-mcp/brockmann.json --consensus docs/brockmann_consensus_refs.json \
        --a <archive>/vlm_baseline_all50_a1.json <archive>/vlm_baseline_all50_a2.json \
        --b <archive>/vlm_baseline_all50_b1.json <archive>/vlm_baseline_all50_b2.json --out docs/vlm_baseline_all50.json
"""
import argparse
import collections
import hashlib
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
import detect_surya as DS                  # noqa: E402  split_wide_lines (번호 줄)
import detector_score as DSc               # noqa: E402
import group_score as GS                   # noqa: E402
import brockmann_stage2_score as S2        # noqa: E402
import explore_split_lines as XS           # noqa: E402

SOM_SCALE = 2


def _p(x):
    return os.path.expanduser(x)


def _tilde(p):
    """기록에 남기는 경로는 홈을 ~ 로 접는다."""
    h = os.path.expanduser('~')
    return '~' + p[len(h):] if isinstance(p, str) and p.startswith(h) else p


def _sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def surya_lines(path, lines, split):
    """번호 딱지 · 번호 대응에 쓰는 줄. split 이면 brockmann_stage2_score 와 같이 split_wide_lines 를 건다."""
    if not split:
        return lines
    gray = np.asarray(Image.open(path).convert('L')).astype(float)
    return DS.split_wide_lines(gray, lines)[0]


def prepare(a):
    W = _p(a.work)
    man = json.load(open(os.path.join(W, 'manifest.json'))); root = _p(man['image_root'])
    L = json.load(open(os.path.join(W, 'lines.json')))['lines']
    cache = json.load(open(_p(a.cache)))['raw']
    C = {p['order']: p for p in json.load(open(a.consensus))['posters']}
    Pl = {it['order']: it for it in json.load(open(a.posters))['main']}
    rows = []
    for it in sorted(man['items'], key=lambda x: x['order']):
        o = it['order']; pl = Pl[o]; ck = f"{pl['folder']}__{pl['file']}"
        if o not in C or ck not in cache:
            continue
        c, _st = XS.missed_causes(C[o], cache[ck]['blocks'])
        rows.append(dict(order=o, key=ck, image=it['image'], seed=it['seed'], 글줄=c['글줄'], 미검출=c['미검출']))
    if a.all:                       # 선정 조건 없음 — 목록의 판 전부
        zero = pick = rows
    else:
        zero = [r for r in rows if r['미검출'] == 0 and r['글줄'] >= 5]
        idx = np.linspace(0, len(zero) - 1, a.n).round().astype(int)
        pick = [zero[i] for i in sorted(set(idx.tolist()))]
    out = _p(a.out_dir); os.makedirs(os.path.join(out, 'som'), exist_ok=True)
    for r in pick:
        k = GS._key(r['seed']); path = os.path.join(root, r['image'])
        im = Image.open(path)
        r['size'] = list(im.size); r['path'] = path
        r['som'] = os.path.join(out, 'som', f"{r['order']:02d}_som.png")
        ls = surya_lines(path, L[k]['lines'], a.split_lines)
        GS.draw_som(im, ls, r['som'])
        r['som_lines'] = [[round(v, 1) for v in l] for l in ls]
        r['file'] = os.path.basename(r['image'])
    if a.prereg:
        rec = [{k: _tilde(v) for k, v in r.items() if k != 'som_lines'} | dict(번호_수=len(r['som_lines'])) for r in pick]
        json.dump(dict(what=f'사전등록 {a.prereg} 의 표본',
                       사전등록_sha256=_sha(a.prereg),
                       고른_방식=f'선정 조건 없음 — 목록의 판 전부 {len(pick)}장' if a.all else
                       f'합의 라벨 기준 현행 미검출 0 · 글줄 5 이상인 판 {len(zero)}장에서 순서대로 고르게 {len(pick)}장',
                       번호_줄='원본 줄에 detect_surya.split_wide_lines 를 건 줄' if a.split_lines else '원본 Surya 줄',
                       판=rec),
                  open(a.sample, 'w'), ensure_ascii=False, indent=1)
    else:
        json.dump(dict(what='탐색용 · 논문 수치 아님',
                       고른_방식=f'합의 라벨 기준 현행 미검출 0 · 글줄 5 이상인 판 {len(zero)}장에서 순서대로 고르게 {len(pick)}장',
                       판=[{k: v for k, v in r.items() if k != 'som_lines'} for r in pick]),
                  open(a.sample, 'w'), ensure_ascii=False, indent=1)
    # 서브에이전트 입력 — 조건 · 회차 · 묶음(5장)
    for cond in ('a', 'b'):
        for run in (1, 2):
            for bi in range(0, len(pick), 5):
                chunk = pick[bi:bi + 5]; n = bi // 5 + 1
                if cond == 'a':
                    items = [dict(file=r['file'], image=r['path'], 크기_px=r['size']) for r in chunk]
                else:
                    items = [dict(file=os.path.basename(r['som']), image=r['som'],
                                  크기_px=[r['size'][0] * SOM_SCALE, r['size'][1] * SOM_SCALE],
                                  번호_수=len(r['som_lines'])) for r in chunk]
                json.dump(dict(조건=cond, 회차=run, 출력=os.path.join(out, f'{cond}{run}_batch{n}.json'), 판=items),
                          open(os.path.join(out, f'{cond}{run}_batch{n}_input.json'), 'w'), ensure_ascii=False, indent=1)
    print('판', [(r['order'], r['file'][:40]) for r in pick])


def targets(p):
    """합의 라벨의 베이스라인 참값 T 와 제외 영역 (line_score 와 같은 정의)."""
    R, X = S2.refs_of(p, 'main')
    med = S2.poster_L_med(R)
    ill = [b for b in R if b['base_mark'] == 'illegible']
    T = []
    for b in R:
        if not b['lines']:
            continue
        Ld, _rn = S2.block_L(b, med)
        if Ld is None:
            continue
        for l in b['lines']:
            if S2._num(l['base']):
                T.append(dict(y=l['base'], lead=Ld, x1=b['box'][0], x2=b['box'][2], k=len(T)))
    excl = [x['box'] for x in X] + [b['box'] for b in ill]
    return T, excl


def keep(P, excl):
    return [q for q in P if not any(e[0] <= (q[1] + q[2]) / 2 <= e[2] and e[1] <= q[0] <= e[3] for e in excl)]


def stats(rows, label_den=False):
    """rows = [(T, P, pairs)] 판마다. label_den 이면 1px 이내 몫을 라벨 줄 분모로도 낸다 (채점 정의는 같다)."""
    nt = sum(len(T) for T, _P, _pr in rows); npred = sum(len(P) for _T, P, _pr in rows)
    prs = [(pr, T) for T, _P, prl in rows for pr in prl]
    ae = [abs(q['err']) for q, _T in prs]
    rel = [abs(q['err']) / T[q['t']]['lead'] for q, T in prs]
    hit = sum(q['hit'] for q, _T in prs)
    f = lambda v, p: round(float(np.percentile(v, p)), 3) if v else None
    out = dict(라벨_줄=nt, 답한_줄=npred, 짝=len(prs), 놓친_줄=nt - len(prs), 없는_줄을_만듦=npred - len(prs),
               오차_절대_px=dict(중앙=f(ae, 50), p90=f(ae, 90)), 오차_행간비=dict(중앙=f(rel, 50), p90=f(rel, 90)),
               편향_px_중앙=f([q['err'] for q, _T in prs], 50),
               일행_이내_몫=(round(float(np.mean([x <= 1 for x in ae])), 4) if ae else None),
               허용_0p2행간_재현=(round(hit / nt, 4) if nt else None), 허용_0p2행간_정밀=(round(hit / npred, 4) if npred else None))
    if label_den:
        out['일행_이내_수'] = sum(1 for x in ae if x <= 1)
        out['일행_이내_몫_라벨분모'] = round(out['일행_이내_수'] / nt, 4) if nt else None
    return out


def load_ans(paths):
    out = []
    for p in paths:
        d = json.load(open(p))
        out.append(({q['file']: q for q in d['posters']}, {k: v for k, v in d.items() if k != 'posters'}))
    return out


def score_ref(S, C, cache, A, B, label_den=False):
    """참조 하나(C = order → 참조 판)로 다섯 조건을 채점한다."""
    rows = collections.defaultdict(list); per = collections.defaultdict(dict)
    by_line = collections.defaultdict(dict)       # (조건회차) → {(order, t): y}
    for r in S:
        o = r['order']; T, excl = targets(C[o])
        # (c) 현행 파이프라인
        mb = cache[r['key']]['blocks']
        Pc = keep([(v, b['x1'], b['x2'], k, li) for k, b in enumerate(mb) for li, v in enumerate(b['bases'])], excl)
        conds = {'c': Pc}
        for n, (ans, _m) in enumerate(A, 1):
            e = ans.get(r['file'], {})
            P = []
            for j, q in enumerate(e.get('lines', [])):
                try:
                    P.append((float(q['y']), float(q['x1']), float(q['x2']), j, 0))
                except (KeyError, TypeError, ValueError):
                    pass
            conds[f'a{n}'] = keep(P, excl)
        for n, (ans, _m) in enumerate(B, 1):
            e = ans.get(os.path.basename(r['som']), {})
            P = []
            for q in e.get('baselines', []):
                try:
                    num, y = int(q[0]), float(q[1]) / SOM_SCALE
                except (TypeError, ValueError, IndexError):
                    continue
                box = LINES[r['order']][num - 1] if 1 <= num <= len(LINES[r['order']]) else None
                if box:
                    P.append((y, box[0], box[2], num, 0))
            conds[f'b{n}'] = keep(P, excl)
        for cn, P in conds.items():
            pr = S2._direct(T, P)
            rows[cn].append((T, P, pr))
            per[cn][o] = dict(라벨_줄=len(T), 답한_줄=len(P), 짝=len(pr))
            for q in pr:
                by_line[cn][(o, q['t'])] = P[q['p']][0]
    res = {cn: stats(v, label_den) for cn, v in rows.items()}
    between = {}
    for c in ('a', 'b'):
        k1, k2 = f'{c}1', f'{c}2'
        if k1 in by_line and k2 in by_line:
            common = set(by_line[k1]) & set(by_line[k2])
            d = [abs(by_line[k1][x] - by_line[k2][x]) for x in common]
            between[c] = dict(두_회차_모두_짝지은_라벨줄=len(common),
                              회차간_y차_px=dict(중앙=round(float(np.median(d)), 3) if d else None,
                                              p90=round(float(np.percentile(d, 90)), 3) if d else None),
                              일행_이내_몫=round(float(np.mean([x <= 1 for x in d])), 4) if d else None,
                              답한_줄=[res[k1]['답한_줄'], res[k2]['답한_줄']],
                              짝=[res[k1]['짝'], res[k2]['짝']])
    return res, between, per


DEFS = dict(짝='brockmann_stage2_score._direct (창 0.5·행간 · 가로 겹침 · 가까운 순 1:1)',
            일행_이내='|오차| ≤ 1 px', 허용='|오차| ≤ 0.2·행간 (stage2 선 채점의 재현 · 정밀)',
            행간='stage2 block_L', 제외='제외 사유 블록 · 판독 불가 블록 안의 답은 뺀다',
            b_좌표='답한 y ÷ 2 (2배 이미지), 가로 범위는 그 번호의 Surya 줄 상자')


def score(a):
    S = json.load(open(a.sample))['판']
    cache = json.load(open(_p(a.cache)))['raw']
    C = {p['order']: p for p in json.load(open(a.consensus))['posters']}
    A = load_ans(a.a); B = load_ans(a.b)
    meta = {f'a{n}': m for n, (_x, m) in enumerate(A, 1)} | {f'b{n}': m for n, (_x, m) in enumerate(B, 1)}
    if a.guides:                    # 라벨러A · 라벨러B · 합의 세 참조
        labs = S2.load_labelers(a.guides)
        refs = {n: labs[n]['posters'] for n in S2.LABELERS} | {'합의': C}
        by_ref = {}
        for name, R in refs.items():
            res, between, per = score_ref(S, R, cache, A, B, label_den=True)
            by_ref[name] = dict(조건별=res, 회차간=between, 판별=per)
        defs = DEFS | dict(일행_이내_몫='분모 = 짝지은 줄', 일행_이내_몫_라벨분모='분모 = 라벨 줄 (일행_이내_수 ÷ 라벨_줄)',
                           참조='라벨러A · 라벨러B (brockmann_stage2_score.load_labelers) · 합의 (docs/brockmann_consensus_refs.json). '
                              '참값 줄과 제외 영역은 참조마다 targets 로 따로 구한다')
        cprov = json.load(open(_p(a.cache))).get('provenance', {})
        json.dump(dict(what=f'사전등록 {a.prereg} 의 결과' if a.prereg else '탐색용 · 논문 수치 아님',
                       **({'사전등록_sha256': _sha(a.prereg)} if a.prereg else {}),
                       무엇='VLM 베이스라인 좌표 정확도 — (a) 원본만 · (b) 번호 딱지 2배 이미지 · (c) 현행 파이프라인, 세 참조',
                       정의=defs,
                       입력=dict(표본=a.sample, 표본_sha256=_sha(a.sample), 판=len(S),
                               라벨=[dict(파일=g, sha256=_sha(g)) for g in a.guides],
                               합의=dict(파일=a.consensus, sha256=_sha(a.consensus)),
                               c_캐시=dict(파일=_tilde(_p(a.cache)), commit=cprov.get('commit'), date=cprov.get('date')),
                               번호_줄='원본 줄에 detect_surya.split_wide_lines 를 건 줄' if a.split_lines else '원본 Surya 줄',
                               응답=[dict(조건=k, 파일=_tilde(_p(p)), sha256=_sha(_p(p)))
                                   for k, p in zip([f'a{n}' for n in range(1, len(a.a) + 1)] +
                                                   [f'b{n}' for n in range(1, len(a.b) + 1)], a.a + a.b)]),
                       참조별=by_ref, 응답=meta),
                  open(a.out, 'w'), ensure_ascii=False, indent=1)
        print(json.dumps({n: v['조건별'] for n, v in by_ref.items()}, ensure_ascii=False, indent=1))
        return
    res, between, per = score_ref(S, C, cache, A, B)
    json.dump(dict(what='탐색용 · 논문 수치 아님',
                   무엇='VLM 베이스라인 좌표 정확도 — (a) 원본만 · (b) 번호 딱지 2배 이미지 · (c) 현행 파이프라인, 합의 라벨 기준',
                   정의=dict(짝='brockmann_stage2_score._direct (창 0.5·행간 · 가로 겹침 · 가까운 순 1:1)',
                           일행_이내='|오차| ≤ 1 px', 허용='|오차| ≤ 0.2·행간 (stage2 선 채점의 재현 · 정밀)',
                           행간='stage2 block_L', 제외='제외 사유 블록 · 판독 불가 블록 안의 답은 뺀다',
                           b_좌표='답한 y ÷ 2 (2배 이미지), 가로 범위는 그 번호의 Surya 줄 상자'),
                   조건별=res, 회차간=between, 판별=per,
                   응답={f'a{n}': m for n, (_x, m) in enumerate(A, 1)} | {f'b{n}': m for n, (_x, m) in enumerate(B, 1)}),
              open(a.out, 'w'), ensure_ascii=False, indent=1)
    print(json.dumps(dict(조건별=res, 회차간=between), ensure_ascii=False, indent=1))


LINES = {}


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    p1 = sub.add_parser('prepare')
    for k in ('--work', '--cache', '--consensus', '--posters', '--out-dir', '--sample'):
        p1.add_argument(k, required=True)
    p1.add_argument('--n', type=int, default=10)
    p1.add_argument('--all', action='store_true', help='선정 조건 없이 목록의 판 전부 (--n 무시)')
    p2 = sub.add_parser('score')
    for k in ('--out-dir', '--sample', '--cache', '--consensus', '--work', '--out'):
        p2.add_argument(k, required=True)
    p2.add_argument('--a', nargs='+', required=True); p2.add_argument('--b', nargs='+', required=True)
    p2.add_argument('--guides', nargs='+', help='라벨러 두 파일 — 주면 라벨러A · 라벨러B · 합의 세 참조로 채점한다')
    for p in (p1, p2):
        p.add_argument('--split-lines', action='store_true',
                       help='번호 딱지 · 번호 대응에 원본 줄 대신 detect_surya.split_wide_lines 를 건 줄을 쓴다')
        p.add_argument('--prereg', help='사전등록 파일 — 주면 결과 · 표본 머리에 사전등록과 그 sha256 을 적는다')
    a = ap.parse_args()
    if a.cmd == 'prepare':
        prepare(a)
    else:
        W = _p(a.work)
        man = json.load(open(os.path.join(W, 'manifest.json'))); root = _p(man['image_root'])
        Lr = json.load(open(os.path.join(W, 'lines.json')))['lines']
        for it in man['items']:
            LINES[it['order']] = surya_lines(os.path.join(root, it['image']), Lr[GS._key(it['seed'])]['lines'],
                                             a.split_lines)
        score(a)


if __name__ == '__main__':
    main()
