"""베이스라인과 60등분 가로 칸 선 — 사전등록 docs/baseline_grid60_preregister.json 그대로.

    python eval/baseline_grid60.py \
        --caches VLM_회차1=~/.typo-mcp/vlm-pass1/brockmann.json VLM_회차2=~/.typo-mcp/vlm-pass2/brockmann.json \
        --posters docs/labeling/posters_for_labelers.json \
        --guides labels/guides/guides_labelerA_20260917-2016.json labels/guides/guides_labelerB_20260916-0201.json \
        --size-cache ~/.typo-mcp/brockmann.json \
        --prereg docs/baseline_grid60_preregister.json --out docs/baseline_grid60_result.json

사전등록이 정한 것만 구현한다. 새 지표를 더하지 않고 문턱을 두지 않는다.

  칸      y = i·H/60 (i = 0…60), 한 칸 = H/60. 가로 칸 선만 (결정 1).
  거리    d = |y/(H/60) − round(y/(H/60))|, 0~0.5. 포스터별 **중앙값** (결정 2).
  대조    베이스라인 전체를 세로로 [0, 1칸) 균등 평행 이동, 2,000회, 씨앗 20261007 (결정 3).
  백분위  2,000벌 가운데 중앙값이 실제 중앙값 **미만**인 벌의 몫 (결정 3).
  판정    백분위 < 0.025 이면 «60등분 칸 선에 맞춰짐» (결정 4, 한쪽 꼬리).
  누적    블록마다 r = lead ÷ (H/60) · e = |r − round(r)| · 누적 = e × (n − 1) 칸 (결정 5).
"""
import argparse
import hashlib
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
import brockmann_stage2_score as S2          # noqa: E402  load_labelers · kept · refs_of · _num

N = 60                 # 결정 1
TRIALS = 2000          # 결정 3
SEED = 20261007        # 결정 3
ALPHA = 0.025          # 결정 4 — 한쪽 꼬리
SINSILLA = 'Musica_Viva__1960_Musica viva - Donnerstag, 10. März 1960 - Tonhalle Grosser S.jpg'


def _sha(p):
    return hashlib.sha256(open(os.path.expanduser(p), 'rb').read()).hexdigest()


def _r(x, n=4):
    return None if x is None else round(float(x), n)


def _q(v, n=4):
    a = np.asarray(v, dtype=float)
    if not len(a):
        return dict(n=0)
    return dict(n=int(len(a)), 중앙=_r(np.median(a), n), p25=_r(np.percentile(a, 25), n),
                p75=_r(np.percentile(a, 75), n), 최소=_r(a.min(), n), 최대=_r(a.max(), n))


def cell_d(y, step):
    """결정 2 — 칸 단위 거리 (0~0.5)."""
    t = np.asarray(y, dtype=float) / step
    return np.abs(t - np.round(t))


def rng_for(key):
    """포스터마다 따로 둔 난수 — 씨앗 20261007 과 포스터 열쇠에서 뽑는다.

    사전등록은 씨앗만 정했다 (결정 3). 난수를 하나 두고 포스터를 차례로 돌리면 값이 대상 순서에
    딸려 가므로 (22 절에서 겪은 모듈 수준 rng 문제), 포스터 열쇠로 씨앗을 갈라 순서와 무관하게
    만든다. **수를 보기 전에 한 선택이다.**
    """
    h = int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], 'big')
    return np.random.default_rng([SEED, h])


def poster_stat(bases, H, key):
    """결정 2 · 3 · 4 — 포스터 하나."""
    rng = rng_for(key)
    step = H / N
    b = np.asarray(sorted(bases), dtype=float)
    real = float(np.median(cell_d(b, step)))
    meds = np.empty(TRIALS)
    for i in range(TRIALS):
        meds[i] = np.median(cell_d(b + rng.uniform(0, step), step))
    pct = float(np.mean(meds < real))
    return dict(줄=len(b), 거리_중앙=_r(real), 백분위=_r(pct),
                대조=dict(평균=_r(meds.mean()), 구간=[_r(np.percentile(meds, 2.5)), _r(np.percentile(meds, 97.5))]),
                판정=('60등분 칸 선에 맞춰짐' if pct < ALPHA else '아님'))


def cumulative(blocks, H):
    """결정 5 — 블록마다 줄 간격 ÷ 칸 의 정수 어긋남과 누적."""
    step = H / N
    rows = []
    for b in blocks:
        bs = sorted(b['bases'])
        n = len(bs)
        if n < 2:
            continue
        lead = float(np.median(np.diff(bs)))
        r = lead / step
        e = abs(r - round(r))
        rows.append(dict(줄=n, 줄간격_px=_r(lead, 2), r=_r(r, 4), 가까운정수=int(round(r)),
                         e=_r(e, 4), 누적_칸=_r(e * (n - 1), 4)))
    return rows


def main():
    ap = argparse.ArgumentParser()
    for k in ('--posters', '--size-cache', '--prereg', '--out'):
        ap.add_argument(k, required=True)
    ap.add_argument('--caches', nargs='+', required=True)
    ap.add_argument('--guides', nargs='+', required=True)
    a = ap.parse_args()

    meas = {}
    for s in a.caches:
        k, v = s.split('=', 1)
        meas[k] = (v, json.load(open(os.path.expanduser(v)))['raw'])
    size_raw = json.load(open(os.path.expanduser(a.size_cache)))['raw']
    labs = S2.load_labelers(a.guides)
    Pl = {it['order']: it for it in json.load(open(a.posters))['main']}
    ck = {o: f"{it['folder']}__{it['file']}" for o, it in Pl.items()}

    # 대상 묶음 — {이름: {열쇠: (블록 목록, H)}}
    sets = {}
    for nm, (_p, raw) in meas.items():
        sets[nm] = {k: ([dict(bases=[float(x) for x in b['bases']]) for b in (raw[k].get('blocks') or [])],
                        float(raw[k]['size'][1])) for k in sorted(raw)
                    if (raw[k].get('blocks') or [])}
    for nm in S2.LABELERS:
        ps = labs[nm]['posters']
        d = {}
        for o in sorted(ps):
            if o not in ck or ck[o] not in size_raw or not S2.kept(ps[o]):
                continue
            R, _X = S2.refs_of(ps[o], 'main')
            bl = [dict(bases=[float(l['base']) for l in b['lines'] if S2._num(l['base'])]) for b in R]
            bl = [b for b in bl if b['bases']]
            if bl:
                d[ck[o]] = (bl, float(size_raw[ck[o]]['size'][1]))
        sets[f'라벨 {nm}'] = d

    out = dict(
        what=f'사전등록 {a.prereg} 의 결과', 사전등록_sha256=_sha(a.prereg),
        무엇='베이스라인이 판 높이를 60등분한 가로 칸 선에 맞춰 놓였는지',
        정의=dict(칸=f'y = i·H/{N} (i = 0…{N}), 한 칸 = H/{N}. 가로 칸 선만 · 테두리 포함',
                거리='|y/칸 − round(y/칸)| (0~0.5), 포스터별 중앙값',
                대조=f'베이스라인 전체를 세로로 [0, 1칸) 균등 평행 이동 · {TRIALS}회 · 씨앗 {SEED}',
                백분위='중앙값이 실제 중앙값 미만인 벌의 몫', 난수='포스터마다 따로 — 씨앗과 포스터 열쇠에서 뽑아 대상 순서와 무관하게 한다 (수를 보기 전 선택)',
                판정=f'백분위 < {ALPHA} 이면 «60등분 칸 선에 맞춰짐» (한쪽 꼬리)',
                누적='블록마다 r = 줄간격 ÷ 칸 · e = |r − round(r)| · 누적 = e × (줄 수 − 1) 칸. 줄간격은 베이스라인 간격의 중앙값 (캐시의 lead 필드는 정수로 둥근 값이라 쓰지 않는다)',
                우연_기대=f'백분위가 고르면 판정을 받는 포스터는 약 {ALPHA:.1%}'),
        입력=dict(측정={k: '~' + os.path.expanduser(v[0])[len(os.path.expanduser('~')):] for k, v in meas.items()},
                라벨=[dict(파일=g, sha256=_sha(g)) for g in a.guides],
                판_크기='~' + os.path.expanduser(a.size_cache)[len(os.path.expanduser('~')):]),
        신실라_판=dict(열쇠=SINSILLA, 대상별={}),
        코퍼스별={})

    for nm, d in sets.items():
        # ── 신실라 판 — 블록별 · 줄별
        if SINSILLA in d:
            bl, H = d[SINSILLA]
            step = H / N
            st = poster_stat([x for b in bl for x in b['bases']], H, SINSILLA)
            per = []
            for i, b in enumerate(sorted(bl, key=lambda b: min(b['bases'])), 1):
                bs = sorted(b['bases'])
                per.append(dict(블록=i, 줄=len(bs),
                                줄별=[dict(y=_r(y, 1), 칸=_r(y / step, 3), 거리_칸=_r(float(cell_d(y, step)), 4))
                                     for y in bs]))
            out['신실라_판']['대상별'][nm] = dict(H=_r(H, 1), 칸_px=_r(step, 3), **st,
                                              누적=cumulative(bl, H), 블록별=per)
        # ── 코퍼스별
        rows, cum_e, cum_c = [], [], []
        for k in sorted(d):
            bl, H = d[k]
            bs = [x for b in bl for x in b['bases']]
            if not bs:
                continue
            st = poster_stat(bs, H, k)
            rows.append(dict(열쇠=k, **st))
            for c in cumulative(bl, H):
                cum_e.append(c['e']); cum_c.append(c['누적_칸'])
        hit = [r for r in rows if r['판정'] != '아님']
        out['코퍼스별'][nm] = dict(
            판=len(rows), 줄_합=sum(r['줄'] for r in rows),
            거리_중앙_분포=_q([r['거리_중앙'] for r in rows]),
            백분위_분포=_q([r['백분위'] for r in rows]),
            맞춰짐_판=len(hit), 우연_기대_판=_r(ALPHA * len(rows), 2),
            맞춰짐_목록=[dict(열쇠=r['열쇠'], 줄=r['줄'], 거리_중앙=r['거리_중앙'], 백분위=r['백분위']) for r in hit],
            누적=dict(블록=len(cum_e), e_중앙=_r(np.median(cum_e)) if cum_e else None,
                    누적칸_중앙=_r(np.median(cum_c)) if cum_c else None,
                    e_분포=_q(cum_e), 누적칸_분포=_q(cum_c)),
            판별=rows)
        print(f'  {nm:12} 판 {len(rows):3} · 거리 중앙 {out["코퍼스별"][nm]["거리_중앙_분포"]["중앙"]} · '
              f'맞춰짐 {len(hit)} (기대 {_r(ALPHA * len(rows), 2)})', flush=True)
    json.dump(out, open(a.out, 'w'), ensure_ascii=False, indent=1)
    print('→', a.out)


if __name__ == '__main__':
    main()
