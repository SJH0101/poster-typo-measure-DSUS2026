"""회차 대조와 판정 — 사전등록 docs/vlm_corpus_preregister.json 결정 4.

    python eval/vlm_corpus_summary.py --rules docs/vlm_corpus_rules_pass1.json docs/vlm_corpus_rules_pass2.json \
        --ndiv docs/vlm_corpus_grid_ndiv_pass1.json docs/vlm_corpus_grid_ndiv_pass2.json \
        --module docs/vlm_corpus_grid_module_pass1.json docs/vlm_corpus_grid_module_pass2.json \
        --base-rules docs/typography_rules2_explore.json --base-ndiv docs/grid_ndiv_result.json \
        --base-module docs/grid_module_result.json --prereg docs/vlm_corpus_preregister.json \
        --out docs/vlm_corpus_summary.json

두 회차의 판정이 같을 때만 그 판정을 쓰고, 다르면 «회차 간 불일치» 로 적는다. 규칙 기반(현행)
값을 나란히 둔다. 라벨 대상은 다시 돌리지 않았으므로 판정에 쓰지 않고 대조 결과만 적는다.
"""
import argparse
import json
import os

# 표 6 — 논문 표의 여섯 항목 (paper_numbers 16.1 의 짝)
T6 = [('행간÷x높이 비 일정', ['A', 'A1_판안_일치']),
      ('줄 간격 정수배', ['A', 'A2_판기준']),
      ('블록 사이 간격 정수배', ['A', 'A4', '허용별', '허용_0.15']),
      ('활자 크기 종류 수', ['B', 'B1', '대조']),
      ('왼쪽 정렬 위치 수', ['C', 'C1', '대조']),
      ('인접 크기 비 2.0', ['B', 'B2', '목표별', '2.0']),
      ('인접 크기 비 1.5', ['B', 'B2', '목표별', '1.5']),
      ('인접 크기 비 1.33', ['B', 'B2', '목표별', '1.33'])]
CORP = [('브로크만', '가_측정_브로크만'), ('호프만', '측정_호프만'), ('로제', '측정_로제'), ('루더', '측정_루더'),
        ('측정 50', '나_측정_50')]


def get(o, path):
    for k in path:
        o = o[k]
    return o


def verdict(a, b):
    """두 회차 판정이 같을 때만 쓴다 (결정 4)."""
    if a == b:
        return a
    return '회차 간 불일치'


def main():
    ap = argparse.ArgumentParser()
    for k in ('--rules', '--ndiv', '--module'):
        ap.add_argument(k, nargs=2, required=True)
    for k in ('--base-rules', '--base-ndiv', '--base-module', '--prereg', '--out'):
        ap.add_argument(k, required=True)
    a = ap.parse_args()
    R = [json.load(open(f)) for f in a.rules]
    N = [json.load(open(f)) for f in a.ndiv]
    M = [json.load(open(f)) for f in a.module]
    BR, BN, BM = (json.load(open(a.base_rules)), json.load(open(a.base_ndiv)), json.load(open(a.base_module)))

    out = dict(
        무엇='VLM 블록으로 다시 낸 조판 값 분석 — 회차 대조와 판정 (사전등록 docs/vlm_corpus_preregister.json 결정 4)',
        판정_규칙='두 회차의 판정이 같을 때만 그 판정을 쓴다. 다르면 «회차 간 불일치»',
        비교='규칙 기반(현행, detect_surya.group)을 나란히 둔다',
        라벨_대상=dict(
            무엇='라벨 대상(연구자 A · B · 합의)은 사람이 그은 블록이라 VLM 묶기와 무관하므로 다시 돌리지 않았다',
            가로배수='grid_module 의 라벨 대상 셋은 두 회차 모두 커밋본과 바이트 단위로 같다',
            표6='다_라벨_50 은 바이트 단위로 다르다 — 회차1 48칸 · 회차2 47칸. 다만 **실제값과 판정은 한 칸도 다르지 않고** 달라진 것은 모의 대조(대조_i · 대조_ii 의 평균 · 구간)뿐이다',
            까닭=('eval/explore_typography_rules2.py:29 의 모듈 수준 난수(rng = np.random.default_rng(20260918)) 하나를 '
                 '모든 대상이 차례로 이어서 쓴다. 측정 대상이 라벨 대상보다 먼저 계산되고 이번에는 그 블록 수가 '
                 '달라졌으므로, 라벨 대상 차례에 난수 흐름의 위치가 달라져 모의 대조만 바뀐다. 라벨 대상의 블록은 '
                 '라벨 파일에서 오고 캐시는 판 크기(size)로만 쓰이므로 실측값은 영향을 받지 않는다'),
            사전등록_결정4=('결정 4 는 «대조가 어긋나면 적고 멈춘다» 였다. 위 까닭으로 사용자 결정에 따라 넘어가고 '
                        '계속했다 (2026-10-07). 대상별로 난수를 따로 두는 수정은 커밋된 표 6 값을 모두 바꾸므로 하지 않았다'),
            기록='vlm_responses/vlm_corpus_recalls.json 의 «사전등록_결정4_넘어감»'),
        블록_수={'규칙 기반': {}, '회차1': {}, '회차2': {}},
        표6={}, 표7={}, 가로배수={})

    # 블록 수
    for nm, key in CORP[:4]:
        out['블록_수']['규칙 기반'][nm] = BR['결과'][key]['블록']
        out['블록_수']['회차1'][nm] = R[0]['결과'][key]['블록']
        out['블록_수']['회차2'][nm] = R[1]['결과'][key]['블록']

    # 표 6
    for nm, path in T6:
        row = {}
        for cn, key in CORP:
            b = get(BR['결과'][key], path)
            v1, v2 = get(R[0]['결과'][key], path), get(R[1]['결과'][key], path)
            row[cn] = dict(
                규칙기반=dict(실제=b['실제'], 대조_ii=b['대조_ii']['구간'], 판정=b['판정']),
                회차1=dict(실제=v1['실제'], 대조_ii=v1['대조_ii']['구간'], 판정=v1['판정']),
                회차2=dict(실제=v2['실제'], 대조_ii=v2['대조_ii']['구간'], 판정=v2['판정']),
                VLM_판정=verdict(v1['판정'], v2['판정']))
        out['표6'][nm] = row

    # 표 7 — 측정 대상만
    def ndiv_row(d):
        t = d['대상']['측정_브로크만_123']
        return dict(판=t['판'], 블록=t['블록'], 모서리=t['모서리'],
                    N별_구간밖=len(t['N별_요약']['구간_밖_N']),
                    최적N_중앙=t['최적N']['일치율_중앙'], 대조_ii=t['최적N']['대조_ii']['구간'],
                    판정=t['최적N']['판정'], 최적N의_중앙=t['최적N']['N_중앙'],
                    N60_5=t['최적N']['N_60_5이내_판'])
    b, v1, v2 = ndiv_row(BN), ndiv_row(N[0]), ndiv_row(N[1])
    out['표7'] = dict(규칙기반=b, 회차1=v1, 회차2=v2, VLM_판정=verdict(v1['판정'], v2['판정']))

    # 가로 배수 — 측정 대상만
    def mod_row(d):
        t = d['대상']['측정_브로크만_123']['주_결과']
        return dict(판=t['판'], 쓴_판=t['쓴_판'], 점수_중앙=t['점수_중앙'],
                    대조=t['대조']['구간'], 판정=t['판정'], 최적u_중앙=t['최적u_중앙'])
    b, v1, v2 = mod_row(BM), mod_row(M[0]), mod_row(M[1])
    out['가로배수'] = dict(규칙기반=b, 회차1=v1, 회차2=v2, VLM_판정=verdict(v1['판정'], v2['판정']))

    # 회차 간 불일치 목록
    bad = []
    for nm, row in out['표6'].items():
        for cn, v in row.items():
            if v['VLM_판정'] == '회차 간 불일치':
                bad.append(f'표6 · {nm} · {cn}: 회차1 «{v["회차1"]["판정"]}» · 회차2 «{v["회차2"]["판정"]}»')
    if out['표7']['VLM_판정'] == '회차 간 불일치':
        bad.append(f'표7 최적N: 회차1 «{out["표7"]["회차1"]["판정"]}» · 회차2 «{out["표7"]["회차2"]["판정"]}»')
    if out['가로배수']['VLM_판정'] == '회차 간 불일치':
        bad.append(f'가로배수: 회차1 «{out["가로배수"]["회차1"]["판정"]}» · 회차2 «{out["가로배수"]["회차2"]["판정"]}»')
    out['회차_간_불일치'] = bad
    out['회차_간_불일치_수'] = len(bad)
    json.dump(out, open(a.out, 'w'), ensure_ascii=False, indent=1)
    print(f'  회차 간 불일치 {len(bad)} 건')
    for x in bad:
        print('   -', x)
    print('→', a.out)


if __name__ == '__main__':
    main()
