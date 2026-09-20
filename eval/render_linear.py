"""(b) 빛 기준 렌더 — 합성 판을 선형광에서 섞어 그린다.

docs/constants_preregister.json 수정 1 의 3 · 수정 12 의 3. scratchpad 의 탐색 코드 (mix/verify_synth.py
render_linear) 를 그대로 옮긴 것이다. 판정에는 쓰지 않는다 — (a) 지금 렌더와 나란히 적는 강건성 조건이다.

    (a) 지금 렌더 : 4배 마스터에 인코딩값으로 그리고 LANCZOS 로 줄인다 (eval/synth_gen.render)
    (b) 이 렌더   : 4배 마스터 덮임(알파)을 선형광에서 바탕 · 잉크와 섞고, 선형광에서 줄인 뒤 sRGB 로 되돌린다

    python eval/synth_gen.py --out ~/.typo-mcp/synth_b --manifest docs/synth_b_manifest.json \
        --seeds 8001 … 8050 --render linear
"""
import numpy as np
from PIL import Image, ImageDraw


def lin(v):
    """0~255 인코딩값 → 선형광 0~1 (IEC 61966-2-1)."""
    c = np.asarray(v, dtype=float) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def enc(c):
    """선형광 0~1 → 0~255 인코딩값."""
    c = np.clip(np.asarray(c, dtype=float), 0.0, 1.0)
    s = np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)
    return s * 255.0


def render(lay, cond, W800, H800, polarity):
    """synth_gen.render 와 같은 자리에 쓴다 — (이미지, 배율) 을 돌려준다."""
    pol = polarity[cond['polarity']]
    Wm, Hm = lay['canvas']
    mask = Image.new('L', (Wm, Hm), 0)
    d = ImageDraw.Draw(mask)
    for b in lay['blocks']:
        for l in b['lines']:
            d.text((l['x'], l['baseline']), l['text'], font=b['font'], fill=255, anchor='ls')
    cov = np.asarray(mask).astype(float) / 255.0          # 덮임 (알파)
    s = cond['resolution'] / H800
    size = (int(round(W800 * s)), int(round(H800 * s)))
    chans = []
    for c in range(3):
        bl, il = float(lin(pol['ground'][c])), float(lin(pol['ink'][c]))
        m = (bl + (il - bl) * cov).astype(np.float32)     # 선형광에서 섞는다
        r = np.asarray(Image.fromarray(m, 'F').resize(size, Image.Resampling.LANCZOS)).astype(float)
        chans.append(np.clip(np.round(enc(r)), 0, 255).astype(np.uint8))
    return Image.fromarray(np.stack(chans, -1), 'RGB'), s
