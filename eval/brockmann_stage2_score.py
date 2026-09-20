"""브로크만 실물 50장 2단계 채점 — 사전등록 docs/brockmann_stage2_preregister.json (f844621, 수정 1 21a61a2 · 수정 2 3396590).

    python eval/brockmann_stage2_score.py check --guides G1.json G2.json --posters docs/labeling/posters_for_labelers.json
    python eval/brockmann_stage2_score.py consensus --guides G1.json G2.json --posters … --out docs/brockmann_consensus_refs.json
    python eval/brockmann_stage2_score.py score --unseal --unsealed-at … --unsealed-commit … \\
        --guides G1.json G2.json [--consensus docs/brockmann_consensus_refs.json] --posters … --selection docs/labeling/selection.json \\
        --work ~/.typo-mcp/brockmann50 --vlm boxes/brockmann_vlm_pass1.json --vlm boxes/brockmann_vlm_pass2.json \\
        --cache ~/.typo-mcp/brockmann.json --prereg docs/brockmann_stage2_preregister.json --out docs/brockmann_stage2_result.json

check · consensus 는 1단계 봉인 파일을 읽지 않는다. score 는 봉인 파일(Surya 줄 · VLM 패스)을 읽으므로 --unseal 없이는 돌지 않는다.
사전등록에 적힌 정의만 구현한다. 새 지표를 더하지 않는다. 결과는 «정확도» 가 아니라 «참조와의 일치도» 다 (라벨러 2).
세 값을 나란히 낸다 (수정 1): ① 라벨러B 기준 · ② 라벨러A 기준 · ③ 두 라벨러 일치 항목 (채점 범위를 좁힌 값, 새 참조가 아니다).
셋을 합친 판정은 내지 않는다.
"""
import argparse
import hashlib
import json
import os
import sys
from collections import Counter, defaultdict

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
import detect_surya as DS                  # noqa: E402
import detector_score as DSc               # noqa: E402
import group_gap as GG                     # noqa: E402
import group_score as GS                   # noqa: E402
import oracle_group as OG                  # noqa: E402  ink_lines · covered (오라클 원인 3 의 잉크 줄)
from measure import ground as G            # noqa: E402
from brockmann_group_explore import neighbours   # noqa: E402  1단계와 같은 이웃 정의

# ── 사전등록 값 (바꾸지 않는다) ──────────────────────────────────
LABELERS = ('라벨러A', '라벨러B')             # 차 = 라벨러A − 라벨러B (부호 약속일 뿐)
VALUES = ('라벨러B', '라벨러A', '일치')        # 보고 차례 — ① 라벨러B 기준 · ② 라벨러A 기준 · ③ 두 라벨러 일치 항목 (수정 1)
IOU_MAIN, IOU_SENS = 0.5, 0.3
INSIDE = DSc.INSIDE                        # 0.5
LINE_WIN, LINE_TOL = 0.5, 0.2              # 합성 판 전체 직접 짝과 같다
OUTSIDE = OG.OUTSIDE                       # 0.5 — 오라클 원인 «상자를 넘는 줄»
SIZE_RATIO, SMALL_H, SMALL_W = 1.5, 0.6, 0.25   # 추가 1 유형 값
MIN_PAIRS = 10                             # 추가 1 · S3 판단 가능 최소 수
C_PAD = 'neighbor_half'
BOOT_N, BOOT_SEED = 2000, 20260914
SYNTH_DIFF = {'VLM1': 0.023, 'VLM2': 0.017}     # 추가 1 E1 — 합성 층 가중 (VLM − C) 블록 F1
SYNTH_C_FALLBACK = 0.010                   # S2 · E3 — 합성 깨끗한 세트 Surya 줄 기준
SYNTH_ORACLE = 1.000                       # S4
LEGACY = {'없음': 'no_glyph', '못 가림': 'illegible', '가로 아님': 'rotated', '활자 아님': 'lettering'}
TYPES = ('base', 'cap', 'asc', 'xh')
TNAME = dict(base='베이스라인', cap='캡선', asc='어센더선', xh='x높이선')
STATE = {'no_glyph': '글자 없음', 'illegible': '판독 불가'}


def _tilde(p):
    """기록에 남기는 경로는 홈을 ~ 로 접는다."""
    h = os.path.expanduser('~')
    return '~' + p[len(h):] if p.startswith(h) else p


def _sha(p):
    return hashlib.sha256(open(os.path.expanduser(p), 'rb').read()).hexdigest()


def _code(v):
    return LEGACY.get(v, v) if v is not None else None


def _cell(g):
    """칸 값 → 정수 y · 'no_glyph' · 'illegible' · None(미입력)."""
    if g is None:
        return None
    if g.get('y') is not None:
        return int(g['y'])
    return _code(g.get('mark'))


def _num(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _q(a, p):
    a = [x for x in a if x is not None]
    return round(float(np.percentile(a, p)), 3) if a else None


def _r(x, n=4):
    return None if x is None else round(float(x), n)


def _div(a, b):
    return (a / b) if b else None


def _f1(pairs, n1, n2):
    return _div(2 * pairs, n1 + n2)


# ── 라벨러 파일 읽기 · 수령 검증 ───────────────────────────────────

def _norm_poster(p):
    blocks = []
    for b in p.get('blocks', []):
        lines = [dict(no=l.get('no'), **{t: _cell(l.get(t)) for t in TYPES}) for l in b.get('lines', [])]
        blocks.append(dict(no=b.get('no'), box=(float(b['x1']), float(b['y1']), float(b['x2']), float(b['y2'])),
                           flag=_code(b.get('flag')), base_mark=_code(b.get('base_mark')), lines=lines))
    return dict(order=p['order'], folder=p.get('folder'), file=p.get('file'), sha256=p.get('sha256'),
                done=bool(p.get('done')), n_missing=p.get('n_missing'), n_invalid=p.get('n_invalid'), blocks=blocks)


def load_labelers(paths):
    """라벨러마다 가장 늦은 exported_at 파일을 쓴다. {이름: 정보}."""
    by = defaultdict(list)
    for path in paths:
        o = json.load(open(os.path.expanduser(path)))
        if o.get('schema') not in ('typo-guides/1', 'typo-guides/2'):
            sys.exit(f'가이드 긋기 도구가 내보낸 파일이 아니다: {path}')
        by[o.get('labeler')].append((o.get('exported_at') or '', path, o))
    if set(by) != set(LABELERS):
        sys.exit(f'라벨러 이름이 {LABELERS} 와 다르다: {sorted(map(str, by))}')
    out = {}
    for name, fs in by.items():
        fs.sort(key=lambda t: t[0])
        at, path, o = fs[-1]
        out[name] = dict(file=path, sha256=_sha(path), exported_at=at, schema=o['schema'], data_fp=o.get('data_fp'),
                         tool=o.get('tool'), skipped=[p for _a, p, _o in fs[:-1]],
                         posters={p['order']: _norm_poster(p) for p in o['posters'] if p.get('set') == 'main'})
    return out


def kept(p):
    """사전등록 «판» — done 이고 n_missing · n_invalid 가 0 인 판만."""
    return p['done'] and p['n_missing'] == 0 and p['n_invalid'] == 0


def receipt(labs, posters_path):
    P = json.load(open(posters_path)); main = {it['order']: it for it in P['main']}
    rep, ok = dict(목록=posters_path, 목록_sha256=_sha(posters_path), 판=len(main)), True
    fps = {n: v['data_fp'] for n, v in labs.items()}
    rep['data_fp_같음'] = len(set(fps.values())) == 1
    ok &= rep['data_fp_같음']
    for name in LABELERS:
        v = labs[name]; ps = v['posters']
        bad_sha = [o for o, it in main.items() if o not in ps or ps[o]['sha256'] != it['sha256']
                   or ps[o]['folder'] != it['folder'] or ps[o]['file'] != it['file']]
        extra = sorted(set(ps) - set(main))
        out_p = {o: dict(done=p['done'], n_missing=p['n_missing'], n_invalid=p['n_invalid'])
                 for o, p in sorted(ps.items()) if not kept(p)}
        blocks = [b for p in ps.values() for b in p['blocks']]
        rep[name] = dict(파일=v['file'], 파일_sha256=v['sha256'], 내보낸_때=v['exported_at'], schema=v['schema'], 도구=v['tool'],
                         쓰지_않은_옛_파일=v['skipped'], main_판=len(ps), 목록과_다른_판=bad_sha, 목록에_없는_판=extra,
                         채점에서_빼는_판=out_p, 남는_판=len(ps) - len(out_p), 블록=len(blocks),
                         제외_사유=dict(Counter(b['flag'] for b in blocks if b['flag'])),
                         글줄_판독_불가_블록=sum(1 for b in blocks if b['base_mark'] == 'illegible'),
                         글줄=sum(len(b['lines']) for b in blocks),
                         칸_상태={TNAME[t]: dict(Counter('선' if _num(l[t]) else STATE.get(l[t], '미입력')
                                                       for b in blocks for l in b['lines'])) for t in TYPES})
        ok &= not bad_sha and not extra and len(ps) == len(main)
    rep['통과'] = bool(ok)
    return rep


def cmd_check(a):
    labs = load_labelers(a.guides)
    rep = receipt(labs, a.posters)
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    if a.out:
        json.dump(rep, open(a.out, 'w'), ensure_ascii=False, indent=1)
    sys.exit(0 if rep['통과'] else 1)


# ── 기하 ────────────────────────────────────────────────────────

def match_t(R, P, t):
    """detector_score.match 와 같다 — 문턱만 인자."""
    pairs = sorted(((DSc.iou(r, p), i, j) for i, r in enumerate(R) for j, p in enumerate(P)), key=lambda x: -x[0])
    mr, mp = {}, {}
    for v, i, j in pairs:
        if v < t:
            break
        if i in mr or j in mp:
            continue
        mr[i], mp[j] = j, i
    return mr, mp


def _union(bs):
    return (min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs))


def _xo(a, b):
    return min(a[2], b[2]) - max(a[0], b[0])


# ── 합의 참조 ─────────────────────────────────────────────────────

def _half_even(x):
    return int(round(x))


def block_L(block, poster_med):
    """행간 L — 사전등록 «선 채점 · 행간 L» 의 차례. (값, 규칙 번호)."""
    bases = sorted(l['base'] for l in block['lines'] if _num(l['base']))
    if len(bases) >= 2:
        return float(np.median(np.diff(bases))), 1
    hx = [l['base'] - l['xh'] for l in block['lines'] if _num(l['base']) and _num(l['xh'])]
    if hx:
        return 2.0 * float(np.median(hx)), 2
    if poster_med is not None:
        return poster_med, 3
    return None, None


def poster_L_med(blocks):
    v = []
    for b in blocks:
        bases = sorted(l['base'] for l in b['lines'] if _num(l['base']))
        if len(bases) >= 2:
            v.append(float(np.median(np.diff(bases))))
    return float(np.median(v)) if v else None


def pair_lines(bs, bm, Ls, Lm):
    """짝지은 블록 안 글줄 짝 — 베이스라인 차가 작은 순서로 1:1, |차| ≤ 0.5 × L (L = 두 라벨러 값 가운데 작은 쪽)."""
    Lv = [x for x in (Ls, Lm) if x is not None]
    if not Lv:
        return None
    L = min(Lv)
    ls = [(i, l) for i, l in enumerate(bs['lines']) if _num(l['base'])]
    lm = [(j, l) for j, l in enumerate(bm['lines']) if _num(l['base'])]
    cand = sorted((abs(p['base'] - q['base']), i, j) for i, p in ls for j, q in lm if abs(p['base'] - q['base']) <= LINE_WIN * L)
    ui, uj, out = set(), set(), []
    for _d, i, j in cand:
        if i in ui or j in uj:
            continue
        ui.add(i); uj.add(j); out.append((i, j))
    return out


def consensus_poster(S, M):
    """사전등록 «합의 참조». 제외: 어느 한쪽이라도 제외 사유가 있는 짝과 짝 없는 제외 블록을 뺀다 → 남은 블록끼리 다시 짝짓는다."""
    allS, allM = [b['box'] for b in S['blocks']], [b['box'] for b in M['blocks']]
    mr, _ = match_t(allS, allM, IOU_MAIN)
    drop_s, drop_m, excl = set(), set(), []
    for i, j in mr.items():
        if S['blocks'][i]['flag'] or M['blocks'][j]['flag']:
            drop_s.add(i); drop_m.add(j)
            excl.append(dict(box=[S['blocks'][i]['box'], M['blocks'][j]['box']], flag=[S['blocks'][i]['flag'], M['blocks'][j]['flag']]))
    for i, b in enumerate(S['blocks']):
        if b['flag'] and i not in drop_s:
            drop_s.add(i); excl.append(dict(box=[b['box']], flag=[b['flag'], None]))
    for j, b in enumerate(M['blocks']):
        if b['flag'] and j not in drop_m:
            drop_m.add(j); excl.append(dict(box=[b['box']], flag=[None, b['flag']]))
    rs = [i for i in range(len(S['blocks'])) if i not in drop_s]
    rm = [j for j in range(len(M['blocks'])) if j not in drop_m]
    mr2, _ = match_t([allS[i] for i in rs], [allM[j] for j in rm], IOU_MAIN)
    medS, medM = poster_L_med([S['blocks'][i] for i in rs]), poster_L_med([M['blocks'][j] for j in rm])
    blocks, mismatch = [], []
    for ii, jj in sorted(mr2.items()):
        bs, bm = S['blocks'][rs[ii]], M['blocks'][rm[jj]]
        box = tuple(_half_even((u + v) / 2) for u, v in zip(bs['box'], bm['box']))
        lp = pair_lines(bs, bm, block_L(bs, medS)[0], block_L(bm, medM)[0]) or []
        lines = []
        for i, j in lp:
            p, q = bs['lines'][i], bm['lines'][j]
            ln = {}
            for t in TYPES:
                u, v = p[t], q[t]
                if _num(u) and _num(v) and abs(u - v) <= 1:
                    ln[t] = _half_even((u + v) / 2)
                elif not _num(u) and not _num(v) and u is not None and u == v:
                    ln[t] = u
                else:
                    ln[t] = None
                    mismatch.append(dict(종류='칸', 블록=[bs['no'], bm['no']], 글줄=[p['no'], q['no']], 선=TNAME[t], 값=[u, v]))
            lines.append(ln)
        for i, l in enumerate(bs['lines']):
            if i not in {x for x, _ in lp}:
                mismatch.append(dict(종류='짝 없는 글줄', 라벨러='라벨러A', 블록=bs['no'], 글줄=l['no']))
        for j, l in enumerate(bm['lines']):
            if j not in {y for _, y in lp}:
                mismatch.append(dict(종류='짝 없는 글줄', 라벨러='라벨러B', 블록=bm['no'], 글줄=l['no']))
        blocks.append(dict(no=len(blocks) + 1, box=box, flag=None,
                           base_mark=('illegible' if bs['base_mark'] == bm['base_mark'] == 'illegible' else None),
                           lines=sorted(lines, key=lambda l: l['base'] if _num(l['base']) else 1e9)))
    for ii in range(len(rs)):
        if ii not in mr2:
            mismatch.append(dict(종류='짝 없는 블록', 라벨러='라벨러A', 블록=S['blocks'][rs[ii]]['no']))
    jm = set(mr2.values())
    for jj in range(len(rm)):
        if jj not in jm:
            mismatch.append(dict(종류='짝 없는 블록', 라벨러='라벨러B', 블록=M['blocks'][rm[jj]]['no']))
    for e in excl:
        for bx in e['box']:
            blocks.append(dict(no=len(blocks) + 1, box=tuple(bx), flag=next(f for f in e['flag'] if f), base_mark=None, lines=[]))
    return dict(order=S['order'], folder=S['folder'], file=S['file'], sha256=S['sha256'], done=True, n_missing=0, n_invalid=0,
                blocks=blocks), mismatch


def cmd_consensus(a):
    labs = load_labelers(a.guides)
    rep = receipt(labs, a.posters)
    if not rep['통과']:
        sys.exit('수령 검증을 통과하지 못했다 — check 결과를 본다')
    S, M = labs['라벨러A']['posters'], labs['라벨러B']['posters']
    posters, mism = [], {}
    for o in sorted(set(S) & set(M)):
        if not (kept(S[o]) and kept(M[o])):
            continue
        p, mm = consensus_poster(S[o], M[o])
        posters.append(p); mism[o] = mm
    out = dict(schema='typo-guides-consensus/1', 무엇='두 라벨러 합의 참조 — 보조, 주 결과 아님 (사전등록 «합의 참조»)',
               사전등록=a.prereg, 사전등록_sha256=_sha(a.prereg), 라벨러_파일={n: dict(파일=v['file'], sha256=v['sha256']) for n, v in labs.items()},
               적는_법='«두 라벨러가 함께 그은 블록 · 선에 대한 일치도» 로만 적는다',
               posters=[dict(order=p['order'], folder=p['folder'], file=p['file'], sha256=p['sha256'],
                             blocks=[dict(b, box=list(b['box'])) for b in p['blocks']]) for p in posters],
               불일치={str(o): v for o, v in mism.items()},
               불일치_수=dict(Counter(e['종류'] for v in mism.values() for e in v)))
    json.dump(out, open(a.out, 'w'), ensure_ascii=False, indent=1)
    print(f"합의 참조 판 {len(posters)} · 블록 {sum(len(p['blocks']) for p in posters)} · 불일치 {out['불일치_수']} → {a.out}")


def load_consensus(path):
    o = json.load(open(path))
    if o.get('schema') != 'typo-guides-consensus/1':
        sys.exit(f'합의 참조 파일이 아니다: {path}')
    return {p['order']: dict(order=p['order'], folder=p['folder'], file=p['file'], sha256=p['sha256'], done=True, n_missing=0,
                             n_invalid=0, blocks=[dict(b, box=tuple(b['box'])) for b in p['blocks']]) for p in o['posters']}


# ── 판 하나 채점 ──────────────────────────────────────────────────

def refs_of(p, variant):
    """variant 'main' — 제외 사유 블록만 뺀다. 'no_illegible' — 글줄 판독 불가 블록도 뺀다 (민감도)."""
    R = [b for b in p['blocks'] if not b['flag'] and (variant == 'main' or b['base_mark'] != 'illegible')]
    X = [b for b in p['blocks'] if b['flag'] or (variant != 'main' and b['base_mark'] == 'illegible')]
    return R, X


def block_counts(R, X, P, t, src=None):
    """P = [(묶음 id, 상자)]. src = {묶음 id: 출처} (C 만)."""
    keep = [(g, b) for g, b in P if not any(DSc.inside(b, x['box']) >= INSIDE for x in X)]
    Rb = [r['box'] for r in R]; Pb = [b for _g, b in keep]
    mr, mp = match_t(Rb, Pb, t)
    c = Counter(참조=len(Rb), 묶음=len(Pb), 짝=len(mr), 제외로_뺀_묶음=len(P) - len(keep),
                과병합=sum(1 for b in Pb if sum(1 for r in Rb if DSc.held(b, r) >= INSIDE) >= 2),
                과분할=sum(1 for j, b in enumerate(Pb) if j not in mp and any(DSc.inside(b, r) >= INSIDE for r in Rb)),
                헛것=sum(1 for b in Pb if all(DSc.inter(b, r) == 0 for r in Rb)))
    if src is not None:
        c['짝_출처A'] = sum(1 for j in mp if src.get(keep[j][0]) == 'A')
    return c


def oracle(p, lines, gray):
    R, X = refs_of(p, 'main')
    Rb = [r['box'] for r in R]
    live = [i for i, l in enumerate(lines) if not any(DSc.inside(l, x['box']) >= INSIDE for x in X)]
    owner, orphan = {}, 0
    for i in live:
        best, bi = 0.0, None
        for k, r in enumerate(Rb):
            v = DSc.inter(lines[i], r)
            if v > best:
                best, bi = v, k
        if bi is None:
            orphan += 1
        else:
            owner[i] = bi
    groups = defaultdict(list)
    for i, k in owner.items():
        groups[k].append(i)
    P = [(k, _union([lines[i] for i in groups[k]])) for k in sorted(groups)]
    mr, mp = match_t(Rb, [b for _k, b in P], IOU_MAIN)

    def cause(k):
        r = Rb[k]; mine = groups.get(k, [])
        if mine and DSc.iou(_union([lines[i] for i in mine]), r) >= IOU_MAIN:
            return '그 밖', '1:1 충돌'
        if not any(DSc.inter(lines[i], r) > 0 for i in live):
            return '줄을 못 찾음', '전부'
        if not mine:
            return '줄 상자가 두 블록에 걸침', '이웃 블록으로 간 줄'
        hb = [l['base'] for l in R[k]['lines'] if _num(l['base'])]
        if hb:
            miss = any(not any(lines[j][1] <= y <= lines[j][3] and _xo(lines[j], r) > 0 for j in mine) for y in hb)
        else:
            ink = OG.ink_lines(gray, r)
            miss = ink is not None and any(not any(OG.covered(q, lines[j]) for j in mine) for q in ink)
        if miss:
            return '줄을 못 찾음', '일부'
        over = [j for j in mine if DSc.area(lines[j]) and 1 - DSc.inter(lines[j], r) / DSc.area(lines[j]) >= OUTSIDE]
        if over:
            if any(DSc.inter(lines[j], Rb[q]) > 0 for j in over for q in range(len(Rb)) if q != k):
                return '줄 상자가 두 블록에 걸침', '상자를 넘는 줄 · 다른 블록에 걸침'
            return '그 밖', '상자를 넘는 줄 · 다른 블록 없음'
        u = _union([lines[i] for i in mine])
        how = '합집합이 작다' if DSc.inside(u, r) >= 0.8 else '합집합이 크다' if DSc.held(u, r) >= 0.8 else '어긋남'
        return '그 밖', how

    c = Counter(참조=len(Rb), 오라클_블록=len(P), 짝=len(mr), 안겹치는_줄=orphan, 제외로_뺀_줄=len(lines) - len(live))
    causes = {k: cause(k) for k in range(len(Rb)) if k not in mr}
    for k, (big, small) in causes.items():
        c[f'재현손실|{big}'] += 1; c[f'재현손실_세부|{big} · {small}'] += 1
    for j in range(len(P)):
        if j not in mp:
            k = P[j][0]
            big, small = causes[k] if k not in mr else ('그 밖', '1:1 충돌')
            c[f'정밀손실|{big}'] += 1
    return c, owner, set(mr), causes


def neighbour_pairs(p, lines, owner, els, Wd, asgs):
    """추가 1 — 이웃 참조 블록 쌍 · 유형 · 방식별 쌍 병합."""
    R, _X = refs_of(p, 'main')
    by = defaultdict(list)
    for i, k in owner.items():
        by[k].append(i)
    ebl = defaultdict(list)
    for e in els:
        ebl[e['line']].append(e['b'])
    size = {k: (float(np.median([lines[i][3] - lines[i][1] for i in by[k]])) if by.get(k) else None) for k in range(len(R))}
    elb = {k: sorted(b for i in by.get(k, []) for b in ebl.get(i, [])) for k in range(len(R))}
    lead = {k: (float(np.median(np.diff(v))) if len(v) >= 2 else None) for k, v in elb.items()}
    out = []
    for kind, i, j in neighbours([r['box'] for r in R]):
        bi, bj = R[i]['box'], R[j]['box']
        if kind == '세로':
            u, l = (i, j) if (bi[1] + bi[3]) < (bj[1] + bj[3]) else (j, i)
        else:
            u, l = i, j
        su, sl = size[u], size[l]
        merged = {}
        for m, asg in asgs.items():
            gu = Counter(asg[x] for x in by.get(u, []) if asg[x] is not None)
            gl = Counter(asg[x] for x in by.get(l, []) if asg[x] is not None)
            merged[m] = (gu.most_common(1)[0][0] == gl.most_common(1)[0][0]) if gu and gl else None
        types = set(); cont = None
        if su and sl:
            ratio = max(su, sl) / min(su, sl)
            small_k = u if su <= sl else l
            if min(su, sl) <= SMALL_H * max(su, sl) and (R[small_k]['box'][2] - R[small_k]['box'][0]) <= SMALL_W * Wd:
                types.add('나')
            if kind == '세로':
                L = lead[u] if lead[u] is not None else lead[l]
                if L is not None and elb[u] and elb[l]:
                    gap = elb[l][0] - elb[u][-1]
                    cont = abs(gap - L) <= max(1.0, 0.1 * L)
                if cont:
                    types.add('가' if ratio >= SIZE_RATIO else '다')
            if not types:
                types.add('판정 못함' if (kind == '세로' and cont is None) else '그 외')
        else:
            types.add('판정 못함')
        out.append(dict(u=u, l=l, 이웃=kind, 유형=sorted(types), 간격이_이어짐=cont, 병합=merged))
    return out


DIRECT = [('베이스라인', 'bases', lambda l: l['base']),
          ('x높이선', 'xtops', lambda l: l['xh']),
          ('상단 잉크선', 'caps', lambda l: min([v for v in (l['cap'], l['asc']) if _num(v)], default=None)),
          ('상단 잉크선_캡선만', 'caps', lambda l: l['cap']),
          ('상단 잉크선_어센더선만', 'caps', lambda l: l['asc'])]


def _direct(T, P):
    cand = sorted((abs(p[0] - t['y']), i, j) for i, t in enumerate(T) for j, p in enumerate(P)
                  if abs(p[0] - t['y']) <= LINE_WIN * t['lead'] and min(t['x2'], p[2]) - max(t['x1'], p[1]) > 0)
    mi, mj, pairs = set(), set(), []
    for _d, i, j in cand:
        if i in mi or j in mj:
            continue
        mi.add(i); mj.add(j)
        e = P[j][0] - T[i]['y']
        pairs.append(dict(t=i, p=j, err=e, hit=abs(e) <= LINE_TOL * T[i]['lead']))
    return pairs


def line_score(p, mblocks):
    """판 하나의 선 채점. 참조 블록 = 제외 사유 없는 블록 (글줄 판독 불가 블록은 글줄이 없다)."""
    R, X = refs_of(p, 'main')
    med = poster_L_med(R)
    ill = [b for b in R if b['base_mark'] == 'illegible']
    ex_f = [k for k, mb in enumerate(mblocks) if any(DSc.inside((mb['x1'], mb['y1'], mb['x2'], mb['y2']), x['box']) >= INSIDE for x in X)]
    ex_i = [k for k, mb in enumerate(mblocks) if k not in ex_f and
            any(DSc.inside((mb['x1'], mb['y1'], mb['x2'], mb['y2']), b['box']) >= INSIDE for b in ill)]
    live = [k for k in range(len(mblocks)) if k not in ex_f and k not in ex_i]
    info = Counter(측정블록_제외사유로_뺌=len(ex_f), 측정블록_판독불가로_뺌=len(ex_i))
    rule, lines = Counter(), []
    for bi, b in enumerate(R):
        if not b['lines']:
            continue
        L, rn = block_L(b, med)
        if L is None:
            info['L_없어_뺀_글줄'] += len(b['lines']); continue
        rule[rn] += 1
        for li, l in enumerate(b['lines']):
            lines.append(dict(block=bi, line=li, lead=L, x1=b['box'][0], x2=b['box'][2], l=l))
    res = {}
    for name, mk, tf in DIRECT:
        T = [dict(y=tf(x['l']), lead=x['lead'], x1=x['x1'], x2=x['x2'], k=n) for n, x in enumerate(lines) if _num(tf(x['l']))]
        P = [(mblocks[k][mk][li], mblocks[k]['x1'], mblocks[k]['x2'], k, li) for k in live
             for li in range(len(mblocks[k][mk])) if mblocks[k][mk][li] is not None]
        res[name] = dict(T=T, P=P, pairs=_direct(T, P),
                         표시=Counter(STATE.get(tf(x['l']), '미입력') for x in lines if not _num(tf(x['l']))))
    # 숫자만 있는 글줄 — 캡선 · 어센더선이 둘 다 선이 아닌 사람 글줄 + 베이스라인 짝의 caps
    B = res['베이스라인']; top = res['상단 잉크선']
    base_of = {B['T'][q['t']]['k']: (B['P'][q['p']][3], B['P'][q['p']][4]) for q in B['pairs']}
    paired_mb = set(base_of.values())
    top_pp = {(top['P'][q['p']][3], top['P'][q['p']][4]) for q in top['pairs']}
    nd = []
    for n, x in enumerate(lines):
        l = x['l']
        if not _num(l['cap']) and not _num(l['asc']) and n in base_of:
            k, li = base_of[n]
            if mblocks[k]['caps'][li] is not None:
                nd.append((k, li))
    Pn = [q for q in top['P'] if (q[3], q[4]) not in set(nd)]
    pn = _direct(top['T'], Pn)
    num = Counter(글줄=len(lines), 캡어센더_없고_caps_값=len(nd), 그_caps_짝없음=sum(1 for q in nd if q not in top_pp),
                  베이스라인_짝없어_못_이은_caps=sum(1 for k in live for li in range(len(mblocks[k]['caps']))
                                              if mblocks[k]['caps'][li] is not None and (k, li) not in paired_mb),
                  뺀_뒤_측정선=len(Pn), 뺀_뒤_창안짝=len(pn), 뺀_뒤_허용안짝=sum(q['hit'] for q in pn))
    # caps 가 무엇을 잡는가
    what = Counter()
    for q in top['pairs']:
        l = lines[top['T'][q['t']]['k']]['l']
        if _num(l['cap']) and _num(l['asc']) and abs(l['cap'] - l['asc']) >= 2:
            v = top['P'][q['p']][0]; dc, da = abs(v - l['cap']), abs(v - l['asc'])
            what['캡선에_가깝다' if dc < da else '어센더선에_가깝다' if da < dc else '같다'] += 1
    return res, lines, info, rule, num, what


# ── ③ 두 라벨러 일치 항목 (수정 1) ─────────────────────────────────

def agreed_blocks(S, M):
    """일치 블록 — 라벨러마다 제외 사유 없는 블록끼리 IoU ≥ 0.5 탐욕 1:1. (라벨러A 참조 블록, 라벨러B 참조 블록, [(송 번호, 신 번호)])."""
    RS, _ = refs_of(S, 'main'); RM, _ = refs_of(M, 'main')
    mr, _ = match_t([b['box'] for b in RS], [b['box'] for b in RM], IOU_MAIN)
    return RS, RM, sorted(mr.items())


def block_counts_agreed(S, M, RS, RM, pairs, P, t, variant, src=None):
    if variant == 'no_illegible':
        pairs = [(i, j) for i, j in pairs if RS[i]['base_mark'] != 'illegible' and RM[j]['base_mark'] != 'illegible']
    ai, aj = {i for i, _ in pairs}, {j for _, j in pairs}
    X = ([b['box'] for b in S['blocks'] if b['flag']] + [b['box'] for b in M['blocks'] if b['flag']]
         + [b['box'] for n, b in enumerate(RS) if n not in ai] + [b['box'] for n, b in enumerate(RM) if n not in aj])
    keep = [(g, b) for g, b in P if not any(DSc.inside(b, x) >= INSIDE for x in X)]
    Pb = [b for _g, b in keep]
    A = [(RS[i]['box'], RM[j]['box']) for i, j in pairs]
    cand = sorted(((min(DSc.iou(p, a[0]), DSc.iou(p, a[1])), n, m) for n, a in enumerate(A) for m, p in enumerate(Pb)),
                  key=lambda x: -x[0])
    mr, mp = {}, {}
    for v, n, m in cand:
        if v < t:
            break
        if n in mr or m in mp:
            continue
        mr[n], mp[m] = m, n
    allb = [b['box'] for b in S['blocks']] + [b['box'] for b in M['blocks']]
    c = Counter(참조=len(A), 묶음=len(Pb), 짝=len(mr), 제외로_뺀_묶음=len(P) - len(keep),
                과병합=sum(1 for p in Pb if sum(1 for a in A if min(DSc.held(p, a[0]), DSc.held(p, a[1])) >= INSIDE) >= 2),
                과분할=sum(1 for m, p in enumerate(Pb) if m not in mp and
                        any(min(DSc.inside(p, a[0]), DSc.inside(p, a[1])) >= INSIDE for a in A)),
                헛것=sum(1 for p in Pb if all(DSc.inter(p, b) == 0 for b in allb)))
    if src is not None:
        c['짝_출처A'] = sum(1 for m in mp if src.get(keep[m][0]) == 'A')
    return c


def oracle_agreed(pairs, orS, orM):
    """orS · orM = (짝지은 참조 번호, 원인). 손실은 (라벨러B 원인 / 라벨러A 원인) 쌍."""
    c = Counter(참조=len(pairs))
    for i, j in pairs:
        okS, okM = i in orS[0], j in orM[0]
        if okS and okM:
            c['짝'] += 1
        else:
            cm = '짝 지음' if okM else orM[1][j][0]
            cs = '짝 지음' if okS else orS[1][i][0]
            c[f'재현손실|{cm} / {cs}'] += 1
    return c


def neighbours_agreed(pairs, npS, npM):
    s2m = dict(pairs)
    idxM = {frozenset((q['u'], q['l'])): q for q in npM}
    out = []
    for q in npS:
        if q['u'] not in s2m or q['l'] not in s2m:
            continue
        r = idxM.get(frozenset((s2m[q['u']], s2m[q['l']])))
        if r is None or r['이웃'] != q['이웃']:
            continue
        out.append(dict(이웃=q['이웃'], 유형=sorted(set(q['유형']) & set(r['유형'])),
                        병합={m: (q['병합'][m] if q['병합'][m] == r['병합'][m] else None) for m in q['병합']}))
    return out


def _cand1(p, t):
    return abs(p[0] - t['y']) <= LINE_WIN * t['lead'] and min(t['x2'], p[2]) - max(t['x1'], p[1]) > 0


def _cand2(p, t):
    return (abs(p[0] - t['yS']) <= LINE_WIN * t['lead'] and abs(p[0] - t['yM']) <= LINE_WIN * t['lead']
            and min(t['x2'], p[2]) - max(t['x1'], p[1]) > 0)


def _match_agreed(T, P, fullS, fullM):
    """일치 칸 짝짓기 — 비용 = 두 차 가운데 큰 쪽, 허용 = 두 차 모두 ≤ 0.2 × L. 정밀 분모에서 뺄 측정 선 수도 센다."""
    cand = sorted((max(abs(p[0] - t['yS']), abs(p[0] - t['yM'])), i, j) for i, t in enumerate(T) for j, p in enumerate(P) if _cand2(p, t))
    mi, mj, pairs = set(), set(), []
    for _d, i, j in cand:
        if i in mi or j in mj:
            continue
        mi.add(i); mj.add(j)
        v, t = P[j][0], T[i]
        pairs.append(dict(t=i, p=j, errS=v - t['yS'], errM=v - t['yM'],
                          hit=abs(v - t['yS']) <= LINE_TOL * t['lead'] and abs(v - t['yM']) <= LINE_TOL * t['lead']))
    excl = sum(1 for j, p in enumerate(P) if j not in mj and not any(_cand2(p, t) for t in T)
               and (any(_cand1(p, t) for t in fullS) or any(_cand1(p, t) for t in fullM)))
    return pairs, excl


def line_agreed(S, M, RS, RM, pairs, resS, resM, mblocks):
    medS, medM = poster_L_med(RS), poster_L_med(RM)
    ex = [b['box'] for Q in (S, M) for b in Q['blocks'] if b['flag'] or b['base_mark'] == 'illegible']
    live = [k for k, mb in enumerate(mblocks) if not any(DSc.inside((mb['x1'], mb['y1'], mb['x2'], mb['y2']), x) >= INSIDE for x in ex)]
    info = Counter(측정블록_뺌=len(mblocks) - len(live))
    agl = []
    for i, j in pairs:
        bs, bm = RS[i], RM[j]
        Ls, Lm = block_L(bs, medS)[0], block_L(bm, medM)[0]
        lp = pair_lines(bs, bm, Ls, Lm)
        if lp is None:
            info['L_없어_뺀_일치블록'] += 1; continue
        L = min(x for x in (Ls, Lm) if x is not None)
        x1, x2 = max(bs['box'][0], bm['box'][0]), min(bs['box'][2], bm['box'][2])
        for u, v in lp:
            agl.append(dict(s=bs['lines'][u], m=bm['lines'][v], lead=L, x1=x1, x2=x2))
    res = {}
    for name, mk, tf in DIRECT:
        T, notag = [], 0
        for n, g in enumerate(agl):
            ys, ym = tf(g['s']), tf(g['m'])
            if _num(ys) and _num(ym) and abs(ys - ym) <= 1:
                T.append(dict(yS=ys, yM=ym, lead=g['lead'], x1=g['x1'], x2=g['x2'], k=n))
            elif _num(ys) or _num(ym):
                notag += 1
        P = [(mblocks[k][mk][li], mblocks[k]['x1'], mblocks[k]['x2'], k, li) for k in live
             for li in range(len(mblocks[k][mk])) if mblocks[k][mk][li] is not None]
        prs, nex = _match_agreed(T, P, resS[name]['T'], resM[name]['T'])
        res[name] = dict(T=T, P=P, pairs=prs, 정밀분모_뺌=nex, 일치하지_않은_칸=notag)
    B, top = res['베이스라인'], res['상단 잉크선']
    base_of = {B['T'][q['t']]['k']: (B['P'][q['p']][3], B['P'][q['p']][4]) for q in B['pairs']}
    nd = []
    for n, g in enumerate(agl):
        if not any(_num(g[w][c]) for w in ('s', 'm') for c in ('cap', 'asc')) and n in base_of:
            k, li = base_of[n]
            if mblocks[k]['caps'][li] is not None:
                nd.append((k, li))
    top_pp = {(top['P'][q['p']][3], top['P'][q['p']][4]) for q in top['pairs']}
    Pn = [q for q in top['P'] if (q[3], q[4]) not in set(nd)]
    pn, nexn = _match_agreed(top['T'], Pn, resS['상단 잉크선']['T'], resM['상단 잉크선']['T'])
    paired_mb = set(base_of.values())
    num = Counter(일치_글줄=len(agl), 캡어센더_없고_caps_값=len(nd), 그_caps_짝없음=sum(1 for q in nd if q not in top_pp),
                  베이스라인_짝없어_못_이은_caps=sum(1 for k in live for li in range(len(mblocks[k]['caps']))
                                              if mblocks[k]['caps'][li] is not None and (k, li) not in paired_mb),
                  뺀_뒤_측정선=len(Pn) - nexn, 뺀_뒤_창안짝=len(pn), 뺀_뒤_허용안짝=sum(q['hit'] for q in pn))
    what = Counter()
    for q in top['pairs']:
        g = agl[top['T'][q['t']]['k']]; v = top['P'][q['p']][0]
        if all(_num(g[w]['cap']) and _num(g[w]['asc']) and abs(g[w]['cap'] - g[w]['asc']) >= 2 for w in ('s', 'm')):
            near = ['캡선' if abs(v - g[w]['cap']) < abs(v - g[w]['asc']) else '어센더선' if abs(v - g[w]['asc']) < abs(v - g[w]['cap'])
                    else '같다' for w in ('s', 'm')]
            what['캡선에_가깝다' if near == ['캡선', '캡선'] else '어센더선에_가깝다' if near == ['어센더선', '어센더선'] else '갈림'] += 1
    return res, agl, info, num, what


def _stats_agreed(prs, n_t, n_m):
    bm = _stats([dict(err=q['errM'], hit=q['hit']) for q in prs], n_t, n_m)
    bs = _stats([dict(err=q['errS'], hit=q['hit']) for q in prs], n_t, n_m)
    out = {k: bm[k] for k in ('참값_선', '측정_선', '창안_짝', '허용안_짝', '재현율', '정밀도', '창안짝_정밀도')}
    ek = ('오차_절대_중앙', '오차_절대_10_90', '편향_중앙', '오차_분포')
    out['오차_라벨러B'] = {k: bm[k] for k in ek}; out['오차_라벨러A'] = {k: bs[k] for k in ek}
    return out


def _stats(prs, n_t, n_m):
    ae = [abs(q['err']) for q in prs]; e = [q['err'] for q in prs]; hit = sum(q['hit'] for q in prs)
    return dict(참값_선=n_t, 측정_선=n_m, 창안_짝=len(prs), 허용안_짝=hit, 재현율=_r(_div(hit, n_t)),
                정밀도=_r(_div(hit, n_m)), 창안짝_정밀도=_r(_div(len(prs), n_m)),
                오차_절대_중앙=_q(ae, 50), 오차_절대_10_90=[_q(ae, 10), _q(ae, 90)], 편향_중앙=_q(e, 50),
                오차_분포=(dict(행_단위_일치=_r(np.mean([abs(x) <= 0.5 for x in e])), 위로_1행_이상=_r(np.mean([x <= -1 for x in e])),
                              아래로_1행_이상=_r(np.mean([x >= 1 for x in e])), 최악=[_r(min(e), 3), _r(max(e), 3)]) if e else None))


# ── 라벨러 간 일치도 ──────────────────────────────────────────────

def agree_poster(S, M):
    c = Counter(); rows = defaultdict(list)
    allS, allM = [b['box'] for b in S['blocks']], [b['box'] for b in M['blocks']]
    mr_all, _ = match_t(allS, allM, IOU_MAIN)
    for i, j in mr_all.items():
        fs, fm = S['blocks'][i]['flag'], M['blocks'][j]['flag']
        if fs != fm:
            c['제외사유_갈림|' + ('한쪽만 제외' if (fs is None) != (fm is None) else '사유가 다름')] += 1
    RS, _ = refs_of(S, 'main'); RM, _ = refs_of(M, 'main')
    medS, medM = poster_L_med(RS), poster_L_med(RM)
    for t in (IOU_MAIN, IOU_SENS):
        mr, _ = match_t([b['box'] for b in RS], [b['box'] for b in RM], t)
        c[f'블록|{t}|짝'] += len(mr); c[f'블록|{t}|라벨러A'] += len(RS); c[f'블록|{t}|라벨러B'] += len(RM)
        if t != IOU_MAIN:
            continue
        for i, j in mr.items():
            bs, bm = RS[i], RM[j]
            rows['IoU'].append(DSc.iou(bs['box'], bm['box']))
            for n, key in enumerate(('x1', 'y1', 'x2', 'y2')):
                rows['경계|' + key].append(bs['box'][n] - bm['box'][n])
            lp = pair_lines(bs, bm, block_L(bs, medS)[0], block_L(bm, medM)[0])
            if lp is None:
                c['글줄|L_없어_짝짓지_않은_블록'] += 1; continue
            c['글줄|라벨러A'] += sum(1 for l in bs['lines'] if _num(l['base'])); c['글줄|라벨러B'] += sum(1 for l in bm['lines'] if _num(l['base']))
            c['글줄|짝'] += len(lp)
            for u, v in lp:
                p, q = bs['lines'][u], bm['lines'][v]
                ta = min([x for x in (p['cap'], p['asc']) if _num(x)], default=None)
                tb = min([x for x in (q['cap'], q['asc']) if _num(x)], default=None)
                if ta is not None and tb is not None:
                    rows['차|top'].append(ta - tb)
                for tp in TYPES:
                    a_, b_ = p[tp], q[tp]
                    sa = '선' if _num(a_) else STATE.get(a_, '미입력'); sb = '선' if _num(b_) else STATE.get(b_, '미입력')
                    c[f'종류|{tp}|{sa}|{sb}'] += 1
                    if _num(a_) and _num(b_):
                        d = a_ - b_
                        rows['차|' + tp].append(d)
                        c[f'위치|{tp}|n'] += 1; c[f'위치|{tp}|le1'] += (abs(d) <= 1)
    return c, rows


def _diff_row(e):
    """수정 2 견줌 — 칸 수 · |차| 중앙 · |차| = 0 몫 · |차| ≤ 1행 몫 · 차 중앙."""
    return dict(칸=len(e), 절대_중앙=_q([abs(x) for x in e], 50), 몫_0=_r(_div(sum(abs(x) < 0.5 for x in e), len(e))),
                몫_1이하=_r(_div(sum(abs(x) <= 1 for x in e), len(e))), 차_중앙=_q(e, 50))


def kappa(tab):
    cats = sorted({a for a, _ in tab} | {b for _, b in tab})
    n = sum(tab.values())
    if not n:
        return None, None
    po = sum(v for (a, b), v in tab.items() if a == b) / n
    pa = Counter(); pb = Counter()
    for (a, b), v in tab.items():
        pa[a] += v; pb[b] += v
    pe = sum(pa[k] * pb[k] for k in cats) / n / n
    return (None if pe >= 1 else _r((po - pe) / (1 - pe))), _r(po)


def agree_summary(c, rows):
    out = dict(블록={str(t): dict(짝=c[f'블록|{t}|짝'], 라벨러A=c[f'블록|{t}|라벨러A'], 라벨러B=c[f'블록|{t}|라벨러B'],
                                  대칭_F1=_r(_f1(c[f'블록|{t}|짝'], c[f'블록|{t}|라벨러A'], c[f'블록|{t}|라벨러B']))) for t in (IOU_MAIN, IOU_SENS)},
               짝_IoU=dict(중앙=_q(rows['IoU'], 50), 구간_10_90=[_q(rows['IoU'], 10), _q(rows['IoU'], 90)]),
               경계_차={k: dict(중앙=_q(rows['경계|' + k], 50), 절대_중앙=_q([abs(x) for x in rows['경계|' + k]], 50),
                                구간_10_90=[_q(rows['경계|' + k], 10), _q(rows['경계|' + k], 90)]) for k in ('x1', 'y1', 'x2', 'y2')},
               제외사유_갈린_짝={k.split('|')[1]: v for k, v in c.items() if k.startswith('제외사유_갈림|')},
               글줄=dict(라벨러A=c['글줄|라벨러A'], 라벨러B=c['글줄|라벨러B'], 짝=c['글줄|짝'], L_없어_짝짓지_않은_블록=c['글줄|L_없어_짝짓지_않은_블록']),
               선_위치={}, 선_종류_판정={})
    for tp in TYPES:
        d = rows['차|' + tp]; nz = [x for x in d if x != 0]
        out['선_위치'][TNAME[tp]] = dict(칸=len(d), 중앙=_q(d, 50), 구간_10_90=[_q(d, 10), _q(d, 90)],
                                        최악=([min(d), max(d)] if d else None),
                                        몫_0=_r(_div(sum(x == 0 for x in d), len(d))), 몫_1이하=_r(_div(sum(abs(x) <= 1 for x in d), len(d))),
                                        몫_1초과=_r(_div(sum(abs(x) > 1 for x in d), len(d))),
                                        영아닌_차=len(nz), 영아닌_차_양=_r(_div(sum(x > 0 for x in nz), len(nz))),
                                        영아닌_차_음=_r(_div(sum(x < 0 for x in nz), len(nz))))
        tab = {(k.split('|')[2], k.split('|')[3]): v for k, v in c.items() if k.startswith(f'종류|{tp}|')}
        kp, po = kappa(tab)
        out['선_종류_판정'][TNAME[tp]] = dict(칸=sum(tab.values()), 일치_몫=po, 카파=kp if kp is not None else 'κ 없음',
                                           교차표_라벨러A_라벨러B={f'{a} / {b}': v for (a, b), v in sorted(tab.items())})
    return out


# ── score ────────────────────────────────────────────────────────

METHODS = ('C', 'VLM1', 'VLM2', 'A')


def cmd_score(a):
    if not a.unseal:
        sys.exit('score 는 1단계 봉인 파일을 읽는다 — 사전등록의 봉인 해제 조건을 확인하고 --unseal 을 준다')
    labs = load_labelers(a.guides)
    rec = receipt(labs, a.posters)
    if not rec['통과']:
        sys.exit('수령 검증을 통과하지 못했다')
    refs = {n: labs[n]['posters'] for n in LABELERS}
    if a.consensus:
        refs['합의'] = load_consensus(a.consensus)
    Wk = os.path.expanduser(a.work)
    man = json.load(open(os.path.join(Wk, 'manifest.json'))); root = os.path.expanduser(man['image_root'])
    L = json.load(open(os.path.join(Wk, 'lines.json')))['lines']
    vlms = [GS.load_vlm(v) for v in a.vlm]
    cache = json.load(open(os.path.expanduser(a.cache)))['raw']
    sel = {x['order']: x for x in json.load(open(a.selection))['list']}
    Pl = {it['order']: it for it in json.load(open(a.posters))['main']}
    items = sorted(man['items'], key=lambda it: it['order'])
    if sorted(it['order'] for it in items) != sorted(Pl):
        sys.exit('작업 폴더 판 목록과 라벨링 목록이 다르다')

    percnt = defaultdict(Counter)          # 판 순서 → 틀 군집용 수
    blk = defaultdict(Counter)             # (참조, 변형, 문턱, 방식) → 수
    orc = defaultdict(Counter); nbp = defaultdict(list)
    lin = defaultdict(lambda: defaultdict(list)); lin_n = defaultdict(Counter); lin_info = defaultdict(Counter)
    lin_rule = defaultdict(Counter); lin_num = defaultdict(Counter); lin_what = defaultdict(Counter)
    lin_split = defaultdict(lambda: defaultdict(list)); lin_split_n = defaultdict(Counter)
    agr = Counter(); agr_rows = defaultdict(list); agr_op = Counter(); agr_op_rows = defaultdict(list)
    fb = Counter(); vparse = [Counter() for _ in vlms]; meas = Counter(); tmpl = {}; n_posters = Counter()
    for it in items:
        o = it['order']; k = GS._key(it['seed']); path = os.path.join(root, it['image'])
        pl = Pl[o]
        if it['image'] != f"{pl['folder']}/{pl['file']}" or it['image_sha256'] != pl['sha256'] or _sha(path) != pl['sha256'] \
                or L[k]['sha256'] != pl['sha256']:
            sys.exit(f'목록과 다른 이미지 또는 줄 파일: 순서 {o}')
        tmpl[o] = it['template']
        size = tuple(L[k]['size'])
        gray = np.asarray(Image.open(path).convert('L')).astype(float); Wd = gray.shape[1]
        # 사전등록 수정 16 — 줄 상자 가르기를 기본 경로로. A · C · VLM 이 모두 갈린 줄을 받는다
        lines, _parent = DS.split_wide_lines(gray, L[k]['lines'])
        # 방식
        c_asg, cd = GG.group_gap(gray, lines, pad_rule=C_PAD)
        src = cd['source']; gsrc = {}
        for i, j in enumerate(c_asg):
            if j is not None:
                gsrc.setdefault(j, src[i])
        fb['줄'] += len(lines); fb['줄_A'] += sum(1 for s in src if s == 'A'); fb['줄_소속없음'] += sum(1 for s in src if s is None)
        fb['C묶음'] += len(gsrc); fb['C묶음_A'] += sum(1 for s in gsrc.values() if s == 'A')
        percnt[o]['C폴백|줄'] += len(lines); percnt[o]['C폴백|줄_A'] += sum(1 for s in src if s == 'A')
        asgs = {'C': c_asg}
        for n, (vm, _i) in enumerate(vlms):
            asgs[f'VLM{n + 1}'], info = GS.groups_vlm(lines, vm.get(k))
            vparse[n].update(info); vparse[n]['없는 장'] += (k not in vm)
        Ablocks = DS.group(lines)
        P = {m: GS.boxes_of(lines, asgs[m]) for m in asgs}
        P = {m: [(g, tuple(b[:4])) for g, b in v] for m, v in P.items()}
        P['A'] = [(n, tuple(b[:4])) for n, b in enumerate(Ablocks)]
        A_syn = sorted(tuple(b[1][:4]) for b in GS.boxes_of(lines, GS.groups_A(lines)))
        meas['A_합성정의와_상자가_다른_판'] += (sorted(b for _g, b in P['A']) != A_syn)
        # 선 측정 — A 블록을 ground.entry 로 (measure_corpus 와 같은 경로), 캐시와 같아야 한다
        m_e, _ = G.entry(path, DS.boxes_norm(lines, size), coords='norm')
        ck = f"{pl['folder']}__{pl['file']}"
        if m_e['blocks'] != cache[ck]['blocks']:
            sys.exit(f'선 측정이 파이프라인 캐시와 다르다: 순서 {o} — 사전등록대로 멈춘다')
        meas['캐시와_같은_판'] += 1
        mblocks = m_e['blocks']
        linked = {max(range(len(Ablocks)), key=lambda g: DSc.inter((mb['x1'], mb['y1'], mb['x2'], mb['y2']), Ablocks[g][:4]))
                  for mb in mblocks} if Ablocks else set()
        meas['A_묶음'] += len(Ablocks); meas['측정_블록'] += len(mblocks); meas['측정_없는_A_묶음'] += len(Ablocks) - len(linked)
        els = GG.elements(gray, lines, C_PAD)[0]
        # 참조마다
        or_loc, np_loc, res_loc = {}, {}, {}
        for ref, RP in refs.items():
            if o not in RP or not kept(RP[o]):
                continue
            p = RP[o]; n_posters[ref] += 1
            for variant in ('main', 'no_illegible'):
                R, X = refs_of(p, variant)
                for t in (IOU_MAIN, IOU_SENS):
                    if variant != 'main' and t != IOU_MAIN:
                        continue
                    for m in METHODS:
                        cc = block_counts(R, X, P[m], t, gsrc if m == 'C' else None)
                        blk[(ref, variant, t, m)].update(cc)
                        if variant == 'main' and t == IOU_MAIN:
                            for key in ('짝', '참조', '묶음', '과병합', '과분할'):
                                percnt[o][f'블록|{ref}|{m}|{key}'] += cc[key]
            oc, owner, omatched, ocauses = oracle(p, lines, gray)
            orc[ref].update(oc); or_loc[ref] = (omatched, ocauses)
            percnt[o][f'오라클|{ref}|짝'] += oc['짝']; percnt[o][f'오라클|{ref}|참조'] += oc['참조']; percnt[o][f'오라클|{ref}|묶음'] += oc['오라클_블록']
            if ref in LABELERS:
                np_loc[ref] = neighbour_pairs(p, lines, owner, els, Wd, {m: asgs[m] for m in asgs})
                nbp[ref] += np_loc[ref]
            res, lines_h, info, rule, num, what = line_score(p, mblocks)
            res_loc[ref] = res
            lin_info[ref].update(info); lin_rule[ref].update({str(k_): v for k_, v in rule.items()})
            lin_num[ref].update(num); lin_what[ref].update(what)
            cap_cell = sel.get(o, {}).get('cap')
            for name, r in res.items():
                lin[ref][name] += r['pairs']
                lin_n[ref][name + '|T'] += len(r['T']); lin_n[ref][name + '|P'] += len(r['P'])
                lin_n[ref].update({f'{name}|표시|{s}': v for s, v in r['표시'].items()})
                lin_split[ref][f'{name}|판|{cap_cell}'] += r['pairs']
                lin_split_n[ref][f'{name}|판|{cap_cell}|T'] += len(r['T']); lin_split_n[ref][f'{name}|판|{cap_cell}|P'] += len(r['P'])
                for key, fn in (('캡선_그은_글줄', lambda l: _num(l['cap'])), ('어센더선_그은_글줄', lambda l: _num(l['asc']))):
                    for flag in (True, False):
                        sub = {n for n, tt in enumerate(r['T']) if fn(lines_h[tt['k']]['l']) == flag}
                        lin_split[ref][f'{name}|{key}|{flag}'] += [q for q in r['pairs'] if q['t'] in sub]
                        lin_split_n[ref][f'{name}|{key}|{flag}|T'] += len(sub)
                if name in ('베이스라인', 'x높이선', '상단 잉크선'):
                    percnt[o][f'선|{ref}|{name}|hit'] += sum(q['hit'] for q in r['pairs']); percnt[o][f'선|{ref}|{name}|T'] += len(r['T'])
        # 라벨러 간
        S_, M_ = refs['라벨러A'].get(o), refs['라벨러B'].get(o)
        if S_ and M_ and kept(S_) and kept(M_):
            ac, ar = agree_poster(S_, M_)
            agr.update(ac)
            for kk, v in ar.items():
                agr_rows[kk] += v
            if sel.get(o, {}).get('idml_guides'):
                agr_op.update(ac)
                for kk, v in ar.items():
                    agr_op_rows[kk] += v
            percnt[o]['일치|짝'] += ac[f'블록|{IOU_MAIN}|짝']; percnt[o]['일치|송'] += ac[f'블록|{IOU_MAIN}|라벨러A']; percnt[o]['일치|신'] += ac[f'블록|{IOU_MAIN}|라벨러B']
            for tp in TYPES:
                percnt[o][f'일치|{tp}|le1'] += ac[f'위치|{tp}|le1']; percnt[o][f'일치|{tp}|n'] += ac[f'위치|{tp}|n']
            # ③ 두 라벨러 일치 항목 (수정 1)
            n_posters['일치'] += 1
            RS, RM, apairs = agreed_blocks(S_, M_)
            for variant in ('main', 'no_illegible'):
                for t in (IOU_MAIN, IOU_SENS):
                    if variant != 'main' and t != IOU_MAIN:
                        continue
                    for m in METHODS:
                        cc = block_counts_agreed(S_, M_, RS, RM, apairs, P[m], t, variant, gsrc if m == 'C' else None)
                        blk[('일치', variant, t, m)].update(cc)
                        if variant == 'main' and t == IOU_MAIN:
                            for key in ('짝', '참조', '묶음', '과병합', '과분할'):
                                percnt[o][f'블록|일치|{m}|{key}'] += cc[key]
            orc['일치'].update(oracle_agreed(apairs, or_loc['라벨러A'], or_loc['라벨러B']))
            nbp['일치'] += neighbours_agreed(apairs, np_loc['라벨러A'], np_loc['라벨러B'])
            resA, agl, infoA, numA, whatA = line_agreed(S_, M_, RS, RM, apairs, res_loc['라벨러A'], res_loc['라벨러B'], mblocks)
            lin_info['일치'].update(infoA); lin_num['일치'].update(numA); lin_what['일치'].update(whatA)
            cap_cell = sel.get(o, {}).get('cap')
            for name, r in resA.items():
                lin['일치'][name] += r['pairs']
                lin_n['일치'][name + '|T'] += len(r['T']); lin_n['일치'][name + '|P'] += len(r['P']) - r['정밀분모_뺌']
                lin_n['일치'][name + '|정밀분모_뺌'] += r['정밀분모_뺌']; lin_n['일치'][name + '|일치하지_않은_칸'] += r['일치하지_않은_칸']
                lin_split['일치'][f'{name}|판|{cap_cell}'] += r['pairs']
                lin_split_n['일치'][f'{name}|판|{cap_cell}|T'] += len(r['T'])
                lin_split_n['일치'][f'{name}|판|{cap_cell}|P'] += len(r['P']) - r['정밀분모_뺌']
                for key, c_ in (('캡선_그은_글줄', 'cap'), ('어센더선_그은_글줄', 'asc')):
                    for flag in (True, False):
                        sub = {n for n, tt in enumerate(r['T'])
                               if _num(agl[tt['k']]['s'][c_]) == flag and _num(agl[tt['k']]['m'][c_]) == flag}
                        lin_split['일치'][f'{name}|{key}|{flag}'] += [q for q in r['pairs'] if q['t'] in sub]
                        lin_split_n['일치'][f'{name}|{key}|{flag}|T'] += len(sub)
                if name in ('베이스라인', 'x높이선', '상단 잉크선'):
                    percnt[o][f'선|일치|{name}|hit'] += sum(q['hit'] for q in r['pairs']); percnt[o][f'선|일치|{name}|T'] += len(r['T'])
        print(f'  순서 {o} 끝', flush=True)

    # ── 모으기 ──
    def bsum(c):
        return dict(**{k_: v for k_, v in sorted(c.items())}, 재현=_r(_div(c['짝'], c['참조'])), 정밀=_r(_div(c['짝'], c['묶음'])),
                    F1=_r(_f1(c['짝'], c['참조'], c['묶음'])), 과병합_몫=_r(_div(c['과병합'], c['참조'])),
                    과분할_몫=_r(_div(c['과분할'], c['참조'])),
                    **({'짝지은_블록_출처A_몫': _r(_div(c['짝_출처A'], c['짝']))} if '짝_출처A' in c else {}))

    per_ref = {}
    for ref in refs:                        # ① · ② · 합의 — ③ 은 아래에서 따로
        blocks = {}
        for (r_, variant, t, m), c in blk.items():
            if r_ == ref:
                blocks.setdefault(f'{variant}|IoU≥{t}', {})[m] = bsum(c)
        oc = orc[ref]
        ol = {}
        for key in ('재현손실', '정밀손실'):
            ol[key] = {k_.split('|', 1)[1]: dict(수=v, 몫=_r(_div(v, oc['참조'] if key == '재현손실' else oc['오라클_블록'])))
                       for k_, v in sorted(oc.items()) if k_.startswith(key + '|')}
        ol['재현손실_세부'] = {k_.split('|', 1)[1]: v for k_, v in sorted(oc.items()) if k_.startswith('재현손실_세부|')}
        lines_out = {name: _stats(lin[ref][name], lin_n[ref][name + '|T'], lin_n[ref][name + '|P']) for name, _mk, _tf in DIRECT}
        for name, _mk, _tf in DIRECT:
            lines_out[name]['표시로_뺀_칸'] = {k_.split('|')[2]: v for k_, v in lin_n[ref].items() if k_.startswith(name + '|표시|')}
        nm = lin_num[ref]
        per_ref[ref] = dict(
            판=n_posters[ref], 블록=blocks,
            오라클=dict(참조=oc['참조'], 오라클_블록=oc['오라클_블록'], 짝=oc['짝'], F1=_r(_f1(oc['짝'], oc['참조'], oc['오라클_블록'])),
                     재현=_r(_div(oc['짝'], oc['참조'])), 안겹치는_줄=oc['안겹치는_줄'], 제외로_뺀_줄=oc['제외로_뺀_줄'], 손실_분해=ol),
            선=dict(종류=lines_out, 측정블록_뺌=dict(lin_info[ref]), 행간_L_규칙별_블록=dict(lin_rule[ref]),
                   숫자만_있는_글줄=dict(**dict(nm), 상단잉크선_정밀도_뺀_뒤=_r(_div(nm['뺀_뒤_허용안짝'], nm['뺀_뒤_측정선'])),
                                    상단잉크선_창안짝_정밀도_뺀_뒤=_r(_div(nm['뺀_뒤_창안짝'], nm['뺀_뒤_측정선'])),
                                    상단잉크선_정밀도_뺀_전=lines_out['상단 잉크선']['정밀도'],
                                    상단잉크선_창안짝_정밀도_뺀_전=lines_out['상단 잉크선']['창안짝_정밀도']),
                   caps_가_잡는_것=dict(lin_what[ref]),
                   나눠_본_값={kk: _stats(v, lin_split_n[ref][kk + '|T'], lin_split_n[ref].get(kk + '|P', 0))
                              for kk, v in sorted(lin_split[ref].items())}))
    if orc.get('일치'):
        oc = orc['일치']
        blocks = {}
        for (r_, variant, t, m), c in blk.items():
            if r_ == '일치':
                blocks.setdefault(f'{variant}|IoU≥{t}', {})[m] = bsum(c)
        lines_out = {}
        for name, _mk, _tf in DIRECT:
            lines_out[name] = _stats_agreed(lin['일치'][name], lin_n['일치'][name + '|T'], lin_n['일치'][name + '|P'])
            lines_out[name]['정밀분모에서_뺀_측정선'] = lin_n['일치'][name + '|정밀분모_뺌']
            lines_out[name]['일치하지_않은_칸'] = lin_n['일치'][name + '|일치하지_않은_칸']
        nm = lin_num['일치']
        per_ref['일치'] = dict(
            뜻='두 라벨러가 일치한 항목에서만 채점한 값 — 새 참조가 아니라 채점 범위를 좁힌 값 (수정 1)',
            판=n_posters['일치'], 블록=blocks,
            오라클=dict(참조=oc['참조'], 짝=oc['짝'], 재현=_r(_div(oc['짝'], oc['참조'])), F1='③ 에서는 정의하지 않는다',
                     손실_분해_라벨러B원인_라벨러A원인={k_.split('|', 1)[1]: v for k_, v in sorted(oc.items()) if k_.startswith('재현손실|')}),
            선=dict(종류=lines_out, 측정블록_뺌=dict(lin_info['일치']),
                   숫자만_있는_글줄=dict(**dict(nm), 상단잉크선_정밀도_뺀_뒤=_r(_div(nm['뺀_뒤_허용안짝'], nm['뺀_뒤_측정선'])),
                                    상단잉크선_창안짝_정밀도_뺀_뒤=_r(_div(nm['뺀_뒤_창안짝'], nm['뺀_뒤_측정선'])),
                                    상단잉크선_정밀도_뺀_전=lines_out['상단 잉크선']['정밀도'],
                                    상단잉크선_창안짝_정밀도_뺀_전=lines_out['상단 잉크선']['창안짝_정밀도']),
                   caps_가_잡는_것=dict(lin_what['일치']),
                   나눠_본_값={kk: _stats_agreed(v, lin_split_n['일치'][kk + '|T'], lin_split_n['일치'].get(kk + '|P', 0))
                              for kk, v in sorted(lin_split['일치'].items())}))
    per_ref = {k_: per_ref[k_] for k_ in (*VALUES, '합의') if k_ in per_ref}
    agree = agree_summary(agr, agr_rows); agree['오페라하우스_IDML_8장'] = agree_summary(agr_op, agr_op_rows)
    E = dict(C_폴백_몫=dict(**dict(fb), 줄_A_몫=_r(_div(fb['줄_A'], fb['줄'])), C묶음_A_몫=_r(_div(fb['C묶음_A'], fb['C묶음']))),
             VLM_파싱={f'VLM{n + 1}': dict(c) for n, c in enumerate(vparse)}, VLM={f'VLM{n + 1}': v[1] for n, v in enumerate(vlms)},
             VLM_패스간_일치=(GS.pass_agreement([(GS._key(it['seed']), None, it) for it in items], L, vlms[0][0], vlms[1][0]) if len(vlms) >= 2 else None),
             측정_확인=dict(meas))
    e2 = {ref: e2_summary(nbp[ref]) for ref in VALUES}
    base_cmp = dict(뜻=('수정 2 — 라벨러 간 차이는 파이프라인 성능을 읽는 기준선이다. 파이프라인 − 라벨러 차이가 라벨러 − 라벨러 차이보다 '
                       '작거나 비슷한 선 종류에서는 그 이상의 정확도를 이 참조로 확인할 수 없다. 판정이 아니라 서술이며 수치 문턱이 없다'))
    for name, tp in (('베이스라인', 'base'), ('x높이선', 'xh'), ('상단 잉크선', 'top')):
        row = {f'파이프라인 − {r}': _diff_row([q['err'] for q in lin[r][name]]) for r in ('라벨러B', '라벨러A')}
        if lin.get('일치'):
            row['파이프라인 − 라벨러B (일치 칸)'] = _diff_row([q['errM'] for q in lin['일치'][name]])
            row['파이프라인 − 라벨러A (일치 칸)'] = _diff_row([q['errS'] for q in lin['일치'][name]])
        row['라벨러A − 라벨러B (라벨러 간)'] = _diff_row(agr_rows['차|' + tp])
        base_cmp[name] = row
    boot = cluster(percnt, tmpl)
    res = dict(무엇='브로크만 실물 50장 2단계 — 사람 라벨 참조 채점 · 라벨러 간 일치도 (정확도가 아니라 참조와의 일치도, 라벨러 2)',
               사전등록=a.prereg, 사전등록_sha256=_sha(a.prereg), 봉인_해제=dict(시각=a.unsealed_at, 커밋=a.unsealed_commit),
               수령=rec, 입력=dict(작업_폴더=a.work, manifest_sha256=_sha(os.path.join(Wk, 'manifest.json')),
                              줄_sha256=_sha(os.path.join(Wk, 'lines.json')), 캐시=_tilde(a.cache), 캐시_sha256=_sha(a.cache),
                              선정=a.selection, 선정_sha256=_sha(a.selection), 합의=a.consensus,
                              합의_sha256=(_sha(a.consensus) if a.consensus else None)),
               참조별=per_ref, 방식=E, 이웃_블록_쌍=e2, 라벨러_간_일치도=agree, 기준선_견줌=base_cmp, 틀_군집=boot)
    res['예측_판정'] = verdicts(res)
    json.dump(res, open(a.out, 'w'), ensure_ascii=False, indent=1)
    print('→', a.out)


# ── 추가 1 이웃 쌍 요약 ─────────────────────────────────────────────

def e2_summary(pairs):
    def rate(m, pred):
        ps = [p for p in pairs if pred(p) and p['병합'][m] is not None]
        return dict(판정가능=len(ps), 병합=sum(p['병합'][m] for p in ps), 병합률=_r(_div(sum(p['병합'][m] for p in ps), len(ps))))
    methods = sorted({m for p in pairs for m in p['병합']})
    kinds = ('가', '나', '다', '그 외', '판정 못함')
    out = dict(쌍=len(pairs), 유형별_쌍=dict(Counter(t for p in pairs for t in p['유형'])),
               방식별={m: {k: rate(m, lambda p, k=k: k in p['유형']) for k in kinds} for m in methods})
    three = lambda p: bool({'가', '나', '다'} & set(p['유형']))
    for m in methods:
        J = [p for p in pairs if p['병합'][m] is not None]
        merged = [p for p in J if p['병합'][m]]
        out['방식별'][m]['몫_가나다_붙인쌍'] = _r(_div(sum(three(p) for p in merged), len(merged)))
        out['방식별'][m]['몫_가나다_모든쌍'] = _r(_div(sum(three(p) for p in J), len(J)))
        out['방식별'][m]['가나다_판정가능'] = sum(three(p) for p in J)
    return out


# ── 틀 군집 ───────────────────────────────────────────────────────

def _metrics(keys_all):
    M = {}
    refs = sorted({k.split('|')[1] for k in keys_all if k.startswith('블록|')})
    for ref in refs:
        for m in METHODS:
            M[f'블록F1|{ref}|{m}'] = (lambda g, ref=ref, m=m: _f1(g(f'블록|{ref}|{m}|짝'), g(f'블록|{ref}|{m}|참조'), g(f'블록|{ref}|{m}|묶음')))
        for v in ('VLM1', 'VLM2'):
            M[f'F1차|{ref}|{v}−C'] = (lambda g, ref=ref, v=v: None if None in (M[f'블록F1|{ref}|{v}'](g), M[f'블록F1|{ref}|C'](g))
                                      else M[f'블록F1|{ref}|{v}'](g) - M[f'블록F1|{ref}|C'](g))
        for name in ('베이스라인', 'x높이선', '상단 잉크선'):
            M[f'선재현|{ref}|{name}'] = (lambda g, ref=ref, name=name: _div(g(f'선|{ref}|{name}|hit'), g(f'선|{ref}|{name}|T')))
    M['라벨러간_블록F1'] = lambda g: _f1(g('일치|짝'), g('일치|송'), g('일치|신'))
    for tp in TYPES:
        M[f'라벨러간_1행이하몫|{TNAME[tp]}'] = (lambda g, tp=tp: _div(g(f'일치|{tp}|le1'), g(f'일치|{tp}|n')))
    return M


def cluster(percnt, tmpl):
    orders = sorted(percnt)
    keys = sorted({k for o in orders for k in percnt[o]})
    idx = {k: i for i, k in enumerate(keys)}
    V = np.array([[percnt[o].get(k, 0) for k in keys] for o in orders], float)
    ts = sorted({tmpl[o] for o in orders})
    Tm = np.array([V[[i for i, o in enumerate(orders) if tmpl[o] == t]].sum(0) for t in ts])
    M = _metrics(keys)
    getter = lambda vec: (lambda k: vec[idx[k]] if k in idx else 0.0)
    total = Tm.sum(0)
    rs = np.random.RandomState(BOOT_SEED)
    draws = [Tm[rs.randint(0, len(ts), len(ts))].sum(0) for _ in range(BOOT_N)]
    first = [min(o for o in orders if tmpl[o] == t) for t in ts]
    one = V[[orders.index(o) for o in first]].sum(0)
    out = dict(틀=len(ts), 판=len(orders), 붓스트랩=dict(n=BOOT_N, seed=BOOT_SEED), 값={})
    for name, fn in M.items():
        pt = fn(getter(total))
        if pt is None:
            continue
        bs = [x for x in (fn(getter(d)) for d in draws) if x is not None]
        loo = [x for x in (fn(getter(total - Tm[i])) for i in range(len(ts))) if x is not None]
        out['값'][name] = dict(점=_r(pt), 구간_95=[_r(np.percentile(bs, 2.5)), _r(np.percentile(bs, 97.5))] if bs else None,
                              틀_하나_뺌=[_r(min(loo)), _r(max(loo))] if loo else None, 틀당_한장=_r(fn(getter(one))))
    return out


# ── 예측 판정 ──────────────────────────────────────────────────────

def _both(vals):
    """한 값 안에서 두 패스(또는 여러 항) — 모두 성립 맞음 · 모두 어김 틀림 · 엇갈림 판단 불가."""
    if any(v is None for v in vals):
        return '판단 불가'
    return '맞음' if all(vals) else '틀림' if not any(vals) else '판단 불가'


def _v(x):
    if x is None:
        return '판단 불가'
    if isinstance(x, list):
        return _both(x)
    return '맞음' if x else '틀림'


def verdicts(res):
    """수정 1 — 참조가 걸린 예측은 ① 라벨러B · ② 라벨러A · ③ 일치 에서 따로 판정한다. 합친 판정은 내지 않는다."""
    R = res['참조별']; V = {}
    F = lambda ref, m: R[ref]['블록']['main|IoU≥0.5'][m]['F1']
    blk = lambda ref, m, k: R[ref]['블록']['main|IoU≥0.5'][m][k]
    passes = ('VLM1', 'VLM2')

    def row(fn, what, only=VALUES):
        out = {}
        for r in VALUES:
            if r not in only:
                out[r] = '판정하지 않음'; continue
            try:
                out[r] = _v(fn(r))
            except (TypeError, KeyError):      # 값이 없어 비교할 수 없다
                out[r] = '판단 불가'
        return dict(값별=out, 기준=what)

    def one(val, ok):
        return dict(값=val, 판정=('판단 불가' if ok is None else '맞음' if ok else '틀림'))

    V['S1 · 실물에서 VLM 이 C 보다 낫다'] = row(lambda r: [F(r, v) > F(r, 'C') for v in passes], '값마다 두 패스 모두 VLM F1 > C F1')
    fb = res['방식']['C_폴백_몫']['줄_A_몫']
    V['S2 · C 폴백 몫이 합성보다 크게 는다'] = one(fb, None if fb is None else fb > SYNTH_C_FALLBACK)
    pos = res['라벨러_간_일치도']['선_위치']
    s3i = [pos[TNAME[t]]['몫_1이하'] for t in TYPES]
    V['S3 · 라벨러 간 선 위치 차이는 1행 수준 (i)'] = one({TNAME[t]: pos[TNAME[t]]['몫_1이하'] for t in TYPES},
                                                   None if None in s3i else all(x >= 0.95 for x in s3i))
    s3 = {}
    for t in ('base', 'xh'):
        d = pos[TNAME[t]]
        s3[TNAME[t]] = None if d['영아닌_차'] < MIN_PAIRS else max(d['영아닌_차_양'], d['영아닌_차_음']) >= 0.80
    V['S3 · (ii) 방향'] = one(s3, None if None in s3.values() else all(s3.values()))
    V['S4 · 실물 오라클은 합성보다 낮다'] = row(lambda r: R[r]['오라클']['F1'] < SYNTH_ORACLE, '오라클 F1 < 1.000 (③ 은 판정하지 않음)', only=LABELERS)
    V['기존 · VLM F1 이 C 보다 0.05 이상 높다'] = row(lambda r: [F(r, v) - F(r, 'C') >= 0.05 for v in passes], '값마다 두 패스')
    rng = lambda x, lo, hi: None if x is None else lo <= x <= hi
    V['기존 · VLM F1 0.60~0.85'] = row(lambda r: [rng(F(r, v), .60, .85) for v in passes], '값마다 두 패스 모두 범위 안')
    V['기존 · C F1 0.45~0.75'] = row(lambda r: rng(F(r, 'C'), .45, .75), '범위 안')
    V['기존 · 과분할 C > VLM'] = row(lambda r: [blk(r, 'C', '과분할_몫') > blk(r, v, '과분할_몫') for v in passes], '÷ 참조 블록, 두 패스')
    V['기존 · 과병합 C ≥ VLM'] = row(lambda r: [blk(r, 'C', '과병합_몫') >= blk(r, v, '과병합_몫') for v in passes], '÷ 참조 블록, 두 패스')
    V['기존 · 짝지은 블록 가운데 C 폴백 몫 ≥ 20%'] = row(lambda r: blk(r, 'C', '짝지은_블록_출처A_몫') >= 0.20, '짝지은 C 묶음 가운데 출처 A')
    ag = res['라벨러_간_일치도']['블록']['0.5']['대칭_F1']
    V['기존 · 라벨러 간 블록 대칭 F1 ≥ 0.80'] = one(ag, None if ag is None else ag >= 0.80)
    V['기존 · 두 방식 F1 은 모두 라벨러 간 F1 보다 낮다'] = row(lambda r: all(F(r, m) < ag for m in ('C', 'VLM1', 'VLM2')),
                                                        '① · ② 의 C · VLM 두 패스 F1 < 라벨러 간 블록 대칭 F1 (③ 은 견주지 않음)', only=LABELERS)
    V['기존 · 오라클 0.75~0.92'] = row(lambda r: rng(R[r]['오라클']['F1'], .75, .92), '범위 안 (③ 은 판정하지 않음)', only=LABELERS)
    V['E1 · (VLM − C) 블록 F1 > 합성의 같은 차'] = row(lambda r: [F(r, v) - F(r, 'C') > SYNTH_DIFF[v] for v in passes], '패스 1 > 0.023 · 패스 2 > 0.017')
    E2 = res['이웃_블록_쌍']
    for T in ('가', '나', '다'):
        def i_(r, T=T):
            d = E2[r]['방식별']['C']
            if d[T]['판정가능'] < MIN_PAIRS or d['그 외']['판정가능'] < MIN_PAIRS:
                return None
            return d[T]['병합률'] > d['그 외']['병합률']
        V[f'E2 (i) ({T}) C 병합률 > 그 외'] = row(i_, '유형 · 그 외 판정 가능한 쌍 10 이상 (값마다)')

        def iii(r, T=T):
            d = E2[r]['방식별']
            if d['C'][T]['판정가능'] < MIN_PAIRS or any(d[v][T]['판정가능'] < MIN_PAIRS for v in passes):
                return None
            return [d['C'][T]['병합률'] > d[v][T]['병합률'] for v in passes]
        V[f'E2 (iii) ({T}) C 병합률 > VLM'] = row(iii, '두 패스 (값마다)')

    def ii(r):
        d = E2[r]['방식별']['C']
        if d['가나다_판정가능'] < MIN_PAIRS:
            return None
        return d['몫_가나다_붙인쌍'] > d['몫_가나다_모든쌍']
    V['E2 (ii) C 가 붙인 쌍에서 (가)∪(나)∪(다) 몫이 더 크다'] = row(ii, '판정 가능한 (가)∪(나)∪(다) 쌍 10 이상 (값마다)')
    V['E3 · C 폴백 몫 > 합성 1.0%'] = one(fb, None if fb is None else fb > SYNTH_C_FALLBACK)
    V['기존 · Surya 줄 기준 C 폴백 몫 ≥ 25%'] = one(fb, None if fb is None else fb >= 0.25)
    return V


def main(argv=None):
    ap = argparse.ArgumentParser(description='브로크만 2단계 채점 — 경로는 모두 인자')
    sub = ap.add_subparsers(dest='cmd', required=True)
    c = sub.add_parser('check'); c.add_argument('--guides', nargs='+', required=True); c.add_argument('--posters', required=True)
    c.add_argument('--out')
    k = sub.add_parser('consensus'); k.add_argument('--guides', nargs='+', required=True); k.add_argument('--posters', required=True)
    k.add_argument('--prereg', required=True); k.add_argument('--out', required=True)
    s = sub.add_parser('score')
    s.add_argument('--unseal', action='store_true', help='1단계 봉인 파일을 읽는다 — 사전등록의 봉인 해제 조건을 모두 채운 뒤에만')
    s.add_argument('--unsealed-at', required=True); s.add_argument('--unsealed-commit', required=True)
    s.add_argument('--guides', nargs='+', required=True); s.add_argument('--consensus')
    s.add_argument('--posters', required=True); s.add_argument('--selection', required=True)
    s.add_argument('--work', required=True); s.add_argument('--vlm', action='append', required=True)
    s.add_argument('--cache', required=True); s.add_argument('--prereg', required=True); s.add_argument('--out', required=True)
    a = ap.parse_args(argv)
    dict(check=cmd_check, consensus=cmd_consensus, score=cmd_score)[a.cmd](a)


if __name__ == '__main__':
    main()
