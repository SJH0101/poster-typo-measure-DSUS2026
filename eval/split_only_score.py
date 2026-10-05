"""줄 가르기만 다른 선 채점 · 미검출 원인 재집계 — docs/paper_numbers.md 6.3 · 12 절의 값.

    python eval/split_only_score.py --work ~/.typo-mcp/brockmann50 \
        --posters docs/labeling/posters_for_labelers.json \
        --guides labels/guides/guides_labelerA_20260917-2016.json labels/guides/guides_labelerB_20260916-0201.json \
        --consensus docs/brockmann_consensus_refs.json --cache ~/.typo-mcp/brockmann.json \
        --out docs/split_only_score.json

봉인된 줄(`{work}/lines.json`)에 detect_surya.split_wide_lines 를 끄고 · 켜는 것만 다르게 하고
나머지는 현행 코드 그대로 둔다 (H_RATIO 는 고정하지 않는다 — 현행 값을 결과에 적는다).
채점은 기존 함수를 그대로 부른다: brockmann_stage2_score 의 line_score · agreed_blocks ·
line_agreed · _stats · _stats_agreed, explore_split_lines.missed_causes. 기존 함수는 고치지 않는다.

미검출을 두 가지로 센다.
  기존   explore_split_lines.missed_causes — 측정 선을 거르지 않고 행간 ℓ 규칙이 다르다 (6.4 절).
  선채점 missed_causes_ls (아래) — 원인 분류(가로 병합 · 띠 없음 · 어긋남)만 위 함수에서 가져오고
         짝짓기 · 측정 선 거르기 · ℓ · 허용 판정은 line_score 를 그대로 쓴다 (12 절).
         그래서 «미검출 합 = 참값 선 − 허용 안 짝» 이 성립한다.
"""
import argparse
import collections
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
import detect_surya as DS                  # noqa: E402
import group_score as GS                   # noqa: E402
import brockmann_stage2_score as S2        # noqa: E402
import explore_split_lines as XS           # noqa: E402
from measure import ground as G            # noqa: E402

STATES = ('끔', '켬')
REFS = ('라벨러A', '라벨러B', '합의')
KIND = '베이스라인'


def _p(path):
    return os.path.expanduser(path)


def _short(path):
    """결과에 적을 경로 — 홈 아래면 ~ 로 돌려 쓴 사람의 홈 이름이 남지 않게 한다."""
    if path is None:
        return None
    full, home = os.path.abspath(_p(path)), os.path.abspath(os.path.expanduser('~'))
    return '~' + full[len(home):] if full == home or full.startswith(home + os.sep) else path


def missed_causes_ls(p, mblocks, kind=KIND):
    """12 절 — 원인 분류는 missed_causes 그대로, 짝은 line_score 의 T · P · pairs 를 그대로 쓴다."""
    r = S2.line_score(p, mblocks)[0][kind]
    T, P, pairs = r['T'], r['P'], r['pairs']
    mj = {q['p'] for q in pairs}
    hit = {q['t']: q['hit'] for q in pairs}
    c = collections.Counter(글줄=len(T))
    st = []
    for i, t in enumerate(T):
        if hit.get(i):
            st.append('짝'); continue
        c['미검출'] += 1
        near = [j for j, q in enumerate(P)
                if abs(q[0] - t['y']) <= 1 and min(t['x2'], q[2]) - max(t['x1'], q[1]) > 0]
        if any(j in mj for j in near):
            k = '가로 병합'
        elif not any(abs(q[0] - t['y']) <= S2.LINE_WIN * t['lead']
                     and min(t['x2'], q[2]) - max(t['x1'], q[1]) > 0 for q in P):
            k = '띠 없음'
        else:
            k = '어긋남'
        c[k] += 1; st.append(k)
    return c, st


def main():
    ap = argparse.ArgumentParser()
    for k in ('--work', '--posters', '--consensus', '--out'):
        ap.add_argument(k, required=True)
    ap.add_argument('--guides', nargs='+', required=True)
    ap.add_argument('--cache', help='코퍼스 캐시 — 끔 · 켬 가운데 어느 쪽과 같은지만 센다 (12.5 절)')
    a = ap.parse_args()

    W = _p(a.work)
    man = json.load(open(os.path.join(W, 'manifest.json')))
    root = _p(man['image_root'])
    Lr = json.load(open(os.path.join(W, 'lines.json')))['lines']
    Pl = {it['order']: it for it in json.load(open(a.posters))['main']}
    labs = S2.load_labelers(a.guides)
    cons = S2.load_consensus(a.consensus)
    refs = {n: labs[n]['posters'] for n in S2.LABELERS}
    refs['합의'] = cons
    cache = json.load(open(_p(a.cache)))['raw'] if a.cache else None

    lin = collections.defaultdict(list); lin_n = collections.defaultdict(collections.Counter)
    agl = collections.defaultdict(list); agl_n = collections.defaultdict(collections.Counter)
    old = {s: {r: collections.Counter() for r in REFS} for s in STATES}
    new = {s: {r: collections.Counter() for r in REFS} for s in STATES}
    same = collections.Counter()
    for state in STATES:
        for it in sorted(man['items'], key=lambda x: x['order']):
            o = it['order']; k = GS._key(it['seed']); path = os.path.join(root, it['image'])
            gray = np.asarray(Image.open(path).convert('L')).astype(float)
            lines = DS.split_wide_lines(gray, Lr[k]['lines'])[0] if state == '켬' else Lr[k]['lines']
            mb = G.entry(path, DS.boxes_norm(lines, tuple(Lr[k]['size'])), coords='norm')[0]['blocks']
            if cache is not None:
                ck = f"{Pl[o]['folder']}__{Pl[o]['file']}"
                same[state] += (ck in cache and mb == cache[ck]['blocks'])
            for rn, RP in refs.items():
                p = RP.get(o)
                if p is None or not S2.kept(p):
                    continue
                r, _l, info, _ru, _nu, _wh = S2.line_score(p, mb)
                lin[(state, rn)] += r[KIND]['pairs']
                lin_n[(state, rn)].update(T=len(r[KIND]['T']), P=len(r[KIND]['P']))
                lin_n[(state, rn)].update(info)
                old[state][rn].update(XS.missed_causes(p, mb)[0])
                new[state][rn].update(missed_causes_ls(p, mb)[0])
            sp, mp = labs['라벨러A']['posters'].get(o), labs['라벨러B']['posters'].get(o)
            if sp and mp and S2.kept(sp) and S2.kept(mp):
                RS, RM, pr = S2.agreed_blocks(sp, mp)
                ag = S2.line_agreed(sp, mp, RS, RM, pr, S2.line_score(sp, mb)[0],
                                    S2.line_score(mp, mb)[0], mb)[0]
                agl[state] += ag[KIND]['pairs']
                agl_n[state].update(T=len(ag[KIND]['T']), P=len(ag[KIND]['P']))
        print(f'  {state} 끝', flush=True)

    def row(state, rn):
        n, o_, w = lin_n[(state, rn)], old[state][rn], new[state][rn]
        s = S2._stats(lin[(state, rn)], n['T'], n['P'])
        return dict(선채점={k: s[k] for k in ('참값_선', '측정_선', '창안_짝', '허용안_짝', '재현율', '정밀도',
                                             '창안짝_정밀도', '오차_절대_중앙')},
                    미검출_기존=dict(글줄=o_['글줄'], 미검출=o_['미검출'], 가로병합=o_['가로 병합'],
                                 띠없음=o_['띠 없음'], 어긋남=o_['어긋남']),
                    미검출_선채점=dict(글줄=w['글줄'], 미검출=w['미검출'], 가로병합=w['가로 병합'],
                                  띠없음=w['띠 없음'], 어긋남=w['어긋남']),
                    확인=dict(참값_빼기_허용안짝=s['참값_선'] - s['허용안_짝'], 선채점_미검출=w['미검출'],
                            같은가=(s['참값_선'] - s['허용안_짝']) == w['미검출']))

    res = dict(
        무엇='줄 가르기만 다른 선 채점(6.3 절) 과 미검출 원인 두 셈(12 절)',
        H_RATIO=list(DS.H_RATIO), LINE_WIN=S2.LINE_WIN, LINE_TOL=S2.LINE_TOL,
        입력=dict(work=_short(a.work), posters=_short(a.posters), guides=[_short(g) for g in a.guides],
                consensus=_short(a.consensus), cache=_short(a.cache)),
        판=len(man['items']),
        대상={f'{s}|{r}': row(s, r) for s in STATES for r in REFS},
        일치={s: S2._stats_agreed(agl[s], agl_n[s]['T'], agl_n[s]['P']) for s in STATES},
        캐시와_같은_판={s: same[s] for s in STATES} if cache is not None else None,
        주의='미검출 «기존» 은 explore_split_lines.missed_causes 그대로 — 측정 선을 거르지 않는다 (6.4 절)')
    json.dump(res, open(a.out, 'w'), ensure_ascii=False, indent=1)
    print('→', a.out)


if __name__ == '__main__':
    main()
