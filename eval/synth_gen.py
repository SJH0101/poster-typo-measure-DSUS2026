"""합성 포스터 생성기 — 정답을 알고 그린다.

사전등록 docs/synth_preregister.json (af0b145, 수정 1) 을 그대로 옮긴 것이다. 수준 · 템플릿 ·
좌표 약속은 거기 있고, 여기서 새로 정한 것은 없다. 결과를 보고 이 파일의 상수를
바꾸지 않는다.

docs/constants_preregister.json 수정 2 (48bdfa0) — 같은 열 블록을 위에서부터 쌓고(앞 블록 마지막
베이스라인 + 2g 이상, 13셀 전부), 무작위 간격에 1.75 × x높이 하한을 두고, 겹침 검사를 기본으로 켠다.

    python eval/synth_gen.py --out ~/.typo-mcp/synth --manifest docs/synth_manifest.json
    python eval/synth_gen.py --out /tmp/x --cells base xh_18 --seeds 1 2     # 일부만

generate.py · render.py 와 다른 점 하나 — 장마다 정답 JSON 을 함께 쓴다. 낱말
주머니는 render.py 에서 import 한다 (옮기지 않는다).

좌표 약속. 마스터(800px 판의 4배)에 정수 좌표로 그리고 LANCZOS 로 줄인다. 정답은
출력 이미지의 연속 좌표다. 행 r 은 [r, r+1) 을 덮으므로 베이스라인 y=b 이면 평평한
글자 바닥이 행 b−1 에서 끝나고, measure/ink.py baseline() (마지막 잉크 행 + 1) 의
기대값은 b 자체다.
"""
import argparse
import colorsys
import datetime
import hashlib
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont, features

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import render as R  # noqa: E402  낱말 주머니

W800, H800 = 566, 800          # F4. 실물 283장 폭 중앙 566 · 높이 800
MASTER = 4                     # 마스터 배율
XH_BASE = 8                    # 기준 x높이 (800px 판 px)
LEAD_RATIO = 2.0               # g = 행간 = 2.0 × x높이
TITLE_MULT = 2.0               # 표제 x높이 = 2 × 본문
MARGIN = 0.04                  # 좌우 여백 / W
GUTTER = 0.035                 # 단 사이 틈 / W
FILL = (0.60, 1.00)            # 줄이 단 폭을 채우는 비율
INDEP_RATIOS = (1.75, 2.0, 2.36)   # 블록별 독립: 행간 / x높이 (실물 25 · 50 · 75%)
RANDOM_JITTER = (0.70, 1.30)       # 무작위: 간격 × U
RANDOM_MIN_XH = 1.75               # 무작위 간격 하한 / 블록 x높이 = INDEP_RATIOS 최솟값 (constants_preregister 수정 2)
BLOCK_GAP_G = 2.0                  # 같은 열 앞 블록 마지막 베이스라인 → 다음 블록 첫 베이스라인 최소 (g 단위).
                                   # base 셀 E→D 간격 (constants_preregister 수정 2)
BOTTOM_PAD = 0.02             # 넘침 판정 — 마지막 디센더가 H·(1−0.02) 를 넘으면 다시 뽑는다

# (id, 역할, 열, 첫 베이스라인 g, 줄 수, x높이 배수, 행간 g)
TEMPLATE = [
    ('T', 'title', 'span', 3, 2, TITLE_MULT, 2),
    ('A', 'body', 0, 9, 5, 1.0, 1),
    ('C', 'body', 0, 16, 3, 1.0, 1),
    ('B', 'body', 1, 6, 8, 1.0, 1),
    ('E', 'single', 1, 14, 1, 1.0, 1),
    ('D', 'body', 1, 16, 4, 1.0, 1),
]

FONTS = {
    'helvetica': dict(file='/System/Library/Fonts/Helvetica.ttc', index=0),   # 서체 1종 (사전등록 수정 1)
}

def _hsv(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h / 360.0, s, v)
    return (int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))

POLARITY = {
    'white_black': dict(ground=(255, 255, 255), ink=(0, 0, 0)),
    'colored_black': dict(ground=_hsv(40, 0.35, 0.72), ink=(0, 0, 0)),
    'dark_light': dict(ground=(25, 25, 28), ink=(245, 245, 242)),
}

BASE = dict(resolution=800, polarity='white_black', xh_px_at_800=XH_BASE, jpeg_q=72,
            rule='shared_grid', font='helvetica')

CELLS = {
    'base': {},
    'res_1600': dict(resolution=1600), 'res_400': dict(resolution=400),
    'pol_colored': dict(polarity='colored_black'), 'pol_dark': dict(polarity='dark_light'),
    'xh_3': dict(xh_px_at_800=3), 'xh_5': dict(xh_px_at_800=5),
    'xh_12': dict(xh_px_at_800=12), 'xh_18': dict(xh_px_at_800=18),
    'jpeg_95': dict(jpeg_q=95), 'jpeg_45': dict(jpeg_q=45),
    'rule_independent': dict(rule='independent'), 'rule_random': dict(rule='random'),
}

# 본문 블록 역할마다 문구를 짓는 법. 주머니는 render.py 의 것
def _phrase(rnd, kind):
    c = lambda pool: pool[rnd.randint(len(pool))]
    if kind == 0: return c(R.SUB)
    if kind == 1: return c(R.VENUE)
    if kind == 2: return c(R.WHEN) + '  ' + c(R.HOUR)
    if kind == 3: return c(R.COMPOSER) + '  ' + c(R.WORK)
    if kind == 4: return c(R.ROLE) + '  ' + c(R.PERSON)
    return c(R.SALE)


def _condition(cell):
    c = dict(BASE); c.update(CELLS[cell]); return c


def _font_info(name):
    f = FONTS[name]
    probe = ImageFont.truetype(f['file'], 1000, index=f['index'])
    cap = -probe.getbbox('H', anchor='ls')[1]
    xh = -probe.getbbox('x', anchor='ls')[1]
    return dict(file=f['file'], index=f['index'], name=' '.join(probe.getname()),
                sha256=hashlib.sha256(open(f['file'], 'rb').read()).hexdigest(),
                cap_over_em=cap / 1000.0, xh_over_em=xh / 1000.0)


def _lum(rgb):
    def ch(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _gray(rgb):
    return int(round(0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]))   # PIL 'L'


def contrast(ground, ink):
    lg, li = _lum(ground), _lum(ink)
    hi, lo = max(lg, li), min(lg, li)
    return dict(ground_rgb=list(ground), ink_rgb=list(ink),
                ground_luminance=round(lg, 4), ink_luminance=round(li, 4),
                wcag_ratio=round((hi + 0.05) / (lo + 0.05), 2),
                michelson=round((hi - lo) / (hi + lo), 4) if hi + lo else 0.0,
                gray_delta=abs(_gray(ground) - _gray(ink)))


def fill_line(rnd, kind, font, width):
    """문구를 이어 붙여 폭의 60~100% 를 채운다. 넘치면 마지막 문구를 뺀다. 활자는 안 줄인다.

    문구 하나도 안 들어가는 폭(x높이 18 의 단)에서는 그 역할 주머니에서 들어가는
    문구를 seed 순서로 찾고, 그래도 없으면 들어가는 가장 넓은 것을 쓴다. 한 글자로
    줄이지 않는다 — 한 글자 줄은 글줄이 아니다."""
    best = None
    for _ in range(40):
        parts = []
        while len(parts) < 6:
            cand = parts + [_phrase(rnd, kind)]
            if font.getlength('  '.join(cand)) <= width:
                parts = cand
            else:
                break
        if parts:
            t = '  '.join(parts)
            if font.getlength(t) >= FILL[0] * width:
                return t
            if best is None or font.getlength(t) > font.getlength(best):
                best = t
    if best is not None:
        return best
    # (폭, 문자열) 순 — 폭이 같은 낱말의 순서가 해시 순서를 따르지 않게 (constants_preregister 수정 3)
    pool = sorted({w for P in (R.HOUR, R.SUB, R.VENUE, R.COMPOSER, R.SALE) for w in P}, key=lambda w: (font.getlength(w), w))
    fit = [w for w in pool if font.getlength(w) <= width]
    return fit[rnd.randint(len(fit))] if fit else pool[0]


def title_line(rnd, font, width):
    order = rnd.permutation(len(R.TITLE))
    for i in order:
        if font.getlength(R.TITLE[i]) <= width:
            return R.TITLE[i]
    return R.TITLE[order[0]]


def _cols(col):
    """블록이 걸친 열. 두 열에 걸친 블록(span · column None)은 두 열 모두."""
    return (0, 1) if col in ('span', None) else (col,)


def _place(rule, n, u0, lead, size, xh_b, col, phase, g, Hm, rnd, col_last):
    """한 블록의 정수 베이스라인 — constants_preregister 수정 2.

    첫 베이스라인 = max(u0·g + phase, 같은 열 앞 블록 마지막 베이스라인 + BLOCK_GAP_G·g). 13셀 전부.
    shared_grid 는 phase 0 이고 앞 블록 마지막 베이스라인도 g 의 정수배라 격자 정수배가 유지된다.
    무작위 간격은 RANDOM_MIN_XH × 블록 x높이 아래로 내려가지 않는다. 넘치면 기존처럼 50번까지 다시 뽑는다.
    col_last 에 이 블록이 걸친 열의 마지막 베이스라인을 적는다."""
    ps = [col_last[c] for c in _cols(col) if col_last.get(c) is not None]
    prev = max(ps) if ps else None
    for _try in range(50):
        gaps = [lead] * (n - 1)
        if rule == 'random':
            gaps = [max(lead * rnd.uniform(*RANDOM_JITTER), RANDOM_MIN_XH * xh_b) for _ in gaps]
        first = u0 * g + phase
        if prev is not None:
            first = max(first, prev + BLOCK_GAP_G * g)
        bases = [first]
        for gp in gaps:
            bases.append(bases[-1] + gp)
        if bases[-1] + 0.25 * size <= Hm * (1 - BOTTOM_PAD):
            break
    bases = [int(round(b)) for b in bases]
    for c in _cols(col):
        col_last[c] = bases[-1]
    return bases


def layout(cond, seed, fonts):
    """한 장의 배치 (마스터 좌표, 정수 베이스라인). 같은 seed → 같은 배치."""
    rnd = np.random.RandomState(seed)
    xh = cond['xh_px_at_800'] * MASTER
    g = LEAD_RATIO * xh
    Wm, Hm = W800 * MASTER, H800 * MASTER
    mL = MARGIN * Wm; gut = GUTTER * Wm
    colw = (Wm - 2 * mL - gut) / 2
    fi = fonts[cond['font']]
    rule = cond['rule']
    blocks = []
    col_last = {}
    for bid, role, col, u0, n, mult, lead_u in TEMPLATE:
        xh_b = xh * mult
        size = xh_b / fi['xh_over_em']
        font = ImageFont.truetype(fi['file'], size, index=fi['index'])
        x = mL if col in ('span', 0) else mL + colw + gut
        width = (Wm - 2 * mL) if col == 'span' else colw
        lead = lead_u * g
        phase = 0.0
        if rule in ('independent', 'random'):
            phase = rnd.uniform(0, g)
            if n >= 3:
                lead = INDEP_RATIOS[rnd.randint(len(INDEP_RATIOS))] * xh
        bases = _place(rule, n, u0, lead, size, xh_b, col, phase, g, Hm, rnd, col_last)
        kind0 = rnd.randint(6)
        lines = []
        for i, b in enumerate(bases):
            if role == 'title':
                text = title_line(rnd, font, width)
            else:
                text = fill_line(rnd, (kind0 + i) % 6, font, width)
            bb = font.getbbox(text, anchor='ls')
            lines.append(dict(text=text, x=int(round(x)), baseline=b, fill=round(font.getlength(text) / width, 3),
                              ink=[int(round(x)) + bb[0], b + bb[1], int(round(x)) + bb[2], b + bb[3]],
                              has_ascender=any(ch in 'bdfhklt0123456789ßÄÖÜ' or ch.isupper() for ch in text),
                              has_descender=any(ch in 'gjpqy,;' for ch in text),
                              has_mark=any(ch in 'ijäöü' for ch in text)))
        blocks.append(dict(id=bid, role=role, column=(None if col == 'span' else col), n=n,
                           font_px=size, xh_px=xh_b, cap_px=size * fi['cap_over_em'],
                           lead_px=(float(np.median(np.diff(bases))) if n > 1 else None),
                           gaps_px=[float(d) for d in np.diff(bases)],
                           on_grid=(rule == 'shared_grid'), font=font, lines=lines,
                           _geo=dict(u0=u0, lead=lead, size=size, width=width)))   # 겹침 검사용 (참값에 안 쓴다)
    grid = dict(g_px=g, phi_px=0.0) if rule == 'shared_grid' else None
    return dict(canvas=[Wm, Hm], g=g, grid=grid, blocks=blocks)


# ── 겹침 검사 (사전등록 수정 2, 2026-09-15) ────────────────────────────
# 기존 390장은 겹침 검사 없이 만들었다. constants_preregister 수정 2 부터 기본으로 켠다 (--no-overlap-check 로 끔).
# 판정은 마스터에서 줄마다 따로 그린 글자 마스크(알파 > 0)의 교집합. 상자 겹침과 최소 거리는 기록만 한다.
# 조작변인 수준(행간 · 간격)과 템플릿은 바꾸지 않는다.
TEXT_TRIES = 50     # 한 회차에 문구를 다시 뽑는 최대 번수 (사전등록 수정 2)
GEO_ROUNDS = 20     # 위상 · 간격을 다시 뽑는 최대 회차 (블록별 독립 · 무작위만)


def _line(text, x, b, font, width):
    """layout() 의 줄 사전과 같은 모양."""
    bb = font.getbbox(text, anchor='ls')
    return dict(text=text, x=x, baseline=b, fill=round(font.getlength(text) / width, 3),
                ink=[x + bb[0], b + bb[1], x + bb[2], b + bb[3]],
                has_ascender=any(ch in 'bdfhklt0123456789ßÄÖÜ' or ch.isupper() for ch in text),
                has_descender=any(ch in 'gjpqy,;' for ch in text),
                has_mark=any(ch in 'ijäöü' for ch in text))


def _mask(line, font):
    x0, y0, x1, y1 = [int(v) for v in line['ink']]
    im = Image.new('L', (x1 - x0 + 4, y1 - y0 + 4), 0)
    ImageDraw.Draw(im).text((line['x'] - x0 + 2, line['baseline'] - y0 + 2), line['text'], font=font, fill=255, anchor='ls')
    return np.asarray(im) > 0, (x0 - 2, y0 - 2)


def stroke_overlaps(lay):
    """([(블록, 줄, 블록, 줄, 겹친 픽셀)], 상자 겹침 쌍 수) — 마스터 좌표."""
    L = [(b['id'], i, l, b['font']) for b in lay['blocks'] for i, l in enumerate(b['lines'])]
    masks = {}
    out, nbox = [], 0
    for a in range(len(L)):
        for c in range(a + 1, len(L)):
            ia, la = L[a][2]['ink'], L[c][2]['ink']
            if not (min(ia[2], la[2]) > max(ia[0], la[0]) and min(ia[3], la[3]) > max(ia[1], la[1])):
                continue
            nbox += 1
            for j in (a, c):
                if j not in masks:
                    masks[j] = _mask(L[j][2], L[j][3])
            (ma, (ax, ay)), (mc, (cx, cy)) = masks[a], masks[c]
            x0, y0 = max(ax, cx), max(ay, cy)
            x1, y1 = min(ax + ma.shape[1], cx + mc.shape[1]), min(ay + ma.shape[0], cy + mc.shape[0])
            if x1 <= x0 or y1 <= y0:
                continue
            n = int((ma[y0 - ay:y1 - ay, x0 - ax:x1 - ax] & mc[y0 - cy:y1 - cy, x0 - cx:x1 - cx]).sum())
            if n > 0:
                out.append((L[a][0], L[a][1], L[c][0], L[c][1], n))
    return out, nbox


def _refill(lay, ids, rnd):
    """겹친 쌍에 든 블록의 문구만 다시 뽑는다. 줄 수 · 베이스라인 · 가로 자리 · 글자 크기는 그대로."""
    for b in lay['blocks']:
        if b['id'] not in ids:
            continue
        w = b['_geo']['width']
        kind0 = rnd.randint(6)
        b['lines'] = [_line(title_line(rnd, b['font'], w) if b['role'] == 'title'
                            else fill_line(rnd, (kind0 + i) % 6, b['font'], w), l['x'], l['baseline'], b['font'], w)
                      for i, l in enumerate(b['lines'])]


def _regeo(lay, cond, rnd):
    """위상을 [0, g) 에서 (무작위는 간격 ×U 도) 다시 뽑는다. 블록 행간 수준은 원래 값 그대로.
    쌓기 · 간격 하한은 layout() 과 같은 _place() (constants_preregister 수정 2)."""
    g, Hm = lay['g'], lay['canvas'][1]
    col_last = {}
    for b in lay['blocks']:
        geo, n = b['_geo'], b['n']
        phase = rnd.uniform(0, g)
        bases = _place(cond['rule'], n, geo['u0'], geo['lead'], geo['size'], b['xh_px'], b['column'], phase, g, Hm, rnd, col_last)
        b['lines'] = [_line(l['text'], l['x'], nb, b['font'], geo['width']) for l, nb in zip(b['lines'], bases)]
        b['lead_px'] = float(np.median(np.diff(bases))) if n > 1 else None
        b['gaps_px'] = [float(d) for d in np.diff(bases)]


_EXT = {}


def _min_distance(lay, fi):
    """판에 쓰인 글자의 가장 깊은 아래끝 + 가장 높은 윗끝 (x높이 단위) · 행간이 그보다 짧은 블록. 기록만 한다."""
    cs = {ch for b in lay['blocks'] for l in b['lines'] for ch in l['text'] if ch.strip()}
    key = (fi['file'], fi['index'])
    if key not in _EXT:
        _EXT[key] = (ImageFont.truetype(fi['file'], 1000, index=fi['index']), {})
    probe, memo = _EXT[key]
    for ch in sorted(cs - set(memo)):   # 정렬 순회 (constants_preregister 수정 3 — 결과는 최댓값이라 같다)
        bb = probe.getbbox(ch, anchor='ls'); memo[ch] = (-bb[1] / 1000.0, bb[3] / 1000.0)
    asc = max(memo[ch][0] for ch in cs); desc = max(memo[ch][1] for ch in cs)
    short = [b['id'] for b in lay['blocks'] if b['n'] > 1 and b['lead_px'] is not None
             and min(b['gaps_px']) < (asc + desc) * b['font_px']]
    return round((asc + desc) / fi['xh_over_em'], 4), short


def layout_checked(cond, seed, fonts):
    """layout() → 획 겹침이 있으면 문구 → (독립 · 무작위만) 위상 · 간격 순으로 다시 뽑는다."""
    lay = layout(cond, seed, fonts)
    pairs, nbox = stroke_overlaps(lay)
    rec = dict(원래_획_겹침_쌍=len(pairs), 문구_다시_뽑음=0, 위상간격_다시_뽑음=0)
    rnd_round = 0
    while pairs:
        t = 0
        while pairs and t < TEXT_TRIES:
            t += 1
            rec['문구_다시_뽑음'] += 1
            _refill(lay, {p[0] for p in pairs} | {p[2] for p in pairs}, np.random.RandomState([seed, 1, rnd_round, t]))
            pairs, nbox = stroke_overlaps(lay)
        if not pairs or cond['rule'] == 'shared_grid' or rnd_round >= GEO_ROUNDS:
            break
        rnd_round += 1
        rec['위상간격_다시_뽑음'] += 1
        _regeo(lay, cond, np.random.RandomState([seed, 2, rnd_round]))
        pairs, nbox = stroke_overlaps(lay)
    dmin, short = _min_distance(lay, fonts[cond['font']])
    rec.update(최종_획_겹침_쌍=len(pairs), 상자_겹침_쌍=nbox, 최소_거리_x높이=dmin, 행간이_최소_거리보다_짧은_블록=short,
               기준='사전등록 수정 2 — 획 기준(마스터 글자 마스크 교집합). 상자 겹침 · 최소 거리는 기록만')
    return lay, rec


def render(lay, cond):
    pol = POLARITY[cond['polarity']]
    im = Image.new('RGB', tuple(lay['canvas']), pol['ground'])
    d = ImageDraw.Draw(im)
    for b in lay['blocks']:
        for l in b['lines']:
            d.text((l['x'], l['baseline']), l['text'], font=b['font'], fill=pol['ink'], anchor='ls')
    s = cond['resolution'] / H800
    out = im.resize((int(round(W800 * s)), int(round(H800 * s))), Image.Resampling.LANCZOS)
    return out, s


def truth(lay, cond, cell, seed, s, fi, prov):
    k = MASTER / s               # 마스터 → 출력 px
    pol = POLARITY[cond['polarity']]
    blocks = []
    for b in lay['blocks']:
        ls = []
        for l in b['lines']:
            x1, y1, x2, y2 = l['ink']
            ls.append(dict(text=l['text'], fill=l['fill'], baseline_y=l['baseline'] / k,
                           cap_y=(l['baseline'] - b['cap_px']) / k,
                           xtop_y=(l['baseline'] - b['xh_px']) / k,
                           desc_y=y2 / k if l['has_descender'] else None,
                           x1=x1 / k, x2=x2 / k, ink_box=[x1 / k, y1 / k, x2 / k, y2 / k],
                           has_ascender=l['has_ascender'], has_descender=l['has_descender'],
                           has_mark=l['has_mark']))
        xs1 = min(l['ink'][0] for l in b['lines']); ys1 = min(l['ink'][1] for l in b['lines'])
        xs2 = max(l['ink'][2] for l in b['lines']); ys2 = max(l['ink'][3] for l in b['lines'])
        blocks.append(dict(id=b['id'], role=b['role'], column=b['column'], n=b['n'],
                           font_px=b['font_px'] / k, xh_px=b['xh_px'] / k, cap_px=b['cap_px'] / k,
                           lead_px=(None if b['lead_px'] is None else b['lead_px'] / k),
                           gaps_px=[x / k for x in b['gaps_px']], on_grid=b['on_grid'],
                           ink_box=[xs1 / k, ys1 / k, xs2 / k, ys2 / k], lines=ls))
    grid = None if lay['grid'] is None else dict(g_px=lay['grid']['g_px'] / k, phi_px=0.0)
    return dict(cell=cell, seed=seed, condition=cond,
                canvas=[int(round(W800 * s)), int(round(H800 * s))], scale_from_800=s,
                master_scale=MASTER,
                font={k_: v for k_, v in fi.items()},
                contrast=contrast(pol['ground'], pol['ink']),
                grid=grid, grid_note='격자 공유가 아니면 null. 위상 0 = 베이스라인이 g 의 정수배',
                template=[dict(id=t[0], role=t[1], column=t[2], first_unit=t[3], n=t[4],
                               xh_mult=t[5], lead_units=t[6]) for t in TEMPLATE],
                coord_note='연속 좌표. 행 r 은 [r, r+1). 베이스라인 b 이면 평평한 글자 바닥이 행 b−1 에서 끝난다',
                blocks=blocks, provenance=prov)


def _sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser(description='합성 포스터와 정답을 만든다')
    ap.add_argument('--out', required=True, help='이미지 · 정답 폴더 (저장소 밖, 예 ~/.typo-mcp/synth)')
    ap.add_argument('--manifest', help='sha256 목록 JSON (예 docs/synth_manifest.json)')
    ap.add_argument('--cells', nargs='*', default=list(CELLS), choices=list(CELLS))
    ap.add_argument('--seeds', nargs='*', type=int, default=list(range(1, 31)))
    ap.add_argument('--prereg', default='docs/synth_preregister.json')
    ap.add_argument('--font-helvetica', default=FONTS['helvetica']['file'])
    ap.add_argument('--no-overlap-check', dest='overlap_check', action='store_false',
                    help='겹침 검사를 끈다. 기본은 켬 — 획 겹침이 있으면 다시 뽑고 끝내 남으면 멈춘다 '
                         '(synth_preregister 수정 2, 기본 켬은 constants_preregister 수정 2)')
    ap.add_argument('--render', default='srgb', choices=('srgb', 'linear'),
                    help='linear = (b) 빛 기준 렌더 (eval/render_linear.py, constants_preregister 수정 12 의 3). 판정에 쓰지 않는다')
    ap.add_argument('--merge-manifest', action='store_true',
                    help='manifest 를 덮어쓰지 않고 이번에 만든 (cell, seed) 항목만 바꾼다')
    a = ap.parse_args(argv)
    FONTS['helvetica']['file'] = a.font_helvetica
    out = os.path.expanduser(a.out)
    fonts = {k: _font_info(k) for k in FONTS}
    try:
        commit = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], cwd=ROOT).decode().strip()
    except Exception:
        commit = None
    prov = dict(generator='eval/synth_gen.py', commit=commit, prereg=a.prereg,
                prereg_sha256=(_sha(os.path.join(ROOT, a.prereg)) if os.path.exists(os.path.join(ROOT, a.prereg)) else None),
                render=a.render,
                pillow=Image.__version__, freetype=features.version('freetype2'),
                date=datetime.date.today().isoformat(), synthetic=True)
    items = []
    for cell in a.cells:
        cond = _condition(cell)
        os.makedirs(os.path.join(out, cell), exist_ok=True)
        for seed in a.seeds:
            rec = None
            if a.overlap_check:
                lay, rec = layout_checked(cond, seed, fonts)
                if rec['최종_획_겹침_쌍']:
                    sys.exit(f'{cell}/{seed:03d}: 다시 뽑아도 획 겹침 {rec["최종_획_겹침_쌍"]}쌍이 남는다 — 멈춘다')
                rec['생성기_sha256'] = _sha(os.path.abspath(__file__))   # 커밋 전 작업 트리로 만들 수 있어 파일 자체를 남긴다
            else:
                lay = layout(cond, seed, fonts)
            if a.render == 'linear':
                import render_linear as RL
                im, s = RL.render(lay, cond, W800, H800, POLARITY)
            else:
                im, s = render(lay, cond)
            jp = os.path.join(out, cell, f'{seed:03d}.jpg')
            im.save(jp, 'JPEG', quality=cond['jpeg_q'], subsampling=0, optimize=False, progressive=False)
            t = truth(lay, cond, cell, seed, s, fonts[cond['font']], prov)
            if rec is not None:
                t['겹침_재생성'] = rec
            tp = jp[:-4] + '.json'
            json.dump(t, open(tp, 'w'), ensure_ascii=False, indent=1)
            items.append(dict(cell=cell, seed=seed, image=os.path.relpath(jp, out),
                              image_sha256=_sha(jp), truth_sha256=_sha(tp),
                              n_lines=sum(b['n'] for b in t['blocks'])))
        print(f'{cell:18s} {len(a.seeds)}장  x높이 {cond["xh_px_at_800"]} · {cond["resolution"]}px · '
              f'{cond["polarity"]} · q{cond["jpeg_q"]} · {cond["rule"]} · {cond["font"]}', flush=True)
    if a.manifest and a.merge_manifest:
        mp = os.path.join(ROOT, a.manifest)
        M = json.load(open(mp))
        new = {(it['cell'], it['seed']): it for it in items}
        M['items'] = [new.get((it['cell'], it['seed']), it) for it in M['items']]
        missing = set(new) - {(it['cell'], it['seed']) for it in M['items']}
        if missing:
            sys.exit(f'manifest 에 없는 항목: {sorted(missing)}')
        M.setdefault('재생성', []).append(dict(provenance=prov, 항목=sorted(f'{c}/{s_:03d}' for c, s_ in new),
                                           까닭='사전등록 수정 2 — 획 기준 겹침이 있는 판만'))
        json.dump(M, open(mp, 'w'), ensure_ascii=False, indent=1)
    elif a.manifest:
        json.dump(dict(what='합성 포스터 manifest — 이미지 · 정답의 sha256. 생성기는 seed 에 결정론적이다',
                       out=a.out, cells={c: _condition(c) for c in a.cells}, seeds=a.seeds,
                       fonts=fonts, provenance=prov, items=items),
                  open(os.path.join(ROOT, a.manifest), 'w'), ensure_ascii=False, indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main())
