"""VLM 파이프라인 보충 값 — 사전등록 docs/vlm_supp_preregister.json 그대로.

    python eval/vlm_supp.py --work ~/.typo-mcp/brockmann50 \
        --posters docs/labeling/posters_for_labelers.json \
        --guides labels/guides/guides_labelerA_20260917-2016.json labels/guides/guides_labelerB_20260916-0201.json \
        --consensus docs/brockmann_consensus_refs.json \
        --off boxes/brockmann_vlm_pass1.json boxes/brockmann_vlm_pass2.json \
        --on boxes/brockmann_vlm_split_pass1.json boxes/brockmann_vlm_split_pass2.json \
        --vlm-corpus-rules docs/vlm_corpus_rules_pass1.json docs/vlm_corpus_rules_pass2.json \
        --vlm-corpus-ndiv docs/vlm_corpus_grid_ndiv_pass1.json docs/vlm_corpus_grid_ndiv_pass2.json \
        --vlm-corpus-module docs/vlm_corpus_grid_module_pass1.json docs/vlm_corpus_grid_module_pass2.json \
        --caches 브로크만=~/.typo-mcp/vlm-pass1/brockmann.json … \
        --prereg docs/vlm_supp_preregister.json --out docs/vlm_supp_result.json

결정 1 · 2 는 새로 센다 (VLM 블록으로 선 채점 → 원인 분류 · 끔·켬 비교).
결정 3 은 이미 커밋된 결과 파일을 읽거나 결정론적으로 다시 센다 (난수 없음).
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
import detect_surya as DS                     # noqa: E402
import group_score as GS                      # noqa: E402
import brockmann_stage2_score as S2           # noqa: E402
import split_only_score as SO                 # noqa: E402  missed_causes_ls (12 절 정의)
import explore_typography_rules2 as T2        # noqa: E402
import grid_ndiv as GN                        # noqa: E402
from measure import ground as G               # noqa: E402

KIND = '베이스라인'


def _sha(p):
    return hashlib.sha256(open(os.path.expanduser(p), 'rb').read()).hexdigest()


def _r(x, n=4):
    return None if x is None else round(float(x), n)


def vlm_blocks(path, lines, size, groups):
    """VLM 묶음 → 측정 블록 (vlm_pipeline_50 과 같은 방식, 여유 없음)."""
    asg, _i = GS.groups_vlm(lines, dict(groups=groups))
    bx = [b[:4] for _g, b in GS.boxes_of(lines, asg)]
    nb = [[b[0] / size[0], b[1] / size[1], b[2] / size[0], b[3] / size[1]] for b in bx]
    return (G.entry(path, nb, coords='norm')[0]['blocks'] if nb else []), len(bx)


def _ys(t):
    """참조 선의 y. 일치 항목은 두 라벨러 값(yS · yM)을 쓴다 (_cand2 와 같다)."""
    return [t['y']] if 'y' in t else [t['yS'], t['yM']]


def causes_from(T, P, pairs):
    """결정 1 — 원인 분류 규칙 (missed_causes 그대로), 짝은 넘겨받은 것.

    일치 항목은 T 에 y 가 없고 yS · yM 이 있으므로, line_agreed 의 짝짓기(_cand2)와 같게
    «±1px 안» 과 «창 안» 을 **두 값 모두**에 걸어 본다.
    """
    mj = {q['p'] for q in pairs}
    hit = {q['t']: q['hit'] for q in pairs}
    c = collections.Counter()
    for i, t in enumerate(T):
        if hit.get(i):
            continue
        c['놓친_줄'] += 1
        ys = _ys(t)
        over = lambda q: min(t['x2'], q[2]) - max(t['x1'], q[1]) > 0
        near = [j for j, q in enumerate(P)
                if all(abs(q[0] - y) <= 1 for y in ys) and over(q)]
        if any(j in mj for j in near):
            c['가로_병합'] += 1
        elif not any(all(abs(q[0] - y) <= S2.LINE_WIN * t['lead'] for y in ys) and over(q) for q in P):
            c['띠_없음'] += 1
        else:
            c['어긋남'] += 1
    return c


def main():
    ap = argparse.ArgumentParser()
    for k in ('--work', '--posters', '--consensus', '--prereg', '--out'):
        ap.add_argument(k, required=True)
    ap.add_argument('--guides', nargs='+', required=True)
    ap.add_argument('--off', nargs=2, required=True); ap.add_argument('--on', nargs=2, required=True)
    ap.add_argument('--vlm-corpus-rules', nargs=2, required=True)
    ap.add_argument('--vlm-corpus-ndiv', nargs=2, required=True)
    ap.add_argument('--vlm-corpus-module', nargs=2, required=True)
    ap.add_argument('--caches', nargs='+', required=True, help='회차1/회차2 캐시 — 회차=경로 를 코퍼스마다 (p1_브로크만=… 꼴)')
    a = ap.parse_args()

    W = os.path.expanduser(a.work)
    man = json.load(open(os.path.join(W, 'manifest.json'))); root = os.path.expanduser(man['image_root'])
    L = json.load(open(os.path.join(W, 'lines.json')))['lines']
    labs = S2.load_labelers(a.guides)
    refs = {n: labs[n]['posters'] for n in S2.LABELERS}
    refs['합의'] = S2.load_consensus(a.consensus)
    Pl = {it['order']: it for it in json.load(open(a.posters))['main']}

    OFF = [json.load(open(f)) for f in a.off]
    ON = [json.load(open(f)) for f in a.on]
    def gmap(d):
        return {p['file']: p['groups'] for p in d['posters']}

    # ── 결정 1 · 2 — 조건(끔·켬) × 회차 × 참조
    prs = collections.defaultdict(list); cnt = collections.Counter()
    cz = collections.defaultdict(collections.Counter)
    nblk = collections.Counter(); keyed = collections.Counter()
    for it in sorted(man['items'], key=lambda x: x['order']):
        o = it['order']; k = GS._key(it['seed']); path = os.path.join(root, it['image'])
        size = tuple(L[k]['size'])
        gray = np.asarray(Image.open(path).convert('L')).astype(float)
        lines_off = [list(b) for b in L[k]['lines']]
        lines_on = [list(b) for b in DS.split_wide_lines(gray, L[k]['lines'])[0]]
        for cond, src, lines in (('끔', OFF, lines_off), ('켬', ON, lines_on)):
            for r, d in enumerate(src, 1):
                gm = gmap(d)
                f = next((x for x in (f'{k}_som.png', it.get('image')) if x in gm), None)
                if f is None:
                    continue
                mx = max((x for gr in gm[f] for x in gr), default=0)
                keyed[f'{cond}|회차{r}|최대번호=줄수'] += (mx == len(lines))
                keyed[f'{cond}|회차{r}|판'] += 1
                mb, nb = vlm_blocks(path, lines, size, gm[f])
                nblk[f'{cond}|회차{r}'] += len(mb)
                res_loc = {}
                for ref in ('라벨러A', '라벨러B', '합의'):
                    p = refs[ref].get(o)
                    if p is None or not S2.kept(p):
                        continue
                    res = S2.line_score(p, mb)[0]
                    res_loc[ref] = res
                    rr = res[KIND]
                    key = (cond, r, ref)
                    prs[key] += rr['pairs']
                    cnt[(cond, r, ref, 'T')] += len(rr['T']); cnt[(cond, r, ref, 'P')] += len(rr['P'])
                    cz[key].update(causes_from(rr['T'], rr['P'], rr['pairs']))
                S_, M_ = refs['라벨러A'].get(o), refs['라벨러B'].get(o)
                if S_ and M_ and S2.kept(S_) and S2.kept(M_):
                    RS, RM, ap_ = S2.agreed_blocks(S_, M_)
                    ag = S2.line_agreed(S_, M_, RS, RM, ap_, res_loc['라벨러A'], res_loc['라벨러B'], mb)[0][KIND]
                    key = (cond, r, '일치')
                    prs[key] += ag['pairs']
                    cnt[(cond, r, '일치', 'T')] += len(ag['T'])
                    cnt[(cond, r, '일치', 'P')] += len(ag['P']) - ag['정밀분모_뺌']
                    cz[key].update(causes_from(ag['T'], ag['P'], ag['pairs']))
        print(f'  순서 {o} 끝', flush=True)

    def cell(cond, r, ref):
        t, p_ = cnt[(cond, r, ref, 'T')], cnt[(cond, r, ref, 'P')]
        s = (S2._stats_agreed if ref == '일치' else S2._stats)(prs[(cond, r, ref)], t, p_)
        z = cz[(cond, r, ref)]
        return dict(참값_선=s['참값_선'], 측정_선=s['측정_선'], 창안_짝=s['창안_짝'], 허용안_짝=s['허용안_짝'],
                    재현율=s['재현율'], 정밀도=s['정밀도'], 놓친_줄=t - s['허용안_짝'],
                    가로_병합=z['가로_병합'], 띠_없음=z['띠_없음'], 어긋남=z['어긋남'],
                    원인_합=z['놓친_줄'])

    res = dict(
        what=f'사전등록 {a.prereg} 의 결과', 사전등록_sha256=_sha(a.prereg),
        무엇='VLM 파이프라인 보충 — 놓친 줄 원인 분류 · 줄 가르기 끔·켬 비교 (실물 50점) · 코퍼스 보충 읽기와 결정론적 재셈',
        정의=dict(원인분류='12 절 missed_causes_ls 와 같은 규칙 (가로 병합 · 띠 없음 · 어긋남)',
                블록='VLM 묶음 → GS.boxes_of 픽셀 상자 → [x1/W, y1/H, x2/W, y2/H] (여유 없음) → ground.entry',
                끔=[dict(파일=f, sha256=_sha(f), date=json.load(open(f)).get('date')) for f in a.off],
                켬=[dict(파일=f, sha256=_sha(f), date=json.load(open(f)).get('date')) for f in a.on],
                선=KIND, 회차='1 · 2 를 각각 적고 하나를 고르지 않는다',
                일치항목='line_agreed 의 T · P · pairs 로 같은 원인 규칙을 적용했다 (연구자별과 셈의 단위가 다르다)'),
        끔_패스가_가르기전_줄인가={k: v for k, v in sorted(keyed.items())},
        측정_블록_합={k: v for k, v in sorted(nblk.items())},
        실물_50=dict())
    for cond in ('끔', '켬'):
        for r in (1, 2):
            for ref in ('라벨러A', '라벨러B', '일치', '합의'):
                if cnt[(cond, r, ref, 'T')]:
                    res['실물_50'][f'{cond}|회차{r}|{ref}'] = cell(cond, r, ref)

    # ── 결정 3 — 코퍼스 보충
    RU = [json.load(open(f)) for f in a.vlm_corpus_rules]
    ND = [json.load(open(f)) for f in a.vlm_corpus_ndiv]
    MO = [json.load(open(f)) for f in a.vlm_corpus_module]
    caches = {}
    for s in a.caches:
        kk, v = s.split('=', 1)
        caches[kk] = json.load(open(os.path.expanduser(v)))['raw']
    CORP = [('브로크만', '가_측정_브로크만'), ('호프만', '측정_호프만'), ('로제', '측정_로제'), ('루더', '측정_루더')]

    # 3-a 행간÷x높이 비를 센 포스터 수 (블록이 둘 이상) — a1 과 같은 셈
    pc = {}
    for r in (1, 2):
        for cn, _key in CORP:
            raw = caches[f'p{r}_{cn}']
            n = 0
            for e in raw.values():
                bl = T2.blocks_pipeline(e)
                if not bl:
                    continue
                p = T2.prep(bl, e['size'])
                v = [b['lead'] / b['xh'] for b in p['blocks'] if b['lead'] and b['xh']]
                n += (len(v) >= 2)
            pc[f'회차{r}|{cn}'] = n
    # 3-b 인접 비 1.5 · 1.33 대조 (ii) 구간 (읽기)
    ratio = {}
    for r in (1, 2):
        for t in ('1.5', '1.33'):
            v = RU[r - 1]['결과']['가_측정_브로크만']['B']['B2']['목표별'][t]
            ratio[f'회차{r}|{t}'] = dict(실제=v['실제'], 대조_ii=v['대조_ii']['구간'], 판정=v['판정'])
    # 4 표 7 — 원 분수로 다시 셈 + 범위 + 연이어 벗어남
    t7 = {}
    for r in (1, 2):
        raw = caches[f'p{r}_브로크만']
        def bm(k):
            return [dict(x1=float(b['x1']), y1=float(b['y1']), x2=float(b['x2']), y2=float(b['y2']),
                         bases=sorted(float(x) for x in b['bases'])) for b in (raw[k].get('blocks') or [])]
        P = GN.build(bm, lambda k: raw[k]['size'], sorted(raw))
        tot = int(sum(len(p['edges'][0]) + len(p['edges'][1]) for p in P))
        def share(n):
            hit = 0
            for p in P:
                for v, Ln in ((p['edges'][0], p['H']), (p['edges'][1], p['W'])):
                    if not len(v):
                        continue
                    st = Ln / n
                    d = np.abs(v / st - np.round(v / st))
                    hit += int(np.sum(d <= GN.TOL))
            return hit, tot
        rows = {}
        for n in (30, 60, 90, 120):
            h, tt = share(n)
            rows[str(n)] = dict(분수=f'{h}/{tt}', 정확=round(h / tt, 8), 소수3=round(h / tt, 3))
        allv = []
        for n in GN.NS:
            h, tt = share(n)
            allv.append((h / tt, n))
        mn, mx = min(allv), max(allv)
        t = ND[r - 1]['대상']['측정_브로크만_123']
        out_ns = sorted(t['N별_요약']['구간_밖_N'])
        run = [out_ns[i] for i in range(len(out_ns) - 1) if out_ns[i + 1] - out_ns[i] == 1]
        t7[f'회차{r}'] = dict(N별=rows,
                            무작위_대조i_N60=t['N별']['대조_i']['60']['평균'],
                            범위=dict(최소=dict(N=mn[1], 정확=round(mn[0], 8), 소수3=round(mn[0], 3)),
                                    최대=dict(N=mx[1], 정확=round(mx[0], 8), 소수3=round(mx[0], 3))),
                            구간_밖_N=out_ns, 구간_밖_N_수=len(out_ns),
                            두_N_이상_연이어=bool(run), 연이어_시작=run)
    # 5 가로 배수 — 최빈 u · 하한 판 수 · 보조
    gm = {}
    for r in (1, 2):
        d = MO[r - 1]['대상']['측정_브로크만_123']
        t = d['주_결과']
        dist = t['최적u_도수']
        top = max(dist.items(), key=lambda kv: (kv[1], -float(kv[0])))
        gm[f'회차{r}'] = dict(쓴_판=t['쓴_판'], 점수_중앙=t['점수_중앙'], 대조=t['대조']['구간'], 판정=t['판정'],
                            최적u_중앙=t['최적u_중앙'], 최적u_최빈=dict(u=top[0], 판=top[1]),
                            하한_0p07_판=dist.get('0.07', 0), 최적u_도수=dist,
                            보조={f'위치{m}개이상': dict(쓴_판=d[f'보조_위치{m}개이상']['쓴_판'],
                                                    점수_중앙=d[f'보조_위치{m}개이상']['점수_중앙'],
                                                    대조=d[f'보조_위치{m}개이상']['대조']['구간'],
                                                    판정=d[f'보조_위치{m}개이상']['판정']) for m in (3, 5)})
    # 6 신실라 (읽기)
    sin = {f'회차{r}': ND[r - 1]['신실라_2021_대조']['측정_브로크만_123'] for r in (1, 2)}

    res['코퍼스_보충'] = dict(행간_x높이_센_포스터_수=pc, 인접비_대조구간=ratio, 표7=t7, 가로배수=gm, 신실라=sin)
    json.dump(res, open(a.out, 'w'), ensure_ascii=False, indent=1)
    print('→', a.out)


if __name__ == '__main__':
    main()
