# 탐색용 자료

여기 있는 파일은 **탐색용이며 논문 수치가 아니다**. 사전등록 없이 돌린 것이고, 이 결과로
상수 · 문턱 · 파이프라인을 고치지 않는다. 파일마다 머리에 `"what": "탐색용 · 논문 수치 아님"`
이 있다.

| 파일 | 무엇 |
|---|---|
| `constants_converge_explore.json` | 잉크 문턱과 `detect_surya` 상수를 번갈아 훑어 값이 멎는지 본 반복 (5바퀴 상한) |
| `h_ratio_255_vs_34_explore.json` | `H_RATIO` 상한 2.55 대 3.4 — 줄 가르기를 켠 채 합성 650 · 브로크만 50 재채점 |
| `method_errors_explore.json` | 브로크만 50장에서 방식(C · VLM1 · VLM2 · A)별로 틀린 블록을 판별로 견줌 |
| `vlm_pass_diff_explore.json` | VLM 두 회차가 서로 다르게 판단한 블록과 그 특징 |

앞선 탐색 결과는 `docs/` 바로 아래에 `*_explore.json` 으로 있다 (`split_lines_*` ·
`typography_rules*` · `vlm_*` · `idml_explore.json`). `eval/refs.json` 과 결과 파일들이 그
경로를 기록하고 있어 옮기지 않았다.
