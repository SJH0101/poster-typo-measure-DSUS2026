"""VLM 묶음 받기 준비 — 사전등록 docs/vlm_corpus_preregister.json 결정 1.

    python eval/vlm_corpus_prepare.py --unlabeled ~/.typo-mcp/unlabeled222 \
        --posters docs/labeling/posters_for_labelers.json \
        --caches 브로크만=~/.typo-mcp/brockmann.json 호프만=~/.typo-mcp/corpus.json \
                 로제=~/.typo-mcp/rose.json 루더=~/.typo-mcp/ruder.json \
        --work ~/.typo-mcp/vlm_corpus --max-posters 10 --max-labels 700

하는 일 (새 상수 없음 · 기존 함수만 부른다):
  ① ~/.typo-mcp/unlabeled222 의 Surya 줄 222판을 그대로 받는다 (commit f941ecc · order columns).
  ② 그 세트에 없는 라벨링 연습판 2장을 같은 함수 · 설정으로 검출한다
     (DetectionPredictor + group_score.order_columns, 배치 8).
  ③ 224판 모두에 detect_surya.split_wide_lines 를 건다 (갈린 줄 — 기존 패스와 같다).
  ④ 번호 표지 이미지를 group_score.som 으로 만든다 (2배 LANCZOS).
  ⑤ 묶음 목록을 eval/clean_vlm_batches.py 와 같은 규칙으로 나눈다.
"""
import argparse
import collections
import hashlib
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
import detect_surya as DS                   # noqa: E402
import group_score as GS                    # noqa: E402  _key · order_columns · som · draw_som
import measure_corpus as MC                 # noqa: E402  provenance


def _sha(p):
    return hashlib.sha256(open(os.path.expanduser(p), 'rb').read()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    for k in ('--unlabeled', '--posters', '--work'):
        ap.add_argument(k, required=True)
    ap.add_argument('--caches', nargs='+', required=True)
    ap.add_argument('--max-posters', type=int, default=10)
    ap.add_argument('--max-labels', type=int, default=700)
    a = ap.parse_args()

    W = os.path.expanduser(a.work); os.makedirs(W, exist_ok=True)
    U = os.path.expanduser(a.unlabeled)
    uman = json.load(open(os.path.join(U, 'manifest.json')))
    ulines = json.load(open(os.path.join(U, 'lines.json')))
    P = json.load(open(a.posters)); root = os.path.expanduser(P['image_root'])
    lab_keys = {f"{it['folder']}__{it['file']}" for it in P['main']}

    caches = {}
    for s in a.caches:
        k, v = s.split('=', 1)
        caches[k] = json.load(open(os.path.expanduser(v)))['raw']
    CORP = {'brockmann': '브로크만', 'corpus': '호프만', 'rose': '로제', 'ruder': '루더'}

    # ① 재사용 — unlabeled222 (라벨 50 은 애초에 빠져 있다)
    items, lines = [], {}
    seed = 0
    reused = 0
    for it in sorted(uman['items'], key=lambda x: x['seed']):
        src = ulines['lines'][GS._key(it['seed'])]
        seed += 1; k = GS._key(seed)
        items.append(dict(seed=seed, corpus=it['corpus'], key=it['key'], image=it['image'],
                          vlm_subset=True, 줄_출처='unlabeled222'))
        lines[k] = dict(src); reused += 1

    # ② 연습판 2장만 새로 검출
    prac = [it for it in P['practice']]
    paths = [os.path.join(root, it['folder'], it['file']) for it in prac]
    if paths:
        from surya.detection import DetectionPredictor
        det = DetectionPredictor()
        imgs = [Image.open(p).convert('RGB') for p in paths]
        res = det(imgs)
        for it, p, r, im in zip(prac, paths, res, imgs):
            ls = sorted(([float(v) for v in b.bbox] for b in r.bboxes), key=lambda b: (b[1], b[0]))
            ls, nb = GS.order_columns(ls)
            seed += 1; k = GS._key(seed)
            key = f"{it['folder']}__{it['file']}"
            assert key not in lab_keys, '연습판이 main 에 있다'
            items.append(dict(seed=seed, corpus='brockmann', key=key, image=p,
                              vlm_subset=True, 줄_출처='이번 검출 (연습판)'))
            lines[k] = dict(size=list(im.size), lines=ls, sha256=_sha(p), order='columns', columns_found=nb)

    # ③ 갈린 줄
    split_n = 0
    for it in items:
        k = GS._key(it['seed'])
        gray = np.asarray(Image.open(it['image']).convert('L')).astype(float)
        before = len(lines[k]['lines'])
        lines[k]['lines'] = [list(b) for b in DS.split_wide_lines(gray, lines[k]['lines'])[0]]
        lines[k]['갈라진_조각'] = len(lines[k]['lines']) - before
        split_n += lines[k]['갈라진_조각']

    # 캐시 열쇠와 맞는지
    miss = [it['key'] for it in items if it['key'] not in caches.get(CORP[it['corpus']], {})]
    cnt = collections.Counter(CORP[it['corpus']] for it in items)
    man = dict(무엇='VLM 블록 나누기용 판 목록 — 사전등록 docs/vlm_corpus_preregister.json 결정 1',
               image_root='/', 줄_출처=dict(unlabeled222=reused, 이번_검출=len(prac)),
               연습판_포함=True, 코퍼스별=dict(cnt), 캐시에_없는_열쇠=miss,
               갈라진_조각_합=split_n, items=items)
    json.dump(man, open(os.path.join(W, 'manifest.json'), 'w'), ensure_ascii=False, indent=1)
    prov = MC.provenance('eval/vlm_corpus_prepare.py', len(lines))
    prov['줄_출처'] = ('222판 = ~/.typo-mcp/unlabeled222 (eval/group_score.py detect --order columns, '
                    'commit f941ecc) · 연습판 2장 = 같은 함수 · 설정으로 이번에 검출 · 모두 split_wide_lines 적용')
    json.dump(dict(lines=lines, provenance=prov, order='columns',
                   note='줄 번호 = 목록 순서 + 1. order columns = 단 단위 (group_score.order_columns). split_wide_lines 적용'),
              open(os.path.join(W, 'lines.json'), 'w'), ensure_ascii=False)
    print(f'  판 {len(items)} (재사용 {reused} · 새 검출 {len(prac)}) · 갈라진 조각 {split_n} · 캐시에 없는 열쇠 {len(miss)}')
    print('  코퍼스별', dict(cnt))

    # ④ 번호 표지 이미지
    S = os.path.join(W, 'som')
    GS.som(argparse.Namespace(dir='/', manifest=os.path.join(W, 'manifest.json'),
                              lines=os.path.join(W, 'lines.json'), som_dir=S))

    # ⑤ 묶음 — eval/clean_vlm_batches.py 와 같은 규칙
    rows = [dict(file=f'{GS._key(it["seed"])}_som.png', seed=it['seed'], key=it['key'],
                 corpus=it['corpus'], n_lines=len(lines[GS._key(it['seed'])]['lines'])) for it in items]
    out, cur = [], []
    for r in rows:
        if cur and (len(cur) >= a.max_posters or sum(x['n_lines'] for x in cur) + r['n_lines'] > a.max_labels):
            out.append(cur); cur = []
        cur.append(r)
    if cur:
        out.append(cur)
    B = os.path.join(W, 'batches'); os.makedirs(B, exist_ok=True)
    bl = []
    for i, b in enumerate(out, 1):
        name = f'b{i:02d}'
        json.dump(dict(묶음=name, n=len(b), labels=sum(x['n_lines'] for x in b), som_dir=S, 판=b),
                  open(os.path.join(B, f'{name}.json'), 'w'), ensure_ascii=False, indent=1)
        bl.append(dict(묶음=name, n=len(b), labels=sum(x['n_lines'] for x in b)))
    json.dump(dict(max_posters=a.max_posters, max_labels=a.max_labels, 묶음=bl,
                   som_dir=S, work=a.work), open(os.path.join(B, 'index.json'), 'w'), ensure_ascii=False, indent=1)
    print(f'  {len(out)}묶음 · 판 {sum(x["n"] for x in bl)} · 딱지 {sum(x["labels"] for x in bl)} · '
          f'묶음당 판 {min(x["n"] for x in bl)}~{max(x["n"] for x in bl)} · 딱지 {min(x["labels"] for x in bl)}~{max(x["labels"] for x in bl)}')
    print('→', W)


if __name__ == '__main__':
    main()
