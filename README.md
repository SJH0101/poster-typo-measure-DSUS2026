# 타이포그래피 계측 — 논문 재현 저장소

> 이 저장소는 **논문의 수치를 다시 내기 위한 것**이다. 파이프라인 코드 · 합성 포스터 생성기 ·
> 채점 스크립트 · 사전등록 · 사람 정답 라벨 · 결과 JSON 을 담는다. 실물 포스터 이미지는 들어 있지 않다.

포스터 인쇄물에서 조판을 **재는** 도구와, 그 도구가 무엇을 얼마나 되찾는지 확인한 실험이다.
파이프라인은 «어디를 잴지 짚는 일»(줄 검출 · 블록 묶기)과 «그 안을 재는 일»(베이스라인 · x높이선 ·
상단 잉크선 · 행간)을 나눈다. 정답을 알고 그린 합성 포스터 650장으로 재는 쪽을 검증했고
(베이스라인 오차 중앙 0.0 px, 해상도 400~1600 · JPEG 45~95 · 세 가지 극성에서 같다), 남는 오차는
모두 찾기·묶기에서 온다. 그 다음 실물 포스터(요제프 뮐러브로크만 123장)에 적용하고, 그 가운데 50장은
두 사람이 독립으로 그은 가이드 라벨과 견줬다. 사람 라벨은 정답이 아니라 참조로 쓰며, 결과는
«정확도»가 아니라 «참조와의 일치도»로 적는다.

## 논문 인용

```
(추후 채움 — 저자 · 제목 · 학회/저널 · 연도 · DOI)
```

## 설치

macOS · Python 3.11 기준이다. 합성 포스터는 시스템 Helvetica(`/System/Library/Fonts/Helvetica.ttc`)로
그린다 — 다른 환경에서는 글꼴 경로를 인자로 준다.

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
```

줄 검출은 `surya-ocr` 이 한다 (논문 수치는 0.22.1). 합성 실험만 다시 낼 때는 `easyocr` 없이도 돈다.

## 실행 — 합성 생성 → 측정 → 채점

합성 실험은 저장소 안의 것만으로 처음부터 다시 만들 수 있다. 이미지는 저장소 밖에 쓴다.

```bash
.venv/bin/python eval/synth_gen.py --out ~/.typo-mcp/synth_eval --manifest docs/synth_eval_manifest.json --seeds $(seq 8001 8050)
```

```bash
.venv/bin/python eval/synth_score.py --dir ~/.typo-mcp/synth_eval --manifest docs/synth_eval_manifest.json --prereg docs/synth_preregister.json --cache-dir ~/.typo-mcp/synth_eval_cache --out docs/synth_result.json --remeasure
```

`--remeasure` 가 Surya 줄 검출부터 다시 돌린다. 생략하면 `--cache-dir` 의 측정 캐시를 그대로 쓴다.
채점 결과 `docs/synth_result.json` 이 논문 표 1 · 2 의 근거다.

**소요 시간** (M4 맥북, 2026-09-21 실측): 합성 단계만 — 650장 생성 47초 + 재검출·채점 3분 29초 ≈ **약 4분**.
아래 `run_all` 전체는 측정 캐시가 있을 때 **약 28분**이고, 그 가운데 15분이 `eval/clean_a_sweep.py`,
5분 30초가 `eval/constants_sweep4.py` 다. 자세한 기록은 `docs/REPRODUCTION.md`.

참조 자료가 모두 있으면 채점·분석 전체를 한 명령으로 다시 돌린다.

```bash
.venv/bin/python eval/run_all.py eval/refs.json
```

경로는 코드에 박지 않고 `eval/refs.json` 한 곳에 둔다. 실물 포스터 이미지는 저장소에 들어 있지
않으므로(아래) 그 단계는 자료를 갖춘 사람만 돌릴 수 있다. 자료가 없으면 `run_all` 은 그 단계를
건너뛴다 — 사람 상자 원본 CSV 가 없으면 이미 커밋된 `boxes/human_v2.json` 을 쓰고, 검출기 상자
파일이 모자라면 검출기 비교·오라클 묶기 단계를 건너뛰며, 깨끗한 세트 이미지(`~/.typo-mcp/clean`)가
없으면 그 세트의 생성 검증·채점·A 훑기를 건너뛴다. `--strict` 를 주면 예전처럼 그 자리에서 멈춘다.

## 지금 수치 (브로크만 50장, 합의 참조)

`docs/brockmann_stage2_result.json` (사전등록 `docs/brockmann_stage2_preregister.json`).
사람 라벨은 정답이 아니라 참조이므로 «참조와의 일치도» 다.

| | 값 |
|---|---|
| 베이스라인 재현율 | **0.894** (참값 글줄 921 · 오차 절대 중앙 0.0 px) |
| Surya 가 못 찾은 글줄 | **93 / 921** — 줄 상자 가르기를 켜기 전에는 126 (`docs/split_lines_score_explore.json`, 탐색용) |
| 오라클(묶기 상한) 블록 F1 | **0.918** (재현 0.895, 참조 블록 352) |
| 묶기 블록 F1 (IoU ≥ 0.5) | C 0.761 · VLM2 0.756 · VLM1 0.706 · A 0.705 |

상수는 `docs/constants_preregister.json` 수정 15 (`H_RATIO` 상한 2.55 → 3.4) 와 수정 16
(줄 상자 가르기를 기본 경로로) 까지 반영한 값이다. 합성 650장 쪽 수치는 `docs/synth_result.json` 에 있다.

## 폴더

| 폴더 | 무엇 |
|---|---|
| `measure/` | 재는 쪽 — 잉크 문턱 · 글줄 · 베이스라인 · x높이선 · 상단 잉크선 · 블록 측정 |
| `color/` | 바탕·글자 색과 사진 영역 측정 |
| `tools/` | 레이아웃 검사 모듈 (`eval/series_check.py` 가 부른다) |
| `eval/` | 합성 생성기 · 채점 · 사전등록 실험 스크립트 · `run_all.py` · `refs.json` |
| `docs/` | 사전등록 · 결과 JSON · 실험 기록 · 코퍼스 색인 |
| `docs/explore/` | 탐색용 자료 — 사전등록 없이 돌린 것, 논문 수치가 아니다 (`docs/explore/README.md`) |
| `docs/labeling/` | 라벨 대상 선정 · 가이드 긋기 도구 만들기 · 요청서 자료 |
| `labels/` | 앞선 단계의 사람·코드 판정 자료 (기울기 · 모양 · 분류) |
| `labels/guides/` | 브로크만 50장 가이드 라벨 두 벌 (라벨러A · 라벨러B) |
| `docs/corpus_list/` | 네 코퍼스 판 목록과 eMuseum 원본 URL (이미지는 넣지 않는다) |
| `boxes/` | 검출기 상자 (EasyOCR · Surya) · 사람 상자 · 남겨 둔 VLM 묶음 (`VLM_RESPONSES.md` 참조) |
| `baseline/` · `viewer/` | 옛 검출 경로와 보기 도구 (참고용) |

핵심 코드: `detect_surya.py`(줄 → 블록 묶기) · `measure_corpus.py`(코퍼스 측정) · `remeasure.py`
(네 코퍼스 다시 재기) · `rules.py`(분포에서 규칙 뽑기).

## 자료 출처와 라이선스

| 자료 | 출처 | 상태 |
|---|---|---|
| 합성 포스터 650장 | 이 저장소의 `eval/synth_gen.py` 가 만든다 (이미지 자체는 넣지 않는다) | 코드와 같은 라이선스 |
| 실물 포스터 이미지 (브로크만 · 호프만 · 로제 · 루더) | 취리히 디자인미술관 eMuseum | **저장소에 없다.** 판마다의 원본 URL 은 `docs/corpus_list/posters.csv` 의 `url` 열에 있다. 내려받아 쓰는 조건은 eMuseum 을 따른다 (확인 중) |
| 사람 가이드 라벨 (브로크만 50장, 2인) | **논문 저자 2인이 작성한 정답 라벨**이다 (`labels/guides/`) | 이름은 «라벨러A» · «라벨러B» 로 적는다. 좌표와 상태값만 들어 있고 이미지는 없다 |
| VLM 묶음 `boxes/clean_vlm_pass1·2.json` | **Claude Opus 5(`claude-opus-5`)의 출력**이다. Anthropic 이용약관을 따른다 | 합성 세트 묶기 비교(`docs/clean_result.json`)를 다시 내려면 필요해 남겼다 |
| VLM 묶음 `boxes/brockmann_vlm_split_pass1·2.json` | claude-opus-5 출력. **2026-09-21 에 새로 받은 두 회차**다 — 사전등록 수정 16 의 갈린 줄(910개)로 번호 이미지를 다시 그리고, 사람 상자를 본 적 없는 서로 모르는 새 세션에 같은 지시문(`docs/brockmann_vlm_prompt.md`) · 같은 모델로 받았다 | 2단계 채점(`docs/brockmann_stage2_result.json`)에 필요해 남겼다. **봉인** — 채점 밖에서는 열지 않는다. 옛 회차(갈리지 않은 줄)는 저장소 밖에 두고 sha256 만 `docs/sealed_hashes.md` 에 남겼다 |
| 그 밖의 VLM 응답 | claude-opus-5 출력 | 저장소 밖으로 뺐다 — `boxes/VLM_RESPONSES.md` |

코드는 MIT 라이선스다 (`LICENSE`). 자료(사람 라벨 · 목록)는 코드와 같은 조건으로 쓰되, 실물 포스터
이미지는 저장소에 없으므로 eMuseum 의 조건을 따른다.

## 사람 정답 라벨 형식

브로크만 50장에 두 사람이 각각 그었다. 한 판은 텍스트 블록들로 이뤄지고, 블록마다 글줄이 있으며,
글줄마다 네 종류의 가로선을 긋는다.

| 선 | 뜻 |
|---|---|
| `base` | 베이스라인 — 글자가 얹힌 선 (내림획 제외) |
| `xh` | x높이선 — 소문자 x 윗끝 |
| `cap` | 캡선 — 대문자 윗끝 |
| `asc` | 어센더선 — b · d · h · k · l 윗끝 |

값은 판 원본 이미지의 픽셀 y 좌표다. 그을 수 없으면 상태를 적는다 (`글자 없음` · `판독 불가` · `미입력`).
블록에는 상자 `box = [x1, y1, x2, y2]` 와 제외 사유가 붙는다. 파일은 `labels/guides/` 에 두 벌 있고,
라벨러 이름은 «라벨러A» · «라벨러B» 로 적었다 (실명 대응표는 저장소에 두지 않는다). 두 사람의 파일에서 «일치» 참조와 «합의»
참조를 만드는 규칙은 `docs/brockmann_stage2_preregister.json` 에 있고, 만드는 코드는
`eval/brockmann_stage2_score.py consensus` 다. 채점에서 짝짓기는 창 0.5·행간 · 허용 0.2·행간 ·
가로 겹침 · 가까운 순 1:1 이다.

## 실험 기록

- `docs/RESULTS_FOR_PAPER.md` — 논문에 들어갈 수치와 그 근거 파일 · 커밋
- `docs/*_preregister.json` — 실험마다 돌리기 전에 단독 커밋한 사전등록
- `docs/HANDOFF.md` — 연구 방향 · 파이프라인 구조 · 확정된 사실 · 보류한 작업
- `docs/legacy_numbers.md` — 지금 코드로 재현되지 않는 옛 수치

«탐색용 · 논문 수치 아님» 이 적힌 결과 파일은 사전등록 없이 돌린 탐색이며 논문 수치가 아니다.
최근 것은 `docs/explore/` 에 모았고, 앞선 것은 `docs/` 바로 아래에 `*_explore.json` 으로 있다.
