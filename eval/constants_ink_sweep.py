"""잉크 문턱 합성 스윕 — docs/constants_preregister.json «대상 상수» › threshold() · 배경 × 0.72 (순서 1).

    python eval/constants_ink_sweep.py --dir ~/.typo-mcp/synth_sweep --manifest docs/synth_sweep_manifest.json \
        --lines ~/.typo-mcp/synth_sweep_lines --prereg docs/constants_preregister.json --out docs/constants_ink_threshold.json

세트: 합성 스윕 공용 세트 (수정 1 · 2 · 3, 13셀 × seed 7201~7230). 줄: 사람 확인 뒤 뽑은 Surya 줄
(eval/group_score.py detect --order columns). 재기: measure_corpus.measure_items 와 같은 길 —
detect_surya.boxes_norm → measure.ground.entry (photo 없음, 블록 값은 같다). 코드의 상수는 바꾸지 않고
실행 중에만 measure.ink.threshold 를 «창 중앙값 × k» 로 갈아 끼운다 (k = 0.72 이면 코드와 같은 함수).

지표: 표 1 직접 짝 (eval/synth_score.direct_lines) 의 베이스라인 · x높이선 · 상단 잉크선 (결과 필드 «캡선») 재현율.
실행 전에 정한 해석 (처음 실행 때 사전등록에 적혀 있지 않던 자리. 앞 두 가지는 결과를 열기 전 수정 5 로 사전등록에 올렸다):
  - 셀 재현율 = 셀 안 30판을 모은 허용안 짝 ÷ 참값 선. 결정에 쓰는 곡선 = 13셀 단순 평균
    (같은 파일의 합성 스윕 행 «lines(… body_h=)» 이 적은 «셀 평균» 을 따른다). 전체를 모은 재현율은 참고로만 적는다.
  - 못 잰 판 (상자 없음 · 예외) 은 짝 0 으로 센다.
  - 평평 구간 = 최고 재현율의 격자 점 (여럿이면 가장 작은 k) 을 품는, 재현율 ≥ 최고 − δ 인 연속 격자 점.
  - 교집합의 «가운데 격자 점» = 교집합 격자 점을 k 순으로 늘어놓은 (n − 1) // 2 번째 (짝수 개면 낮은 쪽).
결과 보고까지만 한다 — 코드의 0.72 는 바꾸지 않는다.
"""
import argparse
import hashlib
import json
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'eval'))
import detect_surya as DS          # noqa: E402
import measure_corpus as MC        # noqa: E402  provenance
import synth_score as SS           # noqa: E402  direct_lines (표 1 직접 짝)
from measure import ground as G    # noqa: E402
from measure import ink            # noqa: E402

KINDS = (('베이스라인', '베이스라인'), ('x높이선', 'x높이선'), ('상단 잉크선', '캡선'))
CURRENT = 0.72
ORIGINAL_THRESHOLD = ink.threshold


def _sha(p):
    return hashlib.sha256(open(os.path.expanduser(p), 'rb').read()).hexdigest()


def measure(item, lines, k):
    ink.threshold = (lambda g, k=k: np.median(g) * k)
    try:
        bx = DS.boxes_norm(lines['lines'], lines['size'])
        if not bx:
            return None, '상자 없음'
        e, _ = G.entry(item['image'], bx, coords='norm', photo=False)
        return e, None
    except Exception as ex:                       # measure_items 와 같이 판 실패로 센다
        return None, f'{type(ex).__name__}: {ex}'
    finally:
        ink.threshold = ORIGINAL_THRESHOLD


def flat(ks, vals, delta):
    best = max(vals)
    i = vals.index(best)
    lo = hi = i
    while lo - 1 >= 0 and vals[lo - 1] >= best - delta - 1e-12:
        lo -= 1
    while hi + 1 < len(vals) and vals[hi + 1] >= best - delta - 1e-12:
        hi += 1
    return dict(최고=round(best, 4), 최고_k=ks[i], 구간=[ks[lo], ks[hi]], 격자점=ks[lo:hi + 1])


def main(argv=None):
    ap = argparse.ArgumentParser(description='잉크 문턱 합성 스윕 (constants_preregister 순서 1)')
    ap.add_argument('--dir', required=True); ap.add_argument('--manifest', required=True)
    ap.add_argument('--lines', required=True, help='줄 폴더 (manifest.json · lines.json)')
    ap.add_argument('--prereg', required=True); ap.add_argument('--out', required=True)
    a = ap.parse_args(argv)
    P = json.load(open(a.prereg))
    delta = P['공통 규칙']['합성 스윕']['δ']
    ks = [round(0.50 + 0.02 * i, 2) for i in range(21)]
    D = os.path.expanduser(a.dir); M = json.load(open(a.manifest))
    LW = os.path.expanduser(a.lines); LM = json.load(open(os.path.join(LW, 'manifest.json')))
    LL = json.load(open(os.path.join(LW, 'lines.json')))
    items = []
    by_img = {(it['cell'], it['seed']): it for it in M['items']}
    for li in LM['items']:
        it = by_img[(li['cell'], li['poster_seed'])]
        key = f"{li['seed']:03d}"
        p = os.path.join(D, it['image'])
        if _sha(p) != it['image_sha256'] or LL['lines'][key]['sha256'] != it['image_sha256'] or li['image_sha256'] != it['image_sha256']:
            sys.exit(f'manifest 와 다른 이미지 또는 줄: {p}')
        items.append(dict(cell=it['cell'], seed=it['seed'], image=p, truth=json.load(open(p[:-4] + '.json')), lines=LL['lines'][key]))
    if len(items) != len(M['items']):
        sys.exit('줄 파일이 세트를 다 덮지 않는다')
    # k = 0.72 에서 갈아 끼운 함수가 코드 함수와 같은 결과를 내는지
    same = 0
    for x in items[::30]:
        e1, _ = measure(x, x['lines'], CURRENT)
        e2, _ = G.entry(x['image'], DS.boxes_norm(x['lines']['lines'], x['lines']['size']), coords='norm', photo=False)
        same += (e1 == e2)
    cells = list(M['cells'])
    t0 = time.time()
    grid = {}
    for k in ks:
        per = {c: {name: [0, 0, 0] for name, _f in KINDS} for c in cells}   # 참값 선 · 허용안 짝 · 측정 선 (정밀도, 수정 8)
        fail = {c: [] for c in cells}
        for x in items:
            e, why = measure(x, x['lines'], k)
            d = SS.direct_lines(x['truth'], e if e else dict(blocks=[]))
            if why:
                fail[x['cell']].append([x['seed'], why])
            for name, f in KINDS:
                per[x['cell']][name][0] += d[f]['n_truth']
                per[x['cell']][name][1] += sum(q['hit'] for q in d[f]['pairs'])
                per[x['cell']][name][2] += d[f]['n_meas']
        grid[f'{k:.2f}'] = dict(셀={c: {name: dict(참값_선=v[0], 허용안_짝=v[1], 측정_선=v[2],
                                                   재현율=round(v[1] / v[0], 4) if v[0] else None,
                                                   정밀도=round(v[1] / v[2], 4) if v[2] else None)
                                       for name, v in per[c].items()} for c in cells},
                                못_잰_판={c: v for c, v in fail.items() if v})
        print(f'  k {k:.2f}  {time.time() - t0:.0f}s', flush=True)
    curves, pooled = {}, {}
    for name, _f in KINDS:
        curves[name] = [round(float(np.mean([grid[f'{k:.2f}']['셀'][c][name]['재현율'] for c in cells])), 4) for k in ks]
        pooled[name] = [round(sum(grid[f'{k:.2f}']['셀'][c][name]['허용안_짝'] for c in cells)
                              / sum(grid[f'{k:.2f}']['셀'][c][name]['참값_선'] for c in cells), 4) for k in ks]
    cell_curves = {c: {name: [grid[f'{k:.2f}']['셀'][c][name]['재현율'] for k in ks] for name, _f in KINDS} for c in cells}
    cell_flats = {c: {name: (flat(ks, v, delta) if None not in v else None) for name, v in cc.items()} for c, cc in cell_curves.items()}

    def decide(d):
        fl = {name: flat(ks, curves[name], d) for name in curves}
        it = sorted(set.intersection(*(set(f['격자점']) for f in fl.values())))
        ins = all(CURRENT in f['격자점'] for f in fl.values())
        if ins:
            v = dict(판정='유지', 값=CURRENT)
        elif it:
            v = dict(판정='바꿀 값', 값=it[(len(it) - 1) // 2])
        else:
            v = dict(판정='멈춤', 값=None, 까닭='세 선 종류 평평 구간의 교집합이 없다')
        return fl, it, ins, v

    flats, inter, inside, verdict = decide(delta)
    # 판정 민감도 — 판정은 사전등록 δ 로만 한다. 다른 δ 는 기록만
    sens = {}
    for d in (0.015, 0.02, 0.025):
        fl, it, ins, v = decide(d)
        sens[f'{d}'] = dict(평평_구간={name: f['구간'] for name, f in fl.items()}, 교집합=([it[0], it[-1]] if it else None),
                            교집합_격자점_수=len(it), 가운데=(it[(len(it) - 1) // 2] if it else None), 판정=v)
    # 정밀도 (수정 8) — 판정은 바꾸지 않는다. 표시 = 정밀도 < 현재 값 정밀도 − δ 인 격자 점
    prec = {name: [round(float(np.mean([grid[f'{k:.2f}']['셀'][c][name]['정밀도'] for c in cells])), 4) for k in ks] for name, _f in KINDS}
    ci = ks.index(CURRENT)
    prec_flags = {name: [ks[i] for i, v in enumerate(prec[name]) if prec[name][ci] - v > delta + 1e-12] for name in prec}
    say = lambda v: f"유지 {v['값']}" if v['판정'] == '유지' else (f"{v['값']}" if v['판정'] == '바꿀 값' else '멈춤')
    sensitivity = dict(
        표시='기록만 — 판정은 사전등록 δ 대로 한다',
        δ별=sens,
        곡선_정밀도=prec,
        정밀도_δ이상_떨어진_격자={k: v for k, v in prec_flags.items() if v},
        정밀도_표시_정의='정밀도 = 허용 안 짝 ÷ 측정 선 (13셀 단순 평균). 표시 = 정밀도 < 현재 값 (0.72) 정밀도 − δ 인 격자 점 (수정 8, 판정은 바꾸지 않음)',
        셀별_평평_구간={c: {name: (None if f is None else f['구간']) for name, f in d_.items()} for c, d_ in cell_flats.items()},
        한줄=f"판정은 사전등록 δ {delta} 대로 {say(verdict)}. δ 0.015 에서는 {say(sens['0.015']['판정'])}")
    out = dict(
        무엇='잉크 문턱 합성 스윕 — threshold() 창 중앙값 × k, constants_preregister 순서 1. 결과 보고까지만 (코드의 0.72 는 바꾸지 않음)',
        사전등록=a.prereg, 사전등록_sha256=_sha(a.prereg), manifest=a.manifest, manifest_sha256=_sha(a.manifest),
        줄=dict(폴더=a.lines, manifest_sha256=_sha(os.path.join(LW, 'manifest.json')), lines_sha256=_sha(os.path.join(LW, 'lines.json')),
               provenance=LL.get('provenance'), 순서=LL.get('order')),
        정의=dict(격자=ks, δ=delta, 지표='eval/synth_score.direct_lines 재현율 — 베이스라인 · x높이선 · 상단 잉크선 (필드 «캡선»)',
                재기='detect_surya.boxes_norm → measure.ground.entry (photo=False), 실행 중 measure.ink.threshold = 창 중앙값 × k',
                셀_재현율='셀 30판을 모은 허용안 짝 ÷ 참값 선', 결정_곡선='13셀 단순 평균 (같은 파일 body_h 행의 «셀 평균» 을 따름)',
                못_잰_판='짝 0 으로 셈', 평평='최고 재현율 격자 점 (여럿이면 가장 작은 k) 을 품는, 재현율 ≥ 최고 − δ 인 연속 격자 점',
                가운데='교집합 격자 점을 k 순으로 늘어놓은 (n − 1) // 2 번째 (짝수 개면 낮은 쪽)'),
        k072_코드함수와_같은_판=f'{same}/{len(items[::30])}',
        곡선_셀평균=curves, 참고_곡선_전체모음=pooled, 평평_구간=flats, 교집합=inter,
        참고_셀별=dict(곡선=cell_curves, 평평_구간=cell_flats),
        현재값_모든_평평구간_안=inside, 판정=verdict, 판정_민감도=sensitivity,
        skew='baseline/skew.py:39 의 0.72 는 이 판정을 따라간다 (사전등록)',
        격자별=grid, provenance=MC.provenance('eval/constants_ink_sweep.py', len(items)))
    json.dump(out, open(a.out, 'w'), ensure_ascii=False, indent=1)
    print('판정', verdict, '→', a.out)


if __name__ == '__main__':
    main()
