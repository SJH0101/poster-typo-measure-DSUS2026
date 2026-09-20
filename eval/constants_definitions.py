"""정의로 정하는 상수 (constants_preregister 순서 2 · 수정 4 의 e = 1) — 계산만 하고 코드는 바꾸지 않는다.

    python eval/constants_definitions.py --prereg docs/constants_preregister.json \
        --font /System/Library/Fonts/Helvetica.ttc --out docs/constants_definitions.json

글꼴 비율은 Helvetica (index 0) 1000px 실측. x높이 · 어센더 윗끝은 eval/synth_gen._font_info 와 같게 getbbox (anchor 'ls').
발음기호 (점 · 악센트) 는 1000px 로 그린 글자 마스크 (알파 > 0) 의 8-연결 덩어리 가운데 x높이선 위에 통째로 뜬 것.

실행 전에 정한 해석 (사전등록에 적혀 있지 않은 자리):
  - 몸통 높이_em = 소문자 몸통 = x높이_em.
  - 발음기호 글자 모음 = Latin-1 소문자 가운데 위에 뜬 표시가 있을 수 있는 글자 + i · j
    (àáâãäåèéêëìíîïñòóôõöùúûüýÿ ij). 덩어리가 x높이선 위에 통째로 뜨지 않은 글자는 세지 않는다.
  - 점 아래끝 − x높이선 = x높이선 행 − 뜬 덩어리 아래끝 (마지막 행 + 1), 글자마다 뜬 덩어리 가운데 가장 큰 값, 모음에서 최댓값.
  - 어센더_em = b d h k l 윗끝. 사전등록이 범위 (0.717~0.719) 로 적어 최솟값 · 최댓값 둘 다 계산한다.
  - x높이_px 격자 = 3 · 5 · 8 · 12 · 18 (합성 통제 실험 x높이 수준).
판정: 유도식 값이 현재 값과 같으면 유지, 다르면 바꿀 값. «식 꼴 변경» 행은 상수를 그 식으로 바꾼다 (사전등록 순서 2 결정 규칙).
"""
import argparse
import hashlib
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import measure_corpus as MC        # noqa: E402  provenance

E = 1                               # 수정 4 — e 측정 폐지, e 를 쓰던 식은 e = 1
MARK_CHARS = 'àáâãäåèéêëìíîïñòóôõöùúûüýÿij'
ASC_CHARS = 'bdhkl'
XH_GRID = (3, 5, 8, 12, 18)
PX = 1000


def _sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def marks(font, xh_row):
    """글자마다 x높이선 위에 통째로 뜬 덩어리 — (높이 행, 아래끝 틈 행) 가운데 큰 값."""
    out = {}
    for ch in MARK_CHARS:
        l, t, r, b = font.getbbox(ch, anchor='ls')
        W, H = r - l + 20, b - t + 20
        im = Image.new('L', (W, H), 0)
        base = -t + 10
        ImageDraw.Draw(im).text((-l + 10, base), ch, font=font, fill=255, anchor='ls')
        lab, n = ndimage.label(np.asarray(im) > 0, structure=np.ones((3, 3)))
        xline = base - xh_row                     # x높이선 행 (위 경계)
        hs, gs = [], []
        for i in range(1, n + 1):
            rows = np.where((lab == i).any(axis=1))[0]
            top, bot = int(rows[0]), int(rows[-1]) + 1   # bot = 아래끝 (마지막 행 + 1)
            if bot <= xline:
                hs.append(bot - top); gs.append(xline - bot)
        if hs:
            out[ch] = dict(높이_행=max(hs), 아래끝_틈_행=max(gs))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description='정의로 정하는 상수 계산 (constants_preregister 순서 2)')
    ap.add_argument('--prereg', required=True); ap.add_argument('--font', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args(argv)
    f = ImageFont.truetype(a.font, PX, index=0)
    top = lambda ch: -f.getbbox(ch, anchor='ls')[1]
    xh_row = top('x'); xh_em = xh_row / PX
    asc = {ch: top(ch) / PX for ch in ASC_CHARS}
    mk = marks(f, xh_row)
    small_ch = max(mk, key=lambda c: mk[c]['높이_행'])
    gap_ch = max(mk, key=lambda c: mk[c]['아래끝_틈_행'])
    small = mk[small_ch]['높이_행'] / PX / xh_em
    gap_ratio = mk[gap_ch]['아래끝_틈_행'] / PX / xh_em
    min_h = 2
    rows = []
    rows.append(dict(이름='lines · descender 의 min_h', 위치=['measure/ink.py:44', 'measure/ink.py:142', 'measure/probe.py:30'], 현재=2,
                     계산='수정 4 — 정의: 번진 가장자리 1행 + 몸통 1행 = 2 (= e + 1, e = 1)', 계산값=min_h,
                     판정='유지' if min_h == 2 else '바꿀 값'))
    rows.append(dict(이름='region.measure() · 최소 창', 위치=['measure/region.py:78'], 현재=4,
                     계산=f'2 × min_h = 2 × {min_h}', 계산값=2 * min_h, 판정='유지' if 2 * min_h == 4 else '바꿀 값'))
    rows.append(dict(이름='baseline(… frac=)', 위치=['measure/ink.py:129'], 현재=0.5,
                     계산='frac = 덮임 절반 0.5 (라벨 요청서 6절 «절반 넘게 진하면» 과 같은 약속)', 계산값=0.5, 판정='유지'))
    asc_rows = {}
    for label, em in (('어센더_em 최솟값', min(asc.values())), ('어센더_em 최댓값', max(asc.values()))):
        ratio = (em - xh_em) / xh_em
        asc_rows[label] = dict(어센더_em=em, 비=round(ratio, 5),
                               x높이별={str(x): dict(내림값=math.floor(ratio * x / 2), 문턱=max(E + 1, math.floor(ratio * x / 2))) for x in XH_GRID})
    rows.append(dict(이름='split_marks() · 어센더 2행', 위치=['measure/ink.py:210'], 현재=2, 식_꼴_변경=True,
                     계산=f'문턱 = max(e + 1, ⌊(어센더_em − x높이_em) ÷ x높이_em × x높이_px ÷ 2⌋), e = {E}, x높이_em = {xh_em}, 어센더_em = {asc}',
                     계산값=asc_rows, 판정='바꿀 값 (식으로)'))
    rows.append(dict(이름='lines() · 발음기호 small', 위치=['measure/ink.py:98'], 현재=0.5,
                     계산=f'small = 뜬 덩어리 높이_em ÷ x높이_em 의 최댓값 — {small_ch}: {mk[small_ch]["높이_행"]} ÷ {xh_row}',
                     계산값=round(small, 4), 판정='유지' if round(small, 4) == 0.5 else '바꿀 값'))
    gmin = {str(x): math.ceil(gap_ratio * x) + E for x in XH_GRID}
    rows.append(dict(이름='lines() · 발음기호 틈 최소', 위치=['measure/ink.py:101'], 현재=3, 식_꼴_변경=True,
                     계산=f'틈 최소 = ⌈(점 아래끝 − x높이선)_em ÷ x높이_em × x높이_px⌉ + e, e = {E} — {gap_ch}: {mk[gap_ch]["아래끝_틈_행"]} ÷ {xh_row}',
                     계산값=dict(비=round(gap_ratio, 5), x높이별=gmin), 판정='바꿀 값 (식으로)'))
    rows.append(dict(이름='lines() · 발음기호 틈 비', 위치=['measure/ink.py:101'], 현재=0.6,
                     계산=f'틈 비 = (점 아래끝 − x높이선)_em ÷ x높이_em 의 최댓값 — {gap_ch}: {mk[gap_ch]["아래끝_틈_행"]} ÷ {xh_row}',
                     계산값=round(gap_ratio, 4), 판정='유지' if round(gap_ratio, 4) == 0.6 else '바꿀 값'))
    out = dict(
        무엇='정의로 정하는 상수 — constants_preregister 순서 2 (수정 4 의 e = 1). 계산 결과만, 코드의 값은 바꾸지 않음',
        사전등록=a.prereg, 사전등록_sha256=_sha(a.prereg),
        글꼴=dict(파일=a.font, index=0, sha256=_sha(a.font), 크기_px=PX, 이름=' '.join(f.getname())),
        정의=dict(e=E, 몸통_높이='x높이_em', 발음기호_글자=MARK_CHARS, 어센더_글자=ASC_CHARS, x높이_px_격자=list(XH_GRID),
                뜬_덩어리='1000px 마스크 (알파 > 0) 8-연결 덩어리 가운데 아래끝이 x높이선 위 경계보다 위인 것',
                판정_규칙='유도식 값 = 현재 값이면 유지, 다르면 바꿀 값. 식 꼴 변경 행은 상수를 그 식으로 바꾼다'),
        실측=dict(x높이_em=xh_em, 어센더_em=asc, 발음기호=mk),
        상수=rows,
        provenance=MC.provenance('eval/constants_definitions.py', len(rows)))
    json.dump(out, open(a.out, 'w'), ensure_ascii=False, indent=1)
    for r in rows:
        print(r['이름'], '| 현재', r['현재'], '| 계산값', json.dumps(r['계산값'], ensure_ascii=False), '|', r['판정'])


if __name__ == '__main__':
    main()
