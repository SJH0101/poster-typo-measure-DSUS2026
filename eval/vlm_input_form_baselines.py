"""탐색용 · 논문 수치 아님 — 입력 형태 비교와 **같은 30장 · 같은 채점 정의**로 VLM 을 쓰지 않는
두 방식(규칙 기반 A · 간격 기반 C)의 블록 F1 을 낸다. 원고 4-2 의 «규칙 기반 0.731 · 간격 기반 0.920».

    python eval/vlm_input_form_baselines.py --work ~/.typo-mcp/vlm_input --dir ~/.typo-mcp/clean \
        --lines ~/.typo-mcp/clean-lines.json --c-pad-rule neighbor_half \
        --out docs/vlm_input_form_baselines.json

`docs/vlm_input_form_explore.json` 의 조건별 값과 섞지 않고 새 파일로만 낸다. 고치는 것은 없다 —
채점은 `explore_vlm_input_form.count` · `.f1` · `.truth_boxes` 를, 묶기는 `group_score.groups_A`
(= `detect_surya.group`) 와 `group_gap.group_gap` 을 그대로 부른다.

판마다 원 분수(맞음 / 참조 · 맞음 / 출처)와 합산 분수를 함께 적는다 — F1 = 2·맞음 / (참조 + 출처)
가 되는 것은 재현 · 정밀의 분자가 같기 때문이다.
"""
import argparse
import collections
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
import explore_vlm_input_form as VIF      # noqa: E402  count · f1 · truth_boxes (채점 정의)
import group_gap as GG                    # noqa: E402  방식 C
import group_score as GS                  # noqa: E402  groups_A · boxes_of

EXPECT = {'A': 0.7311, 'C': 0.9197}       # 원고 4-2 · paper_numbers 10.4 의 값


def _p(x):
    return os.path.expanduser(x)


def _short(path):
    """홈 앞머리를 ~ 로 — 셸이 ~ 를 펼쳐도 기록이 같게."""
    h = os.path.expanduser('~')
    p = os.path.abspath(_p(path))
    return '~' + p[len(h):] if p.startswith(h) else p


def frac(a, b):
    return dict(분자=int(a), 분모=int(b), 값=(round(a / b, 4) if b else None))


def main():
    ap = argparse.ArgumentParser()
    for k in ('--work', '--dir', '--lines', '--out'):
        ap.add_argument(k, required=True)
    ap.add_argument('--c-pad-rule', default='neighbor_half', choices=GG.PAD_RULES)
    a = ap.parse_args()

    S = json.load(open(os.path.join(_p(a.work), 'sample.json')))['목록']
    L = json.load(open(_p(a.lines)))['lines']

    per, tot = {}, {}
    for meth in ('A', 'C'):
        rows, agg = [], collections.Counter()
        for r in S:
            k = str(r['seed'])
            t = json.load(open(os.path.join(_p(a.dir), f'{k}.json')))
            T = VIF.truth_boxes(t)
            lines = L[k]['lines']
            if meth == 'A':
                asg = GS.groups_A(lines)
            else:
                g = np.asarray(Image.open(os.path.join(_p(a.dir), r['file'])).convert('L')).astype(float)
                asg, _d = GG.group_gap(g, lines, pad_rule=a.c_pad_rule)
            P = [b[1][:4] for b in GS.boxes_of(lines, asg)]
            c = VIF.count(T, P)
            agg.update(c)
            rows.append(dict(seed=r['seed'], columns=r['columns'], xh=r['xh'], **c, **VIF.f1(c)))
        per[meth] = rows
        tot[meth] = dict(판=len(rows), **dict(agg), **VIF.f1(agg),
                         원_분수=dict(재현=frac(agg['맞음'], agg['참조']),
                                   정밀=frac(agg['맞음'], agg['출처']),
                                   F1=frac(2 * agg['맞음'], agg['참조'] + agg['출처'])))

    res = dict(
        what='탐색용 · 논문 수치 아님 · 사전등록 없음 (입력 형태 비교와 같은 성질의 탐색)',
        무엇='입력 형태 비교와 같은 30장 · 같은 채점 정의로 낸 VLM 없는 두 방식의 블록 F1',
        왜='원고 4-2 의 «같은 30점에서 규칙 기반 0.731 · 간격 기반 0.920» 이 결과 파일에 없던 값이라 남긴다',
        정의=dict(채점='eval/explore_vlm_input_form.py 의 count · f1 · truth_boxes 를 그대로 부른다 — '
                     '블록 IoU ≥ 0.5 1:1 (detector_score.match) · 참값은 c_in 쌍을 합친 정의',
                A='group_score.groups_A — detect_surya.group 의 블록 상자에 줄을 배정',
                C=f'group_gap.group_gap τ {GG.TAU}px · pad_rule {a.c_pad_rule} · 3줄 미만 조각은 detect_surya.group 폴백',
                F1='2·맞음 / (참조 + 출처) — 재현 · 정밀의 분자가 같아 조화평균이 이 분수가 된다',
                판='입력 형태 비교와 같은 30장 (work 의 sample.json 그대로, 다시 뽑지 않는다)'),
        입력=dict(work=_short(a.work), dir=_short(a.dir), lines=_short(a.lines), c_pad_rule=a.c_pad_rule),
        조건별=tot, 판별=per)

    bad = {m: tot[m]['F1'] for m in EXPECT if tot[m]['F1'] != EXPECT[m]}
    res['원고값_대조'] = dict(기대=EXPECT, 낸값={m: tot[m]['F1'] for m in EXPECT},
                         같은가=(not bad), 어긋남=bad or None)
    json.dump(res, open(a.out, 'w'), ensure_ascii=False, indent=1)
    for m in ('A', 'C'):
        f = tot[m]['원_분수']['F1']
        print(f"  {m}: F1 {f['분자']}/{f['분모']} = {f['값']} (맞음 {tot[m]['맞음']} · 참조 {tot[m]['참조']} · 출처 {tot[m]['출처']})")
    print('→', a.out)
    if bad:
        sys.exit(f'원고 값과 다르다: {bad} (기대 {EXPECT})')


if __name__ == '__main__':
    main()
