# 봉인 파일 해시

봉인한 파일은 열지 않는다. 같은 파일인지 확인할 수 있게 sha256 만 남긴다.

## 브로크만 1단계 VLM 패스 (옛 봉인, 갈리지 않은 줄)

2026-09-14 에 받은 묶음이다. 사전등록 수정 16 으로 줄 상자 가르기가 기본 경로가 되면서 줄 번호가
바뀌어 더 쓸 수 없다. 파일은 저장소 밖 `~/Documents/poster/vlm_responses_archive/` 에 그대로 둔다
(`boxes/VLM_RESPONSES.md`).

| 파일 | 크기 (bytes) | sha256 |
|---|---|---|
| `brockmann_vlm_pass1.json` | 31411 | `c387aa5989e8cab156f4a7e0f915e762aff814845a89d1bd7165fd960e49ae86` |
| `brockmann_vlm_pass2.json` | 30079 | `8037631b0517d912764a0de7b4697a4dcf7bb3c33bbb324730f5517fd1af00b5` |

## 브로크만 1단계 VLM 패스 (새 봉인, 갈린 줄)

2026-09-21 에 받았다. 사전등록 수정 16 의 갈린 줄(910개)로 SoM 을 다시 그리고, 사람 상자를 본 적 없는
새 세션 다섯 개씩(묶음 10장)에 같은 지시문(`docs/brockmann_vlm_prompt.md`) · 같은 모델(claude-opus-5)로
받았다. **이 두 파일은 봉인이다 — 2단계 채점 밖에서는 열지 않는다.**

| 파일 | 크기 (bytes) | sha256 |
|---|---|---|
| `boxes/brockmann_vlm_split_pass1.json` | 29192 | `041a3ff981d6228aecd3a982360122bec8b8bc01e3dae0136a91ffab2b779100` |
| `boxes/brockmann_vlm_split_pass2.json` | 28855 | `85854cba15b0158c0cf6b47ec70027eea8b9b1dc29e1b40d1d52b8584a739c02` |
