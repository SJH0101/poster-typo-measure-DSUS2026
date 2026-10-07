"""VLM 묶음 실행 기록 — 사전등록 docs/vlm_corpus_preregister.json 결정 5.

    python eval/vlm_corpus_runlog.py --work ~/.typo-mcp/vlm_corpus \
        --responses vlm_responses --out vlm_responses/vlm_corpus_run_log.json

묶음마다 ① 출력 파일이 있나 ② 번호 검증(모든 딱지가 정확히 한 묶음에) ③ 자기 보고 model
④ 서브에이전트 jsonl 의 message.model ⑤ 열어 본 파일이 목록 밖인지 를 적는다.
«남은 묶음» 을 찍어 주므로 끊긴 지점부터 다시 시작할 수 있다.
"""
import argparse
import collections
import glob
import json
import os


def jsonl_models(sub_dir):
    """서브에이전트 jsonl 마다 message.model 도수. {파일: {model: n}}"""
    out = {}
    for p in sorted(glob.glob(os.path.join(sub_dir, 'agent-*.jsonl'))):
        c = collections.Counter()
        try:
            for ln in open(p, errors='replace'):
                if '"model"' not in ln:
                    continue
                try:
                    d = json.loads(ln)
                except Exception:
                    continue
                m = (d.get('message') or {}).get('model')
                if m:
                    c[m] += 1
        except Exception:
            continue
        if c:
            out[os.path.basename(p)] = dict(c)
    return out


def main():
    ap = argparse.ArgumentParser()
    for k in ('--work', '--responses', '--out'):
        ap.add_argument(k, required=True)
    ap.add_argument('--sub-dir', help='서브에이전트 jsonl 폴더 (모델 확인용)')
    a = ap.parse_args()
    W = os.path.expanduser(a.work)
    idx = json.load(open(os.path.join(W, 'batches', 'index.json')))
    rows, remain = [], []
    for P in (1, 2):
        for b in idx['묶음']:
            nm = b['묶음']
            bd = json.load(open(os.path.join(W, 'batches', f'{nm}.json')))
            want = {p['file']: p['n_lines'] for p in bd['판']}
            fp = os.path.join(a.responses, f'vlm_corpus_pass{P}', f'{nm}.json')
            r = dict(회차=P, 묶음=nm, 판=b['n'], 딱지=b['labels'], 출력=fp, 완료=os.path.exists(fp))
            if r['완료']:
                try:
                    d = json.load(open(fp))
                except Exception as e:
                    r.update(완료=False, 오류=f'읽기 실패 {e}')
                else:
                    r['자기보고_model'] = d.get('model')
                    r['판_수'] = len(d.get('posters') or [])
                    bad = []
                    for p in d.get('posters') or []:
                        n = want.get(p['file'])
                        if n is None:
                            bad.append(f'{p["file"]}: 목록 밖'); continue
                        nums = sorted(x for g in p.get('groups') or [] for x in g)
                        if nums != list(range(1, n + 1)):
                            bad.append(f'{p["file"]}: 번호 {len(nums)} · 기대 1~{n}')
                    miss = [f for f in want if f not in {p['file'] for p in d.get('posters') or []}]
                    r['번호_검증_어긋남'] = bad
                    r['빠진_판'] = miss
                    fo = d.get('files_opened') or []
                    sd = bd.get('som_dir') or os.path.join(W, 'som')
                    allow = {os.path.join(sd, p['file']) for p in bd['판']} \
                        | {os.path.join(W, f'pass{P}_input', f'{nm}_input.json')}
                    r['목록_밖_열람'] = [x for x in fo if x not in allow]
                    r['통과'] = not bad and not miss
            if not r.get('통과'):
                remain.append(f'회차{P}|{nm}')
            rows.append(r)
    out = dict(무엇='VLM 묶음 실행 기록 — 사전등록 docs/vlm_corpus_preregister.json 결정 5',
               묶음_수=len(idx['묶음']), 회차=2, 기대_세션=len(idx['묶음']) * 2,
               완료=sum(1 for r in rows if r.get('통과')), 남은_묶음=remain,
               지시문='docs/brockmann_vlm_prompt.md', 묶음별=rows)
    if a.sub_dir:
        out['서브에이전트_jsonl_model'] = jsonl_models(os.path.expanduser(a.sub_dir))
    json.dump(out, open(a.out, 'w'), ensure_ascii=False, indent=1)
    print(f'  완료 {out["완료"]} / {out["기대_세션"]} · 남은 묶음 {len(remain)}')
    if remain:
        print('  남은:', ' '.join(remain[:12]), '…' if len(remain) > 12 else '')
    print('→', a.out)


if __name__ == '__main__':
    main()
