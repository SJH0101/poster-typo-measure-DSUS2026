"""탐색용 · 논문 수치 아님 — 줄 상자 가르기 (detect_surya.split_wide_lines) 를 켰을 때와 끈 때를 견준다.

기본 경로는 이 처리를 부르지 않는다. 여기서는 저장된 Surya 줄에서 두 조건을 같은 함수로 잰다.
    끔  : 줄 → detect_surya.boxes_norm → measure/ground.entry  (현행 — 캐시와 같아야 한다, 확인한다)
    켬  : 줄 → split_wide_lines → boxes_norm → entry

    (1) 브로크만 50장 — 선 채점 (brockmann_stage2_score.line_score) · A · C 블록 · 오라클 · 미검출 원인.
        VLM 묶음은 줄 번호가 바뀌어 기존 결과를 쓸 수 없다 — «옵션 적용 시 VLM 재실행 필요» 로만 적는다.
    (2) 합성 평가 세트 650장 — eval/synth_score 의 score_poster · summarize, 셀별.

이 결과로 상수 · 파이프라인 · 사전등록을 고치지 않는다.

    python eval/explore_split_lines.py --work ~/.typo-mcp/brockmann50 --cache ~/.typo-mcp/brockmann.json \
        --guides … --consensus docs/brockmann_consensus_refs.json \
        --synth-lines ~/.typo-mcp/synth_eval_lines --synth-cache-dir ~/.typo-mcp/synth_eval_cache \
        --out docs/split_lines_explore.json
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
import detector_score as DSc               # noqa: E402
import group_gap as GG                     # noqa: E402
import group_score as GS                   # noqa: E402
import brockmann_stage2_score as S2        # noqa: E402
import synth_score as SY                   # noqa: E402
from measure import ground as G            # noqa: E402

KINDS = ('베이스라인', 'x높이선', '상단 잉크선')
REFS = ('라벨러B', '라벨러A', '합의')


def r4(x):
    return None if x is None else round(float(x), 4)


def measure(path, lines, size, photo=True):
    return G.entry(path, DS.boxes_norm(lines, size), coords='norm', photo=photo)[0]['blocks']


def spans(lines, blocks):
    """라벨 블록 기준 줄 상자 종류 — 서로 가로로 떨어진 블록 둘 이상을 덮으면 «두 단»."""
    out = []
    for l in lines:
        hit = [b for b in blocks if min(l[2], b[2]) - max(l[0], b[0]) > 0
               and min(l[3], b[3]) - max(l[1], b[1]) >= 0.5 * (l[3] - l[1])]
        dis = any(min(a[2], c[2]) - max(a[0], c[0]) <= 0 for a in hit for c in hit if a is not c)
        out.append('두 단' if len(hit) >= 2 and dis else ('한 단' if len(hit) == 1 else ('없음' if not hit else '기타')))
    return out


def score_cuts(R, lines, parent, pieces):
    """갈린 자리 채점 (참조 블록 R 기준). 줄 상자와 세로로 반 넘게 겹치고 가로로 겹치는 블록만 본다.
    맞음 = x 가 서로 다른 두 블록 사이 · 틀림 = x 가 한 블록 안 · 판정 불가 = 그 밖.
    갈라야 할 자리 = 가로로 떨어진 이웃 블록 쌍 (그 줄 상자가 둘 다 덮을 때), 그 사이에 자른 x 가 있으면 갈림."""
    c = collections.Counter(); wrong = []
    cuts_of = collections.defaultdict(list)
    for j, pa in enumerate(parent):
        cuts_of[pa].append(pieces[j])
    for i, l in enumerate(lines):
        h = l[3] - l[1]
        hit = sorted([b for b in R if min(l[2], b[2]) - max(l[0], b[0]) > 0 and min(l[3], b[3]) - max(l[1], b[1]) >= 0.5 * h],
                     key=lambda b: b[0])
        cx = [q[2] for q in sorted(cuts_of[i], key=lambda q: q[0])[:-1]]
        for x in cx:
            inside = [b for b in hit if b[0] <= x <= b[2]]
            between = any(a[2] <= x <= b[0] for a in hit for b in hit if a is not b)
            if inside:
                c['틀림'] += 1; wrong.append(dict(줄=i, x=round(x, 1), 상자=[round(v, 1) for v in l]))
            elif between:
                c['맞음'] += 1
            else:
                c['판정 불가'] += 1
        for a, b in zip(hit, hit[1:]):
            if a[2] <= b[0]:                      # 가로로 떨어진 이웃 쌍
                c['갈라야 할 자리'] += 1
                c['갈린 자리'] += any(a[2] <= x <= b[0] for x in cx)
    return c, wrong


def missed_causes(p, mblocks):
    """합의 참조 베이스라인 미검출과 원인 (창 0.5·행간 · 허용 0.2·행간, 1:1).
    가로 병합 = 못 짝지은 글줄 ±1px 안에 가로로 겹치는 측정 베이스라인이 있는데 그것이 다른 글줄과 짝지어진 경우."""
    num = lambda v: isinstance(v, (int, float))
    T = []
    for b in p['blocks']:
        if b.get('flag'):
            continue
        bs = [l['base'] for l in b['lines'] if num(l.get('base'))]
        if len(bs) > 1:
            Ld = float(np.median(np.diff(sorted(bs))))
        else:
            xh = [l['base'] - l['xh'] for l in b['lines'] if num(l.get('xh')) and num(l.get('base'))]
            Ld = 2.0 * (xh[0] if xh else 10.0)
        for l in b['lines']:
            if num(l.get('base')):
                T.append(dict(y=l['base'], lead=Ld, x1=b['box'][0], x2=b['box'][2]))
    P = [(v, mb['x1'], mb['x2']) for mb in mblocks for v in mb['bases']]
    cand = sorted((abs(q[0] - t['y']), i, j) for i, t in enumerate(T) for j, q in enumerate(P)
                  if abs(q[0] - t['y']) <= 0.5 * t['lead'] and min(t['x2'], q[2]) - max(t['x1'], q[1]) > 0)
    mi, mj, hit = set(), set(), {}
    for _d, i, j in cand:
        if i in mi or j in mj:
            continue
        mi.add(i); mj.add(j)
        hit[i] = abs(P[j][0] - T[i]['y']) <= 0.2 * T[i]['lead']
    c = collections.Counter(글줄=len(T))
    st = []
    for i, t in enumerate(T):
        if hit.get(i):
            st.append('짝'); continue
        c['미검출'] += 1
        near = [j for j, q in enumerate(P) if abs(q[0] - t['y']) <= 1 and min(t['x2'], q[2]) - max(t['x1'], q[1]) > 0]
        if any(j in mj for j in near):
            k_ = '가로 병합'
        elif not any(abs(q[0] - t['y']) <= 0.5 * t['lead'] and min(t['x2'], q[2]) - max(t['x1'], q[1]) > 0 for q in P):
            k_ = '띠 없음'
        else:
            k_ = '어긋남'
        c[k_] += 1; st.append(k_)
    return c, st


def brockmann(a):
    Wk = os.path.expanduser(a.work)
    man = json.load(open(os.path.join(Wk, 'manifest.json'))); root = os.path.expanduser(man['image_root'])
    L = json.load(open(os.path.join(Wk, 'lines.json')))['lines']
    cache = json.load(open(os.path.expanduser(a.cache)))['raw']
    labs = S2.load_labelers(a.guides)
    refs = {n: labs[n]['posters'] for n in S2.LABELERS}
    refs['합의'] = S2.load_consensus(a.consensus)
    C = json.load(open(a.consensus))
    cons = {p['order']: p for p in C['posters']}
    Pl = {it['order']: it for it in json.load(open(a.posters))['main']}
    lin = {c: collections.defaultdict(collections.Counter) for c in ('끔', '켬')}
    blk = {c: collections.defaultdict(collections.Counter) for c in ('끔', '켬')}
    blk_aff = {c: collections.defaultdict(collections.Counter) for c in ('끔', '켬')}
    orc = {c: collections.defaultdict(collections.Counter) for c in ('끔', '켬')}
    mis = {c: collections.Counter() for c in ('끔', '켬')}
    sp = collections.Counter(); aff = []; same_cache = 0
    status = {'끔': {}, '켬': {}}; cut_list = []
    cutsc = collections.defaultdict(collections.Counter); wrong_cuts = collections.defaultdict(list)
    prs = {c: collections.defaultdict(list) for c in ('끔', '켬')}
    for it in sorted(man['items'], key=lambda x: x['order']):
        o = it['order']; k = GS._key(it['seed']); path = os.path.join(root, it['image'])
        pl = Pl[o]; ck = f"{pl['folder']}__{pl['file']}"
        gray = np.asarray(Image.open(path).convert('L')).astype(float)
        size = tuple(L[k]['size'])
        lines = {'끔': L[k]['lines']}
        lines['켬'], parent = DS.split_wide_lines(gray, L[k]['lines'])
        n_split = len(lines['켬']) - len(lines['끔'])
        kinds = spans(L[k]['lines'], [b['box'] for b in cons[o]['blocks'] if not b.get('flag')]) if o in cons else []
        cnt = collections.Counter(parent)
        for i, kd in enumerate(kinds):
            sp[f'{kd}|줄'] += 1
            sp[f'{kd}|갈림'] += (cnt[i] > 1)
            if cnt[i] > 1:
                pieces = [lines['켬'][j] for j, pa in enumerate(parent) if pa == i]
                l0 = L[k]['lines'][i]
                cut_list.append(dict(order=o, 판=it['image'], 줄=i, 종류=kd, 상자=[round(v, 1) for v in l0],
                                     자른_x=[round(q[2], 1) for q in pieces[:-1]],
                                     자른_위치_상자폭몫=[round((q[2] - l0[0]) / (l0[2] - l0[0]), 3) for q in pieces[:-1]]))
        sp['갈린_줄상자'] += sum(1 for v in cnt.values() if v > 1); sp['새로_생긴_조각'] += n_split
        if n_split:
            aff.append(o)
        for ref, RP in refs.items():
            if o in RP and S2.kept(RP[o]):
                Rb = [r['box'] for r in S2.refs_of(RP[o], 'main')[0]]
                cc_, ww_ = score_cuts(Rb, [list(DS._norm(l)) for l in L[k]['lines']], parent, lines['켬'])
                cutsc[ref].update(cc_)
                wrong_cuts[ref] += [dict(order=o, 판=it['image'], **w) for w in ww_]
        mb = {c: measure(path, lines[c], size) for c in lines}
        same_cache += (mb['끔'] == cache[ck]['blocks'])
        for c in ('끔', '켬'):
            if o in cons:
                cc_, st_ = missed_causes(cons[o], mb[c])
                mis[c].update(cc_); status[c][o] = st_
            A = [(n, tuple(b[:4])) for n, b in enumerate(DS.group(lines[c]))]
            c_asg, cd = GG.group_gap(gray, lines[c], pad_rule=S2.C_PAD)
            Cb = [(g, tuple(b[:4])) for g, b in GS.boxes_of(lines[c], c_asg)]
            for ref, RP in refs.items():
                if o not in RP or not S2.kept(RP[o]):
                    continue
                p = RP[o]
                R, X = S2.refs_of(p, 'main')
                for m, Pm in (('A', A), ('C', Cb)):
                    cc = S2.block_counts(R, X, Pm, S2.IOU_MAIN)
                    blk[c][(ref, m)].update(cc)
                    if n_split:
                        blk_aff[c][(ref, m)].update(cc)
                oc = S2.oracle(p, lines[c], gray)[0]
                orc[c][ref].update(oc)
                res = S2.line_score(p, mb[c])[0]
                for kd in KINDS:
                    r = res[kd]
                    lin[c][(ref, kd)].update(T=len(r['T']), P=len(r['P']), hit=sum(q['hit'] for q in r['pairs']))
                    prs[c][(ref, kd)] += r['pairs']
    def bs(cn):
        return dict(짝=cn['짝'], 참조=cn['참조'], 묶음=cn['묶음'], 과병합=cn['과병합'], 과분할=cn['과분할'],
                    재현=r4(S2._div(cn['짝'], cn['참조'])), 정밀=r4(S2._div(cn['짝'], cn['묶음'])),
                    F1=r4(S2._f1(cn['짝'], cn['참조'], cn['묶음'])))
    out = dict(
        캐시와_같은_판_끔=same_cache, 판=len(man['items']),
        줄상자_가르기=dict(sp), 갈린_판=aff,
        선={c: {f'{ref}|{kd}': dict(참값=v['T'], 측정=v['P'], 짝=v['hit'],
                                     재현율=r4(S2._div(v['hit'], v['T'])), 정밀도=r4(S2._div(v['hit'], v['P'])),
                                     오차_절대_중앙=S2._stats(prs[c][(ref, kd)], v['T'], v['P'])['오차_절대_중앙'])
                 for (ref, kd), v in lin[c].items()} for c in lin},
        분할_채점={ref: dict(**dict(v), 정밀도=r4(S2._div(v['맞음'], v['맞음'] + v['틀림'])),
                          재현율=r4(S2._div(v['갈린 자리'], v['갈라야 할 자리']))) for ref, v in cutsc.items()},
        틀린_자리=dict(wrong_cuts),
        블록_전체={c: {f'{ref}|{m}': bs(v) for (ref, m), v in blk[c].items()} for c in blk},
        블록_갈린판만={c: {f'{ref}|{m}': bs(v) for (ref, m), v in blk_aff[c].items()} for c in blk_aff},
        오라클={c: {ref: dict(짝=v['짝'], 참조=v['참조'], 오라클_블록=v['오라클_블록'],
                             재현=r4(S2._div(v['짝'], v['참조'])), F1=r4(S2._f1(v['짝'], v['참조'], v['오라클_블록'])))
                     for ref, v in orc[c].items()} for c in orc},
        미검출_합의={c: dict(v) for c, v in mis.items()},
        가로병합_줄의_켬_상태=dict(collections.Counter(
            status['켬'][o][i] for o in status['끔'] for i, s_ in enumerate(status['끔'][o]) if s_ == '가로 병합')),
        켬에서_새로_생긴_미검출=dict(collections.Counter(
            status['켬'][o][i] for o in status['끔'] for i, s_ in enumerate(status['끔'][o])
            if s_ == '짝' and status['켬'][o][i] != '짝')),
        잘린_줄상자=cut_list,
        VLM='옵션 적용 시 VLM 재실행 필요 — 줄 번호가 바뀌어 기존 VLM 묶음(봉인 결과)을 쓸 수 없다')
    return out


def synth(a):
    D = os.path.expanduser(a.synth_lines)
    man = json.load(open(os.path.join(D, 'manifest.json')))
    L = json.load(open(os.path.join(D, 'lines.json')))['lines']
    caches = {}
    per = {c: collections.defaultdict(dict) for c in ('끔', '켬')}
    split_n = collections.Counter(); same = collections.Counter(); tot = collections.Counter()
    for it in man['items']:
        k = f"{it['seed']:03d}"; cell = it['cell']; path = it['image']
        if cell not in caches:
            caches[cell] = json.load(open(os.path.join(os.path.expanduser(a.synth_cache_dir), f'synth-{cell}.json')))['raw']
        key = f"{cell}/{int(os.path.basename(path)[:-4]):03d}" if f"{cell}/{int(os.path.basename(path)[:-4]):03d}" in caches[cell] \
            else next(c for c in caches[cell] if c.endswith('/' + os.path.basename(path)[:-4]))
        gray = np.asarray(Image.open(path).convert('L')).astype(float)
        size = tuple(L[k]['size'])
        on_lines, parent = DS.split_wide_lines(gray, L[k]['lines'])
        split_n[cell] += len(on_lines) - len(L[k]['lines'])
        truth = json.load(open(path[:-4] + '.json'))
        for c, ln in (('끔', L[k]['lines']), ('켬', on_lines)):
            e = G.entry(path, DS.boxes_norm(ln, size), coords='norm', photo=False)[0]
            if c == '끔':
                same[cell] += (e['blocks'] == caches[cell][key]['blocks']); tot[cell] += 1
            per[c][cell][key] = SY.score_poster(truth, e)
    out = {}
    for cell in sorted(per['끔']):
        row = {}
        for c in ('끔', '켬'):
            S = SY.summarize(list(per[c][cell].values()))
            d = S['선_직접_짝']
            row[c] = dict(줄_재현율=S['줄_재현율'], 줄_정밀도=S['줄_정밀도'], 블록_재현율=S['블록_재현율'],
                          과병합=S['과병합'], 과분할=S['과분할'],
                          베이스라인_재현=d['베이스라인']['재현율'], 베이스라인_정밀=d['베이스라인']['정밀도'],
                          x높이선_재현=d['x높이선']['재현율'], 상단잉크선_재현=d['캡선']['재현율'])
        out[cell] = dict(**row, 새로_생긴_조각=split_n[cell], 캐시와_같은_판_끔=f'{same[cell]}/{tot[cell]}')
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--work', required=True); ap.add_argument('--cache', required=True)
    ap.add_argument('--guides', nargs='+', required=True); ap.add_argument('--consensus', required=True)
    ap.add_argument('--posters', required=True)
    ap.add_argument('--synth-lines', required=True); ap.add_argument('--synth-cache-dir', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    res = dict(what='탐색용 · 논문 수치 아님',
               무엇=('줄 상자 가르기(detect_surya.split_wide_lines) 를 켠 값과 끈 값 — 규칙은 그 함수 docstring '
                    '(27b0697 부터 «세로 빈 통로» 주 규칙 · 견줄 행이 없을 때만 폭 기준 SPLIT_LINE_GAP)'),
               문턱=DS.SPLIT_LINE_GAP,
               주의=['기본 경로는 이 처리를 부르지 않는다. 끈 값이 현행 캐시와 같은지 판마다 확인했다',
                    'VLM 묶음은 다시 돌리지 않았다 — 옵션 적용 시 VLM 재실행 필요',
                    '이 결과로 상수 · 파이프라인 · 사전등록을 고치지 않는다'])
    print('브로크만 50장 …', flush=True)
    res['브로크만'] = brockmann(a)
    print('합성 평가 세트 650장 …', flush=True)
    res['합성'] = synth(a)
    json.dump(res, open(a.out, 'w'), ensure_ascii=False, indent=1)
    print('→', a.out)


if __name__ == '__main__':
    main()
