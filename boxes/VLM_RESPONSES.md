# VLM 응답 원본

VLM(claude-opus-5) 이 낸 묶기·좌표 응답 파일은 이 저장소에서 뺐다. 모델 출력의 권리 관계를
확인하기 전까지는 공개하지 않는다. 원본은 연구자 컴퓨터의 `~/Documents/poster/vlm_responses_archive/`
에 그대로 있다.

| 뺀 파일 | 무엇 | 까닭 |
|---|---|---|
| `brockmann_vlm_pass1.json` · `pass2.json` | 브로크만 50장 1단계 묶기 (2패스) | 봉인 자료이기도 하다 |
| `group_vlm_pass1.json` · `pass2.json` | 묶기 비교 240장 세트 | 그 세트는 폐기됐다 (docs/GROUP_SET_ANATOMY.md 8절) |
| `vlm_pass1.json` · `pass2.json` | 옛 상자 짚기 패스 | 탐색용 |
| `vlm_input_a.json` · `vlm_input_b.json` | 입력 형태 비교 (탐색용) | 탐색용 |
| `vlm_baseline_a1·a2·b1·b2.json` | 베이스라인 좌표 시험 (탐색용) | 탐색용 |
| `vlm_baseline_all50_a1·a2·b1·b2.json` | 베이스라인 좌표, 브로크만 50장 전부 — **본 응답** (사전등록 `docs/vlm_baseline_all50_preregister.json`, 2026-10-04, claude-opus-5) | 권리 관계 확인 전 (위와 같은 원칙). 결과는 `docs/vlm_baseline_all50.json` |
| `vlm_baseline_all50_opus55_a1·a2·b1·b2.json` | 같은 설계를 claude-opus-5-5 로 받은 **참고** 응답 (사전등록 수정 1 로 본 결과에서 뺐다) | 같은 원칙. 결과는 `docs/vlm_baseline_all50_opus55.json` |

`vlm_baseline_all50_*` 의 sha256 (같은 값이 각 결과 파일의 `입력.응답` 에도 있다):

| 파일 | sha256 |
|---|---|
| `vlm_baseline_all50_a1.json` | `4d3943b0351fa049c0b878390801d6c85fe86b6eaf538743bd6f167d9b759bac` |
| `vlm_baseline_all50_a2.json` | `659b8d23c9a2a77e8fa5c2287627464b31d665c48d8912aa3d2f2b8412d97c9e` |
| `vlm_baseline_all50_b1.json` | `a3fcb8060b1b979c4c730d2259c368adfefceee75b745699aa2b60bd333b2833` |
| `vlm_baseline_all50_b2.json` | `c0f8cab275762cfa12518831fabd8e962380cad6cda56a6bc09bc7d9fe73e595` |
| `vlm_baseline_all50_opus55_a1.json` | `e724f674d0df4ff97d17c72b38a898dd04990f7691b1f0b12ede5d01883ab993` |
| `vlm_baseline_all50_opus55_a2.json` | `0b5170322e738edfddcbbe68dd3044b38300df627bfb84f10bf28cd36d599f23` |
| `vlm_baseline_all50_opus55_b1.json` | `d98af7e219cd56e6b7c3aedcaf46e3c281b4ddb1b3d92eb07ea7bdbd77ade332` |
| `vlm_baseline_all50_opus55_b2.json` | `2bc9bbbf82eb1fca243c3730a4d401ef18bfe7f763ce8438c0d98b8241cf5bc6` |

묶음 답 40개(합치기 전)는 본 응답이 `~/.typo-mcp/vlm_baseline_all50/`, 참고 응답이 그 아래
`opus55/` 에 있고, 묶음마다 sha256 이 합친 파일의 `batches` 에 있다. 번호 딱지 이미지는
`~/.typo-mcp/vlm_baseline_all50/som/` 이다 (두 실행이 같은 이미지를 썼다).

**남겨 둔 것**: `clean_vlm_pass1.json` · `clean_vlm_pass2.json`. 깨끗한 세트(합성)의 묶기 비교
결과 `docs/clean_result.json` 이 논문 수치이고, 그 표를 다시 내려면 이 두 파일이 있어야 한다.
공개 여부를 다시 정하면 함께 옮긴다.
