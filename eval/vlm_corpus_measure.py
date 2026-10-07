"""VLM 묶음을 합치고 그 블록으로 측정해 회차별 캐시를 만든다 — 사전등록 결정 2 · 3 · 6ⓐ.

    python eval/vlm_corpus_measure.py --pass-no 1 \
        --work ~/.typo-mcp/vlm_corpus --work50 ~/.typo-mcp/brockmann50 \
        --posters docs/labeling/posters_for_labelers.json \
        --pass-dir vlm_responses/vlm_corpus_pass1 --pass50 boxes/brockmann_vlm_split_pass1.json \
        --caches 브로크만=~/.typo-mcp/brockmann.json 호프만=~/.typo-mcp/corpus.json \
                 로제=~/.typo-mcp/rose.json 루더=~/.typo-mcp/ruder.json \
        --merged vlm_responses/vlm_corpus_pass1.json --out-dir ~/.typo-mcp/vlm-pass1

측정은 eval/vlm_pipeline_50.py 와 같은 방식 — GS.boxes_of 의 픽셀 상자를 [x1/W, y1/H, x2/W, y2/H]
로 (DS.boxes_norm 과 같은 방식, 여유 없음) measure.ground.entry 에 넘긴다. 기존 캐시는 덮어쓰지
않고 --out-dir 아래 새 파일로만 쓴다. provenance 에 상자 출처가 VLM 임을 적는다 (규칙 7).
"""
import argparse
import collections
import glob
import hashlib
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
import detect_surya as DS                   # noqa: E402
import group_score as GS                    # noqa: E402
import measure_corpus as MC                 # noqa: E402
from measure import ground as G             # noqa: E402

CORP = {'brockmann': '브로크만', 'corpus': '호프만', 'rose': '로제', 'ruder': '루더'}
FILE = {'브로크만': 'brockmann', '호프만': 'corpus', '로제': 'rose', '루더': 'ruder'}


def _sha(p):
    return hashlib.sha256(open(os.path.expanduser(p), 'rb').read()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    for k in ('--work', '--work50', '--posters', '--pass-dir', '--pass50', '--merged', '--out-dir'):
        ap.add_argument(k, required=True)
    ap.add_argument('--pass-no', type=int, required=True)
    ap.add_argument('--caches', nargs='+', required=True)
    a = ap.parse_args()

    W = os.path.expanduser(a.work); W50 = os.path.expanduser(a.work50)
    O = os.path.expanduser(a.out_dir); os.makedirs(O, exist_ok=True)
    man = json.load(open(os.path.join(W, 'manifest.json')))
    Lv = json.load(open(os.path.join(W, 'lines.json')))['lines']
    man50 = json.load(open(os.path.join(W50, 'manifest.json')))
    root50 = os.path.expanduser(man50['image_root'])
    L50 = json.load(open(os.path.join(W50, 'lines.json')))['lines']
    Pl = {it['order']: it for it in json.load(open(a.posters))['main']}
    caches = {}
    for s in a.caches:
        k, v = s.split('=', 1)
        caches[k] = json.load(open(os.path.expanduser(v)))

    # 묶음 파일 합치기 — 새 224판
    groups = {}
    files = sorted(glob.glob(os.path.join(a.pass_dir, 'b*.json')))
    for fp in files:
        d = json.load(open(fp))
        for p in d.get('posters') or []:
            groups[p['file']] = p['groups']
    seed_of = {f'{it["seed"]:03d}_som.png': it for it in man['items']}
    missing = [f for f in seed_of if f not in groups]

    # 라벨 50판 — 기존 패스
    p50 = json.load(open(a.pass50))
    g50 = {}
    for p in p50.get('posters') or []:
        g50[p['file']] = p['groups']

    rows, raw = [], collections.defaultdict(dict)
    nblk = collections.Counter()
    # ① 새 224판
    for it in sorted(man['items'], key=lambda x: x['seed']):
        f = f'{it["seed"]:03d}_som.png'
        if f not in groups:
            continue
        k = GS._key(it['seed']); lines = Lv[k]['lines']; size = tuple(Lv[k]['size'])
        asg, info = GS.groups_vlm(lines, dict(groups=groups[f]))
        bx = [b[:4] for _g, b in GS.boxes_of(lines, asg)]
        nb = [[b[0] / size[0], b[1] / size[1], b[2] / size[0], b[3] / size[1]] for b in bx]
        e = G.entry(it['image'], nb, coords='norm')[0] if nb else None
        cn = CORP[it['corpus']]
        src = caches[cn]['raw'][it['key']]
        ent = dict(src)                                 # size · color · region 등은 그대로
        ent['blocks'] = (e['blocks'] if e else [])
        ent['n_surya_lines'] = len(lines)
        ent['vlm_묶음'] = len(bx)
        raw[cn][it['key']] = ent
        nblk[cn] += len(ent['blocks'])
        rows.append(dict(corpus=cn, key=it['key'], 줄=len(lines), 묶음=len(bx),
                         블록=len(ent['blocks']), 출처='새 224판', **{kk: v for kk, v in info.items() if v}))
    # ② 라벨 50판
    for it in sorted(man50['items'], key=lambda x: x['order']):
        o = it['order']; k = GS._key(it['seed'])
        f = None
        for cand in (f'{k}_som.png', it.get('image')):
            if cand in g50:
                f = cand; break
        if f is None:
            continue
        path = os.path.join(root50, it['image'])
        gray = np.asarray(Image.open(path).convert('L')).astype(float)
        lines = DS.split_wide_lines(gray, L50[k]['lines'])[0]
        size = tuple(L50[k]['size'])
        asg, info = GS.groups_vlm(lines, dict(groups=g50[f]))
        bx = [b[:4] for _g, b in GS.boxes_of(lines, asg)]
        nb = [[b[0] / size[0], b[1] / size[1], b[2] / size[0], b[3] / size[1]] for b in bx]
        e = G.entry(path, nb, coords='norm')[0] if nb else None
        key = f"{Pl[o]['folder']}__{Pl[o]['file']}"
        ent = dict(caches['브로크만']['raw'][key])
        ent['blocks'] = (e['blocks'] if e else [])
        ent['n_surya_lines'] = len(lines)
        ent['vlm_묶음'] = len(bx)
        raw['브로크만'][key] = ent
        nblk['브로크만'] += len(ent['blocks'])
        rows.append(dict(corpus='브로크만', key=key, 줄=len(lines), 묶음=len(bx),
                         블록=len(ent['blocks']), 출처='라벨 50판 (기존 패스)',
                         **{kk: v for kk, v in info.items() if v}))

    json.dump(dict(회차=a.pass_no, 묶음_파일=[os.path.basename(x) for x in files],
                   라벨50_패스=a.pass50, 라벨50_sha256=_sha(a.pass50),
                   지시문='docs/brockmann_vlm_prompt.md', 지시문_sha256=_sha('docs/brockmann_vlm_prompt.md'),
                   새224_묶음_받은_판=len(groups), 묶음_없는_판=missing,
                   판별=rows), open(a.merged, 'w'), ensure_ascii=False, indent=1)

    for cn, r in raw.items():
        prov = MC.provenance(f'eval/vlm_corpus_measure.py (회차 {a.pass_no})', len(r))
        prov.update(grouping='VLM Set-of-Mark (group_score.groups_vlm · boxes_of) — 규칙 기반 group 아님',
                    상자_출처='VLM', vlm_회차=a.pass_no,
                    vlm_pass=(a.pass50 if cn == '브로크만' else None),
                    vlm_새224_묶음=os.path.basename(a.pass_dir),
                    prompt='docs/brockmann_vlm_prompt.md', prompt_sha256=_sha('docs/brockmann_vlm_prompt.md'),
                    model='claude-opus-5',
                    측정='measure/ground.entry — 상자는 [x1/W, y1/H, x2/W, y2/H] (여유 없음)',
                    사전등록='docs/vlm_corpus_preregister.json',
                    주의='한 캐시 안에 상자 출처를 섞지 않는다 (CLAUDE.md 규칙 7). 기존 캐시는 덮어쓰지 않았다')
        fp = os.path.join(O, f'{FILE[cn]}.json')
        json.dump(dict(raw=r, provenance=prov), open(fp, 'w'), ensure_ascii=False)
        print(f'  {cn:5} 판 {len(r):3} · 블록 {nblk[cn]:4} → {fp}')
    print(f'  묶음 없는 판 {len(missing)}')
    print('→', a.merged)


if __name__ == '__main__':
    main()
