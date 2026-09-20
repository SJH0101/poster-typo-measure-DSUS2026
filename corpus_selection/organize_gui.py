#!/usr/bin/env python3
"""
포스터 코퍼스 정리기 (GUI)

더블클릭으로 실행. CSV와 이미지 폴더를 고르고 버튼만 누르면 된다.
파이썬만 있으면 되고 추가 설치는 필요 없다.
"""

import csv, os, re, shutil, traceback
from collections import Counter, defaultdict
import tkinter as tk
from tkinter import filedialog, ttk, messagebox

RATIO_TOL, WELT, EPS = 3.0, 1.4142, 0.03

# 판정은 위에서부터. 먼저 걸리는 것을 채택한다.
# 앞쪽 = 고유명사(장소·행사), 뒤쪽 = 일반 주제
SERIES_RULES = [
    # 판정은 위에서부터. 먼저 걸리는 것을 채택한다.
    # 순서가 중요하다: 행사명이 장소명보다 앞에 와야 한다.
    # ("Stadttheater Zürich - Juni-Festwochen" 은 Juni_Festwochen 으로 가야 한다)

    # 1) 고유 행사·시리즈명
    ("Musica_Viva",         ["musica viva"]),
    ("Juni_Festwochen",     ["juni-fest", "junifest", "juni fest"]),
    ("Freilichtspiele",     ["freilichtspiele"]),
    ("Kunstkredit",         ["kunstkredit", "stipendium"]),
    ("Volg",                ["volg"]),
    ("BEA",                 ["bea ", "viscount"]),

    # 2) 장소·기관
    ("Kunsthalle_Basel",    ["kunsthalle basel", "kunsthalle, basel"]),
    ("Mustermesse_Basel",   ["mustermesse"]),
    ("Gewerbemuseum_Basel", ["gewerbemuseum basel"]),
    ("Gewerbemuseum_etc",   ["gewerbemuseum"]),
    ("Opernhaus_Zuerich",   ["opernhaus"]),
    ("Tonhalle_Zuerich",    ["tonhalle", "kammermusik"]),
    ("Stadttheater_Basel",  ["stadttheater basel", "stadt theater basel"]),
    ("Stadttheater_Zuerich",["stadttheater zuerich"]),
    ("Schauspielhaus",      ["schauspielhaus"]),
    ("Stadttheater_etc",    ["stadttheater", "stadt theater"]),

    # 3) 주제
    ("Verkehr",             ["schuetzt", "laerm", "bruit", "automobil", "radfahrer",
                             "cycliste", "strassenbau", "achtung", "velo", "routier"]),
    ("Konzert",             ["konzert", "chor", "gesangverein", "requiem",
                             "casino", "sinfonie"]),
    ("Ausstellung",         ["kunstgewerbemuseum", "ausstellung", "kunsthalle",
                             "kunsthaus", "kunstmuseum", "museum", "helmhaus",
                             "galerie"]),
    ("Theater_Tanz",        ["theater", "ballett", "giselle", "mime", "oper"]),
]
def series_of(t):
    t = str(t).lower()
    for a, b in (("\u00fc","ue"),("\u00e4","ae"),("\u00f6","oe"),("\u00df","ss")):
        t = t.replace(a, b)
    for name, keys in SERIES_RULES:
        if any(k in t for k in keys):
            return name
    return "Sonstige"


def ratio_ok(r):
    try:
        return float(r.get("ratio_diff_pct", 999)) < RATIO_TOL
    except (TypeError, ValueError):
        return False


def dims_of(r):
    """h_cm/w_cm 열이 있으면 쓰고, 없으면 dimensions 문자열에서 파싱한다."""
    try:
        h, w = float(r["h_cm"]), float(r["w_cm"])
        if h > 0 and w > 0:
            return h, w
    except (TypeError, ValueError, KeyError):
        pass
    m = re.search(r"([\d.]+)\s*[×xX]\s*([\d.]+)\s*cm", str(r.get("dimensions", "")))
    if m:
        return float(m.group(1)), float(m.group(2))
    return None, None


def fmt_family(r):
    h, w = dims_of(r)
    if not h or not w:
        return "불명"
    if abs(h / w - WELT) > EPS:
        return "기타판형"
    return "Weltformat" if h >= 120 else ("F4" if h >= 95 else "소형")


def group_of(r, personal_prefix):
    # 이미 분류된 CSV라면 group 열을 그대로 쓴다
    g = str(r.get("group", "")).strip()
    if g in ("코어", "F4") or g.startswith("제외"):
        return g
    if personal_prefix and not str(r.get("designer", "")).strip().startswith(personal_prefix):
        return "제외_타인명의"
    if not ratio_ok(r):
        return "제외_비율불일치"
    f = fmt_family(r)
    return "코어" if f == "Weltformat" else ("F4" if f == "F4" else "제외_판형")


def safe(s, n=60):
    s = re.sub(r'[/\\:*?"<>|\n\r\t]', "-", str(s))
    return re.sub(r"\s+", " ", s).strip(" .")[:n] or "untitled"


def year_of(r):
    y = str(r.get("year", "")).strip()
    return y if re.fullmatch(r"(19|20)\d{2}", y) else "연도미상"


class App:
    def __init__(self, root):
        self.root = root
        root.title("포스터 코퍼스 정리기")
        root.geometry("760x620")

        self.csv_path = tk.StringVar()
        self.src_dir = tk.StringVar()
        self.out_dir = tk.StringVar()
        self.personal = tk.StringVar(value="Josef Müller-Brockmann CH, 1914")
        self.presets = {
            "브로크만": "Josef Müller-Brockmann CH, 1914",
            "호프만":   "Armin Hofmann CH, 1920",
            "루더":     "Emil Ruder CH, 1914",
            "로제":     "Richard Paul Lohse CH, 1902",
            "게르스트너": "Karl Gerstner CH, 1930",
            "전체 포함": "",
        }
        self.do_move = tk.BooleanVar(value=False)

        pad = {"padx": 12, "pady": 5}

        # --- 입력 ---
        f = ttk.LabelFrame(root, text="1. 파일 선택")
        f.pack(fill="x", **pad)
        self._row(f, "메타데이터 CSV", self.csv_path, self.pick_csv, 0)
        self._row(f, "이미지 폴더", self.src_dir, self.pick_src, 1)
        self._row(f, "저장할 곳", self.out_dir, self.pick_out, 2)
        f.columnconfigure(1, weight=1)

        # --- 옵션 ---
        g = ttk.LabelFrame(root, text="2. 옵션")
        g.pack(fill="x", **pad)
        ttk.Label(g, text="개인 명의 판별 문자열").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(g, textvariable=self.personal).grid(row=0, column=1, sticky="ew", padx=8)
        pf = ttk.Frame(g)
        pf.grid(row=1, column=0, columnspan=2, sticky="w", padx=8)
        for label, val in self.presets.items():
            ttk.Button(pf, text=label, width=8,
                       command=lambda v=val: self.personal.set(v)).pack(side="left", padx=2)
        ttk.Label(g, text="(designer 열이 이 문자열로 시작하면 개인 작업으로 본다. 비우면 전부 포함)",
                  foreground="#666").grid(row=3, column=0, columnspan=2, sticky="w", padx=8)
        ttk.Checkbutton(g, text="복사 대신 이동 (원본이 사라짐)",
                        variable=self.do_move).grid(row=4, column=0, columnspan=2, sticky="w", padx=8, pady=6)
        g.columnconfigure(1, weight=1)

        # --- 버튼 ---
        b = ttk.Frame(root)
        b.pack(fill="x", **pad)
        ttk.Button(b, text="미리보기", command=lambda: self.run(True)).pack(side="left")
        self.go_btn = ttk.Button(b, text="정리 실행", command=lambda: self.run(False))
        self.go_btn.pack(side="left", padx=8)
        self.prog = ttk.Progressbar(b, mode="determinate")
        self.prog.pack(side="left", fill="x", expand=True, padx=8)

        # --- 로그 ---
        l = ttk.LabelFrame(root, text="결과")
        l.pack(fill="both", expand=True, **pad)
        self.log = tk.Text(l, wrap="none", font=("Menlo", 11), bg="#1a1a1a", fg="#e0e0e0")
        sb = ttk.Scrollbar(l, command=self.log.yview)
        self.log.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.log.pack(fill="both", expand=True)

        self.say("CSV와 이미지 폴더를 고른 뒤 [미리보기]를 눌러보세요.\n")

    def _row(self, parent, label, var, cmd, r):
        ttk.Label(parent, text=label).grid(row=r, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(parent, textvariable=var).grid(row=r, column=1, sticky="ew", padx=8)
        ttk.Button(parent, text="찾기", command=cmd).grid(row=r, column=2, padx=8)

    def say(self, s):
        self.log.insert("end", s)
        self.log.see("end")
        self.root.update_idletasks()

    def pick_csv(self):
        p = filedialog.askopenfilename(title="메타데이터 CSV",
                                       filetypes=[("CSV", "*.csv"), ("전체", "*.*")])
        if p:
            self.csv_path.set(p)
            if not self.src_dir.get():
                self.src_dir.set(os.path.dirname(p))
            if not self.out_dir.get():
                self.out_dir.set(os.path.join(os.path.dirname(p), "corpus"))

    def pick_src(self):
        p = filedialog.askdirectory(title="이미지가 들어있는 폴더")
        if p:
            self.src_dir.set(p)

    def pick_out(self):
        p = filedialog.askdirectory(title="정리된 결과를 만들 곳")
        if p:
            self.out_dir.set(os.path.join(p, "corpus"))

    # ---------- 핵심 ----------

    def build_plan(self):
        with open(self.csv_path.get(), encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))

        src = self.src_dir.get()
        # 폴더 전체를 훑어 파일명 → 실제경로 사전을 만든다 (하위폴더 포함)
        index = {}
        for dirpath, _, files in os.walk(src):
            for fn in files:
                index.setdefault(fn, os.path.join(dirpath, fn))

        prefix = self.personal.get().strip()
        plan, missing = [], []

        for r in rows:
            grp = group_of(r, prefix)
            ser = str(r.get("series", "")).strip() or series_of(r.get("title", ""))
            sub = os.path.join(grp, ser) if grp in ("코어", "F4") else grp
            name = f"{year_of(r)}_{safe(r.get('title',''))}.jpg"
            dest = os.path.join(self.out_dir.get(), sub, name)

            raw = str(r.get("image_filename", "")).strip()
            found = None
            if raw:
                for c in (raw, os.path.join(src, raw), index.get(os.path.basename(raw))):
                    if c and os.path.isfile(c):
                        found = c
                        break
            if not found:
                missing.append(r.get("title", "?")[:55])
                continue
            plan.append((found, dest, grp, sub, year_of(r), r))

        # 파일명 중복 처리
        seen, final = Counter(), []
        for s, d, g, sub, y, r in plan:
            seen[d] += 1
            if seen[d] > 1:
                b, e = os.path.splitext(d)
                d = f"{b}_{seen[d]}{e}"
            final.append((s, d, g, sub, y, r))
        return final, missing, len(rows)

    def run(self, preview):
        if not self.csv_path.get() or not self.src_dir.get():
            messagebox.showwarning("입력 필요", "CSV와 이미지 폴더를 먼저 고르세요.")
            return
        self.go_btn.config(state="disabled")
        self.root.after(50, lambda: self._work(preview))

    def _work(self, preview):
        try:
            self.log.delete("1.0", "end")
            plan, missing, total = self.build_plan()

            self.say(f"CSV {total}행\n\n=== 분류 ===\n")
            for g, n in Counter(x[2] for x in plan).most_common():
                self.say(f"  {n:4d}  {g}\n")

            self.say("\n=== 폴더별 ===\n")
            bysub = defaultdict(list)
            for _, _, _, sub, y, _ in plan:
                bysub[sub].append(y)
            for sub in sorted(bysub):
                ys = sorted(y for y in bysub[sub] if y != "연도미상")
                span = f"{ys[0]}–{ys[-1]}" if ys else "-"
                self.say(f"  {len(bysub[sub]):4d}  {sub:34s} {span}\n")

            if missing:
                self.say(f"\n=== 이미지 못 찾음 {len(missing)}건 ===\n")
                for m in missing[:12]:
                    self.say(f"  {m}\n")
                if len(missing) > 12:
                    self.say(f"  ... 외 {len(missing)-12}건\n")
                self.say("  → 이미지 폴더 경로를 확인하세요\n")

            if preview:
                self.say("\n[미리보기] 복사하지 않았습니다. 맞으면 [정리 실행]을 누르세요.\n")
                return

            self.say(f"\n{'이동' if self.do_move.get() else '복사'} 중...\n")
            self.prog["maximum"] = len(plan)
            done = 0
            for i, (s, d, *_ ) in enumerate(plan, 1):
                os.makedirs(os.path.dirname(d), exist_ok=True)
                try:
                    (shutil.move if self.do_move.get() else shutil.copy2)(s, d)
                    done += 1
                except Exception as e:
                    self.say(f"  실패: {os.path.basename(s)} — {e}\n")
                self.prog["value"] = i
                if i % 20 == 0:
                    self.root.update_idletasks()

            # 목록 CSV
            idx = os.path.join(self.out_dir.get(), "index.csv")
            keys = ["group", "folder", "year", "series", "title", "dimensions",
                    "px_w", "px_h", "ratio_diff_pct", "new_path", "url"]
            with open(idx, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
                w.writeheader()
                for s, d, g, sub, y, r in sorted(plan, key=lambda x: (x[3], x[4])):
                    w.writerow({"group": g, "folder": sub, "year": y,
                                "series": series_of(r.get("title", "")),
                                "title": r.get("title", "")[:90],
                                "dimensions": r.get("dimensions", ""),
                                "px_w": r.get("px_w", ""), "px_h": r.get("px_h", ""),
                                "ratio_diff_pct": r.get("ratio_diff_pct", ""),
                                "new_path": os.path.relpath(d, self.out_dir.get()),
                                "url": r.get("url", "")})

            self.say(f"\n완료: {done}건\n{self.out_dir.get()}\n목록 → index.csv\n")
            messagebox.showinfo("완료", f"{done}건 정리했습니다.")

        except Exception as e:
            self.say("\n=== 오류 ===\n" + traceback.format_exc() + "\n")
        finally:
            self.go_btn.config(state="normal")


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
