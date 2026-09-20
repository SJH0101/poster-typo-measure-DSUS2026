# 재현 확인 기록 (2026-09-20)

이 저장소를 GitHub 에서 clone 하고, Python 3.11 새 가상환경에 `requirements.txt` 만 깔아
`python eval/run_all.py eval/refs.json` 을 완주시킨 기록이다. 측정 캐시(`~/.typo-mcp/`)와 실물
포스터 이미지는 저장소 밖에 있으므로, 그 자료를 갖춘 컴퓨터에서 돌렸다.

## 환경

| 항목 | 값 |
|---|---|
| 기계 | Apple Silicon 맥북 (M4) |
| 파이썬 | 3.11.15 — **3.10 이상이 필요하다** (`surya-ocr` 요구). 시스템 `python3` 가 3.9 면 설치가 실패한다 |
| 설치 | `pip install -r requirements.txt` 2분 10초 (surya-ocr 0.22.1 · torch 2.14.0 · numpy 2.4.6 · scipy 1.17.1 · Pillow 10.4.0 · easyocr 1.7.2), 가상환경 1.2 GB |

## 소요 시간

| 단계 | 시간 |
|---|---|
| 합성 650장 생성 (`eval/synth_gen.py`) | 47초 |
| 합성 재검출 · 채점 (`eval/synth_score.py --remeasure`) | 3분 29초 |
| `run_all` 전체 (측정 캐시가 있을 때) | **24분 37초** |
| — 그 가운데 `eval/clean_a_sweep.py` | 14분 58초 |
| — `eval/constants_sweep4.py` | 5분 33초 |
| — `eval/constants_ink_sweep.py` | 1분 36초 |
| — `idml_explore.py score` | 1분 8초 |
| — 나머지 단계 합 | 1분 20초 |

## 자료가 없어 건너뛴 단계

| 단계 | 까닭 |
|---|---|
| 사람 상자 만들기 | 원본 CSV 가 저장소 밖에 있다 — 커밋된 `boxes/human_v2.json` 을 쓴다 |
| 검출기 비교 · 오라클 묶기 | VLM 상자 파일이 저장소에 없다 (`boxes/VLM_RESPONSES.md`) |
| 브로크만 1 · 2단계 | 같은 까닭 (VLM 패스 파일) |

`--strict` 를 주면 건너뛰지 않고 그 자리에서 멈춘다.

## 결과 대조

`run_all` 을 지금 코드로 완주시킨 값을 커밋해 두었다 (커밋 «결과 재산출 — split_columns 반영 후 재산출»).
그 뒤 clone 해서 다시 완주시키면 **모든 결과 파일이 그대로 나온다 — 다른 칸 0**.

| 결과 파일 | 값이 바뀐 자리 |
|---|---|
| `synth_result.json` · `synth_b_result.json` (표 1 · 2) | 0 |
| `clean_result.json` · `clean_check.json` · `clean_c_diag.json` · `clean_a_sweep.json` | 0 |
| `loo_place_text.json` · `measure_pad_result.json` · `constants_definitions.json` | 0 |
| `series_check.json` · `series_check_diag.json` | 0 |
| `constants_ink_threshold.json` · `constants_sweep4.json` | 0 |

기록 필드(`*_sha256` · `commit` · 경로)는 자료를 다시 만들면 바뀌므로 위 셈에서 뺐다.

### 이전 값과의 차이 (2026-09-20 재산출)

재산출 전 커밋값은 `measure/region.py` 에 `split_columns` 이 들어오기 전(커밋 `a0c9f3d` 시점) 것이었다.

| 파일 | 무엇이 달라졌나 |
|---|---|
| `series_check.json` · `_diag` | 브로크만 캐시를 `cb779ea` 코드로 다시 잰 탓. 블록 수 41 → 42 · 327 → 328, 「거부」 14 → 15 |
| `constants_ink_threshold.json` · `constants_sweep4.json` | 스윕이 그 자리에서 다시 재는 탓. 곡선 값이 소수 넷째 자리, 블록 수가 한둘 달라진다 |

**상수 판정은 바뀌지 않았다.** 순서 4 의 14개 상수 판정이 모두 이전과 같고, 잉크 문턱도 「바꿀 값 0.52」로
같다 — 사전등록 수정 14 「상수 동결」에 따라 이 재판정은 값에 반영하지 않고 민감도 자료로만 둔다.
