"""VLM 블록으로 선을 다시 재기 — 사전등록 docs/vlm_pipeline_50_preregister.json 그대로.

    python eval/vlm_pipeline_50.py --work ~/.typo-mcp/brockmann50 \
        --posters docs/labeling/posters_for_labelers.json \
        --guides labels/guides/guides_labelerA_20260917-2016.json labels/guides/guides_labelerB_20260916-0201.json \
        --consensus docs/brockmann_consensus_refs.json \
        --vlm boxes/brockmann_vlm_split_pass1.json --vlm boxes/brockmann_vlm_split_pass2.json \
        --stage2 docs/brockmann_stage2_result.json --prereg docs/vlm_pipeline_50_preregister.json \
        --out docs/vlm_pipeline_50.json

eval/brockmann_stage2_score.py 의 cmd_score 가 하는 선 채점을 그대로 하고, **선 측정에 넘기는
상자 하나만** 바꾼다 (결정 2).

  현행 A   G.entry(path, DS.boxes_norm(lines, size))      — boxes_norm 이 group(lines) 을 부른다
  VLM n    G.entry(path, [[x1/W, y1/H, x2/W, y2/H] …])    — GS.boxes_of(lines, groups_vlm(...)) 의 상자

빼는 것은 cmd_score 846~848 의 «캐시와 같아야 한다» 검사 하나다. 줄 가르기 · 측정 · 선 채점 ·
참조 거르기 · 상수는 바꾸지 않고 커밋된 함수를 import 해서 부른다 (글자 그대로 복사하지 않는다).
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
import detect_surya as DS                   # noqa: E402
import group_score as GS                    # noqa: E402  load_vlm · groups_vlm · boxes_of · _key
import brockmann_stage2_score as S2         # noqa: E402  line_score · agreed_blocks · line_agreed · _stats
from measure import ground as G             # noqa: E402

KINDS = ('베이스라인', 'x높이선', '상단 잉크선')          # 결정 3 — 보고하는 선
ALL_KINDS = [d[0] for d in S2.DIRECT]                     # 결과 파일에는 다섯 가지 모두
REFS_MAIN = ('라벨러A', '라벨러B', '일치')                # 결정 3
METHODS = ('A', 'VLM1', 'VLM2')                           # 결정 3


def _sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def _r(x, n=4):
    return None if x is None else round(float(x), n)


def norm_of(boxes, size):
    """GS.boxes_of 의 픽셀 상자 → 0~1. DS.boxes_norm 과 같은 방식, 여유 없음 (결정 2)."""
    W, H = size
    return [[b[0] / W, b[1] / H, b[2] / W, b[3] / H] for b in boxes]


def main():
    ap = argparse.ArgumentParser()
    for k in ('--work', '--posters', '--consensus', '--stage2', '--prereg', '--out'):
        ap.add_argument(k, required=True)
    ap.add_argument('--guides', nargs='+', required=True)
    ap.add_argument('--vlm', action='append', required=True)
    a = ap.parse_args()

    labs = S2.load_labelers(a.guides)
    refs = {n: labs[n]['posters'] for n in S2.LABELERS}
    refs['합의'] = S2.load_consensus(a.consensus)
    Wk = os.path.expanduser(a.work)
    man = json.load(open(os.path.join(Wk, 'manifest.json'))); root = os.path.expanduser(man['image_root'])
    L = json.load(open(os.path.join(Wk, 'lines.json')))['lines']
    vlms = [GS.load_vlm(v) for v in a.vlm]
    Pl = {it['order']: it for it in json.load(open(a.posters))['main']}

    # (방식, 참조, 선) 별 짝과 분모
    prs = collections.defaultdict(list)
    cnt = collections.Counter()
    blockless = collections.Counter()
    nblocks = collections.Counter()
    nposter = collections.Counter()

    for it in sorted(man['items'], key=lambda x: x['order']):
        o = it['order']; k = GS._key(it['seed']); path = os.path.join(root, it['image'])
        size = tuple(L[k]['size'])
        gray = np.asarray(Image.open(path).convert('L')).astype(float)
        lines, _parent = DS.split_wide_lines(gray, L[k]['lines'])      # 바꾸지 않는다
        boxes = {'A': [b[:4] for b in DS.group(lines)]}
        for n, (vm, _i) in enumerate(vlms):
            asg, _info = GS.groups_vlm(lines, vm.get(k))
            boxes[f'VLM{n + 1}'] = [b[:4] for _g, b in GS.boxes_of(lines, asg)]
        for m in METHODS:
            nb = norm_of(boxes[m], size)
            mblocks = G.entry(path, nb, coords='norm')[0]['blocks'] if nb else []
            blockless[m] += (not mblocks)
            nblocks[m] += len(mblocks)
            res_loc = {}
            for ref in ('라벨러A', '라벨러B', '합의'):
                p = refs[ref].get(o)
                if p is None or not S2.kept(p):
                    continue
                res = S2.line_score(p, mblocks)[0]
                res_loc[ref] = res
                if m == METHODS[0]:
                    nposter[ref] += 1
                for name in ALL_KINDS:
                    r = res[name]
                    prs[(m, ref, name)] += r['pairs']
                    cnt[(m, ref, name, 'T')] += len(r['T']); cnt[(m, ref, name, 'P')] += len(r['P'])
            S_, M_ = refs['라벨러A'].get(o), refs['라벨러B'].get(o)
            if S_ and M_ and S2.kept(S_) and S2.kept(M_):
                if m == METHODS[0]:
                    nposter['일치'] += 1
                RS, RM, ap_ = S2.agreed_blocks(S_, M_)
                resA = S2.line_agreed(S_, M_, RS, RM, ap_, res_loc['라벨러A'], res_loc['라벨러B'], mblocks)[0]
                for name in ALL_KINDS:
                    r = resA[name]
                    prs[(m, '일치', name)] += r['pairs']
                    cnt[(m, '일치', name, 'T')] += len(r['T'])
                    cnt[(m, '일치', name, 'P')] += len(r['P']) - r['정밀분모_뺌']
                    cnt[(m, '일치', name, '정밀분모_뺌')] += r['정밀분모_뺌']
        print(f'  순서 {o} 끝', flush=True)

    def cell(m, ref, name):
        t, p_ = cnt[(m, ref, name, 'T')], cnt[(m, ref, name, 'P')]
        s = (S2._stats_agreed if ref == '일치' else S2._stats)(prs[(m, ref, name)], t, p_)
        out = {kk: s[kk] for kk in ('참값_선', '측정_선', '창안_짝', '허용안_짝', '재현율', '정밀도',
                                    '창안짝_정밀도', '오차_절대_중앙') if kk in s}
        out['놓친_줄'] = t - s['허용안_짝']
        if ref == '일치':
            out['정밀분모_뺌'] = cnt[(m, ref, name, '정밀분모_뺌')]
        return out

    res = dict(
        what=f'사전등록 {a.prereg} 의 결과', 사전등록_sha256=_sha(a.prereg),
        무엇='VLM 블록으로 선을 다시 재고 규칙 기반 A 와 나란히 둔다 (브로크만 라벨 50점)',
        정의=dict(바꾼_것='선 측정에 넘기는 상자만 — P[VLM1] · P[VLM2] 의 상자를 0~1 로 (여유 없음)',
                뺀_것='cmd_score 846~848 의 캐시 비교 검사',
                안_바꾼_것='줄 가르기 · 측정(MIN_LINES 포함) · 선 채점(line_score · line_agreed · _stats) · 참조 거르기 · 상수',
                회차='1 · 2 를 둘 다 적고 주 결과를 고르지 않는다 (평균 내지 않는다)',
                놓친_줄='참값 선 − 허용 안 짝',
                선=list(KINDS), 참조=list(REFS_MAIN) + ['합의 (보조)']),
        입력=dict(work='~' + os.path.expanduser(a.work)[len(os.path.expanduser('~')):],
                줄='{work}/lines.json 에 DS.split_wide_lines 를 건 줄',
                vlm=[dict(파일=v, sha256=_sha(v), 패스=json.load(open(v)).get('패스'),
                          model=json.load(open(v)).get('model')) for v in a.vlm],
                라벨=[dict(파일=g, sha256=_sha(g)) for g in a.guides],
                합의=dict(파일=a.consensus, sha256=_sha(a.consensus))),
        판=len(man['items']), 참조별_판=dict(nposter),
        측정_블록_합={m: nblocks[m] for m in METHODS},
        측정_블록이_0인_판={m: blockless[m] for m in METHODS},
        결과={m: {ref: {name: cell(m, ref, name) for name in ALL_KINDS}
                 for ref in (*REFS_MAIN, '합의')} for m in METHODS})

    # 결정 4 — A 가 커밋된 표 5 와 같은지
    st = json.load(open(a.stage2))['참조별']
    chk, bad = {}, []
    for ref in (*REFS_MAIN, '합의'):
        for name in KINDS:
            want = st.get(ref, {}).get('선', {}).get('종류', {}).get(name)
            got = res['결과']['A'][ref][name]
            if not want:
                continue
            for kk in ('참값_선', '측정_선', '창안_짝', '허용안_짝', '재현율', '정밀도'):
                if kk in want and want[kk] != got.get(kk):
                    bad.append(f'{ref}|{name}|{kk}: 표 5 {want[kk]} · 여기 {got.get(kk)}')
            chk[f'{ref}|{name}'] = '같다' if not bad else '다르다'
    res['A_재현_검사'] = dict(결과=('모두 같다' if not bad else '다르다'), 어긋난_자리=bad,
                          출처=a.stage2, 비교칸=['참값_선', '측정_선', '창안_짝', '허용안_짝', '재현율', '정밀도'])
    json.dump(res, open(a.out, 'w'), ensure_ascii=False, indent=1)
    print('→', a.out)
    if bad:
        print('A 재현 검사가 어긋났다 — 사전등록 결정 4 대로 멈춘다:', *bad[:6], sep='\n  ')
        sys.exit(2)


if __name__ == '__main__':
    main()
