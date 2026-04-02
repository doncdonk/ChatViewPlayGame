"""
dev_horse_test.py - 馬パーツ合成テストツール（開発用・ゲーム本体に影響しない）

使い方:
  python dev_horse_test.py

操作:
  スライダーで各パーツを切り替え・調整
  「走る」ボタンでアニメーション再生
  Seed 変更で別パターンの馬を生成
"""

import tkinter as tk
from tkinter import ttk
import os, sys, math, time, random
from PIL import Image, ImageTk, ImageEnhance, ImageFilter

IMG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")

# ── パーツ定義 ──────────────────────────────────────────
PARTS_BROWN = {
    "head":   "part_brown_02.png",
    "body":   "part_brown_08.png",
    "leg_a":  "part_brown_11.png",  # 脚フレームA（前脚伸ばし）
    "leg_b":  "part_brown_12.png",  # 脚フレームB（中間）
    "leg_c":  "part_brown_13.png",  # 脚フレームC（後脚伸ばし）
    "tail_a": "part_brown_06.png",
    "tail_b": "part_brown_09.png",
    "tail_c": "part_brown_17.png",
    "tail_d": "part_brown_18.png",
}
PARTS_WHITE = {
    "head":   "part_white_01.png",
    "body":   "part_white_02.png",
    "leg_a":  "part_white_09.png",
    "leg_b":  "part_white_10.png",
    "leg_c":  "part_white_11.png",
    "tail_a": "part_white_04.png",
    "tail_b": "part_white_08.png",
    "tail_c": "part_white_12.png",
    "tail_d": "part_white_13.png",
}

BG_COLOR = "#0a0e1a"
CANVAS_W = 900
CANVAS_H = 400

class HorsePartsDev:
    def __init__(self, root):
        self.root = root
        root.title("Horse Parts Dev Tool")
        root.configure(bg="#111")

        self._images  = {}   # キャッシュ
        self._photo   = None
        self._running = False
        self._anim_t  = 0.0
        self._job     = None

        self._build_ui()
        self._load_parts("brown")
        self._render()

    # ── UI 構築 ──────────────────────────────────────────
    def _build_ui(self):
        # 左: Canvas
        left = tk.Frame(self.root, bg="#111")
        left.pack(side="left", fill="both", expand=True, padx=8, pady=8)

        self.canvas = tk.Canvas(left, width=CANVAS_W, height=CANVAS_H,
                                bg=BG_COLOR, highlightthickness=1,
                                highlightbackground="#333")
        self.canvas.pack()

        # コントロールバー
        ctrl = tk.Frame(left, bg="#111")
        ctrl.pack(fill="x", pady=4)

        tk.Label(ctrl, text="毛色:", bg="#111", fg="#aaa",
                 font=("Courier",10)).pack(side="left")
        self._coat_var = tk.StringVar(value="brown")
        for c,l in [("brown","茶馬"),("white","白馬")]:
            tk.Radiobutton(ctrl, text=l, variable=self._coat_var, value=c,
                           bg="#111", fg="#aaa", selectcolor="#222",
                           activebackground="#111", activeforeground="#fff",
                           font=("Courier",10),
                           command=lambda v=c: self._on_coat_change(v)
                           ).pack(side="left", padx=4)

        tk.Label(ctrl, text="  Seed:", bg="#111", fg="#aaa",
                 font=("Courier",10)).pack(side="left")
        self._seed_var = tk.IntVar(value=42)
        tk.Spinbox(ctrl, textvariable=self._seed_var, from_=0, to=9999,
                   width=6, bg="#222", fg="#aaa",
                   font=("Courier",10),
                   command=self._render).pack(side="left", padx=4)

        tk.Label(ctrl, text="  速度:", bg="#111", fg="#aaa",
                 font=("Courier",10)).pack(side="left")
        self._speed_var = tk.DoubleVar(value=1.0)
        tk.Scale(ctrl, variable=self._speed_var, from_=0.2, to=3.0,
                 resolution=0.1, orient="horizontal", length=100,
                 bg="#111", fg="#aaa", troughcolor="#222",
                 highlightthickness=0).pack(side="left")

        self._anim_btn = tk.Button(ctrl, text="▶ 走る",
                                   bg="#1a3a6a", fg="#88ccff",
                                   relief="flat", font=("Courier",10,"bold"),
                                   command=self._toggle_anim)
        self._anim_btn.pack(side="left", padx=8)

        tk.Button(ctrl, text="静止", bg="#222", fg="#aaa",
                  relief="flat", font=("Courier",10),
                  command=self._stop_and_render).pack(side="left")

        # 右: パーツ調整パネル
        right = tk.Frame(self.root, bg="#111", width=220)
        right.pack(side="right", fill="y", padx=4, pady=8)
        right.pack_propagate(False)

        tk.Label(right, text="パーツ調整", bg="#111", fg="#666",
                 font=("Courier",9)).pack(anchor="w", padx=8, pady=(4,2))

        self._sliders = {}
        params = [
            ("scale",    "スケール",  0.3, 1.5, 0.7),
            ("head_x",   "頭 X",    -80,  80,  0.0),
            ("head_y",   "頭 Y",    -60,  60,  0.0),
            ("tail_idx", "尻尾",      0,   3,   0),
            ("horse_x",  "位置 X",   50, 800, 100),
            ("horse_y",  "位置 Y",   50, 350, 200),
        ]
        for key, lbl, lo, hi, default in params:
            f = tk.Frame(right, bg="#111")
            f.pack(fill="x", padx=4, pady=1)
            tk.Label(f, text=lbl, bg="#111", fg="#888",
                     font=("Courier",9), width=8, anchor="w").pack(side="left")
            var = tk.DoubleVar(value=default)
            tk.Scale(f, variable=var, from_=lo, to=hi,
                     resolution=0.5 if key not in ["tail_idx"] else 1,
                     orient="horizontal", length=130,
                     bg="#111", fg="#888", troughcolor="#222",
                     highlightthickness=0,
                     command=lambda v, k=key: self._render()).pack(side="left")
            self._sliders[key] = var

        tk.Label(right, text="\n合成情報", bg="#111", fg="#666",
                 font=("Courier",9)).pack(anchor="w", padx=8)
        self._info_var = tk.StringVar(value="")
        tk.Label(right, textvariable=self._info_var,
                 bg="#111", fg="#556", font=("Courier",8),
                 justify="left").pack(anchor="w", padx=8)

    # ── パーツ読み込み ───────────────────────────────────
    def _load_parts(self, coat):
        parts_def = PARTS_BROWN if coat == "brown" else PARTS_WHITE
        self._images = {}
        for key, fname in parts_def.items():
            path = os.path.join(IMG_DIR, fname)
            if os.path.exists(path):
                self._images[key] = Image.open(path).convert("RGBA")
            else:
                print(f"[WARN] {path} not found")

    def _on_coat_change(self, coat):
        self._load_parts(coat)
        self._render()

    # ── 合成 ────────────────────────────────────────────
    def _compose(self, anim_t=0.0):
        """パーツを合成して1枚のPIL Imageを返す"""
        scale    = self._sliders["scale"].get()
        head_dx  = int(self._sliders["head_x"].get())
        head_dy  = int(self._sliders["head_y"].get())
        tail_idx = int(self._sliders["tail_idx"].get())
        hx       = int(self._sliders["horse_x"].get())
        hy       = int(self._sliders["horse_y"].get())

        # Seed でランダム性を付与
        seed = int(self._seed_var.get())
        rng  = random.Random(seed)

        # キャンバス
        canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (10, 14, 26, 255))

        def paste(part_img, x, y):
            """透過合成"""
            if part_img is None:
                return
            canvas.paste(part_img, (int(x), int(y)), part_img)

        def scaled(key, extra_scale=1.0):
            img = self._images.get(key)
            if img is None:
                return None, 0, 0
            s = scale * extra_scale
            w = max(1, int(img.width * s))
            h = max(1, int(img.height * s))
            return img.resize((w, h), Image.LANCZOS), w, h

        # ── 脚フレーム（アニメーション）──
        # 走りのサイクル: leg_a→leg_b→leg_c→leg_b→leg_a...
        leg_frames = ["leg_a", "leg_b", "leg_c", "leg_b"]
        # 前脚と後脚で位相をずらす
        phase_front = anim_t % (2 * math.pi)
        phase_back  = (anim_t + math.pi) % (2 * math.pi)

        def leg_frame(phase):
            idx = int((math.sin(phase) + 1) / 2 * 3.99)
            return leg_frames[min(idx, 3)]

        # 胴体
        body, bw, bh = scaled("body", 1.0)
        body_x = hx
        body_y = hy - bh + 20

        # 脚（後ろ）
        leg_b_key = leg_frame(phase_back)
        leg_back, lw, lh = scaled(leg_b_key, 0.85)
        # 後脚Y揺れ
        back_dy = int(math.sin(phase_back * 0.5) * 4)
        leg_back_x = body_x + int(bw * 0.15)
        leg_back_y = body_y + bh - int(lh * 0.3) + back_dy

        # 尻尾（揺れ）
        tail_keys = ["tail_a", "tail_b", "tail_c", "tail_d"]
        tail_key  = tail_keys[tail_idx % len(tail_keys)]
        tail_anim = int(abs(math.sin(anim_t * 0.7)) * 3)
        tail_real = tail_keys[(tail_idx + tail_anim) % 4]
        tail, tw, th = scaled(tail_real, 0.8)
        tail_x = body_x - int(tw * 0.6)
        tail_y = body_y + int(bh * 0.1)

        # 脚（前）
        leg_f_key = leg_frame(phase_front)
        leg_front, lfw, lfh = scaled(leg_f_key, 0.9)
        front_dy = int(math.sin(phase_front * 0.5) * 4)
        leg_front_x = body_x + int(bw * 0.6)
        leg_front_y = body_y + bh - int(lfh * 0.3) + front_dy

        # 頭
        head, hw, hh = scaled("head", 0.95)
        # Seedで頭の微妙な位置ずらし
        seed_dx = rng.randint(-5, 5)
        seed_dy = rng.randint(-5, 5)
        # 走り時の頭の上下
        head_anim_dy = int(math.sin(anim_t) * 6)
        head_x = body_x + int(bw * 0.65) + head_dx + seed_dx
        head_y = body_y - int(hh * 0.55) + head_dy + seed_dy + head_anim_dy

        # 描画順: 尻尾→後脚→胴体→前脚→頭
        if tail:   paste(tail,       tail_x,      tail_y)
        if leg_back: paste(leg_back, leg_back_x,  leg_back_y)
        if body:   paste(body,       body_x,      body_y)
        if leg_front: paste(leg_front, leg_front_x, leg_front_y)
        if head:   paste(head,       head_x,      head_y)

        # 情報テキスト更新
        info = (f"seed={seed}\n"
                f"scale={scale:.1f}\n"
                f"body: {bw}x{bh}\n"
                f"head: {hw}x{hh}\n"
                f"leg_f: {leg_f_key}\n"
                f"leg_b: {leg_b_key}\n"
                f"tail: {tail_real}")
        self._info_var.set(info)

        return canvas

    # ── 描画 ────────────────────────────────────────────
    def _render(self, *args):
        if self._running:
            return
        composed = self._compose(0.0)
        self._photo = ImageTk.PhotoImage(composed)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self._photo)

    # ── アニメーション ───────────────────────────────────
    def _toggle_anim(self):
        if self._running:
            self._stop_and_render()
        else:
            self._running = True
            self._anim_btn.config(text="⏹ 停止", bg="#3a1a1a", fg="#ff8888")
            self._anim_t = 0.0
            self._loop()

    def _stop_and_render(self):
        self._running = False
        if self._job:
            self.root.after_cancel(self._job)
            self._job = None
        self._anim_btn.config(text="▶ 走る", bg="#1a3a6a", fg="#88ccff")
        self._render()

    def _loop(self):
        if not self._running:
            return
        speed = self._speed_var.get()
        self._anim_t += 0.12 * speed

        # 馬を横に移動させる（X座標を自動更新）
        hx_slider = self._sliders["horse_x"]
        cur_x = hx_slider.get()
        new_x = cur_x + speed * 3
        if new_x > CANVAS_W + 100:
            new_x = -200
        hx_slider.set(new_x)

        composed = self._compose(self._anim_t)
        self._photo = ImageTk.PhotoImage(composed)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self._photo)

        self._job = self.root.after(33, self._loop)  # 約30fps


def main():
    root = tk.Tk()
    app  = HorsePartsDev(root)
    root.mainloop()

if __name__ == "__main__":
    main()
