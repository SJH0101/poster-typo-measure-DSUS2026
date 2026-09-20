# 수치 상수 전수 조사 — 파이프라인 · 채점기 · 생성기

조사 날짜 2026-09-16, 기준 커밋 `a166e70`. 코드는 고치지 않았다. 봉인 파일은 열지 않았다.

## 대상과 추출 규칙

- **파일:** `measure/` (ink · region · grid · ground · probe) · `baseline/` (detect · scan · skew) · `detect_surya.py` · `group_gap.py` · `eval/group_score.py` · `detector_score.py` · `oracle_group.py` · 합성 생성기 (`eval/synth_gen.py` · `eval/clean_gen.py` · `eval/clean_phrases.py` · `eval/group_gen.py`) · `eval/brockmann_stage2_score.py`.
- **추출:** 파이썬 AST 의 수치 리터럴 (음수 포함). 모듈 상수 · 함수 기본값 · 키워드 인자 · 식 안의 값을 모두 센다. 같은 줄에 같은 이름 · 같은 값이 두 번 나오면 한 행으로 합쳤다.
- **뺀 것 (규칙 · 수):** 0·1·−1 (식 안 · 함수 안 대입) 456 · 첨자 663 · range 41 · 절반·제곱 23 · 축 15 · 서식 116 · 문구 내용 19. «0·1·−1» 은 식 안과 함수 안 대입에만 적용했다 (이름 붙은 모듈 상수 · 기본값의 0 · 1 은 표에 넣었다). «첨자» 는 `b[0]` 같은 색인 · 자르기, «range» 는 `range()` · `enumerate()` 인자, «축» 은 `axis=`, «서식» 은 f-문자열 · `print` · `round()` · `_r()` 의 자릿수 · `indent=`, «절반·제곱» 은 `/ 2` · `** 2`, «문구 내용» 은 문구 주머니의 날짜 · 분 같은 글자 내용이다. 파일 경로는 수치가 아니라 대상이 아니다. 난수 seed 는 표에서 빼고 끝에 목록만 둔다.

## 열

- **같은 역할로 따로 박힌 곳:** 같은 값이 import 가 아니라 리터럴로 다시 적힌 자리 가운데 같은 판정 · 같은 역할인 곳. 값만 같고 역할이 다른 자리(예: `synth_gen` 유색 바탕 HSV 의 0.72)는 적지 않았다. 조사 대상 밖 파일(`eval/synth_score.py` · `eval/brockmann_group_explore.py` · `eval/clean_check.py`)에 있는 것도 적었다.
- **첫 커밋:** 그 줄의 코드(주석 뺀 부분)가 처음 나타난 커밋 — `git log --follow --reverse -S`. 파일 이동 · 쪼개기(`125ac09`: blocks.py → baseline/detect.py · measure/ink.py · measure/grid.py, pipeline.py → baseline/scan.py, rotate.py → baseline/skew.py, ground.py → measure/ground.py, boxmeasure.py → measure/region.py)는 옛 경로까지 찾았다. 줄 모양이 나중에 바뀐 값은 바뀐 커밋이 잡힐 수 있다.
- **근거 기록:** 주석 · 스윕 결과 · 사전등록 · 문서(RESULTS_FOR_PAPER · GROUPING_LOGIC · HANDOFF · HUMAN_DATA) 가운데 그 값에 대해 적힌 것. 없으면 «없음».
- **분류:** **정의** = 수학 · 단위 · 표준 공식 · 자료 형식 · 계산이 성립하는 최소 개수에서 값이 정해진다. **스윕** = 값을 고른 스윕 · 비교 결과가 기록돼 있다. **차용** = 다른 상수 · 사전등록 · 앞선 결과 · 실물 측정값에서 가져왔고 출처가 적혀 있다. **임의** = 위 셋의 기록이 없다 (뜻만 적은 주석, 사전등록에 값만 적은 경우 포함).
- **논문 경로:** 저장소 전체의 정적 호출 그래프(함수 · 모듈 이름 참조)로 뿌리에서 닿는지 본다. 4장 합성 뿌리 = `eval/synth_gen.py` · `eval/synth_score.py` · `eval/clean_gen.py` · `eval/clean_check.py` · `eval/group_score.py` 의 detect · som · score_clean · `eval/clean_c_diag.py` · `eval/clean_a_sweep.py` · `eval/measure_pad_check.py` · `eval/clean_som_samples.py` · `eval/clean_vlm_batches.py` · `eval/group_vlm_merge.py`. 5장 브로크만 뿌리 = `eval/brockmann_group_explore.py` 의 prepare · seal · explore · `eval/brockmann_stage2_score.py` 의 check · consensus · score · `remeasure.py`. `synth_gen` 의 겹침 재생성 경로(`layout_checked` · `_refill` · `_regeo` · `_min_distance` · `_line` · `TEXT_TRIES` · `GEO_ROUNDS`)는 정적으로 닿지만 390장 생성에 쓰지 않아(사전등록 수정 3) «없음» 으로 두었다. 동적 호출은 이름 참조로 넓게 잡았다.
- **갈래 · 근거 후보 (2026-09-16 더함, 2026-09-17 고침):** 분류가 임의이고 논문 경로가 4장 · 5장 · 둘 다인 146행에만 채웠다. 나머지 행은 «—». 뜻은 «임의 · 논문 경로 146행» 절에 적었다. 2026-09-17 — SoM 그림 값 6묶음(16행)을 측정에서 실험조건으로 옮겼고, 영향 출력이 모두 논문에 보고되지 않는 측정 행에 «논문 수치 무관» 을 붙였다 («측정 출력 — 논문 보고 여부» 절).

## 분류 × 논문 경로 (행 수)

| 분류 | 4장 합성 | 5장 브로크만 | 둘 다 | 없음 | 합 |
|---|---|---|---|---|---|
| 정의 | 49 | 29 | 16 | 43 | 137 |
| 스윕 | 0 | 0 | 1 | 5 | 6 |
| 차용 | 20 | 12 | 1 | 6 | 39 |
| 임의 | 67 | 20 | 59 | 79 | 225 |
| 합 | 136 | 61 | 77 | 133 | 407 |

## `measure/ink.py`

| 위치 | 이름 | 값 | 같은 역할로 따로 박힌 곳 | 첫 커밋 | 근거 기록 | 분류 | 판단 근거 | 논문 경로 | 갈래 | 근거 후보 |
|---|---|---|---|---|---|---|---|---|---|---|
| measure/ink.py:16 | `FRAG_WIDE` | 0.4 | — | `9fde4a7` 2026-08-19 큰 글줄에 붙는 부스러기 블록을 버린다 | 주석: 이웃 글줄 폭의 이 비율 이하로 좁으면 글줄이 아니라 조각으로 본다 | 임의 | 주석은 뜻만 적었다 | 둘 다 | 측정 | 라벨 없는 실물 관찰 — 실물 판에서 조각과 글줄의 폭 비 분포가 두 봉우리로 갈리는지 잴 수 있음 |
| measure/ink.py:18 | `FRAG_COVER` | 0.35 | measure/probe.py:78 (조각 판정 0.35) | `cd9851c` 2026-08-24 짚는 쪽을 클로드에게 넘긴다 — measure_boxes | 주석 (한 판 관찰) | 임의 | 한 판 관찰값(점 0.12 · 글줄 0.63~0.92) 사이에서 고른 값, 스윕 기록 없음 | 둘 다 | 측정 | 라벨 없는 실물 관찰 — 주석의 한 판 관찰(점 0.12 · 글줄 0.63~0.92)을 여러 판의 채움 분포로 넓힐 수 있음 |
| measure/ink.py:24 | `INK_FRAC` | 0.06 | — | `a6972b3` 2026-08-18 누락된 blocks.py rotate.py 추가 | 주석 «스윕 결과 0.02~0.10 평평, 0.20부터 줄 소실» | 스윕 | 주석에 스윕 결과가 있다 (표본 · 파일 미기재) | 둘 다 | — | — |
| measure/ink.py:37 | `polarity() · (lo, med, hi)` | 5 | — | `7fde2cf` 2026-08-18 어두운 배경 포스터의 극성을 맞춘다 | 없음 | 임의 | 분포 꼬리를 보는 백분위, 근거 기록 없음 | 둘 다 | 측정 | 라벨 없는 실물 관찰 — 창 안 활자 화소 몫의 분포를 실물에서 재 꼬리 백분위를 정할 수 있음 |
| measure/ink.py:37 | `polarity() · (lo, med, hi)` | 50 | — | `7fde2cf` 2026-08-18 어두운 배경 포스터의 극성을 맞춘다 | 없음 | 정의 | 중앙값 | 둘 다 | — | — |
| measure/ink.py:37 | `polarity() · (lo, med, hi)` | 95 | — | `7fde2cf` 2026-08-18 어두운 배경 포스터의 극성을 맞춘다 | 없음 | 임의 | 분포 꼬리를 보는 백분위, 근거 기록 없음 | 둘 다 | 측정 | 라벨 없는 실물 관찰 — 창 안 활자 화소 몫의 분포를 실물에서 재 꼬리 백분위를 정할 수 있음 |
| measure/ink.py:38 | `polarity() · 식 안` | 255 | — | `7fde2cf` 2026-08-18 어두운 배경 포스터의 극성을 맞춘다 | 없음 | 정의 | 8비트 밝기 뒤집기 | 둘 다 | — | — |
| measure/ink.py:42 | `threshold() · 식 안` | 0.72 | baseline/skew.py:39 | `a6972b3` 2026-08-18 누락된 blocks.py rotate.py 추가 | 주석 «배경 밝기 기준 (회색 활자 대응)» | 임의 | 주석은 뜻만 적었다 | 둘 다 | 측정 | 정의·물리 유도 — 배경 · 잉크 밝기와 픽셀 덮임 비율에서 문턱을 유도할 수 있음 |
| measure/ink.py:44 | `lines(… body_h=)` | 4 | — | `ebb6933` 2026-08-19 활자와 그림이 분리돼 있다는 전제를 버린다 | RESULTS 4.1 («측정 바닥» 으로 인용) | 임의 | 근거 기록 없음 (값을 인용한 문서만 있다) | 둘 다 | 측정 | 합성 스윕 — x높이 3 · 5 셀처럼 작은 활자 조건에서 값을 훑어 평평한 구간을 볼 수 있음 |
| measure/ink.py:44 | `lines(… min_h=)` | 2 | measure/ink.py:142 · measure/probe.py:30 (min_h=2) | `ebb6933` 2026-08-19 활자와 그림이 분리돼 있다는 전제를 버린다 | 없음 | 임의 | 근거 기록 없음 | 둘 다 | 측정 | 정의·물리 유도 — 안티에일리어싱으로 흐린 가장자리 한 행과 몸통 한 행을 합친 최소 높이로 유도할 수 있음 |
| measure/ink.py:50 | `lines() · peak` | 90 | measure/probe.py:46 · baseline/detect.py:114 · :182 | `a6972b3` 2026-08-18 누락된 blocks.py rotate.py 추가 | 주석: 절대량이 아니라 비율로 판정한다. 얼룩·테두리·안티에일리어싱은 / 잉크량이 글자 몸통의 몇 %에 불과하므로 … | 임의 | 주석은 비율 판정의 뜻만 적었다 | 둘 다 | 측정 | 라벨 없는 실물 관찰 — 실물 글줄의 행 잉크량 분포에서 최댓값 대용 백분위를 정할 수 있음 |
| measure/ink.py:51 | `lines() · on` | 5 | measure/probe.py:47 | `a6972b3` 2026-08-18 누락된 blocks.py rotate.py 추가 | 없음 | 임의 | 근거 기록 없음 | 둘 다 | 측정 | 라벨 없는 실물 관찰 — 배경 행 잉크량 분포를 실물에서 잴 수 있음 |
| measure/ink.py:98 | `lines() · small` | 0.5 | — | `9fde4a7` 2026-08-19 큰 글줄에 붙는 부스러기 블록을 버린다 | 없음 | 임의 | 근거 기록 없음 | 둘 다 | 측정 | 정의·물리 유도 — 점 · 악센트 높이의 글꼴 비율에서 유도할 수 있음 |
| measure/ink.py:101 | `lines() · 식 안` | 0.6 | — | `9fde4a7` 2026-08-19 큰 글줄에 붙는 부스러기 블록을 버린다 | 없음 | 임의 | 근거 기록 없음 | 둘 다 | 측정 | 정의·물리 유도 — 점 · 악센트와 몸통 사이 거리의 글꼴 비율에서 유도할 수 있음 |
| measure/ink.py:101 | `lines() · 식 안` | 3 | — | `9fde4a7` 2026-08-19 큰 글줄에 붙는 부스러기 블록을 버린다 | 없음 | 임의 | 근거 기록 없음 | 둘 다 | 측정 | 정의·물리 유도 — 점 · 악센트와 몸통 사이 거리의 글꼴 비율에서 유도할 수 있음 |
| measure/ink.py:126 | `BASE_OFFSET` | 1 | — | `a6972b3` 2026-08-18 누락된 blocks.py rotate.py 추가 | 주석 (1958 Musica Viva 25줄 대조) | 차용 | 사람 손 찍기 25줄 대조(평균 +1.08)에서 온 값 | 둘 다 | — | — |
| measure/ink.py:129 | `baseline(… frac=)` | 0.5 | — | `a6972b3` 2026-08-18 누락된 blocks.py rotate.py 추가 | 없음 | 임의 | 근거 기록 없음 | 둘 다 | 측정 | 정의·물리 유도 — 행 잉크가 몸통의 절반 — 픽셀 덮임 절반이라는 측정 약속으로 둘 수 있음 (라벨 규칙 «절반 넘게 진하면» 과 같은 꼴) |
| measure/ink.py:142 | `descender(… depth=)` | 6 | — | `a6972b3` 2026-08-18 누락된 blocks.py rotate.py 추가 | 없음 | 임의 | 근거 기록 없음 | 둘 다 | 측정 — 논문 수치 무관 | 정의·물리 유도 — 글꼴 디센더 비율(em)과 활자 크기에서 px 로 유도할 수 있음 |
| measure/ink.py:142 | `descender(… min_h=)` | 2 | measure/ink.py:44 (min_h=2) | `a6972b3` 2026-08-18 누락된 blocks.py rotate.py 추가 | 없음 | 임의 | 근거 기록 없음 | 둘 다 | 측정 | 정의·물리 유도 — 안티에일리어싱으로 흐린 가장자리 한 행과 몸통 한 행을 합친 최소 높이로 유도할 수 있음 |
| measure/ink.py:153 | `descender() · structure=` | 3 | measure/ink.py:175 | `a6972b3` 2026-08-18 누락된 blocks.py rotate.py 추가 | 없음 | 정의 | 3×3 (8-연결) 라벨링 | 둘 다 | — | — |
| measure/ink.py:175 | `split_marks() · structure=` | 3 | measure/ink.py:153 | `a6972b3` 2026-08-18 누락된 blocks.py rotate.py 추가 | 없음 | 정의 | 3×3 (8-연결) 라벨링 | 둘 다 | — | — |
| measure/ink.py:187 | `split_marks() · xh` | 0.5 | — | `a6972b3` 2026-08-18 누락된 blocks.py rotate.py 추가 | 주석 · 사전등록 xheight_g1 (되돌림 규칙으로 유지) | 임의 | G1 사전등록은 새 규칙만 정했다. 0.5 는 되돌림(옛 어깨) 값이고 근거 기록 없음 | 둘 다 | 측정 | 합성 스윕 — 되돌림이 쓰이는 줄을 합성 정답으로 모아 값을 훑을 수 있음 |
| measure/ink.py:210 | `split_marks() · kind` | 2 | eval/brockmann_stage2_score.py:523 · :669 (같은 «2행» 기준) | `a6972b3` 2026-08-18 누락된 blocks.py rotate.py 추가 | 주석: 몸통 조각 대다수가 x 높이에서 시작하면 어센더 없음 | 임의 | 주석은 뜻만 적었다 (2행 이상이면 어센더) | 둘 다 | 측정 | 정의·물리 유도 — 어센더 − x높이 글꼴 비율 × 활자 크기와 가장자리 한 행에서 유도할 수 있음 |
| measure/ink.py:221 | `strokes(… pad=)` | 1 | — | `a3517d3` 2026-09-07 활자를 «상자» 가 아니라 «획» 으로 잰다 — 그리고 갈림 둘을 물린다 | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| measure/ink.py:238 | `strokes() · 식 안` | 2 | — | `a3517d3` 2026-09-07 활자를 «상자» 가 아니라 «획» 으로 잰다 — 그리고 갈림 둘을 물린다 | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| measure/ink.py:243 | `strokes() · 식 안` | 1e-06 | — | `a3517d3` 2026-09-07 활자를 «상자» 가 아니라 «획» 으로 잰다 — 그리고 갈림 둘을 물린다 | 없음 | 정의 | 0 나눗셈을 막는 수치 여유 | 없음 | — | — |
| measure/ink.py:250 | `_otsu_t() · bins=` | 64 | — | `a3517d3` 2026-09-07 활자를 «상자» 가 아니라 «획» 으로 잰다 — 그리고 갈림 둘을 물린다 | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| measure/ink.py:254 | `_otsu_t() · ok` | 1e-06 | — | `a3517d3` 2026-09-07 활자를 «상자» 가 아니라 «획» 으로 잰다 — 그리고 갈림 둘을 물린다 | 없음 | 정의 | 0 나눗셈을 막는 수치 여유 | 없음 | — | — |

## `measure/region.py`

| 위치 | 이름 | 값 | 같은 역할로 따로 박힌 곳 | 첫 커밋 | 근거 기록 | 분류 | 판단 근거 | 논문 경로 | 갈래 | 근거 후보 |
|---|---|---|---|---|---|---|---|---|---|---|
| measure/region.py:30 | `PAD` | 3 | baseline/scan.py:10 · baseline/skew.py:17 (pad 6, 다른 값) | `97d61d9` 2026-08-21 상자를 받아 그 안만 재는 쪽을 따로 둔다 | 주석 (뜻) · GROUPING_LOGIC («기존» 값으로 인용) | 임의 | 주석은 뜻만 적었다 | 둘 다 | 측정 | 합성 스윕 — pad 검증 사전등록(measure_pad)과 같은 방식으로 값을 훑을 수 있음 |
| measure/region.py:31 | `ALIGN_EPS` | 3 | — | `97d61d9` 2026-08-21 상자를 받아 그 안만 재는 쪽을 따로 둔다 | 주석 «왼쪽은 이보다 훨씬 고르다» | 임의 | 주석은 관찰 서술뿐, 수치 근거 없음 | 둘 다 | 측정 — 논문 수치 무관 | 라벨 없는 실물 관찰 — 실물 블록 줄 왼쪽 끝의 흩어짐 분포를 잴 수 있음 |
| measure/region.py:36 | `_align() · 식 안` | 2 | — | `97d61d9` 2026-08-21 상자를 받아 그 안만 재는 쪽을 따로 둔다 | 없음 | 정의 | 흩어짐 계산에 값 둘이 필요 | 둘 다 | — | — |
| measure/region.py:78 | `measure() · 식 안` | 4 | — | `97d61d9` 2026-08-21 상자를 받아 그 안만 재는 쪽을 따로 둔다 | 없음 | 임의 | 근거 기록 없음 | 둘 다 | 측정 | 정의·물리 유도 — min_h 2 에 가장자리를 더한 최소 창으로 유도할 수 있음 |

## `measure/grid.py`

| 위치 | 이름 | 값 | 같은 역할로 따로 박힌 곳 | 첫 커밋 | 근거 기록 | 분류 | 판단 근거 | 논문 경로 | 갈래 | 근거 후보 |
|---|---|---|---|---|---|---|---|---|---|---|
| measure/grid.py:13 | `fit_grid() · 식 안` | 3 | — | `a6972b3` 2026-08-18 누락된 blocks.py rotate.py 추가 | 없음 | 임의 | 근거 기록 없음 | 둘 다 | 측정 — 논문 수치 무관 | 정의·물리 유도 — 격자 주기를 보려면 간격 둘 이상이 필요하다는 조건으로 유도할 수 있음 |
| measure/grid.py:21 | `fit_grid() · 식 안` | 3 | — | `3941b0e` 2026-08-19 측정 실패 2장의 원인 — fit_grid 의 음수 슬라이스 | 없음 | 임의 | 근거 기록 없음 | 둘 다 | 측정 — 논문 수치 무관 | 미정 — 프로파일 구간 길이의 뜻이 코드에 적혀 있지 않음 |
| measure/grid.py:27 | `fit_grid() · hi` | 60 | — | `a6972b3` 2026-08-18 누락된 blocks.py rotate.py 추가 | HANDOFF [5] 설계 절 (서술) | 임의 | 근거 기록 없음 (HANDOFF 는 «블록 잉크 프로파일에 맞춘 값» 이라고 서술만) | 둘 다 | 측정 — 논문 수치 무관 | 라벨 없는 실물 관찰 — 실물 행간(px) 분포에서 탐색 창을 정할 수 있음 |
| measure/grid.py:27 | `fit_grid() · lo` | 5 | — | `a6972b3` 2026-08-18 누락된 blocks.py rotate.py 추가 | HANDOFF [5] 설계 절 (서술) | 임의 | 근거 기록 없음 (HANDOFF 는 «블록 잉크 프로파일에 맞춘 값» 이라고 서술만) | 둘 다 | 측정 — 논문 수치 무관 | 라벨 없는 실물 관찰 — 실물 행간(px) 분포에서 탐색 창을 정할 수 있음 |
| measure/grid.py:31 | `fit_grid() · peaks` | 0.25 | — | `a6972b3` 2026-08-18 누락된 blocks.py rotate.py 추가 | HANDOFF [5] 설계 절 (서술) | 임의 | 근거 기록 없음 (HANDOFF 서술만) | 둘 다 | 측정 — 논문 수치 무관 | 합성 스윕 — 합성 격자 공유 · 독립 셀에서 값을 훑어 평평한 구간을 볼 수 있음 |
| measure/grid.py:35 | `fit_grid() · 식 안` | 2 | — | `a6972b3` 2026-08-18 누락된 blocks.py rotate.py 추가 | 주석: 실측과 크게 다르면 신뢰하지 않음 | 임의 | 주석은 뜻만 적었다 | 둘 다 | 측정 — 논문 수치 무관 | 정의·물리 유도 — 정수 베이스라인 양자화에서 간격 차 허용을 유도할 수 있음 (τ 1px 와 같은 방식) |
| measure/grid.py:44 | `apply_grid() · 식 안` | 3 | measure/grid.py:13 (3) | `a6972b3` 2026-08-18 누락된 blocks.py rotate.py 추가 | 없음 | 임의 | 근거 기록 없음 | 둘 다 | 측정 — 논문 수치 무관 | 정의·물리 유도 — 격자 주기를 보려면 간격 둘 이상이 필요하다는 조건으로 유도할 수 있음 |
| measure/grid.py:46 | `apply_grid() · (fitted, lead, resid)` | 8 | — | `a6972b3` 2026-08-18 누락된 blocks.py rotate.py 추가 | 주석: 측정값은 그대로 둔다. 격자는 별도 열로만 남긴다. | 임의 | 근거 기록 없음 | 둘 다 | 측정 — 논문 수치 무관 | 정의·물리 유도 — 첫 줄 위 캡 높이 · 마지막 줄 아래 디센더의 글꼴 비율에서 유도할 수 있음 |
| measure/grid.py:46 | `apply_grid() · (fitted, lead, resid)` | 20 | — | `a6972b3` 2026-08-18 누락된 blocks.py rotate.py 추가 | 주석: 측정값은 그대로 둔다. 격자는 별도 열로만 남긴다. | 임의 | 근거 기록 없음 | 둘 다 | 측정 — 논문 수치 무관 | 정의·물리 유도 — 첫 줄 위 캡 높이 · 마지막 줄 아래 디센더의 글꼴 비율에서 유도할 수 있음 |

## `measure/ground.py`

| 위치 | 이름 | 값 | 같은 역할로 따로 박힌 곳 | 첫 커밋 | 근거 기록 | 분류 | 판단 근거 | 논문 경로 | 갈래 | 근거 후보 |
|---|---|---|---|---|---|---|---|---|---|---|
| measure/ground.py:30 | `MIN_LINES` | 1 | — | `cd9851c` 2026-08-24 짚는 쪽을 클로드에게 넘긴다 — measure_boxes | 주석 (뜻) | 정의 | 줄을 하나도 못 찾은 상자를 뺀다는 조건 | 둘 다 | — | — |

## `measure/probe.py`

| 위치 | 이름 | 값 | 같은 역할로 따로 박힌 곳 | 첫 커밋 | 근거 기록 | 분류 | 판단 근거 | 논문 경로 | 갈래 | 근거 후보 |
|---|---|---|---|---|---|---|---|---|---|---|
| measure/probe.py:30 | `bands(… min_h=)` | 2 | measure/ink.py:44 (min_h=2) | `86dc9f2` 2026-08-24 짚기 진단기 — 어디를 자를지 보여준다 | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| measure/probe.py:46 | `bands() · peak` | 90 | measure/ink.py:50 | `86dc9f2` 2026-08-24 짚기 진단기 — 어디를 자를지 보여준다 | 없음 | 임의 | ink.lines 와 같은 식을 따로 적었다, 근거 기록 없음 | 없음 | — | — |
| measure/probe.py:47 | `bands() · on` | 5 | measure/ink.py:51 | `86dc9f2` 2026-08-24 짚기 진단기 — 어디를 자를지 보여준다 | 없음 | 임의 | ink.lines 와 같은 식을 따로 적었다, 근거 기록 없음 | 없음 | — | — |
| measure/probe.py:77 | `show() · 식 안` | 0.95 | — | `86dc9f2` 2026-08-24 짚기 진단기 — 어디를 자를지 보여준다 | 없음 | 임의 | 진단 표시 문턱, 근거 기록 없음 | 없음 | — | — |
| measure/probe.py:78 | `show() · 식 안` | 0.35 | measure/ink.py:18 (FRAG_COVER) | `86dc9f2` 2026-08-24 짚기 진단기 — 어디를 자를지 보여준다 | 없음 | 임의 | FRAG_COVER 와 같은 값을 참조 없이 따로 적었다 | 없음 | — | — |
| measure/probe.py:79 | `show() · 식 안` | 3 | — | `86dc9f2` 2026-08-24 짚기 진단기 — 어디를 자를지 보여준다 | 없음 | 임의 | 진단 표시 문턱, 근거 기록 없음 | 없음 | — | — |

## `baseline/detect.py`

| 위치 | 이름 | 값 | 같은 역할로 따로 박힌 곳 | 첫 커밋 | 근거 기록 | 분류 | 판단 근거 | 논문 경로 | 갈래 | 근거 후보 |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline/detect.py:18 | `EPS` | 2 | — | `a6972b3` 2026-08-18 누락된 blocks.py rotate.py 추가 | 주석: 측정 오차 (안티에일리어싱 2~3px). 절대 하한으로 쓴다. | 임의 | 주석은 서술(안티에일리어싱 2~3px)뿐, 측정 기록 없음 | 없음 | — | — |
| baseline/detect.py:19 | `GAP_RATIO` | 1.5 | — | `a6972b3` 2026-08-18 누락된 blocks.py rotate.py 추가 | 주석 (뜻) · GROUPING_LOGIC («스윕 기록이 없다») | 임의 | GROUPING_LOGIC: 스윕 기록 없음 | 없음 | — | — |
| baseline/detect.py:20 | `SIZE_RATIO` | 0.25 | — | `a6972b3` 2026-08-18 누락된 blocks.py rotate.py 추가 | 주석 (뜻) · GROUPING_LOGIC («스윕 기록이 없다») | 임의 | GROUPING_LOGIC: 스윕 기록 없음 | 없음 | — | — |
| baseline/detect.py:23 | `COL_FRAC` | 0.13 | — | `eeaf12d` 2026-08-19 열 분리도 상대 비율로 본다 | 주석 (코어 108장 스윕 표) · GROUPING_LOGIC | 스윕 | 주석에 코어 108장 스윕 표 | 없음 | — | — |
| baseline/detect.py:36 | `STRATA_RATIO` | 3 | — | `ebb6933` 2026-08-19 활자와 그림이 분리돼 있다는 전제를 버린다 | 주석 (36장 스윕) · GROUPING_LOGIC | 스윕 | 주석에 36장 스윕 | 없음 | — | — |
| baseline/detect.py:40 | `COL_GAP_FRAC` | 0.5 | — | `c313c3e` 2026-08-19 바탕이 바뀌는 자리마다 문턱을 다시 잡고, 크기 계층부터 가른다 | 주석 (18점 스윕) · GROUPING_LOGIC | 스윕 | 주석에 오페라하우스 18점 스윕 | 없음 | — | — |
| baseline/detect.py:45 | `BAND_STEP` | 48 | baseline/detect.py:49 (BAND_MIN 48) | `c313c3e` 2026-08-19 바탕이 바뀌는 자리마다 문턱을 다시 잡고, 크기 계층부터 가른다 | 주석 (18점 스윕) · GROUPING_LOGIC | 스윕 | 주석에 오페라하우스 18점 스윕 | 없음 | — | — |
| baseline/detect.py:49 | `BAND_MIN` | 48 | baseline/detect.py:45 (BAND_STEP 48) | `c313c3e` 2026-08-19 바탕이 바뀌는 자리마다 문턱을 다시 잡고, 크기 계층부터 가른다 | 주석 (18점 스윕) | 스윕 | 주석에 오페라하우스 18점 스윕 | 없음 | — | — |
| baseline/detect.py:53 | `SEED_PAD` | 4 | — | `5a67500` 2026-08-19 회전 오검출을 막고, 극성이 뒤집히는 자리를 보강 검출한다 | 주석: 씨앗 상자를 이만큼 넓혀 본다 | 임의 | 주석은 뜻만 적었다 | 없음 | — | — |
| baseline/detect.py:55 | `SHADOW_PAD` | 5 | — | `9fde4a7` 2026-08-19 큰 글줄에 붙는 부스러기 블록을 버린다 | 주석: 큰 블록의 상자를 이만큼 넓혀 그 안에 드는지 본다 | 임의 | 주석은 뜻만 적었다 | 없음 | — | — |
| baseline/detect.py:56 | `SHADOW_H` | 0.45 | baseline/detect.py:62 (SHADOW_W 0.45) | `7c86869` 2026-08-21 조각 블록을 상자 크기로 걸러내고, 정렬축 문턱 고정 버그를 고친다 | 주석 (한 판 사례) | 임의 | 주석은 한 판 사례(Wiener Blut)만, 값 근거 없음 | 없음 | — | — |
| baseline/detect.py:62 | `SHADOW_W` | 0.45 | baseline/detect.py:56 (SHADOW_H 0.45) | `7c86869` 2026-08-21 조각 블록을 상자 크기로 걸러내고, 정렬축 문턱 고정 버그를 고친다 | 주석 (한 판 사례) | 임의 | 주석은 한 판 사례(Wiener Blut)만, 값 근거 없음 | 없음 | — | — |
| baseline/detect.py:77 | `_measured() · 식 안` | 2 | — | `fc53936` 2026-08-24 행간은 잰 값을 쓴다 — 격자값은 다른 질문이다 | 없음 | 정의 | 비교에 값 둘이 필요 | 없음 | — | — |
| baseline/detect.py:82 | `trim(… frac=)` | 0.8 | — | `a6972b3` 2026-08-18 누락된 blocks.py rotate.py 추가 | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| baseline/detect.py:82 | `trim(… max_fringe=)` | 3 | — | `a6972b3` 2026-08-18 누락된 blocks.py rotate.py 추가 | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| baseline/detect.py:106 | `columns(… min_gap=)` | 6 | baseline/detect.py:179 · :331 (6) | `a6972b3` 2026-08-18 누락된 blocks.py rotate.py 추가 | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| baseline/detect.py:114 | `columns() · peak` | 90 | baseline/detect.py:182 · measure/ink.py:50 · measure/probe.py:46 | `eeaf12d` 2026-08-19 열 분리도 상대 비율로 본다 | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| baseline/detect.py:124 | `columns() · 식 안` | 10 | baseline/detect.py:192 (10) | `a6972b3` 2026-08-18 누락된 blocks.py rotate.py 추가 | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| baseline/detect.py:143 | `shares_axis() · 식 안` | 2 | — | `83fb535` 2026-08-19 정렬 방식을 코드에 박지 않는다 | 주석: 가운데 | 정의 | 가운데 비교는 양 끝의 합이라 허용이 두 배 | 없음 | — | — |
| baseline/detect.py:179 | `columns_mask(… min_gap=)` | 6 | baseline/detect.py:106 · :331 (6) | `c313c3e` 2026-08-19 바탕이 바뀌는 자리마다 문턱을 다시 잡고, 크기 계층부터 가른다 | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| baseline/detect.py:182 | `columns_mask() · peak` | 90 | baseline/detect.py:114 · measure/ink.py:50 · measure/probe.py:46 | `eeaf12d` 2026-08-19 열 분리도 상대 비율로 본다 | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| baseline/detect.py:192 | `columns_mask() · 식 안` | 10 | baseline/detect.py:124 (10) | `a6972b3` 2026-08-18 누락된 blocks.py rotate.py 추가 | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| baseline/detect.py:200 | `group() · 식 안` | 2 | — | `a6972b3` 2026-08-18 누락된 blocks.py rotate.py 추가 | 없음 | 정의 | 비교에 값 둘이 필요 | 없음 | — | — |
| baseline/detect.py:225 | `group() · nxt` | 2 | — | `85a8733` 2026-08-19 한 줄만 튀는 것을 크기 변화로 오인하지 않는다 | 주석 (규칙 서술 · 한 판 사례) | 정의 | 튄 줄의 다음 줄을 본다 (주석의 규칙) | 없음 | — | — |
| baseline/detect.py:261 | `bands() · 식 안` | 2 | — | `c313c3e` 2026-08-19 바탕이 바뀌는 자리마다 문턱을 다시 잡고, 크기 계층부터 가른다 | 없음 | 정의 | 띠 둘로 가를 최소 높이 = min_h 의 두 배 | 없음 | — | — |
| baseline/detect.py:261 | `bands() · 식 안` | 4 | — | `c313c3e` 2026-08-19 바탕이 바뀌는 자리마다 문턱을 다시 잡고, 크기 계층부터 가른다 | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| baseline/detect.py:297 | `seeded() · 식 안` | 6 | — | `5a67500` 2026-08-19 회전 오검출을 막고, 극성이 뒤집히는 자리를 보강 검출한다 | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| baseline/detect.py:297 | `seeded() · 식 안` | 8 | — | `5a67500` 2026-08-19 회전 오검출을 막고, 극성이 뒤집히는 자리를 보강 검출한다 | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| baseline/detect.py:331 | `_panels() · gap` | 6 | baseline/detect.py:106 · :179 (min_gap=6) | `c313c3e` 2026-08-19 바탕이 바뀌는 자리마다 문턱을 다시 잡고, 크기 계층부터 가른다 | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |

## `baseline/scan.py`

| 위치 | 이름 | 값 | 같은 역할로 따로 박힌 곳 | 첫 커밋 | 근거 기록 | 분류 | 판단 근거 | 논문 경로 | 갈래 | 근거 후보 |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline/scan.py:10 | `PAD` | 6 | baseline/skew.py:17 (pad=6) | `e60ddd3` 2026-08-18 조판 규칙 MCP 서버 초기 커밋 | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| baseline/scan.py:11 | `FLAT` | 1 | — | `e60ddd3` 2026-08-18 조판 규칙 MCP 서버 초기 커밋 | 주석: 이보다 작은 각은 회전하지 않는다 | 임의 | 주석은 뜻만 적었다 | 없음 | — | — |
| baseline/scan.py:12 | `ANGLE_SD` | 2 | — | `5a67500` 2026-08-19 회전 오검출을 막고, 극성이 뒤집히는 자리를 보강 검출한다 | 주석 (18점 대조) · HUMAN_DATA | 임의 | 주석은 회전 끄기 대조(18점)만, 2.0 의 근거 없음 | 없음 | — | — |
| baseline/scan.py:23 | `MAX_SKEW` | 10 | — | `8f6efc5` 2026-08-18 디자인 대각선을 스캔 기울기로 착각하지 않는다 | 주석 (눈 확인 서술) · HUMAN_DATA | 임의 | 주석은 눈 확인(30장 중 16장) 서술, 값 선택 근거 아님 | 없음 | — | — |
| baseline/scan.py:48 | `estimate_angle(… top=)` | 8 | — | `e60ddd3` 2026-08-18 조판 규칙 MCP 서버 초기 커밋 | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| baseline/scan.py:60 | `estimate_angle() · A` | 45 | — | `e60ddd3` 2026-08-18 조판 규칙 MCP 서버 초기 커밋 | 없음 | 정의 | 각도의 90° 모호성 · 한 바퀴 | 없음 | — | — |
| baseline/scan.py:60 | `estimate_angle() · A` | 90 | — | `e60ddd3` 2026-08-18 조판 규칙 MCP 서버 초기 커밋 | 없음 | 정의 | 각도의 90° 모호성 · 한 바퀴 | 없음 | — | — |
| baseline/scan.py:65 | `estimate_angle() · 식 안` | 90 | — | `e60ddd3` 2026-08-18 조판 규칙 MCP 서버 초기 커밋 | 없음 | 정의 | 각도의 90° 모호성 · 한 바퀴 | 없음 | — | — |

## `baseline/skew.py`

| 위치 | 이름 | 값 | 같은 역할로 따로 박힌 곳 | 첫 커밋 | 근거 기록 | 분류 | 판단 근거 | 논문 경로 | 갈래 | 근거 후보 |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline/skew.py:12 | `STEP` | 0.5 | — | `a6972b3` 2026-08-18 누락된 blocks.py rotate.py 추가 | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| baseline/skew.py:13 | `RANGE` | 90 | — | `a6972b3` 2026-08-18 누락된 blocks.py rotate.py 추가 | 주석 (뜻) | 정의 | ±90° 는 방향 전 범위 | 없음 | — | — |
| baseline/skew.py:14 | `MIN_W` | 40 | — | `a6972b3` 2026-08-18 누락된 blocks.py rotate.py 추가 | 주석: 이보다 좁은 상자는 각도 추정을 신뢰하지 않음 | 임의 | 주석은 뜻만 적었다 | 없음 | — | — |
| baseline/skew.py:17 | `crop(… pad=)` | 6 | baseline/scan.py:10 (PAD 6) | `a6972b3` 2026-08-18 누락된 blocks.py rotate.py 추가 | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| baseline/skew.py:32 | `sharpness() · 식 안` | 1e-09 | — | `a6972b3` 2026-08-18 누락된 blocks.py rotate.py 추가 | 없음 | 정의 | 0 나눗셈을 막는 수치 여유 | 없음 | — | — |
| baseline/skew.py:37 | `coarse_angle() · 식 안` | 8 | — | `a6972b3` 2026-08-18 누락된 blocks.py rotate.py 추가 | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| baseline/skew.py:39 | `coarse_angle() · th` | 0.72 | measure/ink.py:42 | `a6972b3` 2026-08-18 누락된 blocks.py rotate.py 추가 | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| baseline/skew.py:67 | `box_angle() · cand` | 90 | — | `a6972b3` 2026-08-18 누락된 blocks.py rotate.py 추가 | 없음 | 정의 | 각도의 90° 모호성 · 한 바퀴 | 없음 | — | — |
| baseline/skew.py:67 | `box_angle() · cand` | 180 | — | `a6972b3` 2026-08-18 누락된 blocks.py rotate.py 추가 | 없음 | 정의 | 각도의 90° 모호성 · 한 바퀴 | 없음 | — | — |
| baseline/skew.py:68 | `box_angle() · cand` | 360 | — | `a6972b3` 2026-08-18 누락된 blocks.py rotate.py 추가 | 없음 | 정의 | 각도의 90° 모호성 · 한 바퀴 | 없음 | — | — |

## `detect_surya.py`

| 위치 | 이름 | 값 | 같은 역할로 따로 박힌 곳 | 첫 커밋 | 근거 기록 | 분류 | 판단 근거 | 논문 경로 | 갈래 | 근거 후보 |
|---|---|---|---|---|---|---|---|---|---|---|
| detect_surya.py:24 | `H_RATIO` | 0.6 | — | `d7a1250` 2026-08-31 검출을 Surya 로 갈아끼운다 — 찾기와 재기가 갈라진다 | RESULTS 4.3 · GROUPING_LOGIC («근거 기록 없음», d7a1250) | 임의 | RESULTS 4.3 · GROUPING_LOGIC 에 «스윕 · 검증 기록 없음» | 둘 다 | 측정 | 라벨 없는 실물 관찰 — 이웃 줄 높이 비 분포에서 크기 계층 봉우리를 잴 수 있음 |
| detect_surya.py:24 | `H_RATIO` | 1.7 | — | `d7a1250` 2026-08-31 검출을 Surya 로 갈아끼운다 — 찾기와 재기가 갈라진다 | RESULTS 4.3 · GROUPING_LOGIC («근거 기록 없음», d7a1250) | 임의 | RESULTS 4.3 · GROUPING_LOGIC 에 «스윕 · 검증 기록 없음» | 둘 다 | 측정 | 라벨 없는 실물 관찰 — 이웃 줄 높이 비 분포에서 크기 계층 봉우리를 잴 수 있음 |
| detect_surya.py:25 | `X_OVER` | 0.15 | — | `d7a1250` 2026-08-31 검출을 Surya 로 갈아끼운다 — 찾기와 재기가 갈라진다 | RESULTS 4.3 · GROUPING_LOGIC («근거 기록 없음», d7a1250) | 임의 | RESULTS 4.3 · GROUPING_LOGIC 에 «스윕 · 검증 기록 없음» | 둘 다 | 측정 | 라벨 없는 실물 관찰 — 같은 단 줄끼리의 가로 겹침 몫 분포를 실물에서 잴 수 있음 |
| detect_surya.py:26 | `Y_GAP` | -0.4 | — | `d7a1250` 2026-08-31 검출을 Surya 로 갈아끼운다 — 찾기와 재기가 갈라진다 | RESULTS 4.3 · GROUPING_LOGIC («근거 기록 없음», d7a1250) | 임의 | RESULTS 4.3 · GROUPING_LOGIC 에 «스윕 · 검증 기록 없음» | 둘 다 | 측정 | 라벨 없는 실물 관찰 — 세로 틈 ÷ 줄 높이 분포에서 줄 사이 · 블록 사이 봉우리를 잴 수 있음 |
| detect_surya.py:26 | `Y_GAP` | 1.6 | — | `d7a1250` 2026-08-31 검출을 Surya 로 갈아끼운다 — 찾기와 재기가 갈라진다 | RESULTS 4.3 · GROUPING_LOGIC («근거 기록 없음», d7a1250) | 임의 | RESULTS 4.3 · GROUPING_LOGIC 에 «스윕 · 검증 기록 없음» | 둘 다 | 측정 | 라벨 없는 실물 관찰 — 세로 틈 ÷ 줄 높이 분포에서 줄 사이 · 블록 사이 봉우리를 잴 수 있음 |
| detect_surya.py:28 | `MIN_AREA` | 200 | — | `d7a1250` 2026-08-31 검출을 Surya 로 갈아끼운다 — 찾기와 재기가 갈라진다 | RESULTS 4.3 · GROUPING_LOGIC («근거 기록 없음», d7a1250) | 임의 | RESULTS 4.3 · GROUPING_LOGIC 에 «스윕 · 검증 기록 없음» | 둘 다 | 측정 | 라벨 없는 실물 관찰 — Surya 상자 넓이 분포에서 부스러기 봉우리를 잴 수 있음 |
| detect_surya.py:81 | `COL_GAP` | 0.02 | — | `0e1f8a3` 2026-08-31 깨끗한 상자로 다시 재니 면여유가 죽었다 — 그리고 새 둘이 살았다 | 주석: ── 단 ────────────────────────────────────────────────────── … | 임의 | 주석은 뜻 · 문제 서술만 | 둘 다 | 측정 — 논문 수치 무관 | 라벨 없는 실물 관찰 — 실물 판에서 줄이 안 걸친 세로 띠 폭 분포를 잴 수 있음 |
| detect_surya.py:82 | `COL_MIN` | 0.05 | — | `0e1f8a3` 2026-08-31 깨끗한 상자로 다시 재니 면여유가 죽었다 — 그리고 새 둘이 살았다 | 주석: 이보다 좁은 단은 세지 않는다 (쪽번호·여백 글자) | 임의 | 주석은 뜻 · 문제 서술만 | 둘 다 | 측정 — 논문 수치 무관 | 라벨 없는 실물 관찰 — 실물 판에서 단 폭 분포의 작은 봉우리(쪽번호 등)를 잴 수 있음 |
| detect_surya.py:83 | `COL_H` | 1.6 | — | `0e1f8a3` 2026-08-31 깨끗한 상자로 다시 재니 면여유가 죽었다 — 그리고 새 둘이 살았다 | 주석: 줄 높이가 중앙값의 이 배를 넘으면 표제로 보고 단 세기에서 뺀다. / 판을 가로지르는 표제 한 줄이 폭 전… | 임의 | 주석은 뜻 · 문제 서술만 | 둘 다 | 측정 — 논문 수치 무관 | 라벨 없는 실물 관찰 — 실물 판에서 표제 줄 높이 ÷ 중앙값 분포를 잴 수 있음 |
| detect_surya.py:86 | `COL_W` | 0.75 | — | `0e1f8a3` 2026-08-31 깨끗한 상자로 다시 재니 면여유가 죽었다 — 그리고 새 둘이 살았다 | 주석: 판을 가로지르는 표제 한 줄이 폭 전체를 덮어 늘 «1단» 이 나왔다. / 옛 detect.py 가 크기 계… | 임의 | 주석은 뜻 · 문제 서술만 | 둘 다 | 측정 — 논문 수치 무관 | 라벨 없는 실물 관찰 — 실물 판에서 가로지르는 줄 폭 ÷ 판 폭 분포를 잴 수 있음 |
| detect_surya.py:136 | `SPLIT_MIN` | 2 | — | `72744e0` 2026-09-03 재귀를 갈아엎는다 — 검출 한 번, 나머지는 기하 | 주석: ── 재귀용 «한 번만 가르기» ──────────────────────────────────── / gro… | 임의 | 주석은 뜻(«이웃보다 두 배»)만 | 없음 | — | — |
| detect_surya.py:144 | `_gap_split() · 식 안` | 2 | — | `72744e0` 2026-09-03 재귀를 갈아엎는다 — 검출 한 번, 나머지는 기하 | 없음 | 정의 | 가르기에 값 둘이 필요 | 없음 | — | — |
| detect_surya.py:159 | `split_once() · 식 안` | 2 | — | `72744e0` 2026-09-03 재귀를 갈아엎는다 — 검출 한 번, 나머지는 기하 | 없음 | 정의 | 가르기에 값 둘이 필요 | 없음 | — | — |

## `group_gap.py`

| 위치 | 이름 | 값 | 같은 역할로 따로 박힌 곳 | 첫 커밋 | 근거 기록 | 분류 | 판단 근거 | 논문 경로 | 갈래 | 근거 후보 |
|---|---|---|---|---|---|---|---|---|---|---|
| group_gap.py:21 | `TAU` | 1 | — | `873eb6b` 2026-09-14 방식 C (간격 일정성 묶기) 구현 · 채점 — 사전등록 수정 1 (ef… | 사전등록 group 수정 1 · GROUPING_LOGIC · RESULTS 4.2 | 정의 | 정수 베이스라인 ±0.5px 양자화에서 간격 ±1px | 둘 다 | — | — |
| group_gap.py:120 | `_owners() · pat` | 2 | — | `873eb6b` 2026-09-14 방식 C (간격 일정성 묶기) 구현 · 채점 — 사전등록 수정 1 (ef… | 사전등록 group 수정 1 · GROUPING_LOGIC | 정의 | 간격 둘(3줄)이 있어야 «같은가» 를 본다 | 둘 다 | — | — |

## `eval/group_score.py`

| 위치 | 이름 | 값 | 같은 역할로 따로 박힌 곳 | 첫 커밋 | 근거 기록 | 분류 | 판단 근거 | 논문 경로 | 갈래 | 근거 후보 |
|---|---|---|---|---|---|---|---|---|---|---|
| eval/group_score.py:33 | `MAIN_LEVELS` | 1.5 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 임의 | 근거 기록 없음 (폐기 세트의 곡선 수준) | 없음 | — | — |
| eval/group_score.py:33 | `MAIN_LEVELS` | 2 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 임의 | 근거 기록 없음 (폐기 세트의 곡선 수준) | 없음 | — | — |
| eval/group_score.py:33 | `MAIN_LEVELS` | 3 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 임의 | 근거 기록 없음 (폐기 세트의 곡선 수준) | 없음 | — | — |
| eval/group_score.py:33 | `MAIN_LEVELS` | 5 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 임의 | 근거 기록 없음 (폐기 세트의 곡선 수준) | 없음 | — | — |
| eval/group_score.py:34 | `LOW_LEVELS` | 0.5 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 임의 | 근거 기록 없음 (폐기 세트의 곡선 수준) | 없음 | — | — |
| eval/group_score.py:34 | `LOW_LEVELS` | 1 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 임의 | 근거 기록 없음 (폐기 세트의 곡선 수준) | 없음 | — | — |
| eval/group_score.py:82 | `SOM_FONT` | 1 | — | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | 주석 | 정의 | Helvetica.ttc 안 Bold 의 번호 | 둘 다 | — | — |
| eval/group_score.py:82 | `SOM_FONT` | 15 | — | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | RESULTS 4.2 (SoM 이미지: «근거 없음») · 사전등록 clean (그림 정의) | 임의 | RESULTS 4.2 에 «근거 없음» | 둘 다 | 실험조건 (SoM — 측정에서 옮김 (2026-09-17)) | — |
| eval/group_score.py:83 | `SOM_LABEL_H` | 18 | — | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | RESULTS 4.2 (SoM 이미지: «근거 없음») · 사전등록 clean (그림 정의) | 임의 | RESULTS 4.2 에 «근거 없음» | 둘 다 | 실험조건 (SoM — 측정에서 옮김 (2026-09-17)) | — |
| eval/group_score.py:112 | `draw_som() · big` | 2 | — | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | RESULTS 4.2 (SoM 이미지: «근거 없음») · 사전등록 clean (그림 정의) | 임의 | RESULTS 4.2 에 «근거 없음» (2배 · 2px) | 둘 다 | 실험조건 (SoM — 측정에서 옮김 (2026-09-17)) | — |
| eval/group_score.py:116 | `draw_som() · outline=` | 30 | — | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | RESULTS 4.2 (SoM 이미지: «근거 없음») · 사전등록 clean (그림 정의) | 임의 | RESULTS 4.2 에 «근거 없음» (색) | 둘 다 | 실험조건 (SoM — 측정에서 옮김 (2026-09-17)) | — |
| eval/group_score.py:116 | `draw_som() · outline=` | 220 | — | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | RESULTS 4.2 (SoM 이미지: «근거 없음») · 사전등록 clean (그림 정의) | 임의 | RESULTS 4.2 에 «근거 없음» (색) | 둘 다 | 실험조건 (SoM — 측정에서 옮김 (2026-09-17)) | — |
| eval/group_score.py:116 | `draw_som() · width=` | 2 | — | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | RESULTS 4.2 (SoM 이미지: «근거 없음») · 사전등록 clean (그림 정의) | 임의 | RESULTS 4.2 에 «근거 없음» (2배 · 2px) | 둘 다 | 실험조건 (SoM — 측정에서 옮김 (2026-09-17)) | — |
| eval/group_score.py:116 | `draw_som() · 식 안` | 2 | eval/group_score.py:112 (2배) | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | 없음 | 정의 | 2배 확대 좌표 | 둘 다 | — | — |
| eval/group_score.py:119 | `draw_som() · tw` | 6 | — | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | 없음 | 임의 | 근거 기록 없음 (딱지 여백) | 둘 다 | 실험조건 (SoM — 측정에서 옮김 (2026-09-17)) | — |
| eval/group_score.py:120 | `draw_som() · bx` | 2 | eval/group_score.py:112 (2배) | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | 없음 | 정의 | 2배 확대 좌표 | 둘 다 | — | — |
| eval/group_score.py:120 | `draw_som() · bx` | 3 | — | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | RESULTS 4.2 (SoM 이미지: «근거 없음») · 사전등록 clean (그림 정의) | 임의 | 근거 기록 없음 (딱지 자리) | 둘 다 | 실험조건 (SoM — 측정에서 옮김 (2026-09-17)) | — |
| eval/group_score.py:120 | `draw_som() · by` | 2 | eval/group_score.py:112 (2배) | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | 없음 | 정의 | 2배 확대 좌표 | 둘 다 | — | — |
| eval/group_score.py:121 | `draw_som() · fill=` | 255 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | RESULTS 4.2 (SoM 이미지: «근거 없음») · 사전등록 clean (그림 정의) | 임의 | RESULTS 4.2 에 «근거 없음» (색) | 둘 다 | 실험조건 (SoM — 측정에서 옮김 (2026-09-17)) | — |
| eval/group_score.py:121 | `draw_som() · outline=` | 30 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | RESULTS 4.2 (SoM 이미지: «근거 없음») · 사전등록 clean (그림 정의) | 임의 | RESULTS 4.2 에 «근거 없음» (색) | 둘 다 | 실험조건 (SoM — 측정에서 옮김 (2026-09-17)) | — |
| eval/group_score.py:121 | `draw_som() · outline=` | 60 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | RESULTS 4.2 (SoM 이미지: «근거 없음») · 사전등록 clean (그림 정의) | 임의 | RESULTS 4.2 에 «근거 없음» (색) | 둘 다 | 실험조건 (SoM — 측정에서 옮김 (2026-09-17)) | — |
| eval/group_score.py:121 | `draw_som() · outline=` | 220 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | RESULTS 4.2 (SoM 이미지: «근거 없음») · 사전등록 clean (그림 정의) | 임의 | RESULTS 4.2 에 «근거 없음» (색) | 둘 다 | 실험조건 (SoM — 측정에서 옮김 (2026-09-17)) | — |
| eval/group_score.py:122 | `draw_som() · fill=` | 30 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | RESULTS 4.2 (SoM 이미지: «근거 없음») · 사전등록 clean (그림 정의) | 임의 | RESULTS 4.2 에 «근거 없음» (색) | 둘 다 | 실험조건 (SoM — 측정에서 옮김 (2026-09-17)) | — |
| eval/group_score.py:122 | `draw_som() · fill=` | 60 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | RESULTS 4.2 (SoM 이미지: «근거 없음») · 사전등록 clean (그림 정의) | 임의 | RESULTS 4.2 에 «근거 없음» (색) | 둘 다 | 실험조건 (SoM — 측정에서 옮김 (2026-09-17)) | — |
| eval/group_score.py:122 | `draw_som() · fill=` | 220 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | RESULTS 4.2 (SoM 이미지: «근거 없음») · 사전등록 clean (그림 정의) | 임의 | RESULTS 4.2 에 «근거 없음» (색) | 둘 다 | 실험조건 (SoM — 측정에서 옮김 (2026-09-17)) | — |
| eval/group_score.py:122 | `draw_som() · 식 안` | 3 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | RESULTS 4.2 (SoM 이미지: «근거 없음») · 사전등록 clean (그림 정의) | 임의 | 근거 기록 없음 (딱지 자리) | 둘 다 | 실험조건 (SoM — 측정에서 옮김 (2026-09-17)) | — |
| eval/group_score.py:134 | `label_overlaps() · boxes` | 2 | eval/group_score.py:112 (2배) | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | 없음 | 정의 | 2배 확대 좌표 | 둘 다 | — | — |
| eval/group_score.py:135 | `label_overlaps() · 식 안` | 0.25 | — | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | 없음 | 임의 | 근거 기록 없음 (딱지 겹침 판정) | 둘 다 | 채점정의 — 사전등록 값 없음 | — |
| eval/group_score.py:136 | `label_overlaps() · 식 안` | 0.25 | — | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | 없음 | 임의 | 근거 기록 없음 (딱지 겹침 판정) | 둘 다 | 채점정의 — 사전등록 값 없음 | — |
| eval/group_score.py:236 | `score_method() · merged` | 2 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 정의 | 과병합 = 참조 블록 둘 이상 | 없음 | — | — |
| eval/group_score.py:278 | `score_method() · norm` | 2 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 임의 | 근거 기록 없음 (상자 여백 2px) | 없음 | — | — |
| eval/group_score.py:290 | `score_method() · F` | 2 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 정의 | F1 식 · 쌍 | 없음 | — | — |
| eval/group_score.py:320 | `meas_summary() · lp` | 100 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 정의 | 퍼센트 환산 | 없음 | — | — |
| eval/group_score.py:324 | `meas_summary() · 절대p90=` | 90 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 정의 | 보고 통계의 백분위 (판정 문턱 아님) | 없음 | — | — |
| eval/group_score.py:324 | `meas_summary() · 절대중앙=` | 50 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 정의 | 보고 통계의 백분위 (판정 문턱 아님) | 없음 | — | — |
| eval/group_score.py:324 | `meas_summary() · 중앙=` | 50 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 정의 | 보고 통계의 백분위 (판정 문턱 아님) | 없음 | — | — |
| eval/group_score.py:325 | `meas_summary() · 절대p90=` | 90 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 정의 | 보고 통계의 백분위 (판정 문턱 아님) | 없음 | — | — |
| eval/group_score.py:325 | `meas_summary() · 절대중앙=` | 50 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 정의 | 보고 통계의 백분위 (판정 문턱 아님) | 없음 | — | — |
| eval/group_score.py:326 | `meas_summary() · 절대p90=` | 90 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 정의 | 보고 통계의 백분위 (판정 문턱 아님) | 없음 | — | — |
| eval/group_score.py:326 | `meas_summary() · 절대중앙=` | 50 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 정의 | 보고 통계의 백분위 (판정 문턱 아님) | 없음 | — | — |
| eval/group_score.py:326 | `meas_summary() · 중앙=` | 50 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 정의 | 보고 통계의 백분위 (판정 문턱 아님) | 없음 | — | — |
| eval/group_score.py:335 | `pass_agreement() · 식 안` | 2 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 정의 | 줄 쌍이 있어야 한다 | 둘 다 | — | — |
| eval/group_score.py:336 | `pass_agreement() · same` | 2 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 정의 | F1 식 · 쌍 | 둘 다 | — | — |
| eval/group_score.py:344 | `pass_agreement() · 블록_F1=` | 2 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 정의 | F1 식 · 쌍 | 둘 다 | — | — |
| eval/group_score.py:434 | `score() · 쌍_주곡선_3줄이상=` | 3 | — | `873eb6b` 2026-09-14 방식 C (간격 일정성 묶기) 구현 · 채점 — 사전등록 수정 1 (ef… | 사전등록 group 수정 1 | 차용 | C 기전의 3줄 조건 | 없음 | — | — |
| eval/group_score.py:435 | `score() · 쌍_1g이하_3줄이상=` | 3 | — | `873eb6b` 2026-09-14 방식 C (간격 일정성 묶기) 구현 · 채점 — 사전등록 수정 1 (ef… | 사전등록 group 수정 1 | 차용 | C 기전의 3줄 조건 | 없음 | — | — |
| eval/group_score.py:451 | `score() · 식 안` | 2 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 정의 | 패스 간 일치에 패스 둘이 필요 | 없음 | — | — |
| eval/group_score.py:496 | `_q() · p25=` | 25 | — | `f71f6de` 2026-09-14 깨끗한 세트 채점 — score-clean · VLM 묶음 나누기 · 실… | 없음 | 정의 | 보고 통계의 백분위 (판정 문턱 아님) | 4장 합성 | — | — |
| eval/group_score.py:497 | `_q() · p75=` | 75 | — | `f71f6de` 2026-09-14 깨끗한 세트 채점 — score-clean · VLM 묶음 나누기 · 실… | 없음 | 정의 | 보고 통계의 백분위 (판정 문턱 아님) | 4장 합성 | — | — |
| eval/group_score.py:511 | `clean_method() · 과병합=` | 2 | — | `f71f6de` 2026-09-14 깨끗한 세트 채점 — score-clean · VLM 묶음 나누기 · 실… | 없음 | 정의 | 과병합 = 참조 블록 둘 이상 | 4장 합성 | — | — |
| eval/group_score.py:543 | `clean_method() · spread` | 2 | — | `f71f6de` 2026-09-14 깨끗한 세트 채점 — score-clean · VLM 묶음 나누기 · 실… | 없음 | 정의 | 묶음 둘 이상에 흩어짐 | 4장 합성 | — | — |
| eval/group_score.py:574 | `clean_blocks() · f` | 2 | — | `f71f6de` 2026-09-14 깨끗한 세트 채점 — score-clean · VLM 묶음 나누기 · 실… | 없음 | 정의 | F1 식 · 쌍 | 4장 합성 | — | — |
| eval/group_score.py:648 | `score_clean() · 식 안` | 2 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 주석: VLM 패스 간 | 정의 | 패스 간 일치에 패스 둘이 필요 | 4장 합성 | — | — |
| eval/group_score.py:718 | `score_clean() · 식 안` | 10 | — | `f71f6de` 2026-09-14 깨끗한 세트 채점 — score-clean · VLM 묶음 나누기 · 실… | 없음 | 정의 | 보고 통계의 백분위 (판정 문턱 아님) | 4장 합성 | — | — |
| eval/group_score.py:718 | `score_clean() · 식 안` | 90 | — | `f71f6de` 2026-09-14 깨끗한 세트 채점 — score-clean · VLM 묶음 나누기 · 실… | 없음 | 정의 | 보고 통계의 백분위 (판정 문턱 아님) | 4장 합성 | — | — |
| eval/group_score.py:749 | `score_clean() · 둘_다_5쌍_이상=` | 5 | — | `f71f6de` 2026-09-14 깨끗한 세트 채점 — score-clean · VLM 묶음 나누기 · 실… | 사전등록 clean («두 쪽이 모두 5쌍 이상») | 임의 | 사전등록의 «5쌍 이상» 을 옮겼다, 값 근거 없음 | 4장 합성 | 채점정의 — 사전등록 고정 (docs/clean_preregister.json · 4c06aa4) | — |
| eval/group_score.py:783 | `clean_verdicts() · ok` | 0.3 | — | `f71f6de` 2026-09-14 깨끗한 세트 채점 — score-clean · VLM 묶음 나누기 · 실… | 사전등록 clean «예측» 문장의 수치 (값만) | 임의 | 사전등록 예측 문장의 수치를 옮겼다, 값 근거 없음 | 4장 합성 | 채점정의 — 사전등록 고정 (docs/clean_preregister.json · 4c06aa4) | — |
| eval/group_score.py:783 | `clean_verdicts() · ok` | 0.5 | — | `f71f6de` 2026-09-14 깨끗한 세트 채점 — score-clean · VLM 묶음 나누기 · 실… | 사전등록 clean «예측» 문장의 수치 (값만) | 임의 | 사전등록 예측 문장의 수치를 옮겼다, 값 근거 없음 | 4장 합성 | 채점정의 — 사전등록 고정 (docs/clean_preregister.json · 4c06aa4) | — |
| eval/group_score.py:783 | `clean_verdicts() · ok` | 0.7 | — | `f71f6de` 2026-09-14 깨끗한 세트 채점 — score-clean · VLM 묶음 나누기 · 실… | 사전등록 clean «예측» 문장의 수치 (값만) | 임의 | 사전등록 예측 문장의 수치를 옮겼다, 값 근거 없음 | 4장 합성 | 채점정의 — 사전등록 고정 (docs/clean_preregister.json · 4c06aa4) | — |
| eval/group_score.py:790 | `clean_verdicts() · 식 안` | 0.5 | — | `f71f6de` 2026-09-14 깨끗한 세트 채점 — score-clean · VLM 묶음 나누기 · 실… | 사전등록 clean «예측» 문장의 수치 (값만) | 임의 | 사전등록 예측 문장의 수치를 옮겼다, 값 근거 없음 | 4장 합성 | 채점정의 — 사전등록 고정 (docs/clean_preregister.json · 4c06aa4) | — |
| eval/group_score.py:798 | `clean_verdicts() · ok` | 0.1 | — | `f71f6de` 2026-09-14 깨끗한 세트 채점 — score-clean · VLM 묶음 나누기 · 실… | 사전등록 clean «예측» 문장의 수치 (값만) | 임의 | 사전등록 예측 문장의 수치를 옮겼다, 값 근거 없음 | 4장 합성 | 채점정의 — 사전등록 고정 (docs/clean_preregister.json · 4c06aa4) | — |
| eval/group_score.py:798 | `clean_verdicts() · ok` | 0.5 | — | `f71f6de` 2026-09-14 깨끗한 세트 채점 — score-clean · VLM 묶음 나누기 · 실… | 사전등록 clean «예측» 문장의 수치 (값만) | 임의 | 사전등록 예측 문장의 수치를 옮겼다, 값 근거 없음 | 4장 합성 | 채점정의 — 사전등록 고정 (docs/clean_preregister.json · 4c06aa4) | — |
| eval/group_score.py:798 | `clean_verdicts() · ok` | 0.9 | — | `f71f6de` 2026-09-14 깨끗한 세트 채점 — score-clean · VLM 묶음 나누기 · 실… | 사전등록 clean «예측» 문장의 수치 (값만) | 임의 | 사전등록 예측 문장의 수치를 옮겼다, 값 근거 없음 | 4장 합성 | 채점정의 — 사전등록 고정 (docs/clean_preregister.json · 4c06aa4) | — |
| eval/group_score.py:801 | `clean_verdicts() · A=` | 0.8 | — | `f71f6de` 2026-09-14 깨끗한 세트 채점 — score-clean · VLM 묶음 나누기 · 실… | 사전등록 clean «예측» 문장의 수치 (값만) | 임의 | 사전등록 예측 문장의 수치를 옮겼다, 값 근거 없음 | 4장 합성 | 채점정의 — 사전등록 고정 (docs/clean_preregister.json · 4c06aa4) | — |
| eval/group_score.py:801 | `clean_verdicts() · C=` | 0.9 | — | `f71f6de` 2026-09-14 깨끗한 세트 채점 — score-clean · VLM 묶음 나누기 · 실… | 사전등록 clean «예측» 문장의 수치 (값만) | 임의 | 사전등록 예측 문장의 수치를 옮겼다, 값 근거 없음 | 4장 합성 | 채점정의 — 사전등록 고정 (docs/clean_preregister.json · 4c06aa4) | — |
| eval/group_score.py:801 | `clean_verdicts() · None=` | 0.9 | — | `f71f6de` 2026-09-14 깨끗한 세트 채점 — score-clean · VLM 묶음 나누기 · 실… | 사전등록 clean «예측» 문장의 수치 (값만) | 임의 | 사전등록 예측 문장의 수치를 옮겼다, 값 근거 없음 | 4장 합성 | 채점정의 — 사전등록 고정 (docs/clean_preregister.json · 4c06aa4) | — |
| eval/group_score.py:807 | `clean_verdicts() · 식 안` | 0.1 | — | `f71f6de` 2026-09-14 깨끗한 세트 채점 — score-clean · VLM 묶음 나누기 · 실… | 사전등록 clean «예측» 문장의 수치 (값만) | 임의 | 사전등록 예측 문장의 수치를 옮겼다, 값 근거 없음 | 4장 합성 | 채점정의 — 사전등록 고정 (docs/clean_preregister.json · 4c06aa4) | — |
| eval/group_score.py:807 | `clean_verdicts() · 식 안` | 0.5 | — | `f71f6de` 2026-09-14 깨끗한 세트 채점 — score-clean · VLM 묶음 나누기 · 실… | 사전등록 clean «예측» 문장의 수치 (값만) | 임의 | 사전등록 예측 문장의 수치를 옮겼다, 값 근거 없음 | 4장 합성 | 채점정의 — 사전등록 고정 (docs/clean_preregister.json · 4c06aa4) | — |
| eval/group_score.py:810 | `clean_verdicts() · 식 안` | 0.05 | — | `f71f6de` 2026-09-14 깨끗한 세트 채점 — score-clean · VLM 묶음 나누기 · 실… | 사전등록 clean «예측» (이 수치는 문장에서 찾지 못함) | 임의 | 예측 판정 문턱, 근거 기록 없음 | 4장 합성 | 채점정의 — 사전등록 고정 (docs/clean_preregister.json · 4c06aa4) | — |
| eval/group_score.py:810 | `clean_verdicts() · 식 안` | 0.1 | — | `f71f6de` 2026-09-14 깨끗한 세트 채점 — score-clean · VLM 묶음 나누기 · 실… | 사전등록 clean «예측» 문장의 수치 (값만) | 임의 | 사전등록 예측 문장의 수치를 옮겼다, 값 근거 없음 | 4장 합성 | 채점정의 — 사전등록 고정 (docs/clean_preregister.json · 4c06aa4) | — |
| eval/group_score.py:826 | `clean_verdicts() · 식 안` | 0.9 | — | `f71f6de` 2026-09-14 깨끗한 세트 채점 — score-clean · VLM 묶음 나누기 · 실… | 사전등록 clean «예측» 문장의 수치 (값만) | 임의 | 사전등록 예측 문장의 수치를 옮겼다, 값 근거 없음 | 4장 합성 | 채점정의 — 사전등록 고정 (docs/clean_preregister.json · 4c06aa4) | — |

## `detector_score.py`

| 위치 | 이름 | 값 | 같은 역할로 따로 박힌 곳 | 첫 커밋 | 근거 기록 | 분류 | 판단 근거 | 논문 경로 | 갈래 | 근거 후보 |
|---|---|---|---|---|---|---|---|---|---|---|
| detector_score.py:27 | `IOU_MIN` | 0.5 | eval/brockmann_stage2_score.py:39 (IOU_MAIN) | `256fdc7` 2026-09-11 검출기 비교 — 사람 상자 v2 와의 일치도로 VLM 이 규칙상 뽑히지만… | 주석 (뜻) · 사전등록 detector («IoU >= 0.5») | 임의 | 사전등록에 값만 있다 | 둘 다 | 채점정의 — 사전등록 고정 (docs/detector_preregister.json · 527656d — 커밋 메시지: 정의는 실행 전, 커밋은 실행 뒤) | — |
| detector_score.py:28 | `INSIDE` | 0.5 | — | `256fdc7` 2026-09-11 검출기 비교 — 사람 상자 v2 와의 일치도로 VLM 이 규칙상 뽑히지만… | 주석: «안에 들었다» 로 보는 넓이 몫 | 임의 | 주석은 뜻만 적었다 | 둘 다 | 채점정의 — 5장 쪽 사전등록 고정 (docs/brockmann_group_preregister.json · ba6c620, «inside ≥ 0.5»). detector_preregister 에는 값 없음 | — |
| detector_score.py:29 | `TOUCH` | 0.1 | — | `256fdc7` 2026-09-11 검출기 비교 — 사람 상자 v2 와의 일치도로 VLM 이 규칙상 뽑히지만… | 주석: «범위 어긋남» 으로 보는 최소 IoU | 임의 | 주석은 뜻만 적었다 | 없음 | — | — |
| detector_score.py:30 | `N_BOOT` | 2000 | eval/brockmann_stage2_score.py:46 (BOOT_N) | `256fdc7` 2026-09-11 검출기 비교 — 사람 상자 v2 와의 일치도로 VLM 이 규칙상 뽑히지만… | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| detector_score.py:32 | `F1_GAP` | 0.05 | — | `256fdc7` 2026-09-11 검출기 비교 — 사람 상자 v2 와의 일치도로 VLM 이 규칙상 뽑히지만… | 주석 «사용자 지정» | 임의 | 주석 «사용자 지정», 값 근거 없음 | 없음 | — | — |
| detector_score.py:97 | `classify() · 식 안` | 2 | — | `256fdc7` 2026-09-11 검출기 비교 — 사람 상자 v2 와의 일치도로 VLM 이 규칙상 뽑히지만… | 없음 | 정의 | 구간 · 과병합 · 과분할 · F1 의 정의상 둘 | 없음 | — | — |
| detector_score.py:111 | `classify() · merged` | 2 | — | `256fdc7` 2026-09-11 검출기 비교 — 사람 상자 v2 와의 일치도로 VLM 이 규칙상 뽑히지만… | 없음 | 정의 | 구간 · 과병합 · 과분할 · F1 의 정의상 둘 | 없음 | — | — |
| detector_score.py:115 | `classify() · 식 안` | 2 | — | `256fdc7` 2026-09-11 검출기 비교 — 사람 상자 v2 와의 일치도로 VLM 이 규칙상 뽑히지만… | 없음 | 정의 | 구간 · 과병합 · 과분할 · F1 의 정의상 둘 | 없음 | — | — |
| detector_score.py:180 | `prf() · f1` | 2 | — | `256fdc7` 2026-09-11 검출기 비교 — 사람 상자 v2 와의 일치도로 VLM 이 규칙상 뽑히지만… | 없음 | 정의 | 구간 · 과병합 · 과분할 · F1 의 정의상 둘 | 없음 | — | — |
| detector_score.py:239 | `boot() · q` | 2.5 | eval/brockmann_stage2_score.py:1093 | `256fdc7` 2026-09-11 검출기 비교 — 사람 상자 v2 와의 일치도로 VLM 이 규칙상 뽑히지만… | 없음 | 정의 | 95% 백분위 구간 | 없음 | — | — |
| detector_score.py:239 | `boot() · q` | 97.5 | eval/brockmann_stage2_score.py:1093 | `256fdc7` 2026-09-11 검출기 비교 — 사람 상자 v2 와의 일치도로 VLM 이 규칙상 뽑히지만… | 없음 | 정의 | 95% 백분위 구간 | 없음 | — | — |
| detector_score.py:309 | `main() · 식 안` | 2 | — | `256fdc7` 2026-09-11 검출기 비교 — 사람 상자 v2 와의 일치도로 VLM 이 규칙상 뽑히지만… | 없음 | 정의 | 구간 · 과병합 · 과분할 · F1 의 정의상 둘 | 없음 | — | — |

## `oracle_group.py`

| 위치 | 이름 | 값 | 같은 역할로 따로 박힌 곳 | 첫 커밋 | 근거 기록 | 분류 | 판단 근거 | 논문 경로 | 갈래 | 근거 후보 |
|---|---|---|---|---|---|---|---|---|---|---|
| oracle_group.py:23 | `OUTSIDE` | 0.5 | — | `032b216` 2026-09-11 오라클 묶기 상한 — 묶기를 완벽히 해도 F1 0.820, 재현율은 줄 … | 주석 (뜻) · 사전등록 oracle («50% 이상») | 임의 | 사전등록에 값만 있다 | 5장 브로크만 | 채점정의 — 사전등록 고정 (docs/oracle_preregister.json · f41f323 — 커밋 메시지: 정의는 실행 전, 커밋은 실행 뒤) | — |
| oracle_group.py:24 | `COVER_X` | 0.5 | — | `032b216` 2026-09-11 오라클 묶기 상한 — 묶기를 완벽히 해도 F1 0.820, 재현율은 줄 … | 주석 (뜻) · 사전등록 oracle («50% 이상») | 임의 | 사전등록에 값만 있다 | 5장 브로크만 | 채점정의 — 사전등록 고정 (docs/oracle_preregister.json · f41f323 — 커밋 메시지: 정의는 실행 전, 커밋은 실행 뒤) | — |
| oracle_group.py:76 | `cause() · how` | 0.8 | eval/brockmann_stage2_score.py:393 | `032b216` 2026-09-11 오라클 묶기 상한 — 묶기를 완벽히 해도 F1 0.820, 재현율은 줄 … | 없음 | 임의 | 서술용 구분, 근거 기록 없음 | 없음 | — | — |
| oracle_group.py:77 | `cause() · how` | 0.8 | eval/brockmann_stage2_score.py:393 | `032b216` 2026-09-11 오라클 묶기 상한 — 묶기를 완벽히 해도 F1 0.820, 재현율은 줄 … | 없음 | 임의 | 서술용 구분, 근거 기록 없음 | 없음 | — | — |

## `eval/synth_gen.py`

| 위치 | 이름 | 값 | 같은 역할로 따로 박힌 곳 | 첫 커밋 | 근거 기록 | 분류 | 판단 근거 | 논문 경로 | 갈래 | 근거 후보 |
|---|---|---|---|---|---|---|---|---|---|---|
| eval/synth_gen.py:34 | `H800` | 800 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | 주석 · RESULTS 4.1 | 차용 | 실물 399 파일 높이 800 | 4장 합성 | — | — |
| eval/synth_gen.py:34 | `W800` | 566 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | 주석 · RESULTS 4.1 | 차용 | 실물 283장 폭 중앙 566 | 4장 합성 | — | — |
| eval/synth_gen.py:35 | `MASTER` | 4 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 | 임의 | RESULTS 4.1 «임의 고정 — 힌팅 회피 (시험 없음)» | 4장 합성 | 실험조건 | — |
| eval/synth_gen.py:36 | `XH_BASE` | 8 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 (실물 근거) | 차용 | 4코퍼스 3줄 이상 블록 x높이 중앙 8 | 4장 합성 | — | — |
| eval/synth_gen.py:37 | `LEAD_RATIO` | 2 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 (실물 근거) | 차용 | 4코퍼스 행간/x높이 중앙 2.0 | 4장 합성 | — | — |
| eval/synth_gen.py:38 | `TITLE_MULT` | 2 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 | 임의 | RESULTS 4.1 템플릿 «임의 고정» | 4장 합성 | 실험조건 | — |
| eval/synth_gen.py:39 | `MARGIN` | 0.04 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 | 차용 | 브로크만 왼쪽 마진 중앙 0.04 (오른쪽에도 같은 상수 — RESULTS 4.1 은 오른쪽을 임의 고정으로 적음) | 4장 합성 | — | — |
| eval/synth_gen.py:40 | `GUTTER` | 0.035 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 | 임의 | RESULTS 4.1 «임의 고정» | 4장 합성 | 실험조건 | — |
| eval/synth_gen.py:41 | `FILL` | 0.6 | eval/clean_phrases.py:105 (FILL_MIN 0.60) | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 | 임의 | RESULTS 4.1 «줄 채우기 임의 고정» | 4장 합성 | 실험조건 | — |
| eval/synth_gen.py:41 | `FILL` | 1 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | 주석: 줄이 단 폭을 채우는 비율 | 정의 | 단 폭을 넘지 않는다 | 4장 합성 | — | — |
| eval/synth_gen.py:42 | `INDEP_RATIOS` | 1.75 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | 주석 · RESULTS 4.1 (실물 근거) | 차용 | 4코퍼스 행간/x높이 25 · 50 · 75% | 4장 합성 | — | — |
| eval/synth_gen.py:42 | `INDEP_RATIOS` | 2 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | 주석 · RESULTS 4.1 (실물 근거) | 차용 | 4코퍼스 행간/x높이 25 · 50 · 75% | 4장 합성 | — | — |
| eval/synth_gen.py:42 | `INDEP_RATIOS` | 2.36 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | 주석 · RESULTS 4.1 (실물 근거) | 차용 | 4코퍼스 행간/x높이 25 · 50 · 75% | 4장 합성 | — | — |
| eval/synth_gen.py:43 | `RANDOM_JITTER` | 0.7 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 | 임의 | RESULTS 4.1 «임의 고정 — 통제 목적» | 4장 합성 | 실험조건 | — |
| eval/synth_gen.py:43 | `RANDOM_JITTER` | 1.3 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 | 임의 | RESULTS 4.1 «임의 고정 — 통제 목적» | 4장 합성 | 실험조건 | — |
| eval/synth_gen.py:44 | `BOTTOM_PAD` | 0.02 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | 주석 (뜻) | 임의 | 근거 기록 없음 | 4장 합성 | 실험조건 | — |
| eval/synth_gen.py:48 | `TEMPLATE` | 2 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 (템플릿 «임의 고정») | 임의 | 템플릿 자리 · 줄 수, RESULTS 4.1 «임의 고정» | 4장 합성 | 실험조건 | — |
| eval/synth_gen.py:48 | `TEMPLATE` | 3 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 (템플릿 «임의 고정») | 임의 | 템플릿 자리 · 줄 수, RESULTS 4.1 «임의 고정» | 4장 합성 | 실험조건 | — |
| eval/synth_gen.py:49 | `TEMPLATE` | 0 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 (템플릿 «임의 고정») | 정의 | 단 번호 · 본문 배수 1 · 행간 1g (템플릿 형식) | 4장 합성 | — | — |
| eval/synth_gen.py:49 | `TEMPLATE` | 1 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 (템플릿 «임의 고정») | 정의 | 본문 x높이 배수 1 · 행간 1g (템플릿 형식) | 4장 합성 | — | — |
| eval/synth_gen.py:49 | `TEMPLATE` | 5 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 (템플릿 «임의 고정») | 임의 | 템플릿 자리 · 줄 수, RESULTS 4.1 «임의 고정» | 4장 합성 | 실험조건 | — |
| eval/synth_gen.py:49 | `TEMPLATE` | 9 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 (템플릿 «임의 고정») | 임의 | 템플릿 자리 · 줄 수, RESULTS 4.1 «임의 고정» | 4장 합성 | 실험조건 | — |
| eval/synth_gen.py:50 | `TEMPLATE` | 0 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 (템플릿 «임의 고정») | 정의 | 단 번호 · 본문 배수 1 · 행간 1g (템플릿 형식) | 4장 합성 | — | — |
| eval/synth_gen.py:50 | `TEMPLATE` | 1 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 (템플릿 «임의 고정») | 정의 | 본문 x높이 배수 1 · 행간 1g (템플릿 형식) | 4장 합성 | — | — |
| eval/synth_gen.py:50 | `TEMPLATE` | 3 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 (템플릿 «임의 고정») | 임의 | 템플릿 자리 · 줄 수, RESULTS 4.1 «임의 고정» | 4장 합성 | 실험조건 | — |
| eval/synth_gen.py:50 | `TEMPLATE` | 16 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 (템플릿 «임의 고정») | 임의 | 템플릿 자리 · 줄 수, RESULTS 4.1 «임의 고정» | 4장 합성 | 실험조건 | — |
| eval/synth_gen.py:51 | `TEMPLATE` | 1 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 (템플릿 «임의 고정») | 정의 | 단 번호 · 본문 배수 1 · 행간 1g (템플릿 형식) | 4장 합성 | — | — |
| eval/synth_gen.py:51 | `TEMPLATE` | 6 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 (템플릿 «임의 고정») | 임의 | 템플릿 자리 · 줄 수, RESULTS 4.1 «임의 고정» | 4장 합성 | 실험조건 | — |
| eval/synth_gen.py:51 | `TEMPLATE` | 8 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 (템플릿 «임의 고정») | 임의 | 템플릿 자리 · 줄 수, RESULTS 4.1 «임의 고정» | 4장 합성 | 실험조건 | — |
| eval/synth_gen.py:52 | `TEMPLATE` | 1 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 (템플릿 «임의 고정») | 정의 | 단 번호 · 본문 배수 1 · 행간 1g (템플릿 형식) | 4장 합성 | — | — |
| eval/synth_gen.py:52 | `TEMPLATE` | 14 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 (템플릿 «임의 고정») | 임의 | 템플릿 자리 · 줄 수, RESULTS 4.1 «임의 고정» | 4장 합성 | 실험조건 | — |
| eval/synth_gen.py:53 | `TEMPLATE` | 1 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 (템플릿 «임의 고정») | 정의 | 단 번호 · 본문 배수 1 · 행간 1g (템플릿 형식) | 4장 합성 | — | — |
| eval/synth_gen.py:53 | `TEMPLATE` | 4 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 (템플릿 «임의 고정») | 임의 | 템플릿 자리 · 줄 수, RESULTS 4.1 «임의 고정» | 4장 합성 | 실험조건 | — |
| eval/synth_gen.py:53 | `TEMPLATE` | 16 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 (템플릿 «임의 고정») | 임의 | 템플릿 자리 · 줄 수, RESULTS 4.1 «임의 고정» | 4장 합성 | 실험조건 | — |
| eval/synth_gen.py:61 | `_hsv() · (r, g, b)` | 360 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | 없음 | 정의 | 색상각 단위 | 4장 합성 | — | — |
| eval/synth_gen.py:62 | `_hsv() · 식 안` | 255 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | 없음 | 정의 | 8비트 최댓값 · 흰 바탕 | 4장 합성 | — | — |
| eval/synth_gen.py:65 | `모듈() · ground=` | 255 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | 없음 | 정의 | 8비트 최댓값 · 흰 바탕 | 4장 합성 | — | — |
| eval/synth_gen.py:66 | `모듈() · ground=` | 0.35 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 | 임의 | RESULTS 4.1 «색값 자체는 임의 고정» | 4장 합성 | 실험조건 | — |
| eval/synth_gen.py:66 | `모듈() · ground=` | 0.72 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 | 임의 | RESULTS 4.1 «색값 자체는 임의 고정» | 4장 합성 | 실험조건 | — |
| eval/synth_gen.py:66 | `모듈() · ground=` | 40 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 | 임의 | RESULTS 4.1 «색값 자체는 임의 고정» | 4장 합성 | 실험조건 | — |
| eval/synth_gen.py:67 | `모듈() · ground=` | 25 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 | 임의 | RESULTS 4.1 «색값 자체는 임의 고정» | 4장 합성 | 실험조건 | — |
| eval/synth_gen.py:67 | `모듈() · ground=` | 28 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 | 임의 | RESULTS 4.1 «색값 자체는 임의 고정» | 4장 합성 | 실험조건 | — |
| eval/synth_gen.py:67 | `모듈() · ink=` | 242 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 | 임의 | RESULTS 4.1 «색값 자체는 임의 고정» | 4장 합성 | 실험조건 | — |
| eval/synth_gen.py:67 | `모듈() · ink=` | 245 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 | 임의 | RESULTS 4.1 «색값 자체는 임의 고정» | 4장 합성 | 실험조건 | — |
| eval/synth_gen.py:70 | `모듈() · jpeg_q=` | 72 | eval/clean_gen.py:70 · :225 · eval/group_gen.py:37 · :151 | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 | 차용 | 실물 399 파일 품질 72 | 4장 합성 | — | — |
| eval/synth_gen.py:70 | `모듈() · resolution=` | 800 | eval/clean_gen.py:69 · eval/group_gen.py:37 | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 | 차용 | 실물 399 파일 높이 800 | 4장 합성 | — | — |
| eval/synth_gen.py:75 | `모듈() · resolution=` | 400 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 | 임의 | RESULTS 4.1 «두 배 · 절반, 임의 고정» | 4장 합성 | 실험조건 | — |
| eval/synth_gen.py:75 | `모듈() · resolution=` | 1600 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 | 임의 | RESULTS 4.1 «두 배 · 절반, 임의 고정» | 4장 합성 | 실험조건 | — |
| eval/synth_gen.py:77 | `모듈() · xh_px_at_800=` | 3 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 | 차용 | 측정 바닥 (ink.lines body_h 4) | 4장 합성 | — | — |
| eval/synth_gen.py:77 | `모듈() · xh_px_at_800=` | 5 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 (실물 근거) | 차용 | 4코퍼스 x높이 25% | 4장 합성 | — | — |
| eval/synth_gen.py:78 | `모듈() · xh_px_at_800=` | 12 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 | 임의 | RESULTS 4.1 에 12 의 근거 없음 (75% 는 14) | 4장 합성 | 실험조건 | — |
| eval/synth_gen.py:78 | `모듈() · xh_px_at_800=` | 18 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 | 정의 | 템플릿이 800px 판에 드는 한계 | 4장 합성 | — | — |
| eval/synth_gen.py:79 | `모듈() · jpeg_q=` | 45 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 | 임의 | RESULTS 4.1 «임의 고정» | 4장 합성 | 실험조건 | — |
| eval/synth_gen.py:79 | `모듈() · jpeg_q=` | 95 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 | 임의 | RESULTS 4.1 «임의 고정» | 4장 합성 | 실험조건 | — |
| eval/synth_gen.py:88 | `_phrase() · 식 안` | 2 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | 없음 | 정의 | 문구 역할 번호 | 4장 합성 | — | — |
| eval/synth_gen.py:89 | `_phrase() · 식 안` | 3 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | 없음 | 정의 | 문구 역할 번호 | 4장 합성 | — | — |
| eval/synth_gen.py:90 | `_phrase() · 식 안` | 4 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | 없음 | 정의 | 문구 역할 번호 | 4장 합성 | — | — |
| eval/synth_gen.py:100 | `_font_info() · probe` | 1000 | eval/clean_gen.py:57 · eval/clean_check.py:101 | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | 없음 | 정의 | em 을 1000 단위로 재는 기준 크기 | 4장 합성 | — | — |
| eval/synth_gen.py:105 | `_font_info() · cap_over_em=` | 1000 | eval/clean_gen.py:57 · eval/clean_check.py:101 | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | 없음 | 정의 | em 을 1000 단위로 재는 기준 크기 | 4장 합성 | — | — |
| eval/synth_gen.py:105 | `_font_info() · xh_over_em=` | 1000 | eval/clean_gen.py:57 · eval/clean_check.py:101 | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | 없음 | 정의 | em 을 1000 단위로 재는 기준 크기 | 4장 합성 | — | — |
| eval/synth_gen.py:110 | `ch() · c` | 255 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | 없음 | 정의 | 8비트 최댓값 · 흰 바탕 | 4장 합성 | — | — |
| eval/synth_gen.py:111 | `ch() · 식 안` | 0.04045 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | 없음 | 정의 | sRGB · WCAG 상대 휘도 · 대비비 공식 | 4장 합성 | — | — |
| eval/synth_gen.py:111 | `ch() · 식 안` | 0.055 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | 없음 | 정의 | sRGB · WCAG 상대 휘도 · 대비비 공식 | 4장 합성 | — | — |
| eval/synth_gen.py:111 | `ch() · 식 안` | 1.055 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | 없음 | 정의 | sRGB · WCAG 상대 휘도 · 대비비 공식 | 4장 합성 | — | — |
| eval/synth_gen.py:111 | `ch() · 식 안` | 2.4 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | 없음 | 정의 | sRGB · WCAG 상대 휘도 · 대비비 공식 | 4장 합성 | — | — |
| eval/synth_gen.py:111 | `ch() · 식 안` | 12.92 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | 없음 | 정의 | sRGB · WCAG 상대 휘도 · 대비비 공식 | 4장 합성 | — | — |
| eval/synth_gen.py:113 | `_lum() · 식 안` | 0.0722 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | 없음 | 정의 | sRGB · WCAG 상대 휘도 · 대비비 공식 | 4장 합성 | — | — |
| eval/synth_gen.py:113 | `_lum() · 식 안` | 0.2126 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | 없음 | 정의 | sRGB · WCAG 상대 휘도 · 대비비 공식 | 4장 합성 | — | — |
| eval/synth_gen.py:113 | `_lum() · 식 안` | 0.7152 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | 없음 | 정의 | sRGB · WCAG 상대 휘도 · 대비비 공식 | 4장 합성 | — | — |
| eval/synth_gen.py:117 | `_gray() · 식 안` | 0.114 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | 주석 «PIL 'L'» | 정의 | ITU-R BT.601 휘도 (PIL «L») | 4장 합성 | — | — |
| eval/synth_gen.py:117 | `_gray() · 식 안` | 0.299 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | 주석 «PIL 'L'» | 정의 | ITU-R BT.601 휘도 (PIL «L») | 4장 합성 | — | — |
| eval/synth_gen.py:117 | `_gray() · 식 안` | 0.587 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | 주석 «PIL 'L'» | 정의 | ITU-R BT.601 휘도 (PIL «L») | 4장 합성 | — | — |
| eval/synth_gen.py:125 | `contrast() · wcag_ratio=` | 0.05 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | 없음 | 정의 | sRGB · WCAG 상대 휘도 · 대비비 공식 | 4장 합성 | — | — |
| eval/synth_gen.py:139 | `fill_line() · 식 안` | 6 | eval/clean_phrases.py:104 (MAX_ATOMS 6) | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | RESULTS 4.1 | 임의 | RESULTS 4.1 «줄 채우기 임의» | 4장 합성 | 실험조건 | — |
| eval/synth_gen.py:173 | `layout() · colw` | 2 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | 없음 | 정의 | 두 단 · 양쪽 여백 | 4장 합성 | — | — |
| eval/synth_gen.py:182 | `layout() · width` | 2 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | 없음 | 정의 | 두 단 · 양쪽 여백 | 4장 합성 | — | — |
| eval/synth_gen.py:187 | `layout() · 식 안` | 3 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | 사전등록 synth | 차용 | 규칙 도출의 «3줄 이상 블록» | 4장 합성 | — | — |
| eval/synth_gen.py:196 | `layout() · 식 안` | 0.25 | eval/synth_gen.py:297 | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | 없음 | 임의 | 근거 기록 없음 (디센더 여유) | 4장 합성 | 실험조건 | — |
| eval/synth_gen.py:199 | `layout() · kind0` | 6 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | 없음 | 정의 | 문구 역할 6개의 순환 | 4장 합성 | — | — |
| eval/synth_gen.py:205 | `layout() · text` | 6 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | 없음 | 정의 | 문구 역할 6개의 순환 | 4장 합성 | — | — |
| eval/synth_gen.py:226 | `TEXT_TRIES` | 50 | — | `3b65e19` 2026-09-16 합성 390장의 획 겹침을 세어 기록한다 — 재생성은 하지 않는다 (사전… | 주석 · 사전등록 synth 수정 2 | 임의 | 사전등록 synth 수정 2 에 값만 (수정 3 에서 재생성 철회) | 없음 | — | — |
| eval/synth_gen.py:227 | `GEO_ROUNDS` | 20 | — | `3b65e19` 2026-09-16 합성 390장의 획 겹침을 세어 기록한다 — 재생성은 하지 않는다 (사전… | 주석 · 사전등록 synth 수정 2 | 임의 | 사전등록 synth 수정 2 에 값만 (수정 3 에서 재생성 철회) | 없음 | — | — |
| eval/synth_gen.py:242 | `_mask() · im` | 4 | — | `3b65e19` 2026-09-16 합성 390장의 획 겹침을 세어 기록한다 — 재생성은 하지 않는다 (사전… | 없음 | 임의 | 근거 기록 없음 (마스크 여백) | 4장 합성 | 채점정의 — 사전등록 값 없음 (synth 수정 2 · 3 은 마스크 교집합만 정의) | — |
| eval/synth_gen.py:243 | `_mask() · fill=` | 255 | — | `3b65e19` 2026-09-16 합성 390장의 획 겹침을 세어 기록한다 — 재생성은 하지 않는다 (사전… | 없음 | 정의 | 8비트 최댓값 · 흰 바탕 | 4장 합성 | — | — |
| eval/synth_gen.py:243 | `_mask() · 식 안` | 2 | — | `3b65e19` 2026-09-16 합성 390장의 획 겹침을 세어 기록한다 — 재생성은 하지 않는다 (사전… | 없음 | 임의 | 근거 기록 없음 (마스크 여백) | 4장 합성 | 채점정의 — 사전등록 값 없음 (synth 수정 2 · 3 은 마스크 교집합만 정의) | — |
| eval/synth_gen.py:244 | `_mask() · 식 안` | 2 | — | `3b65e19` 2026-09-16 합성 390장의 획 겹침을 세어 기록한다 — 재생성은 하지 않는다 (사전… | 없음 | 임의 | 근거 기록 없음 (마스크 여백) | 4장 합성 | 채점정의 — 사전등록 값 없음 (synth 수정 2 · 3 은 마스크 교집합만 정의) | — |
| eval/synth_gen.py:278 | `_refill() · kind0` | 6 | — | `5584e89` 2026-09-12 합성 포스터 생성기 — 정답 JSON 을 함께 쓴다, 경로는 refs.j… | 없음 | 정의 | 문구 역할 6개의 순환 | 없음 | — | — |
| eval/synth_gen.py:280 | `_refill() · b['lines']` | 6 | — | `3b65e19` 2026-09-16 합성 390장의 획 겹침을 세어 기록한다 — 재생성은 하지 않는다 (사전… | 없음 | 정의 | 문구 역할 6개의 순환 | 없음 | — | — |
| eval/synth_gen.py:297 | `_regeo() · 식 안` | 0.25 | eval/synth_gen.py:196 | `3b65e19` 2026-09-16 합성 390장의 획 겹침을 세어 기록한다 — 재생성은 하지 않는다 (사전… | 없음 | 임의 | 근거 기록 없음 (디센더 여유) | 없음 | — | — |
| eval/synth_gen.py:313 | `_min_distance() · _EXT[key]` | 1000 | — | `3b65e19` 2026-09-16 합성 390장의 획 겹침을 세어 기록한다 — 재생성은 하지 않는다 (사전… | 없음 | 정의 | em 을 1000 단위로 재는 기준 크기 | 없음 | — | — |
| eval/synth_gen.py:316 | `_min_distance() · memo[ch]` | 1000 | — | `3b65e19` 2026-09-16 합성 390장의 획 겹침을 세어 기록한다 — 재생성은 하지 않는다 (사전… | 없음 | 정의 | em 을 1000 단위로 재는 기준 크기 | 없음 | — | — |

## `eval/clean_gen.py`

| 위치 | 이름 | 값 | 같은 역할로 따로 박힌 곳 | 첫 커밋 | 근거 기록 | 분류 | 판단 근거 | 논문 경로 | 갈래 | 근거 후보 |
|---|---|---|---|---|---|---|---|---|---|---|
| eval/clean_gen.py:44 | `COLS` | 1 | eval/group_gen.py:24 (COLS) | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | RESULTS 4.2 | 임의 | RESULTS 4.2 «층 — 단 수 임의 고정» | 4장 합성 | 실험조건 | — |
| eval/clean_gen.py:44 | `COLS` | 2 | eval/group_gen.py:24 (COLS) | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | RESULTS 4.2 | 임의 | RESULTS 4.2 «층 — 단 수 임의 고정» | 4장 합성 | 실험조건 | — |
| eval/clean_gen.py:44 | `COLS` | 3 | eval/group_gen.py:24 (COLS) | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | RESULTS 4.2 | 임의 | RESULTS 4.2 «층 — 단 수 임의 고정» | 4장 합성 | 실험조건 | — |
| eval/clean_gen.py:45 | `XH` | 5 | eval/group_gen.py:25 (XH) | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | RESULTS 4.2 (실물 근거) | 차용 | 실물 x높이 25 · 50% | 4장 합성 | — | — |
| eval/clean_gen.py:45 | `XH` | 8 | eval/group_gen.py:25 (XH) | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | RESULTS 4.2 (실물 근거) | 차용 | 실물 x높이 25 · 50% | 4장 합성 | — | — |
| eval/clean_gen.py:45 | `XH` | 12 | eval/group_gen.py:25 (XH) | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | RESULTS 4.2 | 차용 | 합성 통제 실험의 사다리 값 | 4장 합성 | — | — |
| eval/clean_gen.py:46 | `LEVELS` | 0.5 | — | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | RESULTS 4.2 | 임의 | RESULTS 4.2 «임의 고정 (사용자 확정)» | 4장 합성 | 실험조건 | — |
| eval/clean_gen.py:46 | `LEVELS` | 1 | — | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | RESULTS 4.2 | 임의 | RESULTS 4.2 «임의 고정 (사용자 확정)» | 4장 합성 | 실험조건 | — |
| eval/clean_gen.py:46 | `LEVELS` | 1.5 | — | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | RESULTS 4.2 | 임의 | RESULTS 4.2 «임의 고정 (사용자 확정)» | 4장 합성 | 실험조건 | — |
| eval/clean_gen.py:46 | `LEVELS` | 2 | — | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | RESULTS 4.2 | 임의 | RESULTS 4.2 «임의 고정 (사용자 확정)» | 4장 합성 | 실험조건 | — |
| eval/clean_gen.py:46 | `LEVELS` | 2.5 | — | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | RESULTS 4.2 | 임의 | RESULTS 4.2 «임의 고정 (사용자 확정)» | 4장 합성 | 실험조건 | — |
| eval/clean_gen.py:46 | `LEVELS` | 3 | — | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | RESULTS 4.2 | 임의 | RESULTS 4.2 «임의 고정 (사용자 확정)» | 4장 합성 | 실험조건 | — |
| eval/clean_gen.py:46 | `LEVELS` | 4 | — | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | RESULTS 4.2 | 임의 | RESULTS 4.2 «임의 고정 (사용자 확정)» | 4장 합성 | 실험조건 | — |
| eval/clean_gen.py:47 | `LINES` | 3 | — | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | RESULTS 4.2 | 차용 | C 기전의 3줄 조건 | 4장 합성 | — | — |
| eval/clean_gen.py:47 | `LINES` | 8 | — | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | RESULTS 4.2 | 임의 | RESULTS 4.2 «블록당 줄 수 3~8 임의 고정» | 4장 합성 | 실험조건 | — |
| eval/clean_gen.py:57 | `extents() · probe` | 1000 | eval/synth_gen.py:100 | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | 없음 | 정의 | em 을 1000 단위로 재는 기준 크기 | 4장 합성 | — | — |
| eval/clean_gen.py:63 | `extents() · max_ascent_em=` | 1000 | eval/synth_gen.py:100 | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | 없음 | 정의 | em 을 1000 단위로 재는 기준 크기 | 4장 합성 | — | — |
| eval/clean_gen.py:64 | `extents() · max_descender_em=` | 1000 | eval/synth_gen.py:100 | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | 없음 | 정의 | em 을 1000 단위로 재는 기준 크기 | 4장 합성 | — | — |
| eval/clean_gen.py:69 | `condition() · resolution=` | 800 | eval/synth_gen.py:70 | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | RESULTS 4.2 | 차용 | 실물 399 파일 높이 800 | 4장 합성 | — | — |
| eval/clean_gen.py:70 | `condition() · jpeg_q=` | 72 | eval/synth_gen.py:70 · eval/clean_gen.py:70 · :225 | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | RESULTS 4.2 | 차용 | 실물 399 파일 품질 72 | 4장 합성 | — | — |
| eval/clean_gen.py:78 | `distance() · 식 안` | 1e-09 | — | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | 없음 | 정의 | 부동소수 비교 여유 | 4장 합성 | — | — |
| eval/clean_gen.py:96 | `layout() · colw` | 2 | — | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | 없음 | 정의 | 양쪽 여백 | 4장 합성 | — | — |
| eval/clean_gen.py:109 | `layout() · base0` | 2 | — | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | RESULTS 4.2 | 임의 | RESULTS 4.2 «위 여백 2 × 행간 근거 없음» | 4장 합성 | 실험조건 | — |
| eval/clean_gen.py:141 | `layout() · 식 안` | 2 | — | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | RESULTS 4.2 | 임의 | RESULTS 4.2 «블록 최소 수 2 근거 없음» | 4장 합성 | 실험조건 | — |
| eval/clean_gen.py:225 | `main() · quality=` | 72 | eval/synth_gen.py:70 · eval/clean_gen.py:70 · :225 | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | RESULTS 4.2 | 차용 | 실물 399 파일 품질 72 | 4장 합성 | — | — |

## `eval/clean_phrases.py`

| 위치 | 이름 | 값 | 같은 역할로 따로 박힌 곳 | 첫 커밋 | 근거 기록 | 분류 | 판단 근거 | 논문 경로 | 갈래 | 근거 후보 |
|---|---|---|---|---|---|---|---|---|---|---|
| eval/clean_phrases.py:104 | `MAX_ATOMS` | 6 | eval/synth_gen.py:139 (< 6) | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | RESULTS 4.2 | 임의 | RESULTS 4.2 «한 줄 최대 6원자 근거 없음» | 4장 합성 | 실험조건 | — |
| eval/clean_phrases.py:105 | `FILL_MIN` | 0.6 | eval/synth_gen.py:41 (FILL 0.60) | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | RESULTS 4.2 | 임의 | RESULTS 4.2 «60~100% 근거 없음» | 4장 합성 | 실험조건 | — |
| eval/clean_phrases.py:106 | `TRIES` | 40 | eval/synth_gen.py:137 (range(40)) | `4b29a66` 2026-09-14 깨끗한 세트 280장 — 생성기 · 문구 주머니 · 생성 검증 · 표본 … | RESULTS 4.2 | 임의 | RESULTS 4.2 «재시도 최대 40 근거 없음» | 4장 합성 | 실험조건 | — |

## `eval/group_gen.py`

| 위치 | 이름 | 값 | 같은 역할로 따로 박힌 곳 | 첫 커밋 | 근거 기록 | 분류 | 판단 근거 | 논문 경로 | 갈래 | 근거 후보 |
|---|---|---|---|---|---|---|---|---|---|---|
| eval/group_gen.py:23 | `N` | 240 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| eval/group_gen.py:24 | `COLS` | 1 | eval/clean_gen.py:44 (COLS) | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| eval/group_gen.py:24 | `COLS` | 2 | eval/clean_gen.py:44 (COLS) | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| eval/group_gen.py:24 | `COLS` | 3 | eval/clean_gen.py:44 (COLS) | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| eval/group_gen.py:25 | `XH` | 5 | eval/clean_gen.py:45 (XH) | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| eval/group_gen.py:25 | `XH` | 8 | eval/clean_gen.py:45 (XH) | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| eval/group_gen.py:25 | `XH` | 12 | eval/clean_gen.py:45 (XH) | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| eval/group_gen.py:26 | `GAP_LEVELS` | 0.5 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| eval/group_gen.py:26 | `GAP_LEVELS` | 1 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| eval/group_gen.py:26 | `GAP_LEVELS` | 1.5 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| eval/group_gen.py:26 | `GAP_LEVELS` | 2 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| eval/group_gen.py:26 | `GAP_LEVELS` | 3 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| eval/group_gen.py:26 | `GAP_LEVELS` | 5 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| eval/group_gen.py:27 | `MULTS` | 1 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| eval/group_gen.py:27 | `MULTS` | 1.5 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| eval/group_gen.py:27 | `MULTS` | 2.5 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| eval/group_gen.py:28 | `MULT_P` | 0.25 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 주석 (뜻) | 임의 | 주석은 뜻만 적었다 | 없음 | — | — |
| eval/group_gen.py:28 | `MULT_P` | 0.5 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 주석 (뜻) | 임의 | 주석은 뜻만 적었다 | 없음 | — | — |
| eval/group_gen.py:29 | `LINES` | 1 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| eval/group_gen.py:29 | `LINES` | 8 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| eval/group_gen.py:30 | `MAX_BLOCKS` | 8 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 주석 · 사전등록 group | 임의 | 주석: 사전등록 «2~8» 의 상한, 값 근거 없음 | 없음 | — | — |
| eval/group_gen.py:31 | `DESC_EM` | 0.209 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 주석 | 차용 | Helvetica p 디센더 (정답 파일 font 지표와 같은 출처) | 없음 | — | — |
| eval/group_gen.py:37 | `condition() · jpeg_q=` | 72 | eval/synth_gen.py:70 · eval/clean_gen.py:69 · :70 · :225 | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 차용 | 실물 399 파일 높이 800 · 품질 72 (합성 기준 조건) | 없음 | — | — |
| eval/group_gen.py:37 | `condition() · resolution=` | 800 | eval/synth_gen.py:70 · eval/clean_gen.py:69 · :70 · :225 | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 차용 | 실물 399 파일 높이 800 · 품질 72 (합성 기준 조건) | 없음 | — | — |
| eval/group_gen.py:49 | `layout() · colw` | 2 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 정의 | 양쪽 여백 | 없음 | — | — |
| eval/group_gen.py:70 | `layout() · base0` | 2 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| eval/group_gen.py:77 | `layout() · 식 안` | 0.25 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 주석: 위 블록 디센더 바닥과 아래 블록 캡 윗끝이 부딪치면 1g 로 올린다 | 임의 | 주석은 뜻만 적었다 | 없음 | — | — |
| eval/group_gen.py:84 | `layout() · kind0` | 6 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 정의 | 문구 역할 6개의 순환 | 없음 | — | — |
| eval/group_gen.py:87 | `layout() · text` | 6 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 정의 | 문구 역할 6개의 순환 | 없음 | — | — |
| eval/group_gen.py:108 | `layout() · 식 안` | 2 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 임의 | 근거 기록 없음 | 없음 | — | — |
| eval/group_gen.py:151 | `main() · quality=` | 72 | eval/synth_gen.py:70 · eval/clean_gen.py:69 · :70 · :225 | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 차용 | 실물 399 파일 높이 800 · 품질 72 (합성 기준 조건) | 없음 | — | — |
| eval/group_gen.py:159 | `main() · vlm_subset=` | 2 | — | `e36651d` 2026-09-14 묶기 방식 비교 — 240장 세트 · A / VLM Set-of-Mark… | 없음 | 임의 | 근거 기록 없음 (짝수 seed 절반) | 없음 | — | — |

## `eval/brockmann_stage2_score.py`

| 위치 | 이름 | 값 | 같은 역할로 따로 박힌 곳 | 첫 커밋 | 근거 기록 | 분류 | 판단 근거 | 논문 경로 | 갈래 | 근거 후보 |
|---|---|---|---|---|---|---|---|---|---|---|
| eval/brockmann_stage2_score.py:39 | `IOU_MAIN` | 0.5 | detector_score.py:27 (IOU_MIN) | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 사전등록 brockmann_group · 사전등록 brockmann_stage2 | 차용 | detector_score.IOU_MIN (합성 채점과 같은 정의) | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:39 | `IOU_SENS` | 0.3 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 사전등록 brockmann_group | 임의 | 사전등록에 민감도 값만 있다 | 5장 브로크만 | 채점정의 — 사전등록 고정 (docs/brockmann_group_preregister.json · ba6c620) | — |
| eval/brockmann_stage2_score.py:41 | `LINE_TOL` | 0.2 | eval/synth_score.py:38 (LINE_TOL) | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 주석 · 사전등록 brockmann_stage2 | 차용 | synth_score LINE_TOL | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:41 | `LINE_WIN` | 0.5 | eval/synth_score.py:39 (MATCH_WIN) | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 주석 · 사전등록 brockmann_stage2 | 차용 | synth_score MATCH_WIN | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:43 | `SIZE_RATIO` | 1.5 | eval/brockmann_group_explore.py:36 · :37 | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 주석 · 사전등록 brockmann_group 추가 1 | 차용 | 1단계 사전등록 유형 표시 값 | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:43 | `SMALL_H` | 0.6 | eval/brockmann_group_explore.py:36 · :37 | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 주석 · 사전등록 brockmann_group 추가 1 | 차용 | 1단계 사전등록 유형 표시 값 | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:43 | `SMALL_W` | 0.25 | eval/brockmann_group_explore.py:36 · :37 | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 주석 · 사전등록 brockmann_group 추가 1 | 차용 | 1단계 사전등록 유형 표시 값 | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:44 | `MIN_PAIRS` | 10 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 주석 · 사전등록 brockmann_group 추가 1 · 사전등록 brockmann_stage2 | 임의 | 사전등록에 값만 있다 | 5장 브로크만 | 채점정의 — 사전등록 고정 (docs/brockmann_group_preregister.json 추가 1 · 18c6b6e) · (docs/brockmann_stage2_preregister.json · f844621) | — |
| eval/brockmann_stage2_score.py:46 | `BOOT_N` | 2000 | detector_score.py:30 (N_BOOT) | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 사전등록 brockmann_group | 임의 | 사전등록에 값만 있다 (2,000번) | 5장 브로크만 | 채점정의 — 사전등록 고정 (docs/brockmann_group_preregister.json · ba6c620) | — |
| eval/brockmann_stage2_score.py:47 | `SYNTH_DIFF` | 0.017 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 주석 · 사전등록 brockmann_group 추가 1 | 차용 | 합성 깨끗한 세트 층 가중 (VLM − C) 블록 F1 (clean_result) | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:47 | `SYNTH_DIFF` | 0.023 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 주석 · 사전등록 brockmann_group 추가 1 | 차용 | 합성 깨끗한 세트 층 가중 (VLM − C) 블록 F1 (clean_result) | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:48 | `SYNTH_C_FALLBACK` | 0.01 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 주석 · 사전등록 brockmann_stage2 | 차용 | 합성 깨끗한 세트 C 폴백 1.0% (clean_result) | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:49 | `SYNTH_ORACLE` | 1 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 주석 · 사전등록 brockmann_stage2 수정 1 | 차용 | 합성 오라클 1.000 (사용자 서술) | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:91 | `_f1() · 식 안` | 2 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 없음 | 정의 | F1 식 · 과병합 = 둘 이상 | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:199 | `block_L() · 식 안` | 2 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 없음 | 정의 | 간격 · 비교에 값 둘이 필요 | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:203 | `block_L() · 식 안` | 2 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 사전등록 brockmann_stage2 | 차용 | 합성의 한 줄 블록 행간 정의 (2 × x높이) | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:205 | `block_L() · 식 안` | 3 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 없음 | 정의 | 행간 규칙 번호 | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:213 | `poster_L_med() · 식 안` | 2 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 없음 | 정의 | 간격 · 비교에 값 둘이 필요 | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:281 | `consensus_poster() · key=` | 1e+09 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 없음 | 정의 | 정렬 끝으로 보내는 값 | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:342 | `block_counts() · 과병합=` | 2 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 없음 | 정의 | F1 식 · 과병합 = 둘 이상 | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:393 | `cause() · how` | 0.8 | oracle_group.py:76 · :77 | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 사전등록 brockmann_stage2 (oracle 원인 차례) | 차용 | oracle_group.cause 의 서술용 구분 | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:419 | `neighbour_pairs() · lead` | 2 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 없음 | 정의 | 간격 · 비교에 값 둘이 필요 | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:443 | `neighbour_pairs() · cont` | 0.1 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 사전등록 brockmann_group 추가 1 | 임의 | 사전등록 추가 1 «max(1px, 0.1 L)» 의 0.1, 값 근거 없음 (1px 는 τ) | 5장 브로크만 | 채점정의 — 사전등록 고정 (docs/brockmann_group_preregister.json 추가 1 · 18c6b6e) | — |
| eval/brockmann_stage2_score.py:523 | `line_score() · 식 안` | 2 | measure/ink.py:210 (같은 «2행» 기준) | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 사전등록 brockmann_stage2 | 임의 | 사전등록에 값만 있다 (캡선 · 어센더선 차 2행) | 5장 브로크만 | 채점정의 — 사전등록 고정 (docs/brockmann_stage2_preregister.json · f844621) | — |
| eval/brockmann_stage2_score.py:558 | `block_counts_agreed() · 과병합=` | 2 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 없음 | 정의 | F1 식 · 과병합 = 둘 이상 | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:669 | `line_agreed() · 식 안` | 2 | measure/ink.py:210 (같은 «2행» 기준) | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 사전등록 brockmann_stage2 | 임의 | 사전등록에 값만 있다 (캡선 · 어센더선 차 2행) | 5장 브로크만 | 채점정의 — 사전등록 고정 (docs/brockmann_stage2_preregister.json · f844621) | — |
| eval/brockmann_stage2_score.py:689 | `_stats() · 오차_절대_10_90=` | 10 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 없음 | 정의 | 보고 통계의 백분위 (판정 문턱 아님) | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:689 | `_stats() · 오차_절대_10_90=` | 90 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 없음 | 정의 | 보고 통계의 백분위 (판정 문턱 아님) | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:689 | `_stats() · 오차_절대_중앙=` | 50 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 없음 | 정의 | 보고 통계의 백분위 (판정 문턱 아님) | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:689 | `_stats() · 편향_중앙=` | 50 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 없음 | 정의 | 보고 통계의 백분위 (판정 문턱 아님) | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:690 | `_stats() · 행_단위_일치=` | 0.5 | eval/synth_score.py (오차_분포) | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 사전등록 xheight_g1 (필드 정의) | 정의 | \|오차\| ≤ 0.5 = 같은 행 | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:740 | `_diff_row() · 몫_0=` | 0.5 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 없음 | 정의 | 정수 차에서 0 판정 | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:740 | `_diff_row() · 절대_중앙=` | 50 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 없음 | 정의 | 보고 통계의 백분위 (판정 문턱 아님) | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:741 | `_diff_row() · 차_중앙=` | 50 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 없음 | 정의 | 보고 통계의 백분위 (판정 문턱 아님) | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:760 | `agree_summary() · 구간_10_90=` | 10 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 없음 | 정의 | 보고 통계의 백분위 (판정 문턱 아님) | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:760 | `agree_summary() · 구간_10_90=` | 90 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 없음 | 정의 | 보고 통계의 백분위 (판정 문턱 아님) | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:760 | `agree_summary() · 중앙=` | 50 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 없음 | 정의 | 보고 통계의 백분위 (판정 문턱 아님) | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:761 | `agree_summary() · 절대_중앙=` | 50 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 없음 | 정의 | 보고 통계의 백분위 (판정 문턱 아님) | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:761 | `agree_summary() · 중앙=` | 50 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 없음 | 정의 | 보고 통계의 백분위 (판정 문턱 아님) | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:762 | `agree_summary() · 구간_10_90=` | 10 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 없음 | 정의 | 보고 통계의 백분위 (판정 문턱 아님) | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:762 | `agree_summary() · 구간_10_90=` | 90 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 없음 | 정의 | 보고 통계의 백분위 (판정 문턱 아님) | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:768 | `agree_summary() · 구간_10_90=` | 10 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 없음 | 정의 | 보고 통계의 백분위 (판정 문턱 아님) | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:768 | `agree_summary() · 구간_10_90=` | 90 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 없음 | 정의 | 보고 통계의 백분위 (판정 문턱 아님) | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:768 | `agree_summary() · 중앙=` | 50 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 없음 | 정의 | 보고 통계의 백분위 (판정 문턱 아님) | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:1008 | `cmd_score() · VLM_패스간_일치=` | 2 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 없음 | 정의 | 간격 · 비교에 값 둘이 필요 | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:1093 | `cluster() · 구간_95=` | 2.5 | detector_score.py:239 | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 사전등록 brockmann_stage2 | 정의 | 95% 백분위 구간 | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:1093 | `cluster() · 구간_95=` | 97.5 | detector_score.py:239 | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 사전등록 brockmann_stage2 | 정의 | 95% 백분위 구간 | 5장 브로크만 | — | — |
| eval/brockmann_stage2_score.py:1142 | `verdicts() · V['S3 · 라벨러 간 선 위치 차이는 1행 수준 (i)']` | 0.95 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 사전등록 brockmann_stage2 S3 | 임의 | 사전등록 S3 에 값만 (연습판 관찰 서술 동반) | 5장 브로크만 | 채점정의 — 사전등록 고정 (docs/brockmann_stage2_preregister.json · f844621) | — |
| eval/brockmann_stage2_score.py:1146 | `verdicts() · s3[TNAME[t]]` | 0.8 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 사전등록 brockmann_stage2 S3 | 임의 | 사전등록 S3 에 값만 (연습판 관찰 서술 동반) | 5장 브로크만 | 채점정의 — 사전등록 고정 (docs/brockmann_stage2_preregister.json · f844621) | — |
| eval/brockmann_stage2_score.py:1149 | `verdicts() · V['기존 · VLM F1 이 C 보다 0.05 이상 높다']` | 0.05 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 사전등록 brockmann_group «예측» | 임의 | 사전등록 예측 범위 · 문턱, 값 근거 없음 (근거 서술만) | 5장 브로크만 | 채점정의 — 사전등록 고정 (docs/brockmann_group_preregister.json · ba6c620) | — |
| eval/brockmann_stage2_score.py:1151 | `verdicts() · V['기존 · VLM F1 0.60~0.85']` | 0.6 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 사전등록 brockmann_group «예측» | 임의 | 사전등록 예측 범위 · 문턱, 값 근거 없음 (근거 서술만) | 5장 브로크만 | 채점정의 — 사전등록 고정 (docs/brockmann_group_preregister.json · ba6c620) | — |
| eval/brockmann_stage2_score.py:1151 | `verdicts() · V['기존 · VLM F1 0.60~0.85']` | 0.85 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 사전등록 brockmann_group «예측» | 임의 | 사전등록 예측 범위 · 문턱, 값 근거 없음 (근거 서술만) | 5장 브로크만 | 채점정의 — 사전등록 고정 (docs/brockmann_group_preregister.json · ba6c620) | — |
| eval/brockmann_stage2_score.py:1152 | `verdicts() · V['기존 · C F1 0.45~0.75']` | 0.45 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 사전등록 brockmann_group «예측» | 임의 | 사전등록 예측 범위 · 문턱, 값 근거 없음 (근거 서술만) | 5장 브로크만 | 채점정의 — 사전등록 고정 (docs/brockmann_group_preregister.json · ba6c620) | — |
| eval/brockmann_stage2_score.py:1152 | `verdicts() · V['기존 · C F1 0.45~0.75']` | 0.75 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 사전등록 brockmann_group «예측» | 임의 | 사전등록 예측 범위 · 문턱, 값 근거 없음 (근거 서술만) | 5장 브로크만 | 채점정의 — 사전등록 고정 (docs/brockmann_group_preregister.json · ba6c620) | — |
| eval/brockmann_stage2_score.py:1155 | `verdicts() · V['기존 · 짝지은 블록 가운데 C 폴백 몫 ≥ 20%']` | 0.2 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 사전등록 brockmann_group «예측» | 임의 | 사전등록 예측 범위 · 문턱, 값 근거 없음 (근거 서술만) | 5장 브로크만 | 채점정의 — 사전등록 고정 (docs/brockmann_group_preregister.json · ba6c620) | — |
| eval/brockmann_stage2_score.py:1157 | `verdicts() · V['기존 · 라벨러 간 블록 대칭 F1 ≥ 0.80']` | 0.8 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 사전등록 brockmann_group «예측» | 임의 | 사전등록 예측 범위 · 문턱, 값 근거 없음 (근거 서술만) | 5장 브로크만 | 채점정의 — 사전등록 고정 (docs/brockmann_group_preregister.json · ba6c620) | — |
| eval/brockmann_stage2_score.py:1160 | `verdicts() · V['기존 · 오라클 0.75~0.92']` | 0.75 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 사전등록 brockmann_group «예측» | 임의 | 사전등록 예측 범위 · 문턱, 값 근거 없음 (근거 서술만) | 5장 브로크만 | 채점정의 — 사전등록 고정 (docs/brockmann_group_preregister.json · ba6c620) | — |
| eval/brockmann_stage2_score.py:1160 | `verdicts() · V['기존 · 오라클 0.75~0.92']` | 0.92 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 사전등록 brockmann_group «예측» | 임의 | 사전등록 예측 범위 · 문턱, 값 근거 없음 (근거 서술만) | 5장 브로크만 | 채점정의 — 사전등록 고정 (docs/brockmann_group_preregister.json · ba6c620) | — |
| eval/brockmann_stage2_score.py:1185 | `verdicts() · V['기존 · Surya 줄 기준 C 폴백 몫 ≥ 25%']` | 0.25 | — | `5405b17` 2026-09-16 브로크만 2단계 채점기 — 사전등록 f844621 · 수정 1 21a61… | 사전등록 brockmann_group «예측» | 임의 | 사전등록 예측 범위 · 문턱, 값 근거 없음 (근거 서술만) | 5장 브로크만 | 채점정의 — 사전등록 고정 (docs/brockmann_group_preregister.json · ba6c620) | — |

## 임의 · 논문 경로 146행 — 갈래와 근거 후보 (같은 역할은 한 행으로 묶음)

- **갈래:** **실험조건** = 합성 생성기가 만드는 조건의 값. **채점정의** = 채점 · 통계 정의 값 — 결과 산출 전 사전등록에 적힌 값이면 «사전등록 고정 (파일 · 커밋)» 을 함께 적는다 (사전등록 문구가 처음 들어온 커밋을 `git log -S` 로 찾고, 결과 파일의 첫 커밋보다 앞서는지 확인했다). **측정** = 파이프라인이 이미지에서 값을 뽑는 데 쓰는 값 (VLM 입력 그림 SoM 포함).
- **근거 후보 (측정 갈래만):** 강한 순서 — 정의·물리 유도 > 라벨 없는 실물 관찰 (라벨링 세트 50장을 뺀 실물 판) > 합성 스윕 (새 seed 합성 세트) > 차용. 가능해 보이는 것 가운데 가장 강한 하나와 이유 한 줄. 판단이 어려우면 «미정».
- **묶기:** 같은 역할로 여러 곳에 박힌 값은 한 행으로 묶고 위치를 모두 적었다. 146행 밖의 같은 역할 위치는 괄호로 표시했다.

### 갈래별 행 수

| 갈래 | 원래 행 | 묶은 행 |
|---|---|---|
| 측정 | 39 | 32 |
| 채점정의 | 43 | 27 |
| 실험조건 | 64 | 25 |
| 합 | 146 | 84 |

### 측정

| 위치 | 이름 | 값 | 논문 경로 | 영향을 주는 출력 | 논문 수치 무관 | 근거 후보 | 이유 |
|---|---|---|---|---|---|---|---|
| measure/ink.py:16 | FRAG_WIDE | 0.4 | 둘 다 | ink.lines 글줄 분할 → bases · xtops · caps · 블록 n · box_ink · C 요소(→ C 묶음) | — | 라벨 없는 실물 관찰 | 실물 판에서 조각과 글줄의 폭 비 분포가 두 봉우리로 갈리는지 잴 수 있음 |
| measure/ink.py:18 · measure/probe.py:78 | FRAG_COVER | 0.35 | 둘 다 | ink.lines 글줄 분할 → bases · xtops · caps · 블록 n · box_ink · C 요소(→ C 묶음) | — | 라벨 없는 실물 관찰 | 주석의 한 판 관찰(점 0.12 · 글줄 0.63~0.92)을 여러 판의 채움 분포로 넓힐 수 있음 |
| measure/ink.py:44 · measure/ink.py:142 · measure/probe.py:30 | lines · descender 의 min_h | 2 | 둘 다 | ink.lines 글줄 분할 → bases · xtops · caps · 블록 n · box_ink · C 요소(→ C 묶음) / descender: desc (글줄 사전에만, region 출력 없음) | — | 정의·물리 유도 | 안티에일리어싱으로 흐린 가장자리 한 행과 몸통 한 행을 합친 최소 높이로 유도할 수 있음 |
| measure/ink.py:44 | lines(… body_h=) | 4 | 둘 다 | ink.lines 글줄 분할 → bases · xtops · caps · 블록 n · box_ink · C 요소(→ C 묶음) | — | 합성 스윕 | x높이 3 · 5 셀처럼 작은 활자 조건에서 값을 훑어 평평한 구간을 볼 수 있음 |
| measure/ink.py:129 | baseline(… frac=) | 0.5 | 둘 다 | bases | — | 정의·물리 유도 | 행 잉크가 몸통의 절반 — 픽셀 덮임 절반이라는 측정 약속으로 둘 수 있음 (라벨 규칙 «절반 넘게 진하면» 과 같은 꼴) |
| measure/ink.py:142 | descender(… depth=) | 6 | 둘 다 | desc (글줄 사전에만, region 출력 없음) | 논문 수치 무관 | 정의·물리 유도 | 글꼴 디센더 비율(em)과 활자 크기에서 px 로 유도할 수 있음 |
| measure/ink.py:42 · baseline/skew.py:39 (경로 없음) | threshold() · 배경 × 0.72 | 0.72 | 둘 다 | 잉크 마스크 → bases · xtops · caps · box_ink · C 요소(→ C 묶음) | — | 정의·물리 유도 | 배경 · 잉크 밝기와 픽셀 덮임 비율에서 문턱을 유도할 수 있음 |
| measure/ink.py:37 | polarity() 꼬리 백분위 | 5 · 95 | 둘 다 | 극성 뒤집기 여부 → 잉크 마스크 → bases · xtops · caps · box_ink · C 요소(→ C 묶음) | — | 라벨 없는 실물 관찰 | 창 안 활자 화소 몫의 분포를 실물에서 재 꼬리 백분위를 정할 수 있음 |
| measure/ink.py:50 · measure/probe.py:46 · baseline/detect.py:114 (경로 없음) · baseline/detect.py:182 (경로 없음) | lines() · peak 백분위 | 90 | 둘 다 | ink.lines 글줄 분할 → bases · xtops · caps · 블록 n · box_ink · C 요소(→ C 묶음) | — | 라벨 없는 실물 관찰 | 실물 글줄의 행 잉크량 분포에서 최댓값 대용 백분위를 정할 수 있음 |
| measure/ink.py:51 · measure/probe.py:47 | lines() · on 백분위 | 5 | 둘 다 | ink.lines 글줄 분할 → bases · xtops · caps · 블록 n · box_ink · C 요소(→ C 묶음) | — | 라벨 없는 실물 관찰 | 배경 행 잉크량 분포를 실물에서 잴 수 있음 |
| measure/ink.py:210 | split_marks() · 어센더 2행 | 2 | 둘 다 | caps (x높이선보다 2행 미만 위면 None) | — | 정의·물리 유도 | 어센더 − x높이 글꼴 비율 × 활자 크기와 가장자리 한 행에서 유도할 수 있음 |
| measure/ink.py:98 | lines() · 발음기호 small | 0.5 | 둘 다 | 발음기호 흡수 → 글줄 수 · bases · xtops | — | 정의·물리 유도 | 점 · 악센트 높이의 글꼴 비율에서 유도할 수 있음 |
| measure/ink.py:101 | lines() · 발음기호 틈 최소 | 3 | 둘 다 | 발음기호 흡수 → 글줄 수 · bases · xtops | — | 정의·물리 유도 | 점 · 악센트와 몸통 사이 거리의 글꼴 비율에서 유도할 수 있음 |
| measure/ink.py:101 | lines() · 발음기호 틈 비 | 0.6 | 둘 다 | 발음기호 흡수 → 글줄 수 · bases · xtops | — | 정의·물리 유도 | 점 · 악센트와 몸통 사이 거리의 글꼴 비율에서 유도할 수 있음 |
| measure/ink.py:187 | split_marks() · 되돌림 어깨 | 0.5 | 둘 다 | xtops (G1 에 해당 덩어리가 없을 때) | — | 합성 스윕 | 되돌림이 쓰이는 줄을 합성 정답으로 모아 값을 훑을 수 있음 |
| measure/region.py:30 | region.PAD | 3 | 둘 다 | 측정 창 → bases · xtops · caps · box_ink · C 요소(→ C 묶음) | — | 합성 스윕 | pad 검증 사전등록(measure_pad)과 같은 방식으로 값을 훑을 수 있음 |
| measure/region.py:31 | region.ALIGN_EPS | 3.0 | 둘 다 | align · align_spread (rules 정렬 지표) | 논문 수치 무관 | 라벨 없는 실물 관찰 | 실물 블록 줄 왼쪽 끝의 흩어짐 분포를 잴 수 있음 |
| measure/region.py:78 | measure() · 최소 창 | 4 | 둘 다 | 측정 실패 (n_lines 0) → 블록 누락 | — | 정의·물리 유도 | min_h 2 에 가장자리를 더한 최소 창으로 유도할 수 있음 |
| measure/grid.py:13 · measure/grid.py:44 | fit_grid · apply_grid 최소 줄 수 | 3 | 둘 다 | region lead · grid_resid (캐시 블록 필드 bases · caps · xtops · lead 에는 들어가지 않음) | 논문 수치 무관 | 정의·물리 유도 | 격자 주기를 보려면 간격 둘 이상이 필요하다는 조건으로 유도할 수 있음 |
| measure/grid.py:21 | fit_grid() · 최소 구간 길이 | 3 | 둘 다 | region lead · grid_resid (캐시 블록 필드 bases · caps · xtops · lead 에는 들어가지 않음) | 논문 수치 무관 | 미정 | 프로파일 구간 길이의 뜻이 코드에 적혀 있지 않음 |
| measure/grid.py:27 | fit_grid() · 자기상관 창 | 5 · 60 | 둘 다 | region lead · grid_resid (캐시 블록 필드 bases · caps · xtops · lead 에는 들어가지 않음) | 논문 수치 무관 | 라벨 없는 실물 관찰 | 실물 행간(px) 분포에서 탐색 창을 정할 수 있음 |
| measure/grid.py:35 | fit_grid() · 실측과의 차 | 2 | 둘 다 | region lead · grid_resid (캐시 블록 필드 bases · caps · xtops · lead 에는 들어가지 않음) | 논문 수치 무관 | 정의·물리 유도 | 정수 베이스라인 양자화에서 간격 차 허용을 유도할 수 있음 (τ 1px 와 같은 방식) |
| measure/grid.py:46 | apply_grid() · 위 · 아래 여유 | 20 · 8 | 둘 다 | region lead · grid_resid (캐시 블록 필드 bases · caps · xtops · lead 에는 들어가지 않음) | 논문 수치 무관 | 정의·물리 유도 | 첫 줄 위 캡 높이 · 마지막 줄 아래 디센더의 글꼴 비율에서 유도할 수 있음 |
| measure/grid.py:31 | fit_grid() · 봉우리 문턱 | 0.25 | 둘 다 | region lead · grid_resid (캐시 블록 필드 bases · caps · xtops · lead 에는 들어가지 않음) | 논문 수치 무관 | 합성 스윕 | 합성 격자 공유 · 독립 셀에서 값을 훑어 평평한 구간을 볼 수 있음 |
| detect_surya.py:25 | detect_surya.X_OVER | 0.15 | 둘 다 | A 묶음 · C 사슬(→ C 묶음) | — | 라벨 없는 실물 관찰 | 같은 단 줄끼리의 가로 겹침 몫 분포를 실물에서 잴 수 있음 |
| detect_surya.py:28 | detect_surya.MIN_AREA | 200 | 둘 다 | A 묶음(블록 상자 → 측정 창 → bases · xtops · caps) · C 폴백 묶음 | — | 라벨 없는 실물 관찰 | Surya 상자 넓이 분포에서 부스러기 봉우리를 잴 수 있음 |
| detect_surya.py:24 | detect_surya.H_RATIO | 0.60 · 1.70 | 둘 다 | A 묶음(블록 상자 → 측정 창 → bases · xtops · caps) · C 폴백 묶음 | — | 라벨 없는 실물 관찰 | 이웃 줄 높이 비 분포에서 크기 계층 봉우리를 잴 수 있음 |
| detect_surya.py:26 | detect_surya.Y_GAP | −0.40 · 1.60 | 둘 다 | A 묶음(블록 상자 → 측정 창 → bases · xtops · caps) · C 폴백 묶음 | — | 라벨 없는 실물 관찰 | 세로 틈 ÷ 줄 높이 분포에서 줄 사이 · 블록 사이 봉우리를 잴 수 있음 |
| detect_surya.py:81 | detect_surya.COL_GAP | 0.02 | 둘 다 | n_columns | 논문 수치 무관 | 라벨 없는 실물 관찰 | 실물 판에서 줄이 안 걸친 세로 띠 폭 분포를 잴 수 있음 |
| detect_surya.py:82 | detect_surya.COL_MIN | 0.05 | 둘 다 | n_columns | 논문 수치 무관 | 라벨 없는 실물 관찰 | 실물 판에서 단 폭 분포의 작은 봉우리(쪽번호 등)를 잴 수 있음 |
| detect_surya.py:83 | detect_surya.COL_H | 1.6 | 둘 다 | n_columns | 논문 수치 무관 | 라벨 없는 실물 관찰 | 실물 판에서 표제 줄 높이 ÷ 중앙값 분포를 잴 수 있음 |
| detect_surya.py:86 | detect_surya.COL_W | 0.75 | 둘 다 | n_columns | 논문 수치 무관 | 라벨 없는 실물 관찰 | 실물 판에서 가로지르는 줄 폭 ÷ 판 폭 분포를 잴 수 있음 |

### 채점정의

| 위치 | 이름 | 값 | 논문 경로 | 사전등록 |
|---|---|---|---|---|
| eval/group_score.py:783 | clean_verdicts · A 병합률 구간 | 0.5 · 0.3~0.7 | 4장 합성 | 사전등록 고정 (docs/clean_preregister.json · 4c06aa4) |
| eval/group_score.py:790 | clean_verdicts · VLM 병합률 구간 | 0.5 | 4장 합성 | 사전등록 고정 (docs/clean_preregister.json · 4c06aa4) |
| eval/group_score.py:798 | clean_verdicts · C 병합률 구간 | 0.90 · 0.5 · 0.10 | 4장 합성 | 사전등록 고정 (docs/clean_preregister.json · 4c06aa4) |
| eval/group_score.py:801 | clean_verdicts · c_in 세 방식 병합 | A 0.80 · C 0.90 · VLM 0.90 | 4장 합성 | 사전등록 고정 (docs/clean_preregister.json · 4c06aa4) |
| eval/group_score.py:807 | clean_verdicts · x높이 5 · c 0.5 의 C | 0.10~0.50 · 0.10 | 4장 합성 | 사전등록 고정 (docs/clean_preregister.json · 4c06aa4) |
| eval/group_score.py:810 | clean_verdicts · C 폴백 몫 | 0.05 · 0.10 | 4장 합성 | 사전등록 고정 (docs/clean_preregister.json · 4c06aa4) |
| eval/group_score.py:826 | clean_verdicts · VLM 패스 간 블록 F1 | 0.90 | 4장 합성 | 사전등록 고정 (docs/clean_preregister.json · 4c06aa4) |
| eval/group_score.py:749 | score_clean · 둘 다 5쌍 이상 | 5 | 4장 합성 | 사전등록 고정 (docs/clean_preregister.json · 4c06aa4) |
| eval/group_score.py:135 · eval/group_score.py:136 | label_overlaps · SoM 딱지 겹침 확인 | 0.25 | 둘 다 | 사전등록 값 없음 |
| detector_score.py:27 · eval/brockmann_stage2_score.py:39 (IOU_MAIN, 차용) | detector_score.IOU_MIN | 0.5 | 둘 다 | 사전등록 고정 (docs/detector_preregister.json · 527656d — 커밋 메시지: 정의는 실행 전, 커밋은 실행 뒤) |
| detector_score.py:28 | detector_score.INSIDE | 0.5 | 둘 다 | 5장 쪽 사전등록 고정 (docs/brockmann_group_preregister.json · ba6c620, «inside ≥ 0.5»). detector_preregister 에는 값 없음 |
| oracle_group.py:23 · oracle_group.py:24 | oracle_group.OUTSIDE · COVER_X | 0.5 · 0.5 | 5장 브로크만 | 사전등록 고정 (docs/oracle_preregister.json · f41f323 — 커밋 메시지: 정의는 실행 전, 커밋은 실행 뒤) |
| eval/brockmann_stage2_score.py:44 | MIN_PAIRS | 10 | 5장 브로크만 | 사전등록 고정 (docs/brockmann_group_preregister.json 추가 1 · 18c6b6e) · (docs/brockmann_stage2_preregister.json · f844621) |
| eval/brockmann_stage2_score.py:39 | IOU_SENS | 0.3 | 5장 브로크만 | 사전등록 고정 (docs/brockmann_group_preregister.json · ba6c620) |
| eval/brockmann_stage2_score.py:46 · detector_score.py:30 (N_BOOT, 경로 없음) | BOOT_N | 2000 | 5장 브로크만 | 사전등록 고정 (docs/brockmann_group_preregister.json · ba6c620) |
| eval/brockmann_stage2_score.py:523 · eval/brockmann_stage2_score.py:669 | 캡선 · 어센더선 차 2행 | 2 | 5장 브로크만 | 사전등록 고정 (docs/brockmann_stage2_preregister.json · f844621) |
| eval/brockmann_stage2_score.py:1146 | S3 (ii) 방향 몫 | 0.80 | 5장 브로크만 | 사전등록 고정 (docs/brockmann_stage2_preregister.json · f844621) |
| eval/brockmann_stage2_score.py:1142 | S3 (i) \|차\| ≤ 1행 몫 | 0.95 | 5장 브로크만 | 사전등록 고정 (docs/brockmann_stage2_preregister.json · f844621) |
| eval/brockmann_stage2_score.py:1152 | 예측 · C F1 범위 | 0.45~0.75 | 5장 브로크만 | 사전등록 고정 (docs/brockmann_group_preregister.json · ba6c620) |
| eval/brockmann_stage2_score.py:1155 | 예측 · 짝지은 블록 C 폴백 몫 | 0.20 | 5장 브로크만 | 사전등록 고정 (docs/brockmann_group_preregister.json · ba6c620) |
| eval/brockmann_stage2_score.py:1157 | 예측 · 라벨러 간 블록 대칭 F1 | 0.80 | 5장 브로크만 | 사전등록 고정 (docs/brockmann_group_preregister.json · ba6c620) |
| eval/brockmann_stage2_score.py:1160 | 예측 · 오라클 범위 | 0.75~0.92 | 5장 브로크만 | 사전등록 고정 (docs/brockmann_group_preregister.json · ba6c620) |
| eval/brockmann_stage2_score.py:1185 | 예측 · Surya 줄 C 폴백 몫 | 0.25 | 5장 브로크만 | 사전등록 고정 (docs/brockmann_group_preregister.json · ba6c620) |
| eval/brockmann_stage2_score.py:1149 | 예측 · VLM − C F1 차 | 0.05 | 5장 브로크만 | 사전등록 고정 (docs/brockmann_group_preregister.json · ba6c620) |
| eval/brockmann_stage2_score.py:1151 | 예측 · VLM F1 범위 | 0.60~0.85 | 5장 브로크만 | 사전등록 고정 (docs/brockmann_group_preregister.json · ba6c620) |
| eval/brockmann_stage2_score.py:443 | 간격 이어짐 0.1 × L | 0.1 | 5장 브로크만 | 사전등록 고정 (docs/brockmann_group_preregister.json 추가 1 · 18c6b6e) |
| eval/synth_gen.py:242 · eval/synth_gen.py:243 · eval/synth_gen.py:244 | synth_gen._mask · 획 겹침 마스크 여백 | 4 · 2 · 2 | 4장 합성 | 사전등록 값 없음 (synth 수정 2 · 3 은 마스크 교집합만 정의) |

### 실험조건

| 위치 | 이름 | 값 | 논문 경로 |
|---|---|---|---|
| eval/group_score.py:112 | draw_som() · 확대 배율 — SoM — 측정에서 옮김 (2026-09-17) | 2 | 둘 다 |
| eval/group_score.py:116 | draw_som() · 줄 상자 선 두께 — SoM — 측정에서 옮김 (2026-09-17) | 2 | 둘 다 |
| eval/group_score.py:82 | SOM_FONT 크기 — SoM — 측정에서 옮김 (2026-09-17) | 15 | 둘 다 |
| eval/group_score.py:83 | SOM_LABEL_H — SoM — 측정에서 옮김 (2026-09-17) | 18 | 둘 다 |
| eval/group_score.py:116 · eval/group_score.py:121 · eval/group_score.py:122 | draw_som() · 색 — SoM — 측정에서 옮김 (2026-09-17) | 상자 (220,30,30) · 딱지 바탕 255 · 딱지 테두리 · 글자 (30,60,220) | 둘 다 |
| eval/group_score.py:119 · eval/group_score.py:120 · eval/group_score.py:122 | draw_som() · 딱지 여백 · 자리 — SoM — 측정에서 옮김 (2026-09-17) | 6 · 3 · 3 | 둘 다 |
| eval/synth_gen.py:35 | synth_gen.MASTER | 4 | 4장 합성 |
| eval/synth_gen.py:38 | synth_gen.TITLE_MULT | 2.0 | 4장 합성 |
| eval/synth_gen.py:40 | synth_gen.GUTTER | 0.035 | 4장 합성 |
| eval/synth_gen.py:44 · eval/clean_gen.py:48 · eval/group_gen.py:32 (import) | synth_gen.BOTTOM_PAD | 0.02 | 4장 합성 |
| eval/synth_gen.py:41 · eval/clean_phrases.py:105 | 줄 채우기 하한 (FILL · FILL_MIN) | 0.60 | 4장 합성 |
| eval/synth_gen.py:43 | synth_gen.RANDOM_JITTER | 0.70 · 1.30 | 4장 합성 |
| eval/synth_gen.py:48 · eval/synth_gen.py:49 · eval/synth_gen.py:50 · eval/synth_gen.py:51 · eval/synth_gen.py:52 · eval/synth_gen.py:53 | synth_gen.TEMPLATE 자리 · 줄 수 | T 3 · 2 / A 9 · 5 / C 16 · 3 / B 6 · 8 / E 14 / D 16 · 4 | 4장 합성 |
| eval/synth_gen.py:75 | synth_gen 해상도 셀 | 1600 · 400 | 4장 합성 |
| eval/synth_gen.py:78 | synth_gen x높이 셀 | 12 | 4장 합성 |
| eval/synth_gen.py:79 | synth_gen JPEG 셀 | 95 · 45 | 4장 합성 |
| eval/synth_gen.py:139 · eval/clean_phrases.py:104 | 한 줄 최대 문구 수 (fill_line · MAX_ATOMS) | 6 | 4장 합성 |
| eval/synth_gen.py:66 · eval/synth_gen.py:67 | synth_gen 극성 색값 | 유색 HSV(40, 0.35, 0.72) · 어두운 (25,25,28) + (245,245,242) | 4장 합성 |
| eval/synth_gen.py:196 · eval/synth_gen.py:297 (경로 없음) | synth_gen 디센더 여유 | 0.25 | 4장 합성 |
| eval/clean_gen.py:44 · eval/group_gen.py:24 (경로 없음) | clean_gen.COLS | 1 · 2 · 3 | 4장 합성 |
| eval/clean_gen.py:46 | clean_gen.LEVELS | 0.5 · 1.0 · 1.5 · 2.0 · 2.5 · 3.0 · 4.0 | 4장 합성 |
| eval/clean_gen.py:47 | clean_gen.LINES 상한 | 8 | 4장 합성 |
| eval/clean_gen.py:141 | clean_gen 블록 최소 수 | 2 | 4장 합성 |
| eval/clean_gen.py:109 | clean_gen 위 여백 | 2 × 행간 | 4장 합성 |
| eval/clean_phrases.py:106 · eval/synth_gen.py:137 (range(40)) | clean_phrases.TRIES | 40 | 4장 합성 |

## 측정 출력 — 논문 보고 여부 (2026-09-17)

- **읽은 것:** docs/RESULTS_FOR_PAPER.md, 4장 결과 파일 (docs/synth_result.json · docs/clean_result.json), 5장 채점 정의 (docs/brockmann_stage2_preregister.json 과 그 채점기). 코드에서 각 출력이 캐시 필드 · 채점 입력으로 쓰이는지 따라갔다 (ground._block 필드 x1 · y1 · x2 · y2 · n · xh · lead · bases · caps · xtops, 판 필드 n_columns).
- **«논문 수치 무관»:** 측정 행의 영향 출력이 모두 «안 됨» 인 행.

| 출력 | 4장 합성 | 5장 브로크만 |
|---|---|---|
| bases | 보고됨 — RESULTS 1절 표 1 베이스라인 · 표 1-참고 · 표 2 ① ② ③ (docs/synth_result.json 선_직접_짝 · 규칙) | 보고됨 — 2단계 사전등록 «선 채점» 베이스라인 |
| xtops | 보고됨 — 표 1 x높이선 | 보고됨 — «선 채점» x높이선 |
| caps | 보고됨 — 표 1 상단 잉크선 · 상단 잉크 높이, 표 2 ① ③ | 보고됨 — «선 채점» 상단 잉크선 · 숫자만 있는 글줄 |
| 블록 상자 (box_ink) | 보고됨 — 표 1-참고 블록 짝짓기, 표 1 직접 짝의 측정 블록 가로 범위 | 보고됨 — «선 채점» 후보의 측정 블록 가로 범위 |
| A 묶음 | 보고됨 — 표 1-참고 블록 재현 · 과병합 (파이프라인 블록 = A), 2절 표 4~6 · 9 의 A | 보고됨 — 2단계 블록 채점 A (기준선) |
| C 묶음 | 보고됨 — 2절 표 4~8 · 10 의 C | 보고됨 — 2단계 블록 채점 C · 예측 |
| lead (region 격자 lead, fit_grid) | 안 됨 — 캐시 블록 필드에 없음. 채점의 행간은 참값 | 안 됨 |
| 블록 lead (lead_measured) | 안 됨 — 캐시에 있으나 채점 · 규칙 ① 은 bases 로 계산 | 안 됨 |
| grid_resid | 안 됨 — region 출력만 | 안 됨 |
| align | 안 됨 — region 출력만, 캐시에 없음 | 안 됨 |
| n_columns | 안 됨 — 캐시에 있으나 check_layout 은 부분 배치에서 판 단위 지표를 판정하지 않음. 2절 표 5 의 단 수는 생성 조건 | 안 됨 — 2단계 사전등록 · 채점기에 없음. docs/brockmann_group_preregister.json «층 · 칸 (서술용)» 의 단 수는 고정 파일 docs/labeling/selection.json 값 |
| desc | 안 됨 — 글줄 사전에만, region 출력 없음 | 안 됨 |

## 섞임 공간 — 합성 생성기 렌더 경로 (2026-09-17 확인)

- **읽은 코드:** eval/synth_gen.py render (348~357), eval/clean_gen.py:223 · eval/group_gen.py:149 (둘 다 synth_gen.render 를 부름). 저장소 .py 에 감마 · 선형광 · sRGB 변환 코드 없음 (grep). Pillow 10.4.0 · FreeType 2.13.2 · raqm 없음 (basic 배치).
- **실험:** 저장소 밖에서 같은 Pillow 로 확인 (탐색용 · 논문 수치 아님).

| 단계 | 코드 | 섞는 공간 | 확인 |
|---|---|---|---|
| 글자 래스터 | ImageDraw.text → FreeType 덮임 비트맵 (8비트) | 면적 덮임 (감마 없음) | Helvetica 12 · 20 · 32px 세 문구: 1배 덮임 총량 ÷ 16배 렌더 면적 총량 0.91~1.14. 덮임에 감마 2.2 가 들었다고 보면 0.68~0.95. 힌팅으로 흔들림 |
| 글자 · 바탕 섞기 | Image.new('RGB', 바탕) 위 d.text(fill=잉크), 4배 마스터 | sRGB 인코딩값 — 값 = 바탕 + (잉크 − 바탕) × 덮임 | 부분 덮임 2,124 화소: 인코딩값 섞기와의 차 평균 0.00 · 0.26 · 0.25, 선형광 섞기와의 차 평균 52.0 · 36.3 · 34.5 (흰+검 · 유색+검 · 어두운+밝은) |
| 4배 → 출력 축소 | im.resize(…, LANCZOS) | sRGB 인코딩값 | 0 · 255 가 한 행씩 번갈아 든 판을 절반으로: 평균 127.0 ('L' · 'RGB' 같음). 인코딩값 평균 127.5, 선형광 평균을 되돌린 값 187.5 |
| 저장 | im.save('JPEG', quality, subsampling=0) | 인코딩값 (RGB → YCbCr) | 확인 안 함 — libjpeg 표준 동작 |
| 측정 쪽 회색조 | Image.convert('L') (measure_corpus · region 입력) | 인코딩값에 0.299 · 0.587 · 0.114 가중 | RGB(184,162,119) → 164 = 인코딩값 가중합 |

## 섞임 공간 판별 탐색 — 종료 (2026-09-17)

- **성격:** 탐색용 · 논문 수치 아님. 저장소 밖 세션 scratchpad 의 mix/ 에서만 돌렸고 커밋하지 않았다.
- **파일:** mixcheck.py (가장자리 u 통계) · verify_synth.py · verify_synth.json · synth/ (seed 7001~7015, 생성기 그대로와 선형광 렌더 변형) · minimal.py · minimal.json · minimal/ (seed 7101~7110, 사각형 16배 마스터 · box · PNG) · bias_stages.py · bias_stages.json · stages/ (편향 진단, 단계 더하기 LANCZOS · JPEG · 글자, seed 7101~7120).
- **결론:** 판별 불가 — 글자 단계(2(iii)) 흰 바탕 · 검정에서 두 렌더의 인코딩 u 기준값 차 0.0041 로 «가르는가» 불통과. 잉크 문턱 0.72 의 근거와 무관하다.

## 근거 계획 초안 — 측정 갈래 (실행하지 않음, 2026-09-17 고침)

- **의존 순서:** 1 = 섞임 공간 (위 절) · e · 잉크 문턱 → 2 = 정의 유도 → 3 = 새 마스크 위 실물 관찰 → 4 = 합성 스윕. A 상수 4개 (X_OVER · MIN_AREA · H_RATIO · Y_GAP) 는 «병행» — Surya 줄 상자만 쓰고 잉크 마스크에 기대지 않는다. «—» = 논문 수치 무관.
- **논문 수치 무관 12행:** 계획을 적지 않는다 («무관» 표시만).
- **공통 — 라벨 없는 실물 관찰:** 판 = 네 코퍼스 코어 측정 대상에서 라벨링 main 50장 · 연습 2장을 뺀 222장 (브로크만 71 · 호프만 108 · 로제 16 · 루더 27, remeasure.keys_of 기준). Surya 줄은 이 222장에 새로 뽑아 새 파일에 둔다 — ~/.typo-mcp/brockmann50/lines.json 은 쓰지 않는다. KDE = 가우스 커널, 대역폭은 Silverman 규칙 h = 0.9 × min(σ, IQR ÷ 1.34) × n^(−1/5) (통계마다 자료에서 계산), 값 격자 h/20. 두 봉우리 = 국소 최댓값 둘 이상, 둘째 봉우리 높이 ≥ 가장 높은 봉우리의 5%. 값 = 가장 높은 두 봉우리 사이 밀도 최솟점. 두 봉우리가 아니면 Otsu 두 무리 문턱, 두 무리 분리도 η² < 0.5 이면 그 상수는 합성 스윕으로 넘긴다 — 격자는 현재 값 × {0.50, 0.75, 1.00, 1.25, 1.50} 의 5점 (정수 상수는 반올림, 겹친 점은 하나로), 지표는 그 상수가 영향을 주는 선 종류(베이스라인 · x높이선 · 상단 잉크선)의 재현율, 평평 · 결정은 합성 스윕 공통 규칙.
- **공통 — 합성 스윕:** 한 번에 한 상수만 훑고 나머지는 지금 값에 둔다. 평평 = 지표가 최적값에서 δ 안인 격자 점들의 연속 구간, 값 = 그 구간 가운데 격자 점. δ = 0.02 (모든 합성 스윕). 생성 뒤 사람 확인 (CLAUDE.md 규칙 9) 다음에 채점.
- **4장 재실행 계획:** (b) 선형광 렌더 강건성 조건 1행 — 합성 통제 실험 셀 구성에 렌더만 선형광 섞기 · 축소 · sRGB 복귀로 바꾼 조건을 1행 더한다. (b) 경로 (scratchpad mix/verify_synth.py 의 render_linear) 를 eval/ 로 옮길 계획만 적는다 — 아직 옮기지 않았다.
- **seed 구간:** 합성 스윕 = 7001~7999 (새로 만든다). 섞임 공간 탐색에 쓴 7001~7015 · 7101~7120 은 다시 쓰지 않고, 잉크 문턱 스윕은 7201~ 에서 시작한다. 4장 재실행 = 기존 평가 세트 seed 그대로 — 합성 통제 실험 1~30 (docs/synth_manifest.json) · 깨끗한 세트 3001~3718 (docs/clean_manifest.json). 이미 쓴 seed: 합성 진단 101~110 · 묶기 비교 240장 1~240 · pad 검증 개발 901~960 · 검증 2001~2060 · [4] 설계 5001~5040 — 둘 다 이 구간과 겹치지 않는다.
- **공통 — 정의·물리 유도:** 글꼴 비율(em)은 합성 글꼴 Helvetica 를 1000px 로 잰 값으로 초안을 쓴다. «식 꼴 변경» = 지금의 px 고정값이나 배경 비례식이 다른 꼴의 식이 된다.
- **region.PAD 분류 확인:** docs/measure_pad_preregister.json (2eac80c) · docs/measure_pad_result.json (ab59911) 는 pad 규칙 비교 (고정 PAD 3 대 P1 · P2 · P1+P2 · P1a) 이고 «PAD 3 (기존 measure/region.PAD) 만 쓴다» 고 적었다. PAD 값을 훑지 않았으므로 분류 «임의» 를 바꾸지 않았다.
- **한계 (계획):** 섞임 공간은 판별하지 못했다 (위 «섞임 공간 판별 탐색 — 종료»). e 등 밝기 통계는 인코딩값 공간 (현재 파이프라인과 같음) 을 가정한다. 정의·물리 유도의 글꼴 비율은 Helvetica 에서만 잰다.
- **다시 만들 산출물:** 코드 경로로만 판단했다. «파이프라인 캐시 4개» = ~/.typo-mcp/{brockmann, corpus, rose, ruder}.json.

| 순서 | 위치 | 이름 | 값 | 논문 수치 무관 | 근거 후보 | 계획 초안 | 식 꼴 변경 | 다시 만들 산출물 |
|---|---|---|---|---|---|---|---|---|
| 1 | — (새 값, 식에서 쓰임: min_h · 어센더 2행 · 발음기호 틈 최소) | e (가장자리 번짐 행 수) | — (새 값) | — | 라벨 없는 실물 관찰 | 판: 공통 222장, Surya 줄 새로 뽑음. 창 = Surya 줄 상자 + PAD, 극성 맞춤, 섞임 공간 = 인코딩값 공간 (현재 파이프라인과 같음, 한계에 기록). 열마다 세로 밝기 프로파일에서 가장자리 = 배경 평탄 구간과 잉크 평탄 구간 (각각 연속 2행 이상) 사이의 전이. u = (v − 배경 수준) ÷ (잉크 수준 − 배경 수준), 배경 수준 = 창 밝기 중앙값, 잉크 수준 = 잉크 문턱 행과 같은 분위. 폭 = u 가 0.1 을 지나는 자리와 0.9 를 지나는 자리 사이의 행 수 (이웃 행 사이 선형 보간). 위 · 아래 가장자리를 모두 센다. e = ⌈모든 폭의 중앙값⌉ | — | e 를 쓰는 식 (min_h · 어센더 2행 · 발음기호 틈 최소) 의 산출물을 따른다 |
| 1 | measure/ink.py:42 · baseline/skew.py:39 (경로 없음) | threshold() · 배경 × 0.72 | 0.72 | — | 합성 스윕 | 세트: 새 seed 7201~, 셀 구성은 4장 측정 실험(합성 통제 실험, docs/synth_manifest.json 의 13셀)과 같다, 현재 생성기 그대로. 격자: threshold 의 곱 k = 0.50~0.90, 0.02 간격. 지표: 베이스라인 · x높이선 · 상단 잉크선 재현율 (표 1 직접 짝 정의). 평평: 선 종류마다 최고 재현율 − 0.02 안의 연속 구간. 결정: 0.72 가 세 선 종류 모두의 평평 구간 안이면 유지, 아니면 세 구간의 교집합 가운데 격자 점으로 바꾼다. 교집합이 없으면 멈추고 보고한다. 보조 서술 (근거 아님): 흰 바탕 · 검정 글자에서 선형광 기준 절반 덮임은 배경 × 0.735 근처. baseline/skew.py:39 의 0.72 는 같은 값으로 따라간다 | — | 파이프라인 캐시 4개 (remeasure → measure_corpus → ground.entry) · 합성 캐시 synth-*.json → docs/synth_result.json · docs/clean_result.json · docs/clean_c_diag.json · docs/measure_pad_result.json (group_gap.elements · measure_pad_check → region.measure) · 봉인 docs/brockmann_group_explore.json (group_gap.elements) (baseline/skew.py 는 경로 없음) |
| 2 | measure/ink.py:44 · measure/ink.py:142 · measure/probe.py:30 | lines · descender 의 min_h | 2 | — | 정의·물리 유도 | 식: min_h = e + 1. e = 가장자리 번짐 행 수 (e 행, 순서 1) | — | 파이프라인 캐시 4개 (remeasure → measure_corpus → ground.entry) · 합성 캐시 synth-*.json → docs/synth_result.json · docs/clean_result.json · docs/clean_c_diag.json · docs/measure_pad_result.json (group_gap.elements · measure_pad_check → region.measure) · 봉인 docs/brockmann_group_explore.json (group_gap.elements) (descender 쪽은 없음) |
| 2 | measure/ink.py:129 | baseline(… frac=) | 0.5 | — | 정의·물리 유도 | 식: 베이스라인 = (행 잉크 칸 수 ≥ frac × 글줄 최대 행 잉크 칸 수 인 마지막 행) + 1, frac = 덮임 절반 0.5 (라벨 요청서 6절 «절반 넘게 진하면» 과 같은 약속으로 둠) | — | 파이프라인 캐시 4개 · 합성 캐시 → docs/synth_result.json · docs/clean_result.json · docs/clean_c_diag.json (C 요소 베이스라인) · 봉인 docs/brockmann_group_explore.json |
| 2 | measure/ink.py:210 | split_marks() · 어센더 2행 | 2 | — | 정의·물리 유도 | 식: 문턱 = max(e + 1, ⌊(어센더_em − x높이_em) ÷ x높이_em × x높이_px ÷ 2⌋). Helvetica b d h k l 윗끝 0.717~0.719em, x 0.523em → 0.37 × x높이. e = 가장자리 번짐 행 수 (e 행, 순서 1) | 식 꼴 변경 | 파이프라인 캐시 4개 · 합성 캐시 → docs/synth_result.json (caps 는 C 요소에 들어가지 않음) |
| 2 | measure/ink.py:98 | lines() · 발음기호 small | 0.5 | — | 정의·물리 유도 | 식: small = 점 · 악센트 덩어리 높이_em ÷ 몸통 높이_em 의 Helvetica 실측 최댓값 | — | 파이프라인 캐시 4개 (remeasure → measure_corpus → ground.entry) · 합성 캐시 synth-*.json → docs/synth_result.json · docs/clean_result.json · docs/clean_c_diag.json · docs/measure_pad_result.json (group_gap.elements · measure_pad_check → region.measure) · 봉인 docs/brockmann_group_explore.json (group_gap.elements) |
| 2 | measure/ink.py:101 | lines() · 발음기호 틈 최소 | 3 | — | 정의·물리 유도 | 식: 틈 최소 = ⌈(점 아래끝 − x높이선)_em ÷ x높이_em × x높이_px⌉ + e | 식 꼴 변경 | 파이프라인 캐시 4개 (remeasure → measure_corpus → ground.entry) · 합성 캐시 synth-*.json → docs/synth_result.json · docs/clean_result.json · docs/clean_c_diag.json · docs/measure_pad_result.json (group_gap.elements · measure_pad_check → region.measure) · 봉인 docs/brockmann_group_explore.json (group_gap.elements) |
| 2 | measure/ink.py:101 | lines() · 발음기호 틈 비 | 0.6 | — | 정의·물리 유도 | 식: 틈 비 = (점 아래끝 − x높이선)_em ÷ 몸통 높이_em 의 Helvetica 실측 최댓값 | — | 파이프라인 캐시 4개 (remeasure → measure_corpus → ground.entry) · 합성 캐시 synth-*.json → docs/synth_result.json · docs/clean_result.json · docs/clean_c_diag.json · docs/measure_pad_result.json (group_gap.elements · measure_pad_check → region.measure) · 봉인 docs/brockmann_group_explore.json (group_gap.elements) |
| 2 | measure/region.py:78 | measure() · 최소 창 | 4 | — | 정의·물리 유도 | 식: 최소 창 = 2 × min_h (띠 하나 = min_h 행, 위 · 아래 가장자리) | — | 파이프라인 캐시 4개 (remeasure → measure_corpus → ground.entry) · 합성 캐시 synth-*.json → docs/synth_result.json · docs/clean_result.json · docs/clean_c_diag.json · docs/measure_pad_result.json (group_gap.elements · measure_pad_check → region.measure) · 봉인 docs/brockmann_group_explore.json (group_gap.elements) |
| 3 | measure/ink.py:16 | FRAG_WIDE | 0.4 | — | 라벨 없는 실물 관찰 | 통계: 창마다 ink.lines 가 만든 띠 가운데 이웃 글줄이 있는 띠의 폭 ÷ 이웃 글줄 폭 (FRAG_WIDE 판정 전 값, 0~1). KDE (Silverman) 공통 규칙으로 최솟점. 대체: 공통 규칙 | — | 파이프라인 캐시 4개 (remeasure → measure_corpus → ground.entry) · 합성 캐시 synth-*.json → docs/synth_result.json · docs/clean_result.json · docs/clean_c_diag.json · docs/measure_pad_result.json (group_gap.elements · measure_pad_check → region.measure) · 봉인 docs/brockmann_group_explore.json (group_gap.elements) |
| 3 | measure/ink.py:18 · measure/probe.py:78 | FRAG_COVER | 0.35 | — | 라벨 없는 실물 관찰 | 통계: 같은 띠의 제 폭 안 잉크 칸 몫 (FRAG_COVER 판정 전 값, 0~1). KDE (Silverman) 최솟점. 대체: 공통 규칙 | — | 파이프라인 캐시 4개 (remeasure → measure_corpus → ground.entry) · 합성 캐시 synth-*.json → docs/synth_result.json · docs/clean_result.json · docs/clean_c_diag.json · docs/measure_pad_result.json (group_gap.elements · measure_pad_check → region.measure) · 봉인 docs/brockmann_group_explore.json (group_gap.elements) |
| 3 | measure/ink.py:37 | polarity() 꼬리 백분위 | 5 · 95 | — | 라벨 없는 실물 관찰 | 통계: 창마다 활자 화소 몫 (극성 맞춘 뒤 문턱 아래 화소 ÷ 창 화소). 값: 공통 규칙을 따른다 | — | 파이프라인 캐시 4개 (remeasure → measure_corpus → ground.entry) · 합성 캐시 synth-*.json → docs/synth_result.json · docs/clean_result.json · docs/clean_c_diag.json · docs/measure_pad_result.json (group_gap.elements · measure_pad_check → region.measure) · 봉인 docs/brockmann_group_explore.json (group_gap.elements) |
| 3 | measure/ink.py:50 · measure/probe.py:46 · baseline/detect.py:114 (경로 없음) · baseline/detect.py:182 (경로 없음) | lines() · peak 백분위 | 90 | — | 라벨 없는 실물 관찰 | 통계: 창마다 잉크가 있는 행의 행 잉크량 ÷ 그 행들의 중앙값. 값: KDE (Silverman) 로 두 봉우리 (몸통 행 · 테두리 · 가로줄 같은 튀는 행) 사이 최솟점 위의 몫 q, 백분위 = 100 × (1 − q). 대체: 공통 규칙 | — | 파이프라인 캐시 4개 (remeasure → measure_corpus → ground.entry) · 합성 캐시 synth-*.json → docs/synth_result.json · docs/clean_result.json · docs/clean_c_diag.json · docs/measure_pad_result.json (group_gap.elements · measure_pad_check → region.measure) · 봉인 docs/brockmann_group_explore.json (group_gap.elements) (measure/probe.py · baseline/detect.py 는 경로 없음) |
| 3 | measure/ink.py:51 · measure/probe.py:47 | lines() · on 백분위 | 5 | — | 라벨 없는 실물 관찰 | 통계: 창 행 잉크량 ÷ 창 최대 행 잉크량 (배경 행 · 글자 행). KDE (Silverman) 최솟점 v*, 값 = v* 를 넘는 첫 백분위. 대체: 공통 규칙 | — | 파이프라인 캐시 4개 (remeasure → measure_corpus → ground.entry) · 합성 캐시 synth-*.json → docs/synth_result.json · docs/clean_result.json · docs/clean_c_diag.json · docs/measure_pad_result.json (group_gap.elements · measure_pad_check → region.measure) · 봉인 docs/brockmann_group_explore.json (group_gap.elements) |
| 4 | measure/ink.py:44 | lines(… body_h=) | 4 | — | 합성 스윕 | 격자 {2, 3, 4, 5, 6}. 셀: 새 seed xh_3 · xh_5 · base 각 30장. 지표: 표 1 베이스라인 직접 짝 재현율 · 정밀도 (셀 평균). 평평: 두 지표 모두 최적 − δ 안 | — | 파이프라인 캐시 4개 (remeasure → measure_corpus → ground.entry) · 합성 캐시 synth-*.json → docs/synth_result.json · docs/clean_result.json · docs/clean_c_diag.json · docs/measure_pad_result.json (group_gap.elements · measure_pad_check → region.measure) · 봉인 docs/brockmann_group_explore.json (group_gap.elements) |
| 4 | measure/ink.py:187 | split_marks() · 되돌림 어깨 | 0.5 | — | 합성 스윕 | 격자 {0.3, 0.4, 0.5, 0.6, 0.7}. 셀: 새 seed base · xh_5 · xh_12, G1 되돌림이 쓰인 줄만 센다. 지표: x높이선 «참값과 같은 행» 몫. 평평: 최적 − δ 안 | — | 파이프라인 캐시 4개 · 합성 캐시 → docs/synth_result.json · docs/clean_result.json · docs/clean_c_diag.json (C 요소 x높이 — 공유 요소 판정) · 봉인 docs/brockmann_group_explore.json |
| 4 | measure/region.py:30 | region.PAD | 3 | — | 합성 스윕 | 격자 {1, 2, 3, 4, 5, 6}. 셀: 새 seed base · xh_18 과 깨끗한 세트 층 셋. 지표: 표 1 베이스라인 · 상단 잉크선 재현율, 깨끗한 세트 C 블록 F1. 평평: 세 지표 모두 최적 − δ 안 | — | 파이프라인 캐시 4개 (remeasure → measure_corpus → ground.entry) · 합성 캐시 synth-*.json → docs/synth_result.json · docs/clean_result.json · docs/clean_c_diag.json · docs/measure_pad_result.json (group_gap.elements · measure_pad_check → region.measure) · 봉인 docs/brockmann_group_explore.json (group_gap.elements) |
| 병행 | detect_surya.py:25 | detect_surya.X_OVER | 0.15 | — | 라벨 없는 실물 관찰 | 통계: 세로 이웃 줄 쌍 (사이에 다른 줄 없음) 의 가로 겹침 ÷ 좁은 쪽 폭 (0~1). KDE (Silverman) 두 봉우리 (다른 단 · 같은 단) 최솟점. 대체: 공통 규칙 | — | 파이프라인 캐시 4개 (boxes_norm → 측정 창) · 합성 캐시 → docs/synth_result.json · docs/clean_result.json · docs/clean_a_sweep.json · docs/clean_c_diag.json · 봉인 docs/brockmann_group_explore.json (C 사슬 · C 폴백) |
| 병행 | detect_surya.py:28 | detect_surya.MIN_AREA | 200 | — | 라벨 없는 실물 관찰 | 통계: Surya 줄 상자 넓이 log10(px², 800px 판으로 환산). KDE (Silverman) 두 봉우리 (부스러기 · 글줄) 최솟점. 대체: 공통 규칙 | — | 파이프라인 캐시 4개 (boxes_norm → 측정 창) · 합성 캐시 → docs/synth_result.json · docs/clean_result.json · docs/clean_a_sweep.json · docs/clean_c_diag.json · 봉인 docs/brockmann_group_explore.json (C 사슬 · C 폴백) |
| 병행 | detect_surya.py:24 | detect_surya.H_RATIO | 0.60 · 1.70 | — | 라벨 없는 실물 관찰 | 통계: 세로 이웃 줄 쌍 (가로 겹침 > X_OVER) 의 log(큰 높이 ÷ 작은 높이). KDE (Silverman) 두 봉우리 (같은 크기 · 다른 크기) 최솟점 r*, 값 = (e^−r*, e^r*). 대체: 공통 규칙 | — | 파이프라인 캐시 4개 (boxes_norm → 측정 창) · 합성 캐시 → docs/synth_result.json · docs/clean_result.json · docs/clean_a_sweep.json · docs/clean_c_diag.json · 봉인 docs/brockmann_group_explore.json (C 사슬 · C 폴백) |
| 병행 | detect_surya.py:26 | detect_surya.Y_GAP | −0.40 · 1.60 | — | 라벨 없는 실물 관찰 | 통계: 같은 쌍의 세로 틈 ÷ 위 줄 높이. 상한 = KDE (Silverman) 두 봉우리 (줄 사이 · 블록 사이) 최솟점, 하한 = 음수 쪽 1% 분위. 대체: 공통 규칙 | — | 파이프라인 캐시 4개 (boxes_norm → 측정 창) · 합성 캐시 → docs/synth_result.json · docs/clean_result.json · docs/clean_a_sweep.json · docs/clean_c_diag.json · 봉인 docs/brockmann_group_explore.json (C 사슬 · C 폴백) |
| — | measure/ink.py:142 | descender(… depth=) | 6 | 무관 | — | — | — | — |
| — | measure/region.py:31 | region.ALIGN_EPS | 3.0 | 무관 | — | — | — | — |
| — | measure/grid.py:13 · measure/grid.py:44 | fit_grid · apply_grid 최소 줄 수 | 3 | 무관 | — | — | — | — |
| — | measure/grid.py:21 | fit_grid() · 최소 구간 길이 | 3 | 무관 | — | — | — | — |
| — | measure/grid.py:27 | fit_grid() · 자기상관 창 | 5 · 60 | 무관 | — | — | — | — |
| — | measure/grid.py:35 | fit_grid() · 실측과의 차 | 2 | 무관 | — | — | — | — |
| — | measure/grid.py:46 | apply_grid() · 위 · 아래 여유 | 20 · 8 | 무관 | — | — | — | — |
| — | measure/grid.py:31 | fit_grid() · 봉우리 문턱 | 0.25 | 무관 | — | — | — | — |
| — | detect_surya.py:81 | detect_surya.COL_GAP | 0.02 | 무관 | — | — | — | — |
| — | detect_surya.py:82 | detect_surya.COL_MIN | 0.05 | 무관 | — | — | — | — |
| — | detect_surya.py:83 | detect_surya.COL_H | 1.6 | 무관 | — | — | — | — |
| — | detect_surya.py:86 | detect_surya.COL_W | 0.75 | 무관 | — | — | — | — |

## 난수 seed (표에서 뺌)

| 위치 | 값 | 코드 |
|---|---|---|
| detector_score.py:31 | 20260911 | `SEED = 20260911` |
| eval/brockmann_stage2_score.py:46 | 20260914 | `BOOT_N, BOOT_SEED = 2000, 20260914` |
| eval/clean_gen.py:36 | 3001 | `SEED0 = 3001` |
| eval/clean_gen.py:38 | 9 | `SEEDS = list(range(SEED0, SEED0 + 189)) + [3196 + 9 * k for k in range(39)]` |
| eval/clean_gen.py:38 | 3196 | `SEEDS = list(range(SEED0, SEED0 + 189)) + [3196 + 9 * k for k in range(39)]` |
| eval/clean_gen.py:40 | 9 | `SEEDS += ([3547 + 9 * k for k in range(20)]     # 1단 · 12px 60 → 80` |
| eval/clean_gen.py:40 | 3547 | `SEEDS += ([3547 + 9 * k for k in range(20)]     # 1단 · 12px 60 → 80` |
| eval/clean_gen.py:41 | 9 | `+ [3544 + 9 * k for k in range(19)]   # 1단 · 8px 21 → 40` |
| eval/clean_gen.py:41 | 3544 | `+ [3544 + 9 * k for k in range(19)]   # 1단 · 8px 21 → 40` |
| eval/clean_gen.py:42 | 9 | `+ [3539 + 9 * k for k in range(12)]   # 2단 · 12px 21 → 33` |
| eval/clean_gen.py:42 | 3539 | `+ [3539 + 9 * k for k in range(12)]   # 2단 · 12px 21 → 33` |
| eval/clean_gen.py:43 | 3540 | `+ [3540])                             # 3단 · 12px 21 → 22` |
| eval/synth_gen.py:334 | 1 | `_refill(lay, {p[0] for p in pairs} \| {p[2] for p in pairs}, np.random.RandomState([seed, 1` |
| eval/synth_gen.py:340 | 2 | `_regeo(lay, cond, np.random.RandomState([seed, 2, rnd_round]))` |
