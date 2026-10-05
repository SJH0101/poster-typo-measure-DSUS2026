"""선 짝짓기 — 이 파일 하나에만 둔다.

규칙 (원고 3-1 의 채점 지표 문단 · docs/paper_numbers.md 0.1 절과 같다):
  창      참조 선과 측정 선의 차가 `WIN × 행간 ℓ` 이내이고 가로로 겹친다.
  겹침    min(t.x2, p.x2) − max(t.x1, p.x1) > 0 (맞닿기만 한 것은 겹침이 아니다).
  짝짓기  차가 작은 순서로 1:1 탐욕. 한 참조 선과 한 측정 선은 한 번만 쓰인다.
  맞음    오차 e = ŷ − y 가 |e| ≤ `TOL × ℓ`.

행간 ℓ 을 정하는 규칙은 여기 없다 — 블록마다 다르므로 부르는 쪽이 `t['lead']` 로 넘긴다
(`brockmann_stage2_score.block_L` · `synth_score._lead_of`).

T 는 dict 목록으로 `y` · `lead` · `x1` · `x2` 를 쓰고, P 는 tuple 목록으로 `[0]` = 값 ·
`[1]` = x1 · `[2]` = x2 를 쓴다 (뒤 칸은 부르는 쪽이 무엇을 담아도 된다).
`direct` 가 돌려주는 짝의 `t` · `p` 는 T · P 안의 자리 번호다.
"""

WIN, TOL = 0.5, 0.2


def overlap(t, p):
    """가로로 겹치나."""
    return min(t['x2'], p[2]) - max(t['x1'], p[1]) > 0


def in_window(t, p, win=WIN):
    """창 안에 있나 — 차가 win × 행간 이내이고 가로로 겹친다."""
    return abs(p[0] - t['y']) <= win * t['lead'] and overlap(t, p)


def direct(T, P, win=WIN, tol=TOL):
    """창 안에서 차가 작은 순서로 1:1 짝. [{t, p, err, hit}]."""
    cand = sorted((abs(p[0] - t['y']), i, j) for i, t in enumerate(T) for j, p in enumerate(P)
                  if abs(p[0] - t['y']) <= win * t['lead'] and min(t['x2'], p[2]) - max(t['x1'], p[1]) > 0)
    mi, mj, pairs = set(), set(), []
    for _d, i, j in cand:
        if i in mi or j in mj:
            continue
        mi.add(i); mj.add(j)
        e = P[j][0] - T[i]['y']
        pairs.append(dict(t=i, p=j, err=e, hit=abs(e) <= tol * T[i]['lead']))
    return pairs
