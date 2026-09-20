"""Surya 가 준 «줄» 을 우리 «블록» 으로 묶는다.

옛 경로(baseline/detect.py)는 영역 전체를 잉크 문턱으로 훑어 줄을 찾았다.
그래서 사진·색면·도형 위에서도 줄이 나왔다 — 사람이 라벨한 200개로 재보니
상자의 37% 가 글자가 아니었고, 작가별로 브로크만 10% · 루더 53% 로
다섯 배 차이가 났다. 작가 비교가 그 차이를 싣고 있었다.

Surya 는 사진·도형 위에 상자를 치지 않는다. 대신 거대 표제를 더러 놓친다.
**두 실패의 성격이 다르다** — 옛것은 조용히 틀린 값을 내고 Surya 는 빠진다.
빠지는 것은 셀 수 있고 기록할 수 있다.

Surya 는 «줄» 단위라 우리 지표(블록수·행간·단)를 내려면 묶어야 한다.
묶는 규칙은 셋이고, 전부 옛 detect.py 가 쓰던 것과 같은 생각이다.

    크기 계층   높이가 서로 이 배수 안에 들어야 한다 (제목과 본문을 안 섞는다)
    가로 겹침   x 범위가 겹쳐야 한다 (다른 단을 안 붙인다)
    세로 간격   행간이 제 높이의 이 배 안이어야 한다 (떨어진 덩어리를 안 붙인다)

묶은 상자는 measure/ground.py 로 넘긴다 — 짚어준 상자를 재는 그 경로다.
찾기와 재기가 갈라진다.
"""
import numpy as np

# 합성 스윕 판정 (docs/constants_preregister.json 순서 4 · 병행, 결과 docs/constants_sweep4.json · fb1d09a):
# 상한 2.55 → 3.4 는 사전등록 수정 15 (동결 해제) — 재현율 평평 구간 안 과병합 + 과분할 최소.
# H_RATIO 두 끝과 Y_GAP 상한은 조정 세트에서 «바꿀 값», X_OVER · MIN_AREA · Y_GAP 하한은 «유지 (효과 없음)».
H_RATIO = (0.675, 3.4)   # 높이가 이 배수 안이면 같은 크기 계층 (옛 0.60 · 1.70 → 0.675 · 2.55)
X_OVER = 0.15            # 좁은 쪽 폭의 이 비율 넘게 겹쳐야 한 단
Y_GAP = (-0.40, 0.8)     # 세로 틈이 제 높이의 이 배수 안이면 잇는다 (상한 옛 1.60).
                         # 음수는 겹침을 허용한다 — 큰 글자는 상자가 서로 물린다.
MIN_AREA = 200           # 이보다 작은 상자는 부스러기


def _norm(b):
    x1, y1, x2, y2 = b
    return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))


def group(lines):
    """줄상자 목록 → 블록 상자 목록. 각 블록은 (x1,y1,x2,y2,줄수)."""
    L = [_norm(b) for b in lines]
    L = [b for b in L if (b[2] - b[0]) * (b[3] - b[1]) >= MIN_AREA]
    L.sort(key=lambda b: (b[1], b[0]))
    used = [False] * len(L)
    out = []
    for i, a in enumerate(L):
        if used[i]:
            continue
        used[i] = True
        g = [a]
        moved = True
        while moved:
            moved = False
            gx1 = min(b[0] for b in g); gx2 = max(b[2] for b in g)
            gy2 = max(b[3] for b in g)
            gh = float(np.median([b[3] - b[1] for b in g]))
            for j, b in enumerate(L):
                if used[j]:
                    continue
                bh = b[3] - b[1]
                if not (H_RATIO[0] <= bh / max(gh, 1) <= H_RATIO[1]):
                    continue
                if min(gx2, b[2]) - max(gx1, b[0]) <= X_OVER * min(gx2 - gx1, b[2] - b[0]):
                    continue
                if not (Y_GAP[0] * gh <= b[1] - gy2 <= Y_GAP[1] * gh):
                    continue
                g.append(b); used[j] = True; moved = True
        out.append((min(b[0] for b in g), min(b[1] for b in g),
                    max(b[2] for b in g), max(b[3] for b in g), len(g)))
    return out


def boxes_norm(lines, size):
    """묶은 블록을 0~1 좌표로. measure.ground 가 먹는 꼴."""
    W, H = size
    return [[b[0] / W, b[1] / H, b[2] / W, b[3] / H] for b in group(lines)]



SPLIT_LINE_GAP = 0.75   # 선택 처리 split_wide_lines 의 보조 문턱 — 줄 상자 안 가로 빈틈 ÷ 그 상자 높이.
                        # 위아래 행을 견줄 수 없을 때만 쓴다 (주 규칙은 아래 «세로 빈 통로»).
                        # 근거 (2026-09-19 지시로 받은 값): 두 단을 덮는 상자 중앙 0.82 · 최소 0.42,
                        # 한 단만 덮는 정상 상자 중앙 0.15 · p95 0.71. 0.75 는 정상 p95 바로 위다.
                        # 참고 — 이 함수의 빈틈 정의로 브로크만 라벨 50장에서 잰 값은 이와 다르다:
                        # 두 단 33개 중앙 0.647 · 최소 0.312, 한 단 791개 중앙 0.308 · p95 0.667
                        # (docs/split_lines_explore.json, c5d8502). 두 출처의 정의 차이는 확인하지 않았다.


def _ink_cols(gray, x1, y1, x2, y2):
    """[x1, x2) × [y1, y2) 안에서 잉크가 한 행이라도 있는 열 (bool). 너무 작으면 None."""
    from measure import ink
    H, W = gray.shape
    xi1, yi1 = max(0, int(round(x1))), max(0, int(round(y1)))
    xi2, yi2 = min(W, int(round(x2))), min(H, int(round(y2)))
    if xi2 - xi1 < 4 or yi2 - yi1 < 2:
        return None
    g = ink.polarity(gray[yi1:yi2, xi1:xi2])
    return (g < ink.threshold(g)).any(axis=0)


def _near_rows(L, i, above, k=2):
    """줄 i 와 가로로 겹치는 줄 가운데 위(또는 아래)로 가까운 행 k 개의 (y1, y2). 세로로 반 넘게 겹치는 상자는 한 행."""
    x1, y1, x2, y2 = L[i]
    cy, h = (y1 + y2) / 2, y2 - y1
    cand = []
    for j, l in enumerate(L):
        if j == i or min(l[2], x2) - max(l[0], x1) <= 0:
            continue
        if min(l[3], y2) - max(l[1], y1) > 0.5 * min(h, l[3] - l[1]):
            continue                                         # 같은 행
        if ((l[1] + l[3]) / 2 < cy) == above:
            cand.append(l)
    cand.sort(key=lambda l: abs((l[1] + l[3]) / 2 - cy))
    rows = []
    for l in cand:
        for r in rows:
            if min(l[3], r[1]) - max(l[1], r[0]) > 0.5 * min(l[3] - l[1], r[1] - r[0]):
                r[0], r[1] = min(r[0], l[1]), max(r[1], l[3])
                break
        else:
            if len(rows) >= k:
                break
            rows.append([l[1], l[3]])
    return rows[:k]


def split_wide_lines(gray, lines):
    """선택 처리 (기본 경로에서 부르지 않는다) — 줄 상자 안 가로 빈틈이 단 경계면 그 자리에서 가른다.

    까닭. Surya 줄 상자 하나가 좌우로 나란한 두 단을 함께 덮으면 같은 높이의 두 글줄이 한 띠가 되어
    선이 하나만 나온다. 측정 블록을 가르는 region.split_columns 는 그 뒤 단계라 이 경우를 풀지 못한다.
    detect 직후, 묶기(A · C · VLM) 앞에서 줄 상자를 가르면 세 방식 모두 갈린 줄을 받는다.

    규칙 (새 상수 없음). 빈틈 = 잉크 열(상자 안 행 어느 하나라도 잉크 문턱 아래)의 양 끝을 뺀 안쪽 빈 구간.
      주  «세로 빈 통로» — 같은 x 범위에서 위아래로 가까운 행을 2 개씩까지 본다(그 행이 빈틈 양쪽에 잉크가 있을 때만
          견준다). 자기 행과 견준 행 모두에서 빈 열이 이어지는 폭(빈틈 가운데 열을 지나는 연속 구간)이
          그 줄의 다른 빈틈 가운데 가장 넓은 것보다 넓으면 가른다 (다른 빈틈이 없으면 0 과 견준다).
      보조  견줄 행이 하나도 없으면 폭 기준 — 빈틈 > 상자 높이 × SPLIT_LINE_GAP.
    폭 하나로는 단 경계와 낱말 틈이 갈리지 않았다 (문턱 0.75 로 한 단 상자 26 개가 낱말 사이에서 잘림, 사람 확인).
    브로크만 라벨 50장 탐색 (2026-09-19, 결과로 조정하지 않는다): 통로 폭 ÷ 그 줄 다른 빈틈 중앙값이
    단 경계 자리 중앙 6.25 [p25 5.62], 한 단 상자의 가장 큰 빈틈 중앙 0 [p95 0.93],
    폭 0.75 를 넘긴 낱말 틈 중앙 0 [p95 2.63]. 이 규칙으로 두 단 24/33 · 한 단 19/780 이 갈렸다.

    measure_corpus.measure_items(split_lines=True) 또는 eval/synth_score.py --split-lines 로만 켠다.
    돌려주는 것: (새 줄 목록, 부모 줄 번호 목록). 가를 자리가 없는 줄은 그대로 한 번 나온다.
    """
    L = [_norm(b) for b in lines]
    out, parent = [], []
    for i, (x1, y1, x2, y2) in enumerate(L):
        h = y2 - y1
        cuts = []
        col = _ink_cols(gray, x1, y1, x2, y2) if h > 0 else None
        if col is not None:
            idx = np.where(col)[0]
            gaps = []
            if len(idx) >= 2:
                s = None
                for j in range(int(idx[0]), int(idx[-1]) + 1):
                    if not col[j] and s is None:
                        s = j
                    if col[j] and s is not None:
                        gaps.append((s, j)); s = None
            near = []
            if gaps:
                for above in (True, False):
                    for ry1, ry2 in _near_rows(L, i, above):
                        c2 = _ink_cols(gray, x1, ry1, x2, ry2)
                        if c2 is not None and len(c2) == len(col):
                            near.append(c2)
            for n, (s, e) in enumerate(gaps):
                cmp_ = [c2 for c2 in near if c2[:s].any() and c2[e:].any()]
                if cmp_:
                    blank = ~col
                    for c2 in cmp_:
                        blank = blank & ~c2
                    c = (s + e) // 2
                    run = 0
                    if blank[c]:
                        a = c
                        while a > 0 and blank[a - 1]:
                            a -= 1
                        b = c
                        while b < len(blank) - 1 and blank[b + 1]:
                            b += 1
                        run = b - a + 1
                    other = max([e2 - s2 for m, (s2, e2) in enumerate(gaps) if m != n], default=0)
                    ok = run > other
                else:
                    ok = (e - s) > SPLIT_LINE_GAP * h
                if ok:
                    cuts.append(max(0, int(round(x1))) + (s + e) / 2.0)
        if not cuts:
            out.append([float(x1), float(y1), float(x2), float(y2)]); parent.append(i)
            continue
        left = float(x1)
        for c in cuts + [float(x2)]:
            out.append([left, float(y1), float(c), float(y2)]); parent.append(i)
            left = float(c)
    return out, parent

# ── 단 ──────────────────────────────────────────────────────
# 짚어주는 경로(measure/ground.py)는 「열은 짚어주지 않았으므로 재지 않는다」로
# 설계돼 있어 n_columns 가 None 이다. 그래서 갈아끼운 뒤 단수가 100% 결측이
# 됐다. Surya 줄의 x 범위로 직접 센다 — 줄이 가로로 어디에 걸쳐 있는지만
# 보면 되고, 잉크를 다시 볼 필요가 없다.
COL_GAP = 0.02    # 판 너비의 이 비율보다 넓은 «아무 줄도 안 걸친 세로 띠» 를 단 경계로 본다
COL_MIN = 0.05    # 이보다 좁은 단은 세지 않는다 (쪽번호·여백 글자)
COL_H = 1.6       # 줄 높이가 중앙값의 이 배를 넘으면 표제로 보고 단 세기에서 뺀다.
                  # 판을 가로지르는 표제 한 줄이 폭 전체를 덮어 늘 «1단» 이 나왔다.
                  # 옛 detect.py 가 크기 계층 «안에서» 단을 센 이유가 이것이다.
COL_W = 0.75      # 폭이 판의 이 비율을 넘는 줄도 뺀다 (가로지르는 줄)


def columns(lines, W):
    """본문 크기 줄들의 x 범위만 보고 단 수를 센다."""
    L = [_norm(b) for b in lines]
    if not L:
        return 0
    h = np.median([b[3] - b[1] for b in L])
    body = [b for b in L
            if (b[3] - b[1]) <= COL_H * h and (b[2] - b[0]) <= COL_W * W]
    L = body or L
    cov = np.zeros(int(W) + 1, bool)
    for x1, _y1, x2, _y2 in L:
        cov[max(0, int(x1)):min(int(W), int(x2)) + 1] = True
    runs, i, n = [], 0, len(cov)
    while i < n:
        if cov[i]:
            j = i
            while j < n and cov[j]:
                j += 1
            runs.append((i, j)); i = j
        else:
            i += 1
    if not runs:
        return 0
    merged = [list(runs[0])]
    for a, b in runs[1:]:
        if a - merged[-1][1] <= COL_GAP * W:
            merged[-1][1] = b
        else:
            merged.append([a, b])
    return sum(1 for a, b in merged if (b - a) >= COL_MIN * W)


# ── 재귀용 «한 번만 가르기» ────────────────────────────────────
# group() 은 평평한 블록 목록을 만들려고 쓴다 — 크기·겹침·간격을 한꺼번에 보고
# 최종 덩어리까지 붙인다. 재귀에는 안 맞는다. 빽빽한 일정표에서 84줄이 한
# 덩어리가 되고, 자식이 하나면 멈추는 규칙과 물려 트리가 2마디에서 끝났다
# (Opernhaus 1966: surya 84줄 → 트리 2마디).
#
# 재귀는 한 단계에 «한 번만» 갈라야 한다. 나머지는 아래에서 갈린다.
# 무엇으로 가르나 — 가장 뚜렷한 틈 하나다. 셋 중 가장 뚜렷한 것을 고른다.
#
#     크기      크기 계층 사이의 가장 큰 틈 (제목과 본문)
#     세로      줄 사이의 가장 큰 세로 틈
#     가로      단 사이의 가장 큰 가로 틈
#
# 「가장 뚜렷한」은 문턱이 아니다 — 셋을 같은 잣대(틈 ÷ 이웃 간격의 중앙값)로
# 재서 큰 쪽을 고른다. 어느 것도 뚜렷하지 않으면 안 가른다.
SPLIT_MIN = 2.0   # 틈이 이웃 간격 중앙값의 이 배는 되어야 «가른다» 고 본다.
                  # 1.0 이면 아무 데나 갈라지고, 크면 안 갈라진다. 2.0 은
                  # 「이웃보다 두 배 벌어졌다」로, 조판에서 단·계층을 가르는
                  # 최소한이다.


def _gap_split(vals, keys):
    """1차원 값들에서 가장 뚜렷한 틈을 찾는다. (자른 자리, 뚜렷함)"""
    if len(vals) < 2:
        return None, 0.0
    o = np.argsort(vals)
    v = np.asarray(vals, float)[o]
    d = np.diff(v)
    if not len(d) or np.median(d) <= 0:
        return None, 0.0
    i = int(np.argmax(d))
    return float((v[i] + v[i + 1]) / 2), float(d[i] / np.median(d))


def split_once(lines):
    """줄상자들을 «한 번만» 가른다. 못 가르면 원래대로 하나."""
    L = [_norm(b) for b in lines]
    L = [b for b in L if (b[2] - b[0]) * (b[3] - b[1]) >= MIN_AREA]
    if len(L) < 2:
        return [L] if L else []
    hs = [b[3] - b[1] for b in L]
    ys = [(b[1] + b[3]) / 2 for b in L]
    xs = [b[0] for b in L]
    cands = []
    for name, vals in (('크기', hs), ('세로', ys), ('가로', xs)):
        cut, score = _gap_split(vals, L)
        if cut is not None:
            cands.append((score, name, cut, vals))
    if not cands:
        return [L]
    score, name, cut, vals = max(cands)
    if score < SPLIT_MIN:
        return [L]
    a = [b for b, v in zip(L, vals) if v <= cut]
    z = [b for b, v in zip(L, vals) if v > cut]
    return [g for g in (a, z) if g]


def bbox(group):
    return (min(b[0] for b in group), min(b[1] for b in group),
            max(b[2] for b in group), max(b[3] for b in group), len(group))
