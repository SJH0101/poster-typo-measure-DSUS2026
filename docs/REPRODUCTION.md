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

| 결과 파일 | 값이 바뀐 자리 |
|---|---|
| `synth_result.json` · `synth_b_result.json` | **0** |
| `clean_result.json` · `clean_check.json` · `clean_c_diag.json` · `clean_a_sweep.json` | **0** |
| `loo_place_text.json` · `measure_pad_result.json` · `constants_definitions.json` | **0** |
| `series_check.json` · `series_check_diag.json` | 바뀜 — 아래 (1) |
| `constants_ink_threshold.json` · `constants_sweep4.json` | 바뀜 — 아래 (2) |

기록 필드(`*_sha256` · `commit` · 경로)는 자료를 다시 만들면 바뀌므로 위 셈에서 뺐다.

1. **`series_check`** — 커밋된 값은 브로크만 캐시를 `split_columns` 이전(커밋 `a0c9f3d`)으로 잰 것이고,
   지금 캐시는 그 뒤(`cb779ea`)에 다시 잰 것이다. 그래서 «거부» 14 → 15 처럼 판정 수가 조금 달라진다.
2. **`constants_ink_threshold` · `constants_sweep4`** — 두 스윕은 합성 스윕 세트를 그 자리에서 다시 재는데,
   커밋된 값은 `measure/region.py` 에 `split_columns` 이 들어오기 전 것이다. 측정 선 수가 최대 23,
   블록 수가 최대 2 만큼 달라진다.

둘 다 이 저장소를 정리하면서 생긴 차이가 아니라, **결과를 커밋한 뒤 파이프라인이 바뀐 자리**다.
논문에 어느 값을 싣는지는 따로 정한다.
