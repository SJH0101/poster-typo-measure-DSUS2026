"""탐색용 · 논문 수치 아님 — 조판 규칙 탐색 2차. 항목마다 무작위 대조 둘을 함께 낸다.

    (가) 측정 브로크만 123 · (나) 측정 50 (라벨 있는 판) · (다) 라벨 50, 그리고 호프만 · 로제 · 루더.

대조 (i) 균등 무작위      — 그 값이 놓일 수 있는 범위에서 균등하게 뽑는다.
대조 (ii) 구조만 흔들기   — 실제 값의 분포는 그대로 두고 판 배정을 뒤섞거나(순열) 작은 흔들림을 더한다.
«규칙 있음» 은 실제 값이 (ii) 의 95% 구간(2.5~97.5 백분위) 밖일 때만 붙인다.

이 결과로 상수 · 파이프라인을 고치지 않는다.

    python eval/explore_typography_rules2.py --cache 브로크만=~/.typo-mcp/brockmann.json … \
        --consensus docs/brockmann_consensus_refs.json --out docs/typography_rules2_explore.json
"""
import argparse
import collections
import json
import os

import numpy as np

TOL = 0.15                 # 정수에 가깝다고 보는 허용 (칸 · 배수 단위)
TOLS = (0.10, 0.15, 0.20)
TRIALS = 2000
JIT = 2.0                  # (ii) 흔들림 — 픽셀
XH_SAME = 0.10             # x높이가 같은 종류로 보는 상대 허용
LEAD_SAME = 0.10           # 판 행간과 같다고 보는 상대 허용
RATIO_SAME = 0.15          # 비가 같다고 보는 허용
CLUS_W = 0.01              # x 군집을 가르는 틈 (판 폭 몫, 최소 3px)
rng = np.random.default_rng(20260918)


def q(v, r=3):
    v = np.asarray([float(x) for x in v], dtype=float)
    if not len(v):
        return dict(n=0)
    return dict(n=int(len(v)), 중앙=round(float(np.median(v)), r),
                p25=round(float(np.percentile(v, 25)), r), p75=round(float(np.percentile(v, 75)), r))


def near(x, tol=TOL):
    x = np.asarray(x, dtype=float)
    return np.abs(x - np.round(x)) <= tol


def ci(vals):
    a = np.asarray(vals, dtype=float)
    return dict(평균=round(float(a.mean()), 4),
                구간=[round(float(np.percentile(a, 2.5)), 4), round(float(np.percentile(a, 97.5)), 4)])


def judge(real, c2):
    """실제 값이 (ii) 95% 구간 밖이면 «규칙 있음»."""
    if real is None or c2 is None:
        return None
    lo, hi = c2['구간']
    return '규칙 있음' if (real < lo or real > hi) else '없음'


def item(real, c1, c2, note=None):
    out = dict(실제=(None if real is None else round(float(real), 4)),
               대조_i=c1, 대조_ii=c2, 판정=judge(real, c2))
    if note:
        out['주의'] = note
    return out


# ---------------------------------------------------------------- 자료 준비
def blocks_pipeline(e):
    out = []
    for b in e.get('blocks') or []:
        bs = sorted(int(v) for v in b['bases'])
        out.append(dict(bases=bs, xh=float(b['xh']), x1=float(b['x1']), x2=float(b['x2']),
                        y1=float(b['y1']), y2=float(b['y2'])))
    return out


def blocks_label(p):
    out = []
    num = lambda v: isinstance(v, (int, float))
    for b in p['blocks']:
        if b.get('flag'):
            continue
        bs = sorted(l['base'] for l in b['lines'] if num(l.get('base')))
        xh = [l['base'] - l['xh'] for l in b['lines'] if num(l.get('xh')) and num(l.get('base'))]
        if not bs:
            continue
        out.append(dict(bases=[int(v) for v in bs], xh=(float(np.median(xh)) if xh else None),
                        x1=float(b['box'][0]), x2=float(b['box'][2]),
                        y1=float(b['box'][1]), y2=float(b['box'][3])))
    return out


def prep(blocks, size):
    """판 하나의 값 묶음."""
    W, H = size
    for b in blocks:
        g = np.diff(b['bases']) if len(b['bases']) > 1 else np.array([])
        b['gaps'] = [float(v) for v in g]
        b['lead'] = (float(np.median(g)) if len(g) else None)
        b['n'] = len(b['bases'])
    leads = [b['lead'] for b in blocks if b['lead']]
    lead = float(np.median(leads)) if leads else None
    inter, horiz = [], []
    for i, a in enumerate(blocks):
        for j, c in enumerate(blocks):
            if i == j:
                continue
            if min(a['x2'], c['x2']) - max(a['x1'], c['x1']) > 0 and c['y1'] >= a['y2']:
                mid = [k for k, dd in enumerate(blocks) if k not in (i, j)
                       and min(a['x2'], dd['x2']) - max(a['x1'], dd['x1']) > 0
                       and dd['y1'] >= a['y2'] and dd['y2'] <= c['y1']]
                if not mid:
                    inter.append(float(c['bases'][0] - a['bases'][-1]))
            if (min(a['x2'], c['x2']) - max(a['x1'], c['x1']) <= 0 and a['x2'] <= c['x1']
                    and min(a['y2'], c['y2']) - max(a['y1'], c['y1']) > 0):
                mid = [k for k, dd in enumerate(blocks) if k not in (i, j)
                       and dd['x1'] >= a['x2'] and dd['x2'] <= c['x1']
                       and min(a['y2'], dd['y2']) - max(a['y1'], dd['y1']) > 0]
                if not mid:
                    horiz.append(float(c['x1'] - a['x2']))
    xhs = [b['xh'] for b in blocks if b['xh']]
    return dict(W=float(W), H=float(H), blocks=blocks, lead=lead, inter=inter, horiz=horiz,
                xh=(float(np.median(xhs)) if xhs else None))


def clusters(vals, thr):
    vals = sorted(vals)
    out = [[vals[0]]]
    for v in vals[1:]:
        if v - out[-1][-1] <= thr:
            out[-1].append(v)
        else:
            out.append([v])
    return out


# ---------------------------------------------------------------- 공통 도구
def seg_stat(flat, seg, fn):
    """판별 조각마다 fn 을 돌려 평균."""
    out = []
    s = 0
    for n in seg:
        if n:
            out.append(fn(flat[s:s + n]))
        s += n
    return float(np.mean(out)) if out else None


def perm_ctrl(flat, seg, stat, trials=TRIALS):
    """(ii) 순열 — 값의 분포는 그대로, 판 배정만 뒤섞는다."""
    flat = np.asarray(flat, dtype=float)
    res = []
    for _ in range(trials):
        res.append(stat(rng.permutation(flat)))
    return ci([r for r in res if r is not None])


def unif_ctrl(lo, hi, seg, stat, trials=TRIALS):
    """(i) 균등 — 같은 개수를 범위 안에서 균등하게 뽑는다."""
    n = int(np.sum(seg))
    res = []
    for _ in range(trials):
        res.append(stat(rng.uniform(lo, hi, n)))
    return ci([r for r in res if r is not None])


def jit_ctrl(flat, stat, amp=JIT, trials=TRIALS):
    """(ii) 흔들림 — 값마다 ±amp px 안의 흔들림을 더한다."""
    flat = np.asarray(flat, dtype=float)
    res = []
    for _ in range(trials):
        res.append(stat(flat + rng.uniform(-amp, amp, len(flat))))
    return ci([r for r in res if r is not None])


# ---------------------------------------------------------------- A. 행간
def sec_A(P):
    out = {}
    # A1 — 블록 안 줄 간격 ÷ x높이
    rat, seg = [], []
    for p in P:
        v = [b['lead'] / b['xh'] for b in p['blocks'] if b['lead'] and b['xh']]
        rat += v; seg.append(len(v))
    rat = np.asarray(rat, dtype=float)
    out['A1_분포'] = dict(**q(rat), 도수=dict(sorted(collections.Counter(np.round(rat * 2) / 2).items())),
                        _2에_가까움=round(float(np.mean(np.abs(rat - 2.0) <= TOL)), 3) if len(rat) else None)
    def a1(flat):
        s, sh = 0, []
        for n in seg:
            if n >= 2:
                v = flat[s:s + n]; m = np.median(v)
                sh.append(float(np.mean(np.abs(v - m) <= RATIO_SAME * m)))
            s += n
        return float(np.mean(sh)) if sh else None
    real = a1(rat)
    out['A1_판안_일치'] = item(real,
                            unif_ctrl(float(np.percentile(rat, 1)), float(np.percentile(rat, 99)), seg, a1),
                            perm_ctrl(rat, seg, a1),
                            '판마다 블록이 1개면 셈에서 빠진다. 블록 안이 일정한 것과는 다른 값이다')
    # A2 — 한 판의 모든 간격이 하나의 기본 간격의 정수배
    gs, gseg = [], []
    for p in P:
        v = [x for b in p['blocks'] for x in b['gaps']]
        gs += v; gseg.append(len(v))
    gs = np.asarray(gs, dtype=float)
    def a2_poster(flat):
        s, hit, tot = 0, 0, 0
        for n in gseg:
            if n:
                v = flat[s:s + n]; mn = v.min()
                if mn > 0:
                    hit += int(near(v / mn).sum()); tot += n
            s += n
        return hit / tot if tot else None
    # 1차 정의 (블록 기준) — 참고로 같이
    bhit = btot = 0
    for p in P:
        for b in p['blocks']:
            if b['gaps']:
                v = np.asarray(b['gaps']); mn = v.min()
                if mn > 0:
                    bhit += int(near(v / mn).sum()); btot += len(v)
    out['A2_블록기준_1차정의'] = dict(실제=(round(bhit / btot, 4) if btot else None), n=btot,
                                주의='한 블록 안 간격은 거의 같아 비가 1 이 된다 — 정의상 자동으로 높아진다')
    out['A2_판기준'] = item(a2_poster(gs),
                          unif_ctrl(float(np.percentile(gs, 1)), float(np.percentile(gs, 99)), gseg, a2_poster),
                          jit_ctrl(gs, a2_poster),
                          '판 안 최소 간격으로 나누므로 최소 간격 자신은 늘 1 이다')
    # A3 — 판 하나의 행간으로 설명되는 블록 몫
    bl, bseg = [], []
    for p in P:
        v = [b['lead'] for b in p['blocks'] if b['lead']]
        bl += v; bseg.append(len(v))
    bl = np.asarray(bl, dtype=float)
    def a3(flat):
        s, sh = 0, []
        for n in bseg:
            if n:
                v = flat[s:s + n]; m = np.median(v)
                sh.append(float(np.mean(np.abs(v - m) <= LEAD_SAME * m)))
            s += n
        return float(np.median(sh)) if sh else None
    out['A3_판행간_설명몫'] = item(a3(bl),
                             unif_ctrl(float(np.percentile(bl, 1)), float(np.percentile(bl, 99)), bseg, a3),
                             perm_ctrl(bl, bseg, a3),
                             '블록이 1개인 판은 늘 1.0 이 된다')
    # A4 — 블록 사이 세로 간격 ÷ 판 행간
    iv, ivseg, leads = [], [], []
    for p in P:
        if p['lead'] and p['inter']:
            iv += p['inter']; ivseg.append(len(p['inter'])); leads.append(p['lead'])
        else:
            ivseg.append(0); leads.append(p['lead'] or np.nan)
    iv = np.asarray(iv, dtype=float)
    lead_of = np.concatenate([np.full(n, l) for n, l in zip(ivseg, leads) if n]) if len(iv) else np.array([])
    ratio = iv / lead_of if len(iv) else np.array([])
    def a4(flat, tol=TOL):
        return float(np.mean(near(flat / lead_of, tol))) if len(flat) else None
    A4 = {}
    for tol in TOLS:
        f = (lambda t: (lambda flat: a4(flat, t)))(tol)
        A4[f'허용_{tol}'] = item(f(iv),
                               unif_ctrl(0.0, float(np.percentile(iv, 99)), ivseg, f),
                               perm_ctrl(iv, ivseg, f))
    bins = collections.Counter(int(np.clip(round(v), 0, 5)) for v in ratio)
    per_bin = {}
    for k in (1, 2, 3, 4, 5):
        m = (np.round(ratio) == k) if k < 5 else (np.round(ratio) >= 5)
        per_bin[('5이상' if k == 5 else str(k))] = dict(
            n=int(m.sum()), 정수몫=(round(float(np.mean(near(ratio[m]))), 3) if m.sum() else None))
    out['A4'] = dict(분포=q(ratio, 2), 허용별=A4, 반올림_도수=dict(sorted(bins.items())), 배수구간별=per_bin)
    # A5 — g ÷ 행간이 0.5 근처인 판
    half, rows = [], []
    for p in P:
        if not p['lead']:
            continue
        ys = sorted({y for b in p['blocks'] for y in b['bases']})
        ng = np.diff(ys)
        if len(ng) < 2:
            continue
        best = None
        for cand in np.arange(3.0, 80.5, 0.5):
            sh = float(np.mean(near(ng / cand)))
            rs = float(np.median(np.abs(ng / cand - np.round(ng / cand)) * cand))
            if best is None or (sh, -rs) > (best[1], -best[2]):
                best = (float(cand), sh, rs)
        g, sh, rs = best
        g2 = g * 2
        sh2 = float(np.mean(near(ng / g2))); rs2 = float(np.median(np.abs(ng / g2 - np.round(ng / g2)) * g2))
        r = dict(g=g, g_over_lead=g / p['lead'], 몫=sh, 잔차=rs, 몫_2g=sh2, 잔차_2g=rs2)
        rows.append(r)
        if abs(g / p['lead'] - 0.5) <= TOL:
            half.append(r)
    out['A5'] = dict(판=len(rows), g_over_lead=q([r['g_over_lead'] for r in rows], 2),
                     반값_판=len(half),
                     반값_판에서=dict(몫_g=q([r['몫'] for r in half]), 몫_2g=q([r['몫_2g'] for r in half]),
                                  잔차_g=q([r['잔차'] for r in half], 2), 잔차_2g=q([r['잔차_2g'] for r in half], 2),
                                  몫이_2g에서_같거나_큼=sum(1 for r in half if r['몫_2g'] >= r['몫'])),
                     전체에서=dict(몫_g=q([r['몫'] for r in rows]), 몫_2g=q([r['몫_2g'] for r in rows])))
    return out


# ---------------------------------------------------------------- B. 활자 크기
def xh_groups(xhs):
    v = sorted(xhs)
    gr = [[v[0]]]
    for x in v[1:]:
        if x <= gr[-1][-1] * (1 + XH_SAME):
            gr[-1].append(x)
        else:
            gr.append([x])
    return gr


def sec_B(P):
    out = {}
    xh, seg = [], []
    for p in P:
        v = [b['xh'] for b in p['blocks'] if b['xh']]
        xh += v; seg.append(len(v))
    xh = np.asarray(xh, dtype=float)
    def b1(flat):
        s, n_gr = 0, []
        for n in seg:
            if n:
                n_gr.append(len(xh_groups(flat[s:s + n])))
            s += n
        return float(np.mean(n_gr)) if n_gr else None
    cnt = []
    s = 0
    for n in seg:
        if n:
            cnt.append(len(xh_groups(xh[s:s + n])))
        s += n
    out['B1'] = dict(도수=dict(sorted(collections.Counter(cnt).items())), **q(cnt, 2),
                     대조=item(b1(xh),
                             unif_ctrl(float(xh.min()), float(xh.max()), seg, b1),
                             perm_ctrl(xh, seg, b1)))
    def ratios(flat):
        s, rr = 0, []
        for n in seg:
            if n:
                g = xh_groups(flat[s:s + n])
                med = [float(np.median(x)) for x in g]
                rr += [med[i + 1] / med[i] for i in range(len(med) - 1)]
            s += n
        return rr
    rr = np.asarray(ratios(xh), dtype=float)
    TGT = (2.0, 1.5, 1.33)
    def b2(flat, t):
        v = np.asarray(ratios(flat), dtype=float)
        return float(np.mean(np.abs(v - t) <= 0.10)) if len(v) else None
    out['B2'] = dict(분포=q(rr, 3), 도수=dict(sorted(collections.Counter(np.round(rr * 4) / 4).items())),
                     목표별={str(t): item(b2(xh, t),
                                       unif_ctrl(float(xh.min()), float(xh.max()), seg, lambda f, t=t: b2(f, t)),
                                       perm_ctrl(xh, seg, lambda f, t=t: b2(f, t))) for t in TGT})
    # B3 — 제목 ÷ 본문
    b3 = []
    for p in P:
        v = [b['xh'] for b in p['blocks'] if b['xh']]
        if len(v) < 2:
            continue
        g = xh_groups(v)
        body = max(g, key=len)
        b3.append(max(v) / float(np.median(body)))
    out['B3'] = dict(**q(b3, 3), 도수=dict(sorted(collections.Counter(np.round(np.asarray(b3) * 2) / 2).items())),
                     _2에_가까움=round(float(np.mean(np.abs(np.asarray(b3) - 2) <= 0.10)), 3) if b3 else None)
    # B4 — 크기가 다른 블록끼리 행간÷x높이
    diff, same = [], 0
    n_used = 0
    for p in P:
        v = [(b['xh'], b['lead'] / b['xh']) for b in p['blocks'] if b['xh'] and b['lead']]
        if len(v) < 2:
            continue
        g = xh_groups([x for x, _ in v])
        if len(g) < 2:
            continue
        lab = {}
        for gi, grp in enumerate(g):
            for x in grp:
                lab[x] = gi
        med = collections.defaultdict(list)
        for x, r in v:
            med[lab[x]].append(r)
        ms = [float(np.median(m)) for m in med.values() if m]
        if len(ms) < 2:
            continue
        n_used += 1
        d = max(ms) - min(ms)
        diff.append(d)
        same += (d <= RATIO_SAME * float(np.median(ms)))
    out['B4'] = dict(판=n_used, 종류간_차=q(diff, 3), 같은_판_몫=(round(same / n_used, 3) if n_used else None),
                     주의='크기 종류가 둘 이상이고 두 종류 모두 2줄 이상인 판만')
    return out


# ---------------------------------------------------------------- C. 가로
def sec_C(P):
    out = {}
    nx, seg = [], []
    for p in P:
        v = [b['x1'] / p['W'] for b in p['blocks']]
        nx += v; seg.append(len(v))
    nx = np.asarray(nx, dtype=float)
    THR = 0.01
    def c1(flat):
        s, c = 0, []
        for n in seg:
            if n:
                c.append(len(clusters(flat[s:s + n], THR)))
            s += n
        return float(np.mean(c)) if c else None
    cl = []
    s = 0
    for n in seg:
        if n:
            cl.append(len(clusters(nx[s:s + n], THR)))
        s += n
    pos = [round(float(np.median(c)), 3) for p in P for c in clusters([b['x1'] / p['W'] for b in p['blocks']], THR)]
    out['C1'] = dict(군집수=dict(도수=dict(sorted(collections.Counter(cl).items())), **q(cl, 2)),
                     위치_판폭몫=q(pos, 3), 위치_도수=dict(sorted(collections.Counter(np.round(np.asarray(pos), 1)).items())),
                     대조=item(c1(nx), unif_ctrl(0.0, 1.0, seg, c1), perm_ctrl(nx, seg, c1)))
    gapW, gapX = [], []
    for p in P:
        cs = clusters([b['x1'] for b in p['blocks']], max(3, CLUS_W * p['W']))
        med = [float(np.median(c)) for c in cs]
        for i in range(len(med) - 1):
            gapW.append((med[i + 1] - med[i]) / p['W'])
            if p['xh']:
                gapX.append((med[i + 1] - med[i]) / p['xh'])
    out['C2'] = dict(판폭몫=q(gapW, 3), x높이배=q(gapX, 2),
                     x높이_정수몫=(round(float(np.mean(near(gapX))), 3) if gapX else None),
                     도수_판폭몫=dict(sorted(collections.Counter(np.round(np.asarray(gapW), 1)).items())) if gapW else {})
    wid, wseg = [], []
    for p in P:
        v = [(b['x2'] - b['x1']) / p['W'] for b in p['blocks']]
        wid += v; wseg.append(len(v))
    wid = np.asarray(wid, dtype=float)
    def c3(flat):
        s, sh = 0, []
        for n in wseg:
            if n >= 2:
                v = flat[s:s + n]; m = np.median(v)
                sh.append(float(np.mean(np.abs(v - m) <= 0.05)))
            s += n
        return float(np.mean(sh)) if sh else None
    out['C3'] = dict(분포=q(wid, 3), 도수=dict(sorted(collections.Counter(np.round(wid, 1)).items())),
                     판안_같은몫=item(c3(wid), unif_ctrl(0.0, 1.0, wseg, c3), perm_ctrl(wid, wseg, c3)))
    hz, hseg = [], []
    for p in P:
        v = [x / p['xh'] for x in p['horiz']] if p['xh'] else []
        hz += v; hseg.append(len(v))
    hz = np.asarray(hz, dtype=float)
    def c4(flat):
        return float(np.mean(near(flat))) if len(flat) else None
    out['C4'] = dict(분포=q(hz, 2),
                     정수몫=item(c4(hz),
                              unif_ctrl(0.0, float(np.percentile(hz, 99)) if len(hz) else 1.0, hseg, c4),
                              jit_ctrl(hz, c4, amp=0.3)),
                     주의='흔들림 대조는 x높이 배수 단위로 ±0.3')
    r1, r2 = [], []
    for p in P:
        thr = max(3, CLUS_W * p['W'])
        r1.append(len(clusters([b['x1'] for b in p['blocks']], thr)))
        r2.append(len(clusters([b['x2'] for b in p['blocks']], thr)))
    out['C5'] = dict(왼끝_군집=q(r1, 2), 오른끝_군집=q(r2, 2),
                     오른끝_도수=dict(sorted(collections.Counter(r2).items())),
                     왼끝이_더_적은_판=int(sum(1 for a, b in zip(r1, r2) if a < b)),
                     같은_판=int(sum(1 for a, b in zip(r1, r2) if a == b)), 판=len(r1))
    return out


# ---------------------------------------------------------------- D. 판 전체
def sec_D(P):
    out = {}
    M = {k: [] for k in ('왼', '오른', '위', '아래')}
    ink, blk, half = [], [], []
    rep = 0
    for p in P:
        B = p['blocks']
        if not B:
            continue
        m = dict(왼=min(b['x1'] for b in B) / p['W'], 오른=(p['W'] - max(b['x2'] for b in B)) / p['W'],
                 위=min(b['y1'] for b in B) / p['H'], 아래=(p['H'] - max(b['y2'] for b in B)) / p['H'])
        for k, v in m.items():
            M[k].append(v)
        vs = sorted(m.values())
        rep += any(abs(vs[i + 1] - vs[i]) <= 0.01 for i in range(3))
        x1 = min(b['x1'] for b in B); x2 = max(b['x2'] for b in B)
        y1 = min(b['y1'] for b in B); y2 = max(b['y2'] for b in B)
        ink.append((x2 - x1) * (y2 - y1) / (p['W'] * p['H']))
        blk.append(sum((b['x2'] - b['x1']) * (b['y2'] - b['y1']) for b in B) / (p['W'] * p['H']))
        top = sum(1 for b in B for y in b['bases'] if y < p['H'] / 2)
        tot = sum(len(b['bases']) for b in B)
        if tot:
            half.append(top / tot)
    out['D1'] = dict(**{k: q(v, 3) for k, v in M.items()},
                     도수_왼=dict(sorted(collections.Counter(np.round(np.asarray(M['왼']), 2)).items())),
                     두_여백이_0p01안=round(rep / len(M['왼']), 3) if M['왼'] else None)
    out['D2'] = dict(잉크영역_몫=q(ink, 3), 블록넓이_합_몫=q(blk, 3))
    out['D3'] = dict(위절반_줄_몫=q(half, 3),
                     도수=dict(sorted(collections.Counter(np.round(np.asarray(half), 1)).items())) if half else {})
    return out


def run(P, name):
    print('==', name, '· 판', len(P), flush=True)
    return dict(판=len(P), 블록=sum(len(p['blocks']) for p in P),
                A=sec_A(P), B=sec_B(P), C=sec_C(P), D=sec_D(P))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cache', action='append', required=True)
    ap.add_argument('--consensus', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    caches = {}
    for s in a.cache:
        k, v = s.split('=', 1)
        caches[k] = json.load(open(os.path.expanduser(v)))
    BR = next(k for k in caches if '브로크만' in k)
    C = json.load(open(a.consensus))
    sets = {}
    for k, cj in caches.items():
        P = [prep(blocks_pipeline(e), e['size']) for e in cj['raw'].values() if blocks_pipeline(e)]
        sets[('가_측정_' + k) if k == BR else ('측정_' + k)] = P
    raw = caches[BR]['raw']
    keys = [f"{p['folder']}__{p['file']}" for p in C['posters']]
    sets['나_측정_50'] = [prep(blocks_pipeline(raw[k]), raw[k]['size']) for k in keys
                       if k in raw and blocks_pipeline(raw[k])]
    sets['다_라벨_50'] = [prep(blocks_label(p), raw[f"{p['folder']}__{p['file']}"]['size'])
                      for p in C['posters'] if f"{p['folder']}__{p['file']}" in raw and blocks_label(p)]
    res = dict(what='탐색용 · 논문 수치 아님',
               무엇='조판 규칙 탐색 2차 — 항목마다 무작위 대조 (i) 균등 · (ii) 구조만 흔들기 를 함께 낸다',
               규칙=dict(대조_i='그 값의 범위에서 균등하게 뽑는다',
                       대조_ii='실제 분포는 그대로 두고 판 배정을 뒤섞거나(순열) ±%.1f px 흔든다' % JIT,
                       판정='실제 값이 (ii) 의 95% 구간 밖일 때만 «규칙 있음»',
                       시행=TRIALS, 허용=TOL),
               입력={k: dict(commit=v['provenance'].get('commit'), n=v['provenance'].get('n')) for k, v in caches.items()},
               결과={k: run(P, k) for k, P in sets.items()})
    json.dump(res, open(a.out, 'w'), ensure_ascii=False, indent=1)
    print('→', a.out)


if __name__ == '__main__':
    main()
