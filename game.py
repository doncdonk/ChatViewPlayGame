"""
ChatViewPlayGame
- tkinter (Python標準) で描画
- 追加インストール不要（Twitch接続は asyncio+ssl でIRC直結）

画面遷移:
  App
   ├─ TopMenuScreen        … ゲーム選択
   ├─ SettingsScreen       … トークン設定
   └─ MinesweeperLobby     … チャンネル名・難易度選択
        └─ GameScreen      … ゲーム本体
"""
import tkinter as tk
import os
import sys
import threading
import asyncio
import time
import random
import math

from config import load_config, save_config
from minesweeper import Minesweeper
from twitch_client import TwitchClient
from reversi import Reversi, BLACK, WHITE, EMPTY
from horserace import (generate_race, run_race, IconHorseRenderer,
                        ImageHorseRenderer, calc_odds,
                        load_horse_sprites, load_gate_image)

# ══════════════════════════════════════════════
#  定数
# ══════════════════════════════════════════════
CELL         = 38
HEADER_H     = 90
SIDEBAR_W    = 260
FPS_INTERVAL = 33
RESTART_SEC  = 5.0

# ── テーマ定義 ──────────────────────────────────
THEMES = {
    "NightBlue": {
        "BG":         "#0D0F1A", "HEADER_BG":  "#141828", "SIDEBAR_BG": "#0F1120",
        "CELL_HID":   "#242840", "CELL_HOV":   "#363C64", "CELL_OPEN":  "#161C30",
        "CELL_BORDER":"#3C4470", "MINE_COL":   "#FF3C50", "FLAG_COL":   "#FFC832",
        "SAFE_COL":   "#50DCA0", "ACCENT_COL": "#64B4FF", "TEXT_W":     "#E6EBFF",
        "TEXT_G":     "#787896", "BOOM_BG":    "#500A10", "BTN_DARK":   "#1E2238",
        "BTN_DARK_H": "#2A3050", "BTN_MENU":   "#2A2F50", "BTN_MENU_H": "#3A4070",
        "DISABLED_BG":"#181C2C", "DISABLED_FG":"#3A3F58",
        "NUM_COLORS": [None,"#64B4FF","#50DCA0","#FF5050","#B464FF","#FFA040","#3CDCDC","#DCDCDC","#969696"],
        "DANMAKU":    ["#FFFFFF","#64B4FF","#50DCA0","#FFC832","#FF9040","#C882FF","#78FFDC"],
    },
    "TerminalGreen": {
        "BG":         "#050A05", "HEADER_BG":  "#0A140A", "SIDEBAR_BG": "#0A140A",
        "CELL_HID":   "#0D1A0D", "CELL_HOV":   "#163016", "CELL_OPEN":  "#050A05",
        "CELL_BORDER":"#1A3A1A", "MINE_COL":   "#FF4444", "FLAG_COL":   "#FFAA00",
        "SAFE_COL":   "#00FF41", "ACCENT_COL": "#00FF41", "TEXT_W":     "#AAFFAA",
        "TEXT_G":     "#00AA20", "BOOM_BG":    "#3A0000", "BTN_DARK":   "#0A140A",
        "BTN_DARK_H": "#122012", "BTN_MENU":   "#0D1A0D", "BTN_MENU_H": "#163016",
        "DISABLED_BG":"#080E08", "DISABLED_FG":"#1A3A1A",
        "NUM_COLORS": [None,"#00FF41","#AAFFAA","#FF4444","#FFAA00","#00CCFF","#88FF88","#CCFFCC","#559955"],
        "DANMAKU":    ["#00FF41","#AAFFAA","#FFAA00","#00CCFF","#88FF88","#FFFFFF","#CCFFCC"],
    },
    "ArcadeNeon": {
        "BG":         "#0A0010", "HEADER_BG":  "#110022", "SIDEBAR_BG": "#0D0020",
        "CELL_HID":   "#1A0030", "CELL_HOV":   "#280048", "CELL_OPEN":  "#080015",
        "CELL_BORDER":"#440088", "MINE_COL":   "#FF0055", "FLAG_COL":   "#FFFF00",
        "SAFE_COL":   "#00FFCC", "ACCENT_COL": "#FF00FF", "TEXT_W":     "#FF99FF",
        "TEXT_G":     "#AA00AA", "BOOM_BG":    "#440010", "BTN_DARK":   "#110022",
        "BTN_DARK_H": "#1A0033", "BTN_MENU":   "#1A0030", "BTN_MENU_H": "#280048",
        "DISABLED_BG":"#080010", "DISABLED_FG":"#330055",
        "NUM_COLORS": [None,"#FF00FF","#00FFFF","#FF0055","#FFFF00","#FF8800","#00FF88","#FF99FF","#AA00AA"],
        "DANMAKU":    ["#FF00FF","#00FFFF","#FFFF00","#FF0055","#FF8800","#00FF88","#FFFFFF"],
    },
    "SteelGray": {
        "BG":         "#1A1C1E", "HEADER_BG":  "#242628", "SIDEBAR_BG": "#1E2124",
        "CELL_HID":   "#2C3034", "CELL_HOV":   "#383C40", "CELL_OPEN":  "#141618",
        "CELL_BORDER":"#445060", "MINE_COL":   "#CC2200", "FLAG_COL":   "#FF6600",
        "SAFE_COL":   "#88BBCC", "ACCENT_COL": "#C0C8D0", "TEXT_W":     "#E0E8F0",
        "TEXT_G":     "#607080", "BOOM_BG":    "#3A0800", "BTN_DARK":   "#242628",
        "BTN_DARK_H": "#2C3034", "BTN_MENU":   "#2C3034", "BTN_MENU_H": "#383C40",
        "DISABLED_BG":"#181A1C", "DISABLED_FG":"#404850",
        "NUM_COLORS": [None,"#8899AA","#88BBCC","#CC4422","#AA8866","#AABB88","#66AACC","#CCCCCC","#777777"],
        "DANMAKU":    ["#C0C8D0","#8899AA","#88BBCC","#FF6600","#AABB88","#E0E8F0","#66AACC"],
    },
    "SunsetWarm": {
        "BG":         "#1A0D05", "HEADER_BG":  "#241408", "SIDEBAR_BG": "#1E1006",
        "CELL_HID":   "#2A1508", "CELL_HOV":   "#3A1E0A", "CELL_OPEN":  "#120A04",
        "CELL_BORDER":"#604020", "MINE_COL":   "#FF3040", "FLAG_COL":   "#FFD700",
        "SAFE_COL":   "#FF9060", "ACCENT_COL": "#FF8040", "TEXT_W":     "#FFD0A0",
        "TEXT_G":     "#A05030", "BOOM_BG":    "#400008", "BTN_DARK":   "#241408",
        "BTN_DARK_H": "#2A1810", "BTN_MENU":   "#2A1508", "BTN_MENU_H": "#3A1E0A",
        "DISABLED_BG":"#140A04", "DISABLED_FG":"#503020",
        "NUM_COLORS": [None,"#FF8040","#FFD700","#FF3040","#FF60A0","#FF6020","#FFB060","#FFD0A0","#A06040"],
        "DANMAKU":    ["#FF8040","#FFD700","#FF9060","#FF3040","#FFB060","#FFD0A0","#FF60A0"],
    },
    "IceWhite": {
        "BG":         "#E8F0F8", "HEADER_BG":  "#D0DFF0", "SIDEBAR_BG": "#D8E8F4",
        "CELL_HID":   "#C8D8EC", "CELL_HOV":   "#B8CCE4", "CELL_OPEN":  "#EEF4FC",
        "CELL_BORDER":"#90AAC8", "MINE_COL":   "#CC0020", "FLAG_COL":   "#0055CC",
        "SAFE_COL":   "#006688", "ACCENT_COL": "#1A3A6A", "TEXT_W":     "#0A1A30",
        "TEXT_G":     "#4A6080", "BOOM_BG":    "#FFCCCC", "BTN_DARK":   "#D0DFF0",
        "BTN_DARK_H": "#C0D0E8", "BTN_MENU":   "#C8D8EC", "BTN_MENU_H": "#B8CCE4",
        "DISABLED_BG":"#DCE8F4", "DISABLED_FG":"#90A8C4",
        "NUM_COLORS": [None,"#1A5A9A","#006688","#CC0020","#7700AA","#CC6600","#008899","#334455","#778899"],
        "DANMAKU":    ["#1A3A6A","#006688","#0055CC","#CC0020","#7700AA","#CC6600","#1A5A9A"],
    },
    "VoidPurple": {
        "BG":         "#060010", "HEADER_BG":  "#0C0020", "SIDEBAR_BG": "#0A0018",
        "CELL_HID":   "#120028", "CELL_HOV":   "#1C0040", "CELL_OPEN":  "#040008",
        "CELL_BORDER":"#440088", "MINE_COL":   "#FF2266", "FLAG_COL":   "#FFCC00",
        "SAFE_COL":   "#AA44FF", "ACCENT_COL": "#CC44FF", "TEXT_W":     "#EE99FF",
        "TEXT_G":     "#884499", "BOOM_BG":    "#330010", "BTN_DARK":   "#0C0020",
        "BTN_DARK_H": "#140030", "BTN_MENU":   "#120028", "BTN_MENU_H": "#1C0040",
        "DISABLED_BG":"#08000E", "DISABLED_FG":"#280050",
        "NUM_COLORS": [None,"#CC44FF","#AA44FF","#FF2266","#FFCC00","#FF8844","#44AAFF","#EE99FF","#884499"],
        "DANMAKU":    ["#CC44FF","#EE99FF","#FFCC00","#FF2266","#AA44FF","#44AAFF","#FFFFFF"],
    },
}

# アクティブテーマカラーをグローバルに展開する関数
def apply_theme(name):
    global BG,HEADER_BG,SIDEBAR_BG,CELL_HID,CELL_HOV,CELL_OPEN,CELL_BORDER
    global MINE_COL,FLAG_COL,SAFE_COL,ACCENT_COL,TEXT_W,TEXT_G,BOOM_BG
    global BTN_DARK,BTN_DARK_H,BTN_MENU,BTN_MENU_H,DISABLED_BG,DISABLED_FG
    global NUM_COLORS, DANMAKU_COLORS
    t = THEMES.get(name, THEMES["NightBlue"])
    BG=t["BG"]; HEADER_BG=t["HEADER_BG"]; SIDEBAR_BG=t["SIDEBAR_BG"]
    CELL_HID=t["CELL_HID"]; CELL_HOV=t["CELL_HOV"]; CELL_OPEN=t["CELL_OPEN"]
    CELL_BORDER=t["CELL_BORDER"]; MINE_COL=t["MINE_COL"]; FLAG_COL=t["FLAG_COL"]
    SAFE_COL=t["SAFE_COL"]; ACCENT_COL=t["ACCENT_COL"]; TEXT_W=t["TEXT_W"]
    TEXT_G=t["TEXT_G"]; BOOM_BG=t["BOOM_BG"]; BTN_DARK=t["BTN_DARK"]
    BTN_DARK_H=t["BTN_DARK_H"]; BTN_MENU=t["BTN_MENU"]; BTN_MENU_H=t["BTN_MENU_H"]
    DISABLED_BG=t["DISABLED_BG"]; DISABLED_FG=t["DISABLED_FG"]
    NUM_COLORS=t["NUM_COLORS"]; DANMAKU_COLORS=t["DANMAKU"]

# デフォルトテーマを適用
BG=HEADER_BG=SIDEBAR_BG=CELL_HID=CELL_HOV=CELL_OPEN=CELL_BORDER=""
MINE_COL=FLAG_COL=SAFE_COL=ACCENT_COL=TEXT_W=TEXT_G=BOOM_BG=""
BTN_DARK=BTN_DARK_H=BTN_MENU=BTN_MENU_H=DISABLED_BG=DISABLED_FG=""
NUM_COLORS=[]; DANMAKU_COLORS=[]
apply_theme("NightBlue")

HR_COLORS = [
    "#DDDDDD","#888888","#FF4466","#4488FF",
    "#FFCC00","#44DD88","#FF8800","#FF66AA",
]
HR_LANE_H  = 68   # 1レーンの高さ
HR_HORSE_W  = 300  # 左カラム: 馬情報
HR_JOCKEY_W = 200  # 中カラム: 騎手情報
HR_INFO_W   = HR_HORSE_W + HR_JOCKEY_W  # 左+中 合計幅
HR_FPS     = 30

PT_PANEL_W = 130   # ツールパネル幅
PT_COLORS  = [
    "#FFFFFF","#CCCCCC","#888888","#000000",
    "#FF3344","#FF8800","#FFCC00","#44DD44",
    "#00AAFF","#4444FF","#AA44FF","#FF44AA",
    "#00DDCC","#884400","#005500","#000044",
]




# ── 解像度プリセット ────────────────────────────
RESOLUTIONS = {
    "1280x720  (720p)":  (1280, 720),
    "1600x900  (900p)":  (1600, 900),
    "1920x1080 (1080p)": (1920, 1080),
}
DEFAULT_RES = "1600x900  (900p)"

def calc_cell(cols, rows, win_w, win_h, sidebar_w, header_h):
    """盤面セルサイズを解像度に合わせて自動計算"""
    avail_w = win_w - sidebar_w
    avail_h = win_h - header_h
    return max(10, min(avail_w // cols, avail_h // rows))


# 固定難易度プリセット
PRESET_DIFFICULTIES = {
    "小  9×9   地雷10":  (9,  9,  10),
    "中  16×16  地雷40": (16, 16, 40),
    "大  26×16  地雷99": (26, 16, 99),
}

# 連続モードの難化ステップ（クリアごとに地雷+N個）
ENDLESS_MINE_STEP = 3


# ══════════════════════════════════════════════
#  パーティクル
# ══════════════════════════════════════════════
class Particle:
    def __init__(self, canvas, x, y, color):
        self.canvas = canvas
        self.x  = float(x)
        self.y  = float(y)
        self.vx = random.uniform(-5, 5)
        self.vy = random.uniform(-9, -2)
        self.life  = 1.0
        self.decay = random.uniform(0.025, 0.055)
        self.r  = random.randint(3, 7)
        self.id = canvas.create_oval(
            x-self.r, y-self.r, x+self.r, y+self.r,
            fill=color, outline="")

    def update(self):
        self.x  += self.vx
        self.y  += self.vy
        self.vy += 0.4
        self.life -= self.decay
        if self.life <= 0:
            self.canvas.delete(self.id)
            return False
        r = max(1, int(self.r * self.life))
        self.canvas.coords(self.id, self.x-r, self.y-r, self.x+r, self.y+r)
        return True


# ══════════════════════════════════════════════
#  弾幕
# ══════════════════════════════════════════════
class DanmakuMsg:
    SLOT_H    = 30
    MAX_SLOTS = 16

    def __init__(self, canvas, username, text, screen_w):
        txt   = f"{username}: {text}"[:48]
        color = random.choice(DANMAKU_COLORS)
        slot  = random.randint(0, self.MAX_SLOTS - 1)
        self.canvas = canvas
        self.x      = float(screen_w + 10)
        self.y      = float(8 + slot * self.SLOT_H)
        self.speed  = random.uniform(190, 290)
        self.alive  = True
        self.shadow_id = canvas.create_text(
            self.x+2, self.y+2, text=txt,
            fill="#000000", anchor="w", font=("Courier", 13, "bold"))
        self.text_id = canvas.create_text(
            self.x, self.y, text=txt,
            fill=color, anchor="w", font=("Courier", 13, "bold"))

    def update(self, dt):
        dx = self.speed * dt
        self.x -= dx
        self.canvas.move(self.text_id,   -dx, 0)
        self.canvas.move(self.shadow_id, -dx, 0)
        if self.x + 600 < 0:
            self.canvas.delete(self.text_id)
            self.canvas.delete(self.shadow_id)
            self.alive = False


# ══════════════════════════════════════════════
#  共通ユーティリティ
# ══════════════════════════════════════════════
def clear_root(root):
    for w in root.winfo_children():
        w.destroy()

def make_label(parent, text, fg=None, font=None, **kw):
    return tk.Label(parent, text=text,
                    bg=BG, fg=fg or TEXT_W,
                    font=font or ("Courier", 12),
                    **kw)

def make_btn(parent, text, cmd, bg=None, fg=None, **kw):
    return tk.Button(parent, text=text, command=cmd,
                     bg=bg or BTN_MENU, fg=fg or TEXT_W,
                     font=("Courier", 13, "bold"),
                     relief="flat", bd=0,
                     padx=14, pady=8,
                     cursor="hand2",
                     activebackground=BTN_MENU_H,
                     activeforeground=TEXT_W,
                     **kw)


# ══════════════════════════════════════════════
#  設定画面（トークン専用）
# ══════════════════════════════════════════════
class SettingsScreen:
    def __init__(self, root, cfg, on_back):
        self.root    = root
        self.cfg     = cfg
        self.on_back = on_back

        root.title("ChatViewPlayGame - 設定")
        root.configure(bg=BG)

        # ── ヘッダー（固定）──
        make_label(root, "⚙  設定", fg=ACCENT_COL,
                   font=("Courier", 20, "bold")).pack(pady=(24, 4))
        make_label(root, "Twitch connection settings",
                   fg=TEXT_G, font=("Courier", 11)).pack(pady=(0, 8))

        # ── スクロール可能エリア ──
        container = tk.Frame(root, bg=BG)
        container.pack(fill="both", expand=True, padx=0, pady=0)

        canvas = tk.Canvas(container, bg=BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical",
                                 command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        frame = tk.Frame(canvas, bg=BG)
        frame_id = canvas.create_window((0, 0), window=frame, anchor="nw")

        def _on_frame_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        def _on_canvas_configure(e):
            canvas.itemconfig(frame_id, width=e.width)
        frame.bind("<Configure>", _on_frame_configure)
        canvas.bind("<Configure>", _on_canvas_configure)

        # マウスホイールでスクロール
        def _on_mousewheel(e):
            canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # padxはframe側で
        frame.configure(padx=36)

        # ── ウィンドウサイズ ──
        make_label(frame, "Window Size:",
                   font=("Courier", 12, "bold"), anchor="w").pack(fill="x", pady=(0, 6))
        self.res_var = tk.StringVar(value=cfg.get("resolution", DEFAULT_RES))
        res_frame = tk.Frame(frame, bg=BG)
        res_frame.pack(fill="x", pady=(0, 14))
        for name in RESOLUTIONS:
            tk.Radiobutton(res_frame, text=name, variable=self.res_var, value=name,
                           bg=BG, fg=TEXT_W, selectcolor=CELL_HID,
                           activebackground=BG, activeforeground=ACCENT_COL,
                           font=("Courier", 11), anchor="w").pack(fill="x", pady=1)
        make_label(frame, "* Takes effect on next game start",
                   fg=TEXT_G, font=("Courier", 9)).pack(anchor="w", pady=(0, 10))

        tk.Frame(frame, bg=CELL_BORDER, height=1).pack(fill="x", pady=(0, 12))

        # ── テーマ選択 ──
        make_label(frame, "Theme:",
                   font=("Courier", 12, "bold"), anchor="w").pack(fill="x", pady=(0, 6))
        self.theme_var = tk.StringVar(value=cfg.get("theme", "NightBlue"))
        theme_frame = tk.Frame(frame, bg=BG)
        theme_frame.pack(fill="x", pady=(0, 14))
        theme_names = list(THEMES.keys())
        for i, name in enumerate(theme_names):
            rb = tk.Radiobutton(theme_frame, text=name, variable=self.theme_var, value=name,
                                bg=BG, fg=TEXT_W, selectcolor=CELL_HID,
                                activebackground=BG, activeforeground=ACCENT_COL,
                                font=("Courier", 11), anchor="w",
                                command=self._preview_theme)
            rb.grid(row=i//2, column=i%2, sticky="w", padx=(0,20), pady=1)

        tk.Frame(frame, bg=CELL_BORDER, height=1).pack(fill="x", pady=(0, 12))

        make_label(frame, "Twitch Channel Name:",
                   font=("Courier", 12, "bold"), anchor="w").pack(fill="x", pady=(0, 4))
        self.ch_var = tk.StringVar(value=cfg.get("channel", ""))
        tk.Entry(frame, textvariable=self.ch_var, width=44,
                 bg=CELL_HID, fg=TEXT_W, insertbackground=TEXT_W,
                 relief="flat", font=("Courier", 13), bd=6).pack(fill="x")

        make_label(frame, "OAuth Token  (oauth:xxxxx):",
                   font=("Courier", 12, "bold"), anchor="w").pack(fill="x", pady=(12, 4))

        self.tk_var = tk.StringVar(value=cfg.get("token", ""))
        tk.Entry(frame, textvariable=self.tk_var, width=44, show="●",
                 bg=CELL_HID, fg=ACCENT_COL, insertbackground=TEXT_W,
                 relief="flat", font=("Courier", 13), bd=6).pack(fill="x")

        make_label(frame, "▶ https://twitchtokengenerator.com/ で「Bot Chat Token」を取得",
                   fg=TEXT_G, font=("Courier", 10)).pack(anchor="w", pady=(4, 0))
        make_label(frame, "  ※ 取得したトークンの先頭に oauth: を付けて入力してください",
                   fg=TEXT_G, font=("Courier", 10)).pack(anchor="w", pady=(0, 16))

        self.err_var = tk.StringVar()
        tk.Label(frame, textvariable=self.err_var, bg=BG, fg=MINE_COL,
                 font=("Courier", 11)).pack(pady=(0, 4))

        bf = tk.Frame(frame, bg=BG)
        bf.pack(fill="x", pady=(8, 20))
        make_btn(bf, "◀  戻る",         self._back).pack(side="left")
        make_btn(bf, "💾  保存して戻る", self._save,
                 bg=SAFE_COL, fg=BG).pack(side="right")

    def _preview_theme(self):
        """ラジオボタン変更時にテーマをプレビュー適用"""
        apply_theme(self.theme_var.get())

    def _save(self):
        channel = self.ch_var.get().strip().lower()
        token   = self.tk_var.get().strip()
        if not channel:
            self.err_var.set("⚠ チャンネル名を入力してください")
            return
        if not token.startswith("oauth:"):
            self.err_var.set("⚠ トークンは oauth: から始まります")
            return
        res_changed = self.res_var.get() != self.cfg.get("resolution", DEFAULT_RES)
        self.cfg["channel"]    = channel
        self.cfg["token"]      = token
        self.cfg["theme"]      = self.theme_var.get()
        self.cfg["resolution"] = self.res_var.get()
        apply_theme(self.cfg["theme"])
        save_config(self.cfg)
        if res_changed:
            self._show_restart_prompt()
        else:
            self.on_back()

    def _show_restart_prompt(self):
        """解像度変更時の再起動ダイアログ"""
        # 既存のウィジェットを一旦隠してプロンプトを表示
        for w in self.root.winfo_children():
            w.pack_forget()

        frame = tk.Frame(self.root, bg=BG)
        frame.pack(expand=True)

        make_label(frame, "✅  設定を保存しました",
                   fg=SAFE_COL, font=("Courier", 16, "bold")).pack(pady=(40, 8))
        make_label(frame, "ウィンドウサイズの変更を反映するには",
                   fg=TEXT_W, font=("Courier", 12)).pack()
        make_label(frame, "アプリを再起動してください。",
                   fg=TEXT_W, font=("Courier", 12)).pack(pady=(0, 32))

        bf = tk.Frame(frame, bg=BG)
        bf.pack()
        make_btn(bf, "↩  再起動せず戻る", self.on_back,
                 bg=BTN_DARK).pack(side="left", padx=(0, 12))
        make_btn(bf, "🔄  今すぐ再起動", self._restart_app,
                 bg=SAFE_COL, fg=BG).pack(side="left")

    def _restart_app(self):
        """アプリを再起動する"""
        self.root.destroy()
        import subprocess
        subprocess.Popen([sys.executable] + sys.argv)

    def _back(self):
        apply_theme(self.cfg.get("theme", "NightBlue"))
        self.on_back()


# ══════════════════════════════════════════════
#  トップメニュー（ゲーム選択）
# ══════════════════════════════════════════════
GAME_CATALOG = [
    {
        "id":      "minesweeper",
        "icon":    "💣",
        "title":   "ViewBomb",
        "desc":    "A1 to open  /  flag A1 to flag",
        "ready":   True,
    },
    {
        "id":      "reversi",
        "icon":    "♟",
        "title":   "チャットvsリバーシ",
        "desc":    "チャットと配信者がリバーシで対決",
        "ready":   True,
    },
    {
        "id":      "horserace",
        "icon":    "🏇",
        "title":   "競馬",
        "desc":    "コメントでレースに投票して参加",
        "ready":   True,
    },
    {
        "id":      "paint",
        "icon":    "🎨",
        "title":   "ペイント",
        "desc":    "お絵描き配信  チャットが弾幕で流れる",
        "ready":   True,
    },
]

class TopMenuScreen:
    def __init__(self, root, cfg, on_select_game, on_settings):
        self.root           = root
        self.cfg            = cfg
        self.on_select_game = on_select_game
        self.on_settings    = on_settings

        root.title("ChatViewPlayGame")
        root.configure(bg=BG)

        # ヘッダー
        make_label(root, "🎮 ChatViewPlayGame",
                   fg=ACCENT_COL, font=("Courier", 22, "bold")).pack(pady=(28, 4))
        make_label(root, "配信者向け チャット連動ゲームランチャー",
                   fg=TEXT_G, font=("Courier", 11)).pack(pady=(0, 6))

        # チャンネル名・トークン状態
        channel = cfg.get("channel", "")
        token   = cfg.get("token", "")
        ch_ok   = bool(channel)
        tk_ok   = token.startswith("oauth:") and len(token) > 10
        if ch_ok and tk_ok:
            status_txt = f"📺 {channel}  |  🔑 Ready ✅"
            status_fg  = SAFE_COL
        else:
            missing = []
            if not ch_ok: missing.append("Channel")
            if not tk_ok: missing.append("Token")
            status_txt = "⚠ Not set: " + ", ".join(missing) + "  → Settings"
            status_fg  = FLAG_COL
        make_label(root, status_txt, fg=status_fg,
                   font=("Courier", 10)).pack(pady=(0, 6))

        # オンライン/オフライン トグル
        self.online_var = tk.BooleanVar(value=cfg.get("online_mode", True))
        tog_frame = tk.Frame(root, bg=BG)
        tog_frame.pack(pady=(0, 14))
        self._online_btn = tk.Button(
            tog_frame,
            text=self._online_label(),
            font=("Courier", 11, "bold"),
            relief="flat", bd=0, padx=14, pady=4,
            cursor="hand2",
            command=self._toggle_online,
            **self._online_style()
        )
        self._online_btn.pack()
        make_label(tog_frame,
                   "* Offline: play without Twitch connection",
                   fg=TEXT_G, font=("Courier", 9)).pack(pady=(3,0))

        # ゲームカード一覧
        cards = tk.Frame(root, bg=BG)
        cards.pack(padx=28, pady=(0, 8))

        for game in GAME_CATALOG:
            self._make_card(cards, game)

        # 区切り
        tk.Frame(root, bg=CELL_BORDER, height=1).pack(fill="x", padx=28, pady=12)

        # 設定ボタン
        bf = tk.Frame(root, bg=BG)
        bf.pack(pady=(0, 24))
        make_btn(bf, "⚙  Settings", on_settings,
                 bg=BTN_DARK).pack()

    def _online_label(self):
        return "🌐 Online" if self.online_var.get() else "📴 Offline"

    def _online_style(self):
        if self.online_var.get():
            return {"bg": SAFE_COL, "fg": BG,
                    "activebackground": "#40CC90", "activeforeground": BG}
        else:
            return {"bg": BTN_DARK, "fg": TEXT_G,
                    "activebackground": BTN_DARK_H, "activeforeground": TEXT_W}

    def _toggle_online(self):
        self.online_var.set(not self.online_var.get())
        self.cfg["online_mode"] = self.online_var.get()
        save_config(self.cfg)
        self._online_btn.config(
            text=self._online_label(),
            **self._online_style()
        )

    def _make_card(self, parent, game):
        ready = game["ready"]
        card_bg  = BTN_DARK   if ready else DISABLED_BG
        card_fg  = TEXT_W     if ready else DISABLED_FG
        desc_fg  = TEXT_G     if ready else DISABLED_FG
        badge    = ""         if ready else "  [準備中]"

        outer = tk.Frame(parent, bg=CELL_BORDER, padx=1, pady=1)
        outer.pack(fill="x", pady=5)

        inner = tk.Frame(outer, bg=card_bg, padx=16, pady=12)
        inner.pack(fill="x")

        left = tk.Frame(inner, bg=card_bg)
        left.pack(side="left", fill="both", expand=True)

        # アイコン＋タイトル行
        title_row = tk.Frame(left, bg=card_bg)
        title_row.pack(anchor="w")
        tk.Label(title_row, text=game["icon"],
                 bg=card_bg, fg=card_fg,
                 font=("Courier", 18)).pack(side="left", padx=(0, 8))
        tk.Label(title_row,
                 text=game["title"] + badge,
                 bg=card_bg, fg=card_fg,
                 font=("Courier", 14, "bold")).pack(side="left")

        # 説明
        tk.Label(left, text=game["desc"],
                 bg=card_bg, fg=desc_fg,
                 font=("Courier", 10), anchor="w").pack(anchor="w", pady=(4, 0))

        # 起動ボタン（準備中はグレーアウト）
        right = tk.Frame(inner, bg=card_bg)
        right.pack(side="right", padx=(12, 0))

        if ready:
            make_btn(right, "▶ 起動",
                     lambda g=game: self.on_select_game(g["id"]),
                     bg=SAFE_COL, fg=BG).pack()
        else:
            tk.Label(right, text="準備中",
                     bg=DISABLED_BG, fg=DISABLED_FG,
                     font=("Courier", 11), padx=14, pady=8).pack()


# ══════════════════════════════════════════════
#  ViewBomb ロビー画面
#  （チャンネル名・難易度・モード選択）
# ══════════════════════════════════════════════
class MinesweeperLobby:
    def __init__(self, root, cfg, on_start, on_back):
        self.root     = root
        self.cfg      = cfg
        self.on_start = on_start
        self.on_back  = on_back

        root.title("ChatViewPlayGame - ViewBomb")
        root.configure(bg=BG)

        make_label(root, "💣 ViewBomb",
                   fg=ACCENT_COL, font=("Courier", 20, "bold")).pack(pady=(24, 4))
        make_label(root, "ゲーム設定", fg=TEXT_G,
                   font=("Courier", 11)).pack(pady=(0, 18))

        frame = tk.Frame(root, bg=BG)
        frame.pack(padx=36)

        # ── モード選択 ──
        make_label(frame, "モード:",
                   font=("Courier", 12, "bold"), anchor="w").pack(fill="x", pady=(14, 4))
        self.mode_var = tk.StringVar(value=cfg.get("ms_mode", "normal"))

        mode_frame = tk.Frame(frame, bg=BG)
        mode_frame.pack(fill="x")

        modes = [
            ("normal",  "通常モード",   "1ゲームずつプレイ"),
            ("endless", "連続モード",   f"クリアするたびに地雷+{ENDLESS_MINE_STEP}個"),
        ]
        for val, name, desc in modes:
            row = tk.Frame(mode_frame, bg=BG)
            row.pack(fill="x", pady=2)
            tk.Radiobutton(row, text=name, variable=self.mode_var, value=val,
                           bg=BG, fg=TEXT_W, selectcolor=CELL_HID,
                           activebackground=BG, activeforeground=ACCENT_COL,
                           font=("Courier", 12, "bold"), anchor="w",
                           command=self._on_mode_change).pack(side="left")
            tk.Label(row, text=f"  {desc}", bg=BG, fg=TEXT_G,
                     font=("Courier", 10)).pack(side="left")

        # ── 難易度（プリセット or カスタム）──
        make_label(frame, "難易度:",
                   font=("Courier", 12, "bold"), anchor="w").pack(fill="x", pady=(14, 4))
        self.diff_var = tk.StringVar(value=cfg.get("ms_difficulty", list(PRESET_DIFFICULTIES.keys())[0]))

        diff_frame = tk.Frame(frame, bg=BG)
        diff_frame.pack(fill="x")

        preset_names = list(PRESET_DIFFICULTIES.keys()) + ["カスタム"]
        for name in preset_names:
            tk.Radiobutton(diff_frame, text=name, variable=self.diff_var, value=name,
                           bg=BG, fg=TEXT_W, selectcolor=CELL_HID,
                           activebackground=BG, activeforeground=ACCENT_COL,
                           font=("Courier", 11), anchor="w",
                           command=self._on_diff_change).pack(fill="x")

        # カスタム入力フィールド
        self.custom_frame = tk.Frame(frame, bg=BG)
        self.custom_frame.pack(fill="x", pady=(4, 0))

        def num_entry(label, var, w=6):
            f = tk.Frame(self.custom_frame, bg=BG)
            f.pack(side="left", padx=(0, 16))
            tk.Label(f, text=label, bg=BG, fg=TEXT_G,
                     font=("Courier", 10)).pack(anchor="w")
            tk.Entry(f, textvariable=var, width=w,
                     bg=CELL_HID, fg=TEXT_W, insertbackground=TEXT_W,
                     relief="flat", font=("Courier", 12), bd=4).pack()

        self.custom_cols  = tk.StringVar(value="12")
        self.custom_rows  = tk.StringVar(value="12")
        self.custom_mines = tk.StringVar(value="20")
        num_entry("列数 (cols)", self.custom_cols)
        num_entry("行数 (rows)", self.custom_rows)
        num_entry("地雷数",      self.custom_mines)

        # 初期表示更新
        self._on_diff_change()
        self._on_mode_change()

        # エラー
        self.err_var = tk.StringVar()
        tk.Label(frame, textvariable=self.err_var, bg=BG, fg=MINE_COL,
                 font=("Courier", 11)).pack(pady=(10, 0))

        # ── 座標文字サイズ ──
        make_label(frame, "座標文字サイズ:",
                   font=("Courier", 12, "bold"), anchor="w").pack(fill="x", pady=(14, 4))
        coord_row = tk.Frame(frame, bg=BG)
        coord_row.pack(fill="x")
        self.coord_size_var = tk.IntVar(value=cfg.get("ms_coord_size", 0))
        tk.Label(coord_row, text="小", bg=BG, fg=TEXT_G,
                 font=("Courier", 11)).pack(side="left")
        coord_slider = tk.Scale(coord_row, from_=0, to=8,
                                variable=self.coord_size_var,
                                orient="horizontal", length=200,
                                bg=BG, fg=TEXT_W, troughcolor=CELL_HID,
                                highlightthickness=0, showvalue=True,
                                activebackground=ACCENT_COL)
        coord_slider.pack(side="left", padx=8)
        tk.Label(coord_row, text="大", bg=BG, fg=TEXT_G,
                 font=("Courier", 11)).pack(side="left")
        make_label(frame, "0=自動（セルサイズ連動）  1〜8=固定サイズ加算",
                   fg=TEXT_G, font=("Courier", 9)).pack(anchor="w", pady=(2, 0))

        # ボタン
        bf = tk.Frame(frame, bg=BG)
        bf.pack(fill="x", pady=(10, 24))
        make_btn(bf, "◀  戻る",           self.on_back).pack(side="left")
        make_btn(bf, "▶  ゲームスタート", self._start,
                 bg=SAFE_COL, fg=BG).pack(side="right")

    def _on_mode_change(self):
        """連続モード時は難易度を固定（開始時の盤面）にする"""
        pass  # 将来的に制限を入れる場合ここに追記

    def _on_diff_change(self):
        is_custom = (self.diff_var.get() == "カスタム")
        state = "normal" if is_custom else "disabled"
        for w in self.custom_frame.winfo_children():
            for child in w.winfo_children():
                try:
                    child.config(state=state)
                except Exception:
                    pass

    def _parse_difficulty(self):
        d = self.diff_var.get()
        if d in PRESET_DIFFICULTIES:
            return PRESET_DIFFICULTIES[d]
        # カスタム
        try:
            cols  = int(self.custom_cols.get())
            rows  = int(self.custom_rows.get())
            mines = int(self.custom_mines.get())
        except ValueError:
            return None
        if not (2 <= cols <= 26 and 2 <= rows <= 30):
            return None
        max_mines = cols * rows - 9
        if not (1 <= mines <= max_mines):
            return None
        return cols, rows, mines

    def _start(self):
        channel = self.cfg.get("channel", "")
        token   = self.cfg.get("token", "")
        mode    = self.mode_var.get()

        if not channel or not token.startswith("oauth:"):
            self.err_var.set("⚠ Settings not configured → go to Settings first")
            return

        diff = self._parse_difficulty()
        if diff is None:
            self.err_var.set("⚠ Invalid custom values (cols: 2-26, rows: 2-30, mines: 1+)")
            return

        self.cfg["ms_mode"]        = mode
        self.cfg["ms_difficulty"]  = self.diff_var.get()
        self.cfg["ms_coord_size"]  = self.coord_size_var.get()
        save_config(self.cfg)

        cols, rows, mines = diff
        self.on_start(self.cfg, cols, rows, mines, mode)


# ══════════════════════════════════════════════
#  ゲーム画面（ViewBomb）
# ══════════════════════════════════════════════
class GameScreen:
    def __init__(self, root, cfg, cols, rows, mines, mode, on_menu, stage=1):
        self.root      = root
        self.cfg       = cfg
        self.cols      = cols
        self.rows      = rows
        self.mines     = mines   # 現在の地雷数（連続モードで増える）
        self.base_mines= mines   # 初期地雷数（連続モード用）
        self.mode      = mode    # "normal" | "endless"
        self.on_menu   = on_menu
        self.stage     = stage   # 連続モードのステージ番号

        # 解像度設定からウィンドウサイズとセルサイズを決定
        res_name   = cfg.get("resolution", DEFAULT_RES)
        win_w, win_h = RESOLUTIONS.get(res_name, RESOLUTIONS[DEFAULT_RES])
        self.cell  = calc_cell(cols, rows, win_w, win_h, SIDEBAR_W, HEADER_H)
        self.coord_size = cfg.get("ms_coord_size", 0)  # 0=自動、1〜8=加算
        self.board_w = cols * self.cell
        self.board_h = rows * self.cell
        # 実際のウィンドウは固定解像度
        self.win_w   = win_w
        self.win_h   = win_h
        # 盤面の描画オフセット（中央寄せ）
        board_area_w = win_w - SIDEBAR_W
        board_area_h = win_h - HEADER_H
        self.board_ox = (board_area_w - self.board_w) // 2
        self.board_oy = HEADER_H + (board_area_h - self.board_h) // 2

        root.title("ChatViewPlayGame")
        root.configure(bg=BG)
        root.resizable(False, False)

        self.canvas = tk.Canvas(root, width=self.win_w, height=self.win_h,
                                bg=BG, highlightthickness=0)
        self.canvas.pack()

        self.ms          = Minesweeper(cols, rows, mines)
        self.particles   = []
        self.danmaku     = []
        self.action_log  = []
        self.last_user   = None
        self.boom_user   = None
        self.hover       = None
        self.restart_t   = 0.0
        self.prev_time   = time.time()
        self.flash_color = None
        self.flash_t     = 0.0
        self.flash_dur   = 0.0
        self.flash_id    = None
        self._running    = True
        # コピー用テキスト（チャンネル名は起動時に確定）
        ch = cfg["channel"]
        self.hint_text  = f"ViewBomb: A1=open  flag A1=flag  (ch: {ch})"
        self.copy_flash = 0.0   # コピー完了フラッシュ用タイマー

        self.canvas.bind("<Motion>",   self._on_motion)
        self.canvas.bind("<Button-1>", self._on_left_click)
        self.canvas.bind("<Button-3>", self._on_right_click)
        self.canvas.bind("<Button-2>", self._on_right_click)

        self.online_mode = cfg.get("online_mode", True)
        self.twitch = TwitchClient(
            cfg["channel"], cfg["token"],
            on_command=self._on_command,
            on_chat=self._on_chat,
        )
        if self.online_mode:
            threading.Thread(
                target=lambda: asyncio.run(self.twitch.connect()), daemon=True
            ).start()

        self._loop()

    # ── ループ ───────────────────────────────
    def _loop(self):
        if not self._running:
            return
        now = time.time()
        dt  = now - self.prev_time
        self.prev_time = now

        if self.ms.game_over or self.ms.cleared:
            self.restart_t += dt
            if self.restart_t >= RESTART_SEC:
                self._next()

        self.particles = [p for p in self.particles if p.update()]
        for d in self.danmaku:
            d.update(dt)
        self.danmaku = [d for d in self.danmaku if d.alive]
        if self.copy_flash > 0:
            self.copy_flash = max(0.0, self.copy_flash - dt)

        if self.flash_color:
            self.flash_t += dt / self.flash_dur
            if self.flash_t >= 1.0:
                self.flash_color = None
                if self.flash_id:
                    self.canvas.delete(self.flash_id)
                    self.flash_id = None
            else:
                stipple = ("gray75" if self.flash_t < 0.3
                           else "gray50" if self.flash_t < 0.6 else "gray25")
                if self.flash_id:
                    self.canvas.itemconfig(self.flash_id, stipple=stipple)

        self._draw_all()
        self.root.after(FPS_INTERVAL, self._loop)

    def _next(self):
        """ゲームオーバー/クリア後の次の処理"""
        if self.ms.cleared and self.mode == "endless":
            # 連続モード: 地雷を増やして次のステージ
            next_mines = min(
                self.mines + ENDLESS_MINE_STEP,
                self.cols * self.rows - 9
            )
            self._reset(next_mines, self.stage + 1)
        else:
            # 通常モード or ゲームオーバー: 同じ設定でリスタート
            self._reset(self.mines, self.stage if self.mode == "endless" else 1)

    def _reset(self, mines, stage):
        self.mines     = mines
        self.stage     = stage
        self.ms        = Minesweeper(self.cols, self.rows, mines)
        self.particles.clear()
        self.action_log.clear()
        self.last_user  = None
        self.boom_user  = None
        self.restart_t  = 0.0
        self.flash_color = None
        if self.flash_id:
            self.canvas.delete(self.flash_id)
            self.flash_id = None

    # ── メニューへ ────────────────────────────
    def _go_menu(self):
        self._running = False
        self.twitch.stop()
        for d in self.danmaku:
            try:
                self.canvas.delete(d.text_id)
                self.canvas.delete(d.shadow_id)
            except Exception:
                pass
        self.on_menu()

    # ── フラッシュ ────────────────────────────
    def _start_flash(self, color, duration=0.6):
        self.flash_color = color
        self.flash_t     = 0.0
        self.flash_dur   = duration
        if self.flash_id:
            self.canvas.delete(self.flash_id)
        self.flash_id = self.canvas.create_rectangle(
            0, 0, self.win_w, self.win_h,
            fill=color, outline="", stipple="gray75")
        self.canvas.tag_raise(self.flash_id)

    # ── Twitch コールバック ───────────────────
    def _on_command(self, username, col, row, is_flag):
        self._do_action(username, col, row, is_flag)

    def _on_chat(self, username, text):
        self.danmaku.append(DanmakuMsg(self.canvas, username, text, self.win_w))

    # ── マウス ────────────────────────────────
    def _menu_btn_rect(self):
        bx = self.win_w - SIDEBAR_W - 116
        return bx, 6, bx + 108, 36

    def _copy_btn_rect(self):
        """サイドバー内のコピーボタン領域"""
        sx = self.win_w - SIDEBAR_W
        return sx + 8, self.win_h - 58, self.win_w - 8, self.win_h - 8

    def _cell_at(self, x, y):
        col = (x - self.board_ox) // self.cell
        row = (y - self.board_oy) // self.cell
        if 0 <= col < self.cols and 0 <= row < self.rows and y > self.board_oy:
            return col, row
        return None, None

    def _on_motion(self, ev):
        col, row = self._cell_at(ev.x, ev.y)
        self.hover = (col, row) if col is not None else None
        bx1, by1, bx2, by2 = self._menu_btn_rect()
        if bx1 <= ev.x <= bx2 and by1 <= ev.y <= by2:
            self.canvas.itemconfig("menu_btn_bg", fill=BTN_MENU_H)
        else:
            self.canvas.itemconfig("menu_btn_bg", fill=BTN_MENU)
        # コピーボタンホバー
        cx1, cy1, cx2, cy2 = self._copy_btn_rect()
        if cx1 <= ev.x <= cx2 and cy1 <= ev.y <= cy2:
            self.canvas.itemconfig("copy_btn_bg", fill=BTN_MENU_H)
        else:
            self.canvas.itemconfig("copy_btn_bg", fill=BTN_MENU)

    def _on_left_click(self, ev):
        bx1, by1, bx2, by2 = self._menu_btn_rect()
        if bx1 <= ev.x <= bx2 and by1 <= ev.y <= by2:
            self._go_menu()
            return
        cx1, cy1, cx2, cy2 = self._copy_btn_rect()
        if cx1 <= ev.x <= cx2 and cy1 <= ev.y <= cy2:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.hint_text)
            self.copy_flash = 1.8
            return
        col, row = self._cell_at(ev.x, ev.y)
        if col is not None:
            self._do_action("[配信者]", col, row, False)

    def _on_right_click(self, ev):
        col, row = self._cell_at(ev.x, ev.y)
        if col is not None:
            self._do_action("[配信者]", col, row, True)

    # ── アクション共通 ────────────────────────
    def _do_action(self, username, col, row, is_flag):
        if self.ms.game_over or self.ms.cleared:
            return
        cx = self.board_ox + col * self.cell + self.cell // 2
        cy = self.board_oy + row * self.cell + self.cell // 2

        if is_flag:
            self.ms.toggle_flag(col, row)
            self.action_log.append((username, "flag", col, row))
            self.last_user = (username, "🚩")
        else:
            hit = self.ms.open_cell(col, row)
            self.action_log.append((username, "open", col, row))
            self.last_user = (username, "✅")
            if hit:
                self.boom_user = username
                for _ in range(50):
                    self.particles.append(Particle(self.canvas, cx, cy, MINE_COL))
                self._start_flash(MINE_COL, 0.7)
            else:
                for _ in range(10):
                    self.particles.append(Particle(self.canvas, cx, cy, SAFE_COL))

        if self.ms.cleared:
            self._start_flash(SAFE_COL, 1.2)
            for _ in range(60):
                px = random.randint(0, self.board_w)
                py = random.randint(HEADER_H, self.win_h)
                self.particles.append(Particle(self.canvas, px, py,
                    random.choice([SAFE_COL, ACCENT_COL, FLAG_COL])))

    # ── 描画 ─────────────────────────────────
    def _draw_all(self):
        self._draw_board()
        self._draw_header()
        self._draw_sidebar()
        self._draw_overlay()
        if self.flash_id:
            self.canvas.tag_raise(self.flash_id)
        for d in self.danmaku:
            self.canvas.tag_raise(d.shadow_id)
            self.canvas.tag_raise(d.text_id)

    def _draw_board(self):
        c = self.canvas
        for row in range(self.rows):
            for col in range(self.cols):
                x1 = self.board_ox + col * self.cell
                y1 = self.board_oy + row * self.cell
                x2, y2 = x1 + self.cell, y1 + self.cell
                cell  = self.ms.get_cell(col, row)
                hover = (self.hover == (col, row))
                tag   = f"cell_{col}_{row}"
                c.delete(tag)
                half  = self.cell // 2
                nfont = max(8, self.cell - 22)
                if self.coord_size == 0:
                    lfont = max(7, self.cell - 28)
                else:
                    lfont = 6 + self.coord_size

                if cell["open"]:
                    c.create_rectangle(x1,y1,x2,y2,
                        fill=CELL_OPEN, outline=CELL_BORDER, tags=tag)
                    if cell["mine"] and self.ms.game_over:
                        pad = max(4, self.cell//7)
                        c.create_oval(x1+pad,y1+pad,x2-pad,y2-pad,
                            fill=MINE_COL, outline="", tags=tag)
                    elif cell["number"] and cell["number"] > 0:
                        c.create_text(x1+half, y1+half,
                            text=str(cell["number"]),
                            fill=NUM_COLORS[cell["number"]],
                            font=("Courier",nfont,"bold"), tags=tag)
                else:
                    bg = CELL_HOV if hover else CELL_HID
                    c.create_rectangle(x1,y1,x2,y2,
                        fill=bg, outline=CELL_BORDER, tags=tag)
                    if cell["flag"]:
                        c.create_text(x1+half, y1+half,
                            text="🚩", font=("Courier",lfont), tags=tag)
                    else:
                        lbl = chr(ord('A')+col) + str(row+1)
                        c.create_text(x1+3, y1+2, text=lbl, anchor="nw",
                            fill="#6878A8", font=("Courier",lfont), tags=tag)

    def _draw_header(self):
        c = self.canvas
        c.delete("header")
        c.create_rectangle(0,0,self.win_w,HEADER_H,
            fill=HEADER_BG, outline="", tags="header")

        # 左: タイトル・チャンネル
        c.create_text(14, 14, text="💣 VIEWBOMB",
            fill=ACCENT_COL, anchor="nw",
            font=("Courier",15,"bold"), tags="header")
        c.create_text(14, 38, text=f"📺 {self.cfg['channel']}",
            fill=TEXT_G, anchor="nw",
            font=("Courier",11), tags="header")

        # 中央: 地雷数・タイマー・ステージ
        cx = self.board_w // 2
        remain = self.mines - self.ms.count_flags()
        c.create_text(cx, 14, text=f"💣 {remain}",
            fill=MINE_COL, font=("Courier",14,"bold"), tags="header")
        elapsed = int(time.time() - self.ms.start_time) if self.ms.start_time else 0
        c.create_text(cx, 38, text=f"⏱ {elapsed}s",
            fill=TEXT_W, font=("Courier",12), tags="header")
        if self.mode == "endless":
            c.create_text(cx, 60, text=f"STAGE {self.stage}  地雷{self.mines}",
                fill=FLAG_COL, font=("Courier",11,"bold"), tags="header")

        # 左下: 最後の操作者
        if self.last_user:
            usr, icon = self.last_user
            c.create_text(14, 66, text=f"{icon} {usr}",
                fill=SAFE_COL, anchor="nw",
                font=("Courier",11), tags="header")

        # 右下: 操作ガイド
        guide = "左クリック:開く  右クリック:フラグ  /  チャット: A1 / flag A1"
        c.create_text(self.win_w - SIDEBAR_W - 10, 74, text=guide,
            fill=TEXT_G, anchor="ne",
            font=("Courier", 9), tags="header")

        # メニューボタン（ボード内右上）
        bx1, by1, bx2, by2 = self._menu_btn_rect()
        c.create_rectangle(bx1, by1, bx2, by2,
            fill=BTN_MENU, outline=CELL_BORDER, width=1,
            tags=("header", "menu_btn_bg"))
        c.create_text((bx1+bx2)//2, (by1+by2)//2, text="◀ メニュー",
            fill=TEXT_W, font=("Courier",11,"bold"),
            tags=("header", "menu_btn_txt"))

    def _draw_sidebar(self):
        c = self.canvas
        c.delete("sidebar")
        sx = self.win_w - SIDEBAR_W
        c.create_rectangle(sx,0,self.win_w,self.win_h,
            fill=SIDEBAR_BG, outline="", tags="sidebar")
        c.create_line(sx,0,sx,self.win_h,
            fill=CELL_BORDER, width=2, tags="sidebar")

        c.create_text(sx+12, 16, text="💬 LIVE CHAT",
            fill=ACCENT_COL, anchor="nw",
            font=("Courier",13,"bold"), tags="sidebar")
        c.create_text(sx+12, 40, text="最近の操作:",
            fill=TEXT_G, anchor="nw",
            font=("Courier",10), tags="sidebar")

        y = 58
        for entry in reversed(self.action_log[-14:]):
            usr, act, col, row = entry
            lbl  = chr(ord('A')+col) + str(row+1)
            icon = "🚩" if act == "flag" else "🔍"
            col_c = FLAG_COL if act == "flag" else TEXT_W
            txt  = f"{icon} {usr}: {lbl}"[:26]
            c.create_text(sx+12, y, text=txt, fill=col_c, anchor="nw",
                font=("Courier",11), tags="sidebar")
            y += 19
            if y > self.win_h - 90:
                break

        if self.boom_user and self.ms.game_over:
            bx1, by1 = sx+8, self.win_h-148
            bx2, by2 = self.win_w-8, self.win_h-68
            c.create_rectangle(bx1,by1,bx2,by2,
                fill=BOOM_BG, outline=MINE_COL, width=2, tags="sidebar")
            c.create_text(bx1+8, by1+8, text="💥 地雷を踏んだ人",
                fill=MINE_COL, anchor="nw",
                font=("Courier",11,"bold"), tags="sidebar")
            c.create_text(bx1+8, by1+34, text=self.boom_user,
                fill=TEXT_W, anchor="nw",
                font=("Courier",13,"bold"), tags="sidebar")

        # ── コピーボタン（サイドバー最下部）──
        cx1, cy1, cx2, cy2 = self._copy_btn_rect()
        copied = self.copy_flash > 0
        btn_col  = SAFE_COL if copied else BTN_MENU
        txt_col  = SIDEBAR_BG if copied else TEXT_W
        btn_text = "✅ Copied!" if copied else "📋 Copy hint for chat"
        c.create_rectangle(cx1, cy1, cx2, cy2,
            fill=btn_col, outline=CELL_BORDER, width=1,
            tags=("sidebar", "copy_btn_bg"))
        c.create_text((cx1+cx2)//2, cy1+12,
            text=btn_text,
            fill=txt_col, font=("Courier",10,"bold"), tags="sidebar")
        # ヒントテキスト（ボタン内小文字）
        if not copied:
            hint_disp = self.hint_text[:32]
            c.create_text((cx1+cx2)//2, cy1+30,
                text=hint_disp,
                fill=TEXT_G, font=("Courier",8), tags="sidebar")

    def _draw_overlay(self):
        c = self.canvas
        c.delete("overlay")
        bx = self.board_ox + self.board_w // 2
        by = self.board_oy + self.board_h // 2

        if self.ms.game_over:
            c.create_rectangle(self.board_ox, self.board_oy,
                self.board_ox+self.board_w, self.board_oy+self.board_h,
                fill="#000000", stipple="gray50", outline="", tags="overlay")
            c.create_text(bx, by-40, text="💥 GAME OVER",
                fill=MINE_COL, font=("Courier",36,"bold"), tags="overlay")
            if self.boom_user:
                c.create_text(bx, by+10,
                    text=f"踏んだのは {self.boom_user} !",
                    fill=TEXT_W, font=("Courier",16), tags="overlay")
            cd = max(0.0, RESTART_SEC - self.restart_t)
            c.create_text(bx, by+46,
                text=f"{cd:.1f}秒後に再スタート...",
                fill=TEXT_G, font=("Courier",13), tags="overlay")

        elif self.ms.cleared:
            c.create_rectangle(0,HEADER_H,self.board_w,self.win_h,
                fill="#000000", stipple="gray50", outline="", tags="overlay")
            c.create_text(bx, by-40, text="🎉 CLEAR !",
                fill=SAFE_COL, font=("Courier",40,"bold"), tags="overlay")
            if self.mode == "endless":
                next_m = min(self.mines + ENDLESS_MINE_STEP, self.cols*self.rows-9)
                c.create_text(bx, by+10,
                    text=f"次のステージ: 地雷 {next_m}個",
                    fill=FLAG_COL, font=("Courier",14,"bold"), tags="overlay")
            cd = max(0.0, RESTART_SEC - self.restart_t)
            c.create_text(bx, by+46,
                text=f"{cd:.1f}秒後に次へ...",
                fill=TEXT_G, font=("Courier",13), tags="overlay")



def _apply_icon(root):
    """exe・スクリプト両対応のアイコン適用"""
    try:
        if getattr(sys, "frozen", False):
            # PyInstallerでexe化された場合
            base = sys._MEIPASS
        else:
            base = os.path.dirname(os.path.abspath(__file__))
        ico = os.path.join(base, "icon.ico")
        if os.path.exists(ico):
            root.iconbitmap(ico)
    except Exception:
        pass


# ══════════════════════════════════════════════
#  アプリケーション（画面遷移を管理）
# ══════════════════════════════════════════════
class ReversiLobby:
    def __init__(self, root, cfg, on_start, on_back):
        self.root     = root
        self.cfg      = cfg
        self.on_start = on_start
        self.on_back  = on_back

        root.title("ChatViewPlayGame - チャットvsリバーシ")
        root.configure(bg=BG)

        make_label(root, "♟ チャットvsリバーシ",
                   fg=ACCENT_COL, font=("Courier", 20, "bold")).pack(pady=(24,4))
        make_label(root, "配信者(黒) vs Twitchチャット(白)",
                   fg=TEXT_G, font=("Courier", 11)).pack(pady=(0,18))

        frame = tk.Frame(root, bg=BG)
        frame.pack(padx=36)

        # 最大投票時間
        make_label(frame, "チャット側の最大投票時間:",
                   font=("Courier",12,"bold"), anchor="w").pack(fill="x", pady=(0,4))
        self.vote_var = tk.IntVar(value=cfg.get("rv_vote_sec", 60))
        vf = tk.Frame(frame, bg=BG)
        vf.pack(fill="x")
        for sec in [30, 60, 90, 120]:
            tk.Radiobutton(vf, text=f"{sec}秒", variable=self.vote_var, value=sec,
                           bg=BG, fg=TEXT_W, selectcolor=CELL_HID,
                           activebackground=BG, activeforeground=ACCENT_COL,
                           font=("Courier",11)).pack(side="left", padx=(0,16))

        make_label(frame, "※ 配信者がスペースキーで早期締め切り可能",
                   fg=TEXT_G, font=("Courier",10)).pack(anchor="w", pady=(4,14))

        # 同票時の処理
        make_label(frame, "同票時の決定方法:",
                   font=("Courier",12,"bold"), anchor="w").pack(fill="x", pady=(0,4))
        self.tie_var = tk.StringVar(value=cfg.get("rv_tiebreak", "random"))
        tf = tk.Frame(frame, bg=BG)
        tf.pack(fill="x")
        for val, label in [("random","ランダム"), ("first","早着順（先にコメントした方）")]:
            tk.Radiobutton(tf, text=label, variable=self.tie_var, value=val,
                           bg=BG, fg=TEXT_W, selectcolor=CELL_HID,
                           activebackground=BG, activeforeground=ACCENT_COL,
                           font=("Courier",11), anchor="w").pack(fill="x", pady=1)

        # ── 先手/後手選択 ──
        tk.Frame(frame, bg=CELL_BORDER, height=1).pack(fill="x", pady=(14,12))
        make_label(frame, "配信者の手番:",
                   font=("Courier",12,"bold"), anchor="w").pack(fill="x", pady=(0,4))
        self.turn_var = tk.StringVar(value=cfg.get("rv_turn","black"))
        tf2 = tk.Frame(frame, bg=BG)
        tf2.pack(fill="x")
        for val, lbl, desc in [("black","⚫ 黒（先手）","配信者が先手"),
                                ("white","⬜ 白（後手）","チャットが先手")]:
            row = tk.Frame(tf2, bg=BG)
            row.pack(fill="x", pady=2)
            tk.Radiobutton(row, text=lbl, variable=self.turn_var, value=val,
                           bg=BG, fg=TEXT_W, selectcolor=CELL_HID,
                           activebackground=BG, activeforeground=ACCENT_COL,
                           font=("Courier",12,"bold"), anchor="w").pack(side="left")
            tk.Label(row, text=f"  {desc}", bg=BG, fg=TEXT_G,
                     font=("Courier",10)).pack(side="left")

        # ── チャット側自動石配置 ──
        tk.Frame(frame, bg=CELL_BORDER, height=1).pack(fill="x", pady=(14,12))
        make_label(frame, "チャット側 時間切れ時の自動配置:",
                   font=("Courier",12,"bold"), anchor="w").pack(fill="x", pady=(0,4))
        self.auto_place_var = tk.BooleanVar(value=cfg.get("rv_auto_place", True))
        apf = tk.Frame(frame, bg=BG)
        apf.pack(fill="x")
        for val, lbl, desc in [(True,"有効","時間切れ時にランダムで合法手に配置"),
                               (False,"無効","時間切れ時はパスとして扱う")]:
            row = tk.Frame(apf, bg=BG)
            row.pack(fill="x", pady=2)
            tk.Radiobutton(row, text=lbl, variable=self.auto_place_var, value=val,
                           bg=BG, fg=TEXT_W, selectcolor=CELL_HID,
                           activebackground=BG, activeforeground=ACCENT_COL,
                           font=("Courier",12,"bold"), anchor="w").pack(side="left")
            tk.Label(row, text=f"  {desc}", bg=BG, fg=TEXT_G,
                     font=("Courier",10)).pack(side="left")

        self.err_var = tk.StringVar()
        tk.Label(frame, textvariable=self.err_var, bg=BG, fg=MINE_COL,
                 font=("Courier",11)).pack(pady=(10,0))

        bf = tk.Frame(frame, bg=BG)
        bf.pack(fill="x", pady=(12,24))
        make_btn(bf, "◀  戻る",           self.on_back).pack(side="left")
        make_btn(bf, "▶  ゲームスタート", self._start,
                 bg=SAFE_COL, fg=BG).pack(side="right")

    def _start(self):
        channel = self.cfg.get("channel","")
        token   = self.cfg.get("token","")
        online  = self.cfg.get("online_mode", True)
        if online and (not channel or not token.startswith("oauth:")):
            self.err_var.set("⚠ Settings not configured")
            return
        self.cfg["rv_vote_sec"]   = self.vote_var.get()
        self.cfg["rv_tiebreak"]   = self.tie_var.get()
        self.cfg["rv_turn"]       = self.turn_var.get()
        self.cfg["rv_auto_place"] = self.auto_place_var.get()
        save_config(self.cfg)
        self.on_start(self.cfg, self.vote_var.get(), self.tie_var.get())


# ══════════════════════════════════════════════
#  リバーシ ゲーム画面
# ══════════════════════════════════════════════
RV_SIDEBAR_W = 280
RV_HEADER_H  = 80
RV_LABEL_W   = 24
RV_BOARD_OFF = 8

def calc_rv_layout(win_w, win_h):
    """解像度からリバーシのセルサイズと盤面オフセットを計算"""
    avail_w = win_w - RV_SIDEBAR_W - RV_BOARD_OFF*2 - RV_LABEL_W*2
    avail_h = win_h - RV_HEADER_H  - RV_BOARD_OFF*2 - RV_LABEL_W*2
    cell = max(32, min(avail_w // 8, avail_h // 8))
    board_px_w = cell * 8 + RV_BOARD_OFF*2 + RV_LABEL_W*2
    board_px_h = cell * 8 + RV_BOARD_OFF*2 + RV_LABEL_W*2
    ox = (win_w - RV_SIDEBAR_W - board_px_w) // 2
    oy = RV_HEADER_H + (win_h - RV_HEADER_H - board_px_h) // 2
    return cell, ox, oy

RV_CELL = 56
RV_WIN_W = 8*RV_CELL + RV_BOARD_OFF*2 + RV_LABEL_W*2 + RV_SIDEBAR_W
RV_WIN_H = 8*RV_CELL + RV_BOARD_OFF*2 + RV_LABEL_W*2 + RV_HEADER_H

class ReversiGameScreen:
    def __init__(self, root, cfg, max_vote_sec, tiebreak, on_menu):
        self.root         = root
        self.cfg          = cfg
        self.max_vote_sec = max_vote_sec
        self.tiebreak     = tiebreak
        self.on_menu      = on_menu

        root.title("ChatViewPlayGame - チャットvsリバーシ")
        root.configure(bg=BG)

        res_name = cfg.get("resolution", DEFAULT_RES)
        self.rv_win_w, self.rv_win_h = RESOLUTIONS.get(res_name, RESOLUTIONS[DEFAULT_RES])
        self.rv_cell, self.rv_ox, self.rv_oy = calc_rv_layout(self.rv_win_w, self.rv_win_h)

        self.canvas = tk.Canvas(root, width=self.rv_win_w, height=self.rv_win_h,
                                bg=BG, highlightthickness=0)
        self.canvas.pack()

        self.rv          = Reversi()
        # 先手/後手設定（black=配信者先手, white=配信者後手）
        rv_turn = cfg.get("rv_turn", "black")
        if rv_turn == "white":
            # 配信者が白 = チャットが黒(先手)
            self.streamer_color = WHITE
            self.chat_color     = BLACK
        else:
            self.streamer_color = BLACK
            self.chat_color     = WHITE
        self.auto_place = cfg.get("rv_auto_place", True)
        self.votes       = {}        # {"A1": count, ...} / tiebreak="first": {"A1": timestamp}
        self.vote_order  = []        # 早着順用: [(col,row), ...]
        self.vote_timer  = 0.0      # チャットターン残り秒数
        self.voting      = False     # チャットターン中か
        self.hover       = None
        self.prev_time   = time.time()
        self.danmaku     = []
        self.status_msg  = ""
        self._running    = True
        self.copy_flash  = 0.0

        self.hint_text = f"Reversi: A1=vote  (ch: {cfg['channel']})"

        # Twitch接続（オフラインモード時は接続しない）
        self.online_mode = cfg.get("online_mode", True)
        self.twitch = TwitchClient(
            cfg["channel"], cfg["token"],
            on_command=self._on_vote,
            on_chat=self._on_chat,
        )
        if self.online_mode:
            threading.Thread(
                target=lambda: asyncio.run(self.twitch.connect()), daemon=True
            ).start()

        # イベント
        self.canvas.bind("<Motion>",          self._on_motion)
        self.canvas.bind("<Button-1>",        self._on_click)
        root.bind("<space>",                  self._on_space)

        self._start_turn()
        self._loop()

    # ── ターン開始 ────────────────────────────
    def _start_turn(self):
        if self.rv.game_over:
            return
        if self.rv.turn == self.streamer_color:
            self.voting    = False
            col_name = "⚫" if self.streamer_color == BLACK else "⬜"
            self.status_msg = f"{col_name} Your turn — click to place"
        else:
            self.voting    = True
            self.vote_timer = float(self.max_vote_sec)
            self.votes     = {}
            self.vote_order = []
            col_name = "⬜" if self.chat_color == WHITE else "⚫"
            self.status_msg = f"{col_name} Chat voting...  [{self.max_vote_sec}s]  Space = close"

    # ── メインループ ──────────────────────────
    def _loop(self):
        if not self._running:
            return
        now = time.time()
        dt  = now - self.prev_time
        self.prev_time = now

        if self.voting and not self.rv.game_over:
            self.vote_timer -= dt
            self.status_msg = f"Chat voting...  [{max(0,self.vote_timer):.0f}s]  Space = close"
            if self.vote_timer <= 0:
                self._close_vote()

        for d in self.danmaku:
            d.update(dt)
        self.danmaku = [d for d in self.danmaku if d.alive]

        if self.copy_flash > 0:
            self.copy_flash = max(0.0, self.copy_flash - dt)

        self._draw_all()
        self.root.after(FPS_INTERVAL, self._loop)

    # ── 投票締め切り ──────────────────────────
    def _close_vote(self):
        if not self.voting:
            return
        self.voting = False
        legal = self.rv.legal_moves(self.chat_color)
        if not self.votes:
            # 投票なし → auto_place設定に従う
            if self.auto_place and legal:
                import random as _r
                row, col = _r.choice(legal)
                self.rv.place(row, col)
            # auto_place=False または合法手なし → パス（turn交代はreversi.pyが処理）
        else:
            # 最多得票を選ぶ
            if self.tiebreak == "first":
                chosen = None
                for rc in self.vote_order:
                    if rc in legal:
                        chosen = rc
                        break
                if chosen is None and legal:
                    chosen = legal[0]
            else:
                max_v = max(self.votes.values())
                top   = [rc for rc, v in self.votes.items() if v == max_v and rc in legal]
                if not top:
                    top = legal if legal else []
                import random as _r
                chosen = _r.choice(top) if top else None
            if chosen:
                self.rv.place(chosen[0], chosen[1])

        self._start_turn()

    # ── Twitch コールバック ───────────────────
    def _on_vote(self, username, col, row, is_flag):
        """コマンド形式（A1など）をリバーシ投票として受付"""
        if not self.voting or self.rv.game_over:
            return
        legal = self.rv.legal_moves(WHITE)
        if (row, col) not in legal:
            return
        rc = (row, col)
        self.votes[rc] = self.votes.get(rc, 0) + 1
        if self.tiebreak == "first" and rc not in self.vote_order:
            self.vote_order.append(rc)
        self.danmaku.append(DanmakuMsg(self.canvas, username,
                                       f"→ {chr(65+col)}{row+1}", RV_WIN_W))

    def _on_chat(self, username, text):
        self.danmaku.append(DanmakuMsg(self.canvas, username, text, RV_WIN_W))

    # ── 配信者操作 ────────────────────────────
    def _on_space(self, ev):
        if self.voting:
            self._close_vote()

    def _on_motion(self, ev):
        bx1,by1,bx2,by2 = self._menu_btn_rect()
        if bx1<=ev.x<=bx2 and by1<=ev.y<=by2:
            self.canvas.itemconfig("rv_menu_bg", fill=BTN_MENU_H)
        else:
            self.canvas.itemconfig("rv_menu_bg", fill=BTN_MENU)
        cx1,cy1,cx2,cy2 = self._copy_btn_rect()
        if cx1<=ev.x<=cx2 and cy1<=ev.y<=cy2:
            self.canvas.itemconfig("rv_copy_bg", fill=BTN_MENU_H)
        else:
            self.canvas.itemconfig("rv_copy_bg", fill=BTN_MENU)
        # ホバーマス
        col, row = self._cell_at(ev.x, ev.y)
        self.hover = (row, col) if col is not None else None

    def _on_click(self, ev):
        bx1,by1,bx2,by2 = self._menu_btn_rect()
        if bx1<=ev.x<=bx2 and by1<=ev.y<=by2:
            self._go_menu(); return
        cx1,cy1,cx2,cy2 = self._copy_btn_rect()
        if cx1<=ev.x<=cx2 and cy1<=ev.y<=cy2:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.hint_text)
            self.copy_flash = 1.8; return
        # 配信者のターン時のみ盤面クリック有効
        if self.rv.turn == self.streamer_color and not self.voting and not self.rv.game_over:
            col, row = self._cell_at(ev.x, ev.y)
            if col is not None:
                if self.rv.place(row, col):
                    self._start_turn()

    def _go_menu(self):
        self._running = False
        self.twitch.stop()
        for d in self.danmaku:
            try:
                self.canvas.delete(d.text_id)
                self.canvas.delete(d.shadow_id)
            except Exception:
                pass
        self.on_menu()

    # ── 座標ヘルパー ──────────────────────────
    def _board_xy(self):
        """盤面左上座標"""
        return self.rv_ox + RV_BOARD_OFF + RV_LABEL_W, self.rv_oy + RV_BOARD_OFF + RV_LABEL_W

    def _cell_at(self, mx, my):
        bx, by = self._board_xy()
        col = (mx - bx) // self.rv_cell
        row = (my - by) // self.rv_cell
        if 0 <= col < 8 and 0 <= row < 8:
            return col, row
        return None, None

    def _menu_btn_rect(self):
        bx = self.rv_win_w - RV_SIDEBAR_W - 116
        return bx, 6, bx+108, 36

    def _copy_btn_rect(self):
        sx = self.rv_win_w - RV_SIDEBAR_W
        return sx+8, self.rv_win_h-58, self.rv_win_w-8, self.rv_win_h-8

    def _sidebar_x(self):
        return self.rv_win_w - RV_SIDEBAR_W

    # ── 描画 ─────────────────────────────────
    def _draw_all(self):
        self._draw_header()
        self._draw_board()
        self._draw_sidebar()
        for d in self.danmaku:
            self.canvas.tag_raise(d.shadow_id)
            self.canvas.tag_raise(d.text_id)

    def _draw_header(self):
        c = self.canvas
        c.delete("rv_header")
        board_px = self.rv_win_w - RV_SIDEBAR_W
        c.create_rectangle(0,0,self.rv_win_w,RV_HEADER_H,
            fill=HEADER_BG, outline="", tags="rv_header")

        # タイトル
        c.create_text(14,14, text="♟ CHAT vs REVERSI",
            fill=ACCENT_COL, anchor="nw",
            font=("Courier",15,"bold"), tags="rv_header")
        c.create_text(14,38, text=f"📺 {self.cfg['channel']}",
            fill=TEXT_G, anchor="nw",
            font=("Courier",11), tags="rv_header")

        # スコア
        b_cnt = self.rv.count(BLACK)
        w_cnt = self.rv.count(WHITE)
        cx = board_px // 2
        c.create_text(cx-40, 20, text=f"⚫ {b_cnt}",
            fill=TEXT_W, font=("Courier",16,"bold"), tags="rv_header")
        c.create_text(cx+40, 20, text=f"⬜ {w_cnt}",
            fill=TEXT_G, font=("Courier",16,"bold"), tags="rv_header")

        # ステータス
        c.create_text(cx, 55, text=self.status_msg,
            fill=SAFE_COL if not self.voting else FLAG_COL,
            font=("Courier",11), tags="rv_header")

        # メニューボタン
        bx1,by1,bx2,by2 = self._menu_btn_rect()
        c.create_rectangle(bx1,by1,bx2,by2,
            fill=BTN_MENU, outline=CELL_BORDER, width=1,
            tags=("rv_header","rv_menu_bg"))
        c.create_text((bx1+bx2)//2,(by1+by2)//2, text="◀ メニュー",
            fill=TEXT_W, font=("Courier",11,"bold"),
            tags=("rv_header","rv_menu_txt"))

    def _draw_board(self):
        c = self.canvas
        c.delete("rv_board")
        bx, by = self._board_xy()
        legal  = self.rv.legal_moves()

        cell = self.rv_cell
        # 盤面背景
        c.create_rectangle(bx-RV_BOARD_OFF, by-RV_BOARD_OFF,
            bx+8*cell+RV_BOARD_OFF, by+8*cell+RV_BOARD_OFF,
            fill="#1A3A1A", outline=CELL_BORDER, width=2, tags="rv_board")

        for row in range(8):
            for col in range(8):
                x1 = bx + col*cell
                y1 = by + row*cell
                x2, y2 = x1+cell, y1+cell
                is_legal  = (row,col) in legal
                is_hover  = (self.hover == (row,col))
                is_last   = (self.rv.last_move == (row,col))

                # マス
                cell_fill = "#2A5A2A"
                if is_hover and self.rv.turn == BLACK and not self.voting:
                    cell_fill = "#3A7A3A"
                c.create_rectangle(x1,y1,x2,y2,
                    fill=cell_fill, outline="#1A4A1A", width=1, tags="rv_board")

                # 合法手ヒント（薄い丸）
                if is_legal and self.rv.turn == self.streamer_color and not self.voting:
                    r = cell//6
                    cx2 = x1+cell//2
                    cy2 = y1+cell//2
                    c.create_oval(cx2-r,cy2-r,cx2+r,cy2+r,
                        fill="#4A9A4A", outline="", tags="rv_board")

                # 石
                stone = self.rv.board[row][col]
                if stone != EMPTY:
                    pad = 6
                    scx = x1+cell//2
                    scy = y1+cell//2
                    sr  = cell//2 - pad
                    col_fill = "#111111" if stone == BLACK else "#EEEEEE"
                    outline_c = "#444444" if stone == BLACK else "#AAAAAA"
                    if is_last:
                        outline_c = ACCENT_COL
                    c.create_oval(scx-sr,scy-sr,scx+sr,scy+sr,
                        fill=col_fill, outline=outline_c, width=2, tags="rv_board")

                # マス内座標
                if stone == EMPTY:
                    coord = chr(65+col) + str(row+1)
                    cf = max(7, cell-44)
                    if is_legal and self.voting:
                        c.create_text(x1+4, y1+3, text=coord, anchor="nw",
                            fill="#FFFFFF", font=("Courier",cf+2,"bold"), tags="rv_board")
                    elif not is_legal:
                        c.create_text(x1+4, y1+3, text=coord, anchor="nw",
                            fill="#3A6A3A", font=("Courier",cf), tags="rv_board")
                    # 配信者ターンの合法手マスは丸ヒントのみで座標は非表示

        # ── 外周座標ラベル ──────────────────────
        # 列ラベル（A〜H）上下
        for col in range(8):
            lx = bx + col*cell + cell//2
            lbl = chr(65+col)
            # 上
            c.create_text(lx, by - RV_LABEL_W//2 - RV_BOARD_OFF//2,
                text=lbl, fill=ACCENT_COL,
                font=("Courier",13,"bold"), tags="rv_board")
            # 下
            c.create_text(lx, by + 8*cell + RV_LABEL_W//2 + RV_BOARD_OFF//2,
                text=lbl, fill=ACCENT_COL,
                font=("Courier",13,"bold"), tags="rv_board")

        # 行ラベル（1〜8）左右
        for row in range(8):
            ly = by + row*RV_CELL + RV_CELL//2
            lbl = str(row+1)
            # 左
            c.create_text(bx - RV_LABEL_W//2 - RV_BOARD_OFF//2, ly,
                text=lbl, fill=ACCENT_COL,
                font=("Courier",13,"bold"), tags="rv_board")
            # 右
            c.create_text(bx + 8*cell + RV_LABEL_W//2 + RV_BOARD_OFF//2, ly,
                text=lbl, fill=ACCENT_COL,
                font=("Courier",13,"bold"), tags="rv_board")

        # ゲームオーバー表示
        if self.rv.game_over:
            board_cx = bx + 4*cell
            board_cy = by + 4*cell
            c.create_rectangle(bx+20, board_cy-50, bx+8*cell-20, board_cy+60,
                fill=BG, outline=ACCENT_COL, width=2, tags="rv_board")
            if self.rv.winner == BLACK:
                msg = "You Win!"
                col_w = SAFE_COL
            elif self.rv.winner == WHITE:
                msg = "Chat Wins!"
                col_w = FLAG_COL
            else:
                msg = "Draw!"
                col_w = ACCENT_COL
            c.create_text(board_cx, board_cy-20, text=msg,
                fill=col_w, font=("Courier",24,"bold"), tags="rv_board")
            b = self.rv.count(BLACK)
            w = self.rv.count(WHITE)
            c.create_text(board_cx, board_cy+20,
                text=f"⚫ {b}  vs  ⬜ {w}",
                fill=TEXT_W, font=("Courier",14), tags="rv_board")

    def _draw_sidebar(self):
        c = self.canvas
        c.delete("rv_sidebar")
        sx = self._sidebar_x()

        c.create_rectangle(sx,0,self.rv_win_w,self.rv_win_h,
            fill=SIDEBAR_BG, outline="", tags="rv_sidebar")
        c.create_line(sx,0,sx,RV_WIN_H,
            fill=CELL_BORDER, width=2, tags="rv_sidebar")

        c.create_text(sx+12, 16, text="📊 VOTES",
            fill=ACCENT_COL, anchor="nw",
            font=("Courier",13,"bold"), tags="rv_sidebar")

        if self.voting:
            # 投票状況を表示（得票数降順）
            sorted_votes = sorted(self.votes.items(),
                                  key=lambda x: -x[1])
            y = 44
            legal = self.rv.legal_moves(WHITE)
            for (row,col), cnt in sorted_votes[:10]:
                lbl = chr(65+col) + str(row+1)
                valid = (row,col) in legal
                bar_w = min(int(cnt * 18), RV_SIDEBAR_W-60)
                c.create_rectangle(sx+12, y, sx+12+bar_w, y+14,
                    fill=ACCENT_COL if valid else TEXT_G,
                    outline="", tags="rv_sidebar")
                c.create_text(sx+12, y, text=f"{lbl}: {cnt}票",
                    fill=SIDEBAR_BG if bar_w>40 else TEXT_W,
                    anchor="nw", font=("Courier",11,"bold"), tags="rv_sidebar")
                y += 20
                if y > RV_WIN_H - 130:
                    break

            if not self.votes:
                c.create_text(sx+12, 44, text="No votes yet...",
                    fill=TEXT_G, anchor="nw",
                    font=("Courier",11), tags="rv_sidebar")

            # タイマーバー
            ratio = max(0, self.vote_timer / self.max_vote_sec)
            bar_full = RV_SIDEBAR_W - 24
            bar_now  = int(bar_full * ratio)
            bar_col  = SAFE_COL if ratio > 0.4 else FLAG_COL if ratio > 0.15 else MINE_COL
            c.create_rectangle(sx+12, self.rv_win_h-90, sx+12+bar_full, self.rv_win_h-76,
                fill=CELL_HID, outline="", tags="rv_sidebar")
            if bar_now > 0:
                c.create_rectangle(sx+12, self.rv_win_h-90, sx+12+bar_now, self.rv_win_h-76,
                    fill=bar_col, outline="", tags="rv_sidebar")
            c.create_text(sx+RV_SIDEBAR_W//2, self.rv_win_h-100,
                text=f"{max(0,self.vote_timer):.0f}s  [Space = close]",
                fill=bar_col, font=("Courier",10,"bold"), tags="rv_sidebar")

        else:
            if self.rv.turn == BLACK:
                c.create_text(sx+12, 44, text="Your turn",
                    fill=SAFE_COL, anchor="nw",
                    font=("Courier",12,"bold"), tags="rv_sidebar")
                c.create_text(sx+12, 66, text="Click a valid cell",
                    fill=TEXT_G, anchor="nw",
                    font=("Courier",10), tags="rv_sidebar")
            else:
                c.create_text(sx+12, 44, text="Processing...",
                    fill=TEXT_G, anchor="nw",
                    font=("Courier",11), tags="rv_sidebar")

        # コピーボタン
        cx1,cy1,cx2,cy2 = self._copy_btn_rect()
        copied   = self.copy_flash > 0
        btn_col  = SAFE_COL if copied else BTN_MENU
        txt_col  = SIDEBAR_BG if copied else TEXT_W
        btn_text = "✅ Copied!" if copied else "📋 Copy hint for chat"
        c.create_rectangle(cx1,cy1,cx2,cy2,
            fill=btn_col, outline=CELL_BORDER, width=1,
            tags=("rv_sidebar","rv_copy_bg"))
        c.create_text((cx1+cx2)//2, cy1+12, text=btn_text,
            fill=txt_col, font=("Courier",10,"bold"), tags="rv_sidebar")
        if not copied:
            c.create_text((cx1+cx2)//2, cy1+30,
                text=self.hint_text[:32],
                fill=TEXT_G, font=("Courier",8), tags="rv_sidebar")

# ══════════════════════════════════════════════
#  馬プロフィールモーダル（共通関数）
# ══════════════════════════════════════════════
def _modal_pos(pos, win_w, win_h, mw=520, mh=430):
    if pos is not None:
        mx, my = pos
        return max(0, min(win_w-mw, mx)), max(0, min(win_h-mh, my))
    return (win_w-mw)//2, (win_h-mh)//2


def _modal_pentagon(canvas, h, cx, cy, r, tag):
    import math
    keys   = ["speed","stamina","corner","mental","adaptability"]
    labels = ["速度","スタミナ","コーナー","精神力","適応力"]
    n = 5
    for level in [0.25,0.5,0.75,1.0]:
        pts = []
        for i in range(n):
            a = math.pi/2 + 2*math.pi*i/n
            pts.extend([cx+r*level*math.cos(a), cy-r*level*math.sin(a)])
        canvas.create_polygon(pts, fill="", outline="#222244", width=1, tags=tag)
    for i in range(n):
        a = math.pi/2 + 2*math.pi*i/n
        canvas.create_line(cx, cy, cx+r*math.cos(a), cy-r*math.sin(a),
                           fill="#222244", width=1, tags=tag)
    pts = []
    for i, key in enumerate(keys):
        val = h.get(key, 0) / 10.0
        a   = math.pi/2 + 2*math.pi*i/n
        pts.extend([cx+r*val*math.cos(a), cy-r*val*math.sin(a)])
    col = HR_COLORS[(h.get("number",1)-1) % len(HR_COLORS)]
    canvas.create_polygon(pts, fill=col, outline=col, width=2, tags=tag)
    canvas.create_polygon(pts, fill="", outline=col, width=2, tags=tag)
    for i, key in enumerate(keys):
        val = h.get(key, 0) / 10.0
        a   = math.pi/2 + 2*math.pi*i/n
        px, py = cx+r*val*math.cos(a), cy-r*val*math.sin(a)
        canvas.create_oval(px-4, py-4, px+4, py+4, fill=col, outline="", tags=tag)
    for i, (key, lbl) in enumerate(zip(keys, labels)):
        a  = math.pi/2 + 2*math.pi*i/n
        lx = cx+(r+26)*math.cos(a)
        ly = cy-(r+26)*math.sin(a)
        sn = min(5, max(0, round(h.get(key,0)/2)))
        canvas.create_text(lx, ly-7, text=lbl,
            fill=TEXT_G, font=("Courier",9), anchor="center", tags=tag)
        canvas.create_text(lx, ly+7, text="★"*sn+"☆"*(5-sn),
            fill=FLAG_COL, font=("Courier",9), anchor="center", tags=tag)


def draw_horse_modal(canvas, h, pos, win_w, win_h, odds=None, on_close=None):
    tag = "hr_modal"
    canvas.delete(tag)
    mw, mh = 560, 460
    mx, my = _modal_pos(pos, win_w, win_h, mw, mh)
    col    = HR_COLORS[(h.get("number",1)-1) % len(HR_COLORS)]

    # 背景（Canvasの bg=BG が暗幕代わり。stippleはWindowsで重いため省略）
    # 本体
    canvas.create_rectangle(mx, my, mx+mw, my+mh,
        fill="#0D1025", outline=col, width=2, tags=tag)
    # ヘッダー
    canvas.create_rectangle(mx, my, mx+mw, my+44,
        fill=BTN_DARK, outline="", tags=tag)
    mark = "🐴 " if h.get("is_trained") else ""
    canvas.create_text(mx+16, my+22,
        text=f"{mark}{h.get('number','')}番  {h.get('name','')}",
        fill=col, anchor="w", font=("Courier",14,"bold"), tags=tag)
    canvas.create_text(mx+mw//2, my+22, text="⠿ ドラッグで移動",
        fill=TEXT_G, anchor="center", font=("Courier",8), tags=tag)
    # ×ボタン
    canvas.create_rectangle(mx+mw-36, my+8, mx+mw-8, my+36,
        fill="#2A1A1A", outline=MINE_COL, width=1, tags=tag)
    canvas.create_text(mx+mw-22, my+22, text="×",
        fill=MINE_COL, font=("Courier",13,"bold"), tags=tag)

    # 五角形グラフ
    _modal_pentagon(canvas, h, mx+100, my+175, 80, tag)

    # 右側ステータス
    rx, ry2 = mx+230, my+56
    for lbl, key in [("速度","speed"),("スタミナ","stamina"),("コーナー","corner"),
                     ("精神力","mental"),("適応力","adaptability")]:
        val = h.get(key, 0)
        sn  = min(5, max(0, round(val/2)))
        canvas.create_text(rx, ry2, text=f"{lbl}:",
            fill=TEXT_G, anchor="w", font=("Courier",10), tags=tag)
        canvas.create_text(rx+72, ry2, text="★"*sn+"☆"*(5-sn),
            fill=FLAG_COL, anchor="w", font=("Courier",10), tags=tag)
        ry2 += 20

    ry2 += 4
    apt_t = h.get("apt_turf","○")
    apt_d = h.get("apt_dirt","○")
    canvas.create_text(rx, ry2, text=f"芝:{apt_t}  ダート:{apt_d}",
        fill=TEXT_G, anchor="w", font=("Courier",10), tags=tag)
    ry2 += 20
    cond = h.get("condition","○")
    cond_col = SAFE_COL if cond=="◎" else (FLAG_COL if cond=="○" else
               (TEXT_G if cond=="△" else MINE_COL))
    canvas.create_text(rx, ry2, text=f"調子: {cond}",
        fill=cond_col, anchor="w", font=("Courier",11,"bold"), tags=tag)
    ry2 += 20
    if odds:
        ov   = odds.get(h.get("number",0), 0.0)
        ocol = MINE_COL if ov<3.0 else (FLAG_COL if ov<6.0 else SAFE_COL)
        canvas.create_text(rx, ry2, text=f"オッズ: {ov:.1f}倍",
            fill=ocol, anchor="w", font=("Courier",11,"bold"), tags=tag)
        ry2 += 20
    jock = h.get("jockey", {})
    if jock:
        jskl = "★"*jock.get("skill",0)+"☆"*(5-jock.get("skill",0))
        canvas.create_text(rx, ry2, text=f"騎手: {jock.get('name','')}",
            fill=TEXT_W, anchor="w", font=("Courier",10,"bold"), tags=tag)
        ry2 += 17
        canvas.create_text(rx, ry2, text=f"技術:{jskl}  {jock.get('style','')}",
            fill=TEXT_G, anchor="w", font=("Courier",9), tags=tag)
        ry2 += 17
        aff = h.get("affinity","△")
        ac  = SAFE_COL if aff=="◎" else (ACCENT_COL if aff=="○" else
              (FLAG_COL if aff=="△" else MINE_COL))
        canvas.create_text(rx, ry2, text=f"相性: {aff}",
            fill=ac, anchor="w", font=("Courier",10,"bold"), tags=tag)

    # 特性
    traits = h.get("traits", [])
    if traits:
        try:
            from training import COMBO_TRAITS as _CT
            combo_names = {c["name"] for c in _CT}
        except Exception:
            combo_names = set()
        base_t  = [t for t in traits if t not in combo_names]
        combo_t = [t for t in traits if t in combo_names]
        ty = my + mh - 80
        canvas.create_line(mx+10, ty-6, mx+mw-10, ty-6,
            fill=CELL_BORDER, width=1, tags=tag)
        if base_t:
            canvas.create_text(mx+16, ty, text="特性: "+"  ".join(base_t),
                fill=TEXT_G, anchor="w", font=("Courier",10), tags=tag)
            ty += 18
        if combo_t:
            canvas.create_text(mx+16, ty, text="✨ "+"  ".join(combo_t),
                fill=FLAG_COL, anchor="w", font=("Courier",11,"bold"), tags=tag)
            ty += 18

    # コメント
    cy_com = my + mh - 28
    canvas.create_line(mx+10, cy_com-10, mx+mw-10, cy_com-10,
        fill=CELL_BORDER, width=1, tags=tag)
    canvas.create_text(mx+16, cy_com,
        text=f"「{h.get('comment','')[:52]}」",
        fill=FLAG_COL, anchor="w", font=("Courier",9), tags=tag)

class HorseLobby:
    def __init__(self, root, cfg, on_start, on_back, on_train=None, on_code=None):
        self.root     = root
        self.cfg      = cfg
        self.on_start = on_start
        self.on_back  = on_back

        root.title("ChatViewPlayGame - 競馬")
        root.configure(bg=BG)

        self.on_train  = on_train
        self.on_code   = on_code

        make_label(root, "🏇 競馬",
                   fg=ACCENT_COL, font=("Courier", 20, "bold")).pack(pady=(24,4))
        make_label(root, "チャットで馬に投票してレースに参加！",
                   fg=TEXT_G, font=("Courier", 11)).pack(pady=(0,18))

        frame = tk.Frame(root, bg=BG)
        frame.pack(padx=36)

        make_label(frame, "投票時間:",
                   font=("Courier",12,"bold"), anchor="w").pack(fill="x", pady=(0,4))
        self.vote_var = tk.IntVar(value=cfg.get("hr_vote_sec", 60))
        vf = tk.Frame(frame, bg=BG)
        vf.pack(fill="x")
        for sec in [30, 60, 90, 120]:
            tk.Radiobutton(vf, text=f"{sec}秒", variable=self.vote_var, value=sec,
                           bg=BG, fg=TEXT_W, selectcolor=CELL_HID,
                           activebackground=BG, activeforeground=ACCENT_COL,
                           font=("Courier",11)).pack(side="left", padx=(0,16))

        make_label(frame, "* チャットで馬の番号（例: 3）を入力して投票",
                   fg=TEXT_G, font=("Courier",10)).pack(anchor="w", pady=(8,0))

        make_label(frame, "レース数:",
                   font=("Courier",12,"bold"), anchor="w").pack(fill="x", pady=(14,4))
        self.race_count_var = tk.StringVar(value=cfg.get("hr_race_count", "3"))
        rcf = tk.Frame(frame, bg=BG)
        rcf.pack(fill="x")
        for val, label in [("1","1レース"),("3","3レース"),("5","5レース"),("10","10レース"),("0","無限")]:
            tk.Radiobutton(rcf, text=label, variable=self.race_count_var, value=val,
                           bg=BG, fg=TEXT_W, selectcolor=CELL_HID,
                           activebackground=BG, activeforeground=ACCENT_COL,
                           font=("Courier",11)).pack(side="left", padx=(0,12))

        make_label(frame, "レースグレード:",
                   font=("Courier",12,"bold"), anchor="w").pack(fill="x", pady=(14,4))

        from horserace import GRADE_DEFS, DEFAULT_GRADE
        self.grade_var = tk.StringVar(value=cfg.get("hr_grade", DEFAULT_GRADE))
        gf = tk.Frame(frame, bg=BG)
        gf.pack(fill="x")

        grade_colors = {
            "未勝利": "#88aa88",
            "G3":     "#88aacc",
            "G2":     "#4488ff",
            "G1":     "#ffcc44",
            "特別G1": "#ff6644",
        }
        for gkey, gdef in GRADE_DEFS.items():
            col = grade_colors.get(gkey, TEXT_W)
            tk.Radiobutton(gf, text=gdef["label"],
                           variable=self.grade_var, value=gkey,
                           bg=BG, fg=col, selectcolor=CELL_HID,
                           activebackground=BG, activeforeground=col,
                           font=("Courier",10)).pack(anchor="w", pady=1)

        make_label(frame, "育成馬の連続出走:",
                   font=("Courier",12,"bold"), anchor="w").pack(fill="x", pady=(14,4))
        self.keep_trained_var = tk.BooleanVar(value=cfg.get("hr_keep_trained", False))
        kf = tk.Frame(frame, bg=BG)
        kf.pack(fill="x")
        for val, lbl, desc in [
            (True,  "有効", "次のレースにも育成馬が引き続き出走"),
            (False, "無効", "育成馬は1レースのみ"),
        ]:
            row = tk.Frame(kf, bg=BG)
            row.pack(fill="x", pady=1)
            tk.Radiobutton(row, text=lbl, variable=self.keep_trained_var, value=val,
                           bg=BG, fg=TEXT_W, selectcolor=CELL_HID,
                           activebackground=BG, activeforeground=ACCENT_COL,
                           font=("Courier",11,"bold"), anchor="w").pack(side="left")
            tk.Label(row, text=f"  {desc}", bg=BG, fg=TEXT_G,
                     font=("Courier",10)).pack(side="left")

        make_label(frame, "結果後の自動遷移:",
                   font=("Courier",12,"bold"), anchor="w").pack(fill="x", pady=(14,4))
        self.auto_var = tk.IntVar(value=cfg.get("hr_auto_next", 0))
        af = tk.Frame(frame, bg=BG)
        af.pack(fill="x")
        for sec, label in [(0,"なし（手動）"),(15,"15秒"),(30,"30秒"),(60,"60秒")]:
            tk.Radiobutton(af, text=label, variable=self.auto_var, value=sec,
                           bg=BG, fg=TEXT_W, selectcolor=CELL_HID,
                           activebackground=BG, activeforeground=ACCENT_COL,
                           font=("Courier",11)).pack(side="left", padx=(0,14))

        self.err_var = tk.StringVar()
        tk.Label(frame, textvariable=self.err_var, bg=BG, fg=MINE_COL,
                 font=("Courier",11)).pack(pady=(8,0))

        tk.Frame(frame, bg=CELL_BORDER, height=1).pack(fill="x", pady=(12,12))

        bf = tk.Frame(frame, bg=BG)
        bf.pack(fill="x", pady=(0,24))
        make_btn(bf, "◀  戻る", self.on_back).pack(side="left")
        make_btn(bf, "🐴  馬を育てる", self.on_train,
                 bg=FLAG_COL, fg=BG).pack(side="left", padx=(8,0))
        make_btn(bf, "📋  コードで参戦", self.on_code,
                 bg=ACCENT_COL, fg=BG).pack(side="left", padx=(8,0))
        make_btn(bf, "▶  レース開始", self._start,
                 bg=SAFE_COL, fg=BG).pack(side="right")

    def _start(self):
        online = self.cfg.get("online_mode", True)
        if online and (not self.cfg.get("channel") or not self.cfg.get("token","").startswith("oauth:")):
            self.err_var.set("⚠ Settings not configured")
            return
        self.cfg["hr_vote_sec"]      = self.vote_var.get()
        self.cfg["hr_auto_next"]     = self.auto_var.get()
        self.cfg["hr_race_count"]    = self.race_count_var.get()
        self.cfg["hr_keep_trained"]  = self.keep_trained_var.get()
        self.cfg["hr_grade"]         = self.grade_var.get()
        save_config(self.cfg)
        race_count = int(self.race_count_var.get())
        self.on_start(self.cfg, self.vote_var.get(), race_count)


# ══════════════════════════════════════════════
#  競馬 メイン画面
#  フェーズ: vote → gate → race → goal → result
# ══════════════════════════════════════════════

class HorseRaceScreen:
    PHASES = ["vote", "gate", "race", "goal", "result"]

    def __init__(self, root, cfg, vote_sec, race_count, on_menu, trained_horse=None, trained_list=None):
        self.root     = root
        self.cfg      = cfg
        self.vote_sec      = vote_sec
        self.race_count    = race_count
        self.on_menu       = on_menu
        self.trained_horse = trained_horse
        self.trained_list  = trained_list if trained_list else (
            [trained_horse] if trained_horse is not None else [])
        self.keep_trained  = cfg.get("hr_keep_trained", False)

        root.title("ChatViewPlayGame - 競馬")
        root.configure(bg=BG)

        res_name = cfg.get("resolution", DEFAULT_RES)
        self.win_w, self.win_h = RESOLUTIONS.get(res_name, RESOLUTIONS[DEFAULT_RES])

        self.canvas = tk.Canvas(root, width=self.win_w, height=self.win_h,
                                bg=BG, highlightthickness=0)
        self.canvas.pack()

        # レース生成（育成馬がいれば残り枠をランダムで補完）
        t_list = trained_list if trained_list else (
            [trained_horse] if trained_horse is not None else [])
        n_trained  = len(t_list)
        n_random   = max(0, 8 - n_trained)
        if n_trained > 0:
            _gkey = cfg.get("hr_grade", "G3")
            self.race   = generate_race(num_horses=n_random, grade_key=_gkey)
            rand_horses = self.race["horses"]
            # 育成馬を1〜n_trained番、ランダム馬をn_trained+1〜8番に
            for i, h in enumerate(t_list):
                h["number"] = i + 1
            for i, h in enumerate(rand_horses):
                h["number"] = n_trained + i + 1
            self.race["horses"] = t_list + rand_horses
        else:
            _gkey = cfg.get("hr_grade", "G3")
            self.race   = generate_race(num_horses=8, grade_key=_gkey)
        self.horses  = self.race["horses"]
        self.results = None
        self.odds    = self.race["odds"]
        if n_trained > 0:
            from horserace import calc_odds
            self.odds = calc_odds(
                self.horses, self.race["surface"], self.race["distance"])

        # 投票
        self.votes      = {}   # {horse_number: count}
        self.vote_timer = float(vote_sec)
        self.voters     = {}   # {username: horse_number} 1人1票

        # ポイントシステム: {username: points}（初期1pt、的中で倍率×1pt獲得）
        self.points     = {}

        # フェーズ管理
        self.phase      = "vote"
        self.phase_t    = 0.0   # フェーズ内経過時間
        self.prev_time  = time.time()
        self._running   = True

        # アニメーション
        self.anim_frame   = 0
        self.horse_pos    = []  # レース中の各馬x座標 (0.0〜1.0)
        self.gate_open    = False
        self.finish_flash = 0.0
        self.danmaku      = []

        # 画像ロード（失敗時はIconHorseRendererにフォールバック）
        import os
        self.img_dir = os.path.join(
            os.path.dirname(sys.executable) if getattr(sys,"frozen",False)
            else os.path.dirname(os.path.abspath(__file__)),
            "img"
        )
        img_dir = self.img_dir
        track_h   = self.win_h - 80 - 60
        lane_h    = track_h // 8
        target_h  = int(lane_h * 0.85)
        self.horse_sprites = load_horse_sprites(img_dir, target_h)
        self.gate_img      = load_gate_image(img_dir, self.win_w, self.win_h)
        self.use_images    = self.horse_sprites is not None

        # 馬描画レンダラー（馬ごとに個別タグ）
        if self.use_images:
            self.renderers = [
                ImageHorseRenderer(self.horse_sprites, f"horse_{i}")
                for i in range(len(self.horses))
            ]
        else:
            self.renderers = [IconHorseRenderer(f"horse_{i}") for i in range(len(self.horses))]

        # Twitch（オフライン時は接続しない）
        self.online_mode = cfg.get("online_mode", True)
        self.twitch = TwitchClient(
            cfg["channel"], cfg["token"],
            on_command=self._on_cmd,
            on_chat=self._on_chat,
        )
        if self.online_mode:
            threading.Thread(
                target=lambda: asyncio.run(self.twitch.connect()), daemon=True
            ).start()

        root.bind("<space>", self._on_space)
        self.canvas.bind("<Button-1>",       self._on_canvas_click)
        self.canvas.bind("<Motion>",           self._on_canvas_motion)
        self.canvas.bind("<B1-Motion>",        self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>",  self._on_canvas_release)
        self.hover_horse    = None
        self.my_vote        = None
        self._vote_rects    = []
        self._detail_rects  = []    # [(num, x1,y1,x2,y2), ...] 詳細ボタン
        self._result_btn    = None
        self._modal_horse     = None
        self._modal_horse_pos = None  # モーダル左上座標 (mx,my)
        self._modal_close     = None
        self._modal_drag      = None  # ドラッグ開始時の (mouse_x,mouse_y,modal_x,modal_y)
        self._final_btn    = None   # 最終結果ボタン座標
        self._transitioning = False  # 遷移中フラグ（2重防止）
        self.auto_next_sec  = float(cfg.get("hr_auto_next", 0))
        self.result_timer   = 0.0
        self.current_race   = 1
        # 累積成績: {username: {"votes": N, "hits": N, "points": float}}
        self.cumulative     = {}
        self._loop()

    # ── ループ ───────────────────────────────
    def _loop(self):
        if not self._running:
            return
        now = time.time()
        dt  = now - self.prev_time
        self.prev_time = now
        self.anim_frame = (self.anim_frame + 1) % 4

        self.phase_t += dt
        for d in self.danmaku:
            d.update(dt)
        self.danmaku = [d for d in self.danmaku if d.alive]

        if self.finish_flash > 0:
            self.finish_flash = max(0.0, self.finish_flash - dt)

        # ゴール花吹雪パーティクル更新
        if hasattr(self, "_goal_particles") and self._goal_particles:
            for p in self._goal_particles:
                p["x"]  += p["vx"] * dt
                p["y"]  += p["vy"] * dt
                p["vy"] += 120 * dt  # 重力
                if p["y"] > self.win_h + 20:
                    p["alive"] = False
            self._goal_particles = [p for p in self._goal_particles if p["alive"]]

        self._update_phase(dt)
        self._draw()
        if getattr(self, "_modal_horse", None) is not None:
            self._draw_profile_modal()
        self.root.after(1000 // HR_FPS, self._loop)

    def _draw_profile_modal(self):
        """馬プロフィールモーダルをCanvas最前面に描画"""
        h   = self._modal_horse
        if h is None:
            return
        draw_horse_modal(self.canvas, h, self._modal_horse_pos,
                         self.win_w, self.win_h, self.odds,
                         on_close=self._close_modal)
        self._modal_close = getattr(self, "_modal_close", None)

    def _close_modal(self):
        self._modal_horse     = None
        self._modal_horse_pos = None
        self._modal_drag      = None

    def _draw_modal_pentagon(self, canvas, h, cx, cy, r, tag):
        """モーダル用五角形レーダーチャート"""
        import math
        keys   = ["speed","stamina","corner","mental","adaptability"]
        labels = ["速度","スタミナ","コーナー","精神力","適応力"]
        n      = len(keys)
        # 最大値（1〜10スケール）
        max_val = 10.0

        # グリッド
        for level in [0.25, 0.5, 0.75, 1.0]:
            pts = []
            for i in range(n):
                angle = math.pi/2 + 2*math.pi*i/n
                pts.extend([cx + r*level*math.cos(angle),
                             cy - r*level*math.sin(angle)])
            canvas.create_polygon(pts, fill="", outline="#222244", width=1, tags=tag)
        # 軸線
        for i in range(n):
            angle = math.pi/2 + 2*math.pi*i/n
            canvas.create_line(cx, cy,
                cx+r*math.cos(angle), cy-r*math.sin(angle),
                fill="#222244", width=1, tags=tag)
        # ステータス多角形
        pts = []
        for i, key in enumerate(keys):
            val   = h.get(key, 0) / max_val
            angle = math.pi/2 + 2*math.pi*i/n
            pts.extend([cx+r*val*math.cos(angle), cy-r*val*math.sin(angle)])
        col = HR_COLORS[(h["number"]-1) % len(HR_COLORS)]
        canvas.create_polygon(pts, fill=col, outline=col,
                              width=2, tags=tag)
        canvas.create_polygon(pts, fill="", outline=col, width=2, tags=tag)
        # 頂点ドット
        for i, key in enumerate(keys):
            val   = h.get(key, 0) / max_val
            angle = math.pi/2 + 2*math.pi*i/n
            px    = cx+r*val*math.cos(angle)
            py    = cy-r*val*math.sin(angle)
            canvas.create_oval(px-4, py-4, px+4, py+4,
                               fill=col, outline="", tags=tag)
        # ラベル＋星
        for i, (key, lbl) in enumerate(zip(keys, labels)):
            angle = math.pi/2 + 2*math.pi*i/n
            lx    = cx+(r+24)*math.cos(angle)
            ly    = cy-(r+24)*math.sin(angle)
            stars_n = min(5, max(0, round(h.get(key,0)/2)))
            stars   = "★"*stars_n+"☆"*(5-stars_n)
            canvas.create_text(lx, ly-7, text=lbl,
                fill=TEXT_G, font=("Courier",9), anchor="center", tags=tag)
            canvas.create_text(lx, ly+6, text=stars,
                fill=FLAG_COL, font=("Courier",9), anchor="center", tags=tag)

    def _update_phase(self, dt):
        if self.phase == "vote":
            self.vote_timer -= dt
            if self.vote_timer <= 0:
                self._end_vote()

        elif self.phase == "gate":
            if self.phase_t >= 4.0:
                self._start_race()

        elif self.phase == "race":
            # 距離に応じた速度係数（短距離は速く、長距離は遅く）
            dist = self.race["distance"]
            if dist <= 1400:
                dist_factor = 1.30   # 短距離: 速め
            elif dist <= 1800:
                dist_factor = 1.10   # マイル: やや速め
            elif dist <= 2200:
                dist_factor = 1.00   # 中距離: 標準
            elif dist <= 2800:
                dist_factor = 0.85   # 中長距離: やや遅め
            else:
                dist_factor = 0.72   # 長距離: 遅め（長く楽しめる）

            for res in self.results:
                h_num = res["horse"]["number"]
                idx   = next(i for i,h in enumerate(self.horses) if h["number"]==h_num)
                base_speed = (0.0015 + res["norm"] * 0.0008) * dist_factor
                rand_spd   = random.uniform(0.9, 1.1)
                self.horse_pos[idx] = min(1.0, self.horse_pos[idx] + base_speed * rand_spd)

            # 先頭馬がゴールしたらすぐ演出開始（1度だけ）
            if self.horse_pos and max(self.horse_pos) >= 1.0 and not self._goal_triggered:
                self._goal_triggered = True
                self._start_goal()

        elif self.phase == "goal":
            if self.phase_t >= 4.0:
                self.phase          = "result"
                self.phase_t        = 0.0
                self.result_timer   = 0.0
                self._transitioning = False

        elif self.phase == "result":
            if self.auto_next_sec > 0:
                self.result_timer += dt
                if self.result_timer >= self.auto_next_sec:
                    self._next_race_or_end()

    # ── フェーズ遷移 ─────────────────────────
    def _end_vote(self):
        self.phase      = "gate"
        self.phase_t    = 0.0
        self.vote_timer = 0.0
        # 投票結果に基づき馬の調子を微調整
        if self.votes:
            top_num = max(self.votes, key=lambda k: self.votes[k])
            for h in self.horses:
                if h["number"] == top_num:
                    h["cond_mult"] = min(h["cond_mult"] * 1.05, 1.3)

    def _start_race(self):
        self.phase           = "race"
        self.phase_t         = 0.0
        self._goal_triggered = False
        self.results         = run_race(self.horses, self.race["surface"], self.race["distance"])
        self.horse_pos       = [0.0] * len(self.horses)

    def _start_goal(self):
        self.phase        = "goal"
        self.phase_t      = 0.0
        self.finish_flash = 2.0
        # ゴール用花吹雪パーティクル（Particleクラスとは別に独自管理）
        self._goal_particles = []
        if self.results:
            winner = next((r for r in self.results if r["rank"]==1), None)
            if winner:
                win_col = HR_COLORS[(winner["horse"]["number"]-1) % len(HR_COLORS)]
                colors  = [win_col, FLAG_COL, "#FFFFFF", ACCENT_COL, SAFE_COL]
                import random as _r
                for _ in range(100):
                    self._goal_particles.append({
                        "x":     _r.uniform(0, self.win_w),
                        "y":     _r.uniform(-60, self.win_h * 0.3),
                        "vx":    _r.uniform(-40, 40),
                        "vy":    _r.uniform(60, 180),
                        "color": _r.choice(colors),
                        "r":     _r.randint(3, 7),
                        "alive": True,
                    })
        # ゴール背景画像ロード（未ロード時）
        if not hasattr(self, "_goal_bg_img"):
            self._load_goal_bg()

    def _load_goal_bg(self):
        """ゴール背景画像（haikei01優先→rdesign_19917フォールバック）と勝ち馬大画像をロード"""
        import os
        self._goal_bg_img       = None
        self._goal_bg_img_small = None
        self._goal_big_img      = None
        try:
            from PIL import Image, ImageTk
            img_dir = self.img_dir
            # haikei01.png を優先、なければ rdesign_19917.png にフォールバック
            for fname in ("haikei01.png", "rdesign_19917.png"):
                path = os.path.join(img_dir, fname)
                if os.path.exists(path):
                    img  = Image.open(path).convert("RGBA")
                    full = img.resize((self.win_w, self.win_h), Image.LANCZOS)
                    self._goal_bg_img = ImageTk.PhotoImage(full)
                    gw = int(self.win_h * 0.6)
                    gh = int(self.win_h * 0.6)
                    self._goal_bg_img_small = ImageTk.PhotoImage(img.resize((gw,gh), Image.LANCZOS))
                    break
        except Exception as e:
            print(f"[GoalBG] {e}")

        # 勝ち馬の大画像を生成
        if not self.use_images or not self.results:
            return
        winner = next((r for r in self.results if r["rank"]==1), None)
        if not winner:
            return
        try:
            from PIL import Image, ImageTk
            import numpy as np
            from horserace import SPRITE_CROPS
            coat = winner["horse"].get("coat","brown")
            img_dir = os.path.join(
                os.path.dirname(sys.executable) if getattr(sys,"frozen",False)
                else os.path.dirname(os.path.abspath(__file__)), "img")
            path = os.path.join(img_dir,
                "rdesign_19914.png" if coat=="brown" else "rdesign_19916.png")
            x1,y1,x2,y2 = SPRITE_CROPS[winner["horse"]["number"]]
            sheet = Image.open(path).convert("RGBA")
            arr   = np.array(sheet)
            mask  = (arr[:,:,0].astype(int)+arr[:,:,1].astype(int)+arr[:,:,2].astype(int))<=30
            arr[mask,3] = 0
            crop = Image.fromarray(arr,"RGBA").crop((x1,y1,x2,y2))
            crop = crop.transpose(Image.FLIP_LEFT_RIGHT)
            th   = int(self.win_h * 0.55)
            tw   = int(crop.width * th / crop.height)
            crop = crop.resize((tw, th), Image.LANCZOS)
            self._goal_big_img = ImageTk.PhotoImage(crop)
        except Exception as e:
            print(f"[GoalBigImg] {e}")
        # 的中を累積成績とポイントに反映
        if self.results:
            winner_num = self.results[0]["horse"]["number"]
            winner_odds = self.odds.get(winner_num, 2.0)
            for username, voted_num in self.voters.items():
                if username not in self.cumulative:
                    self.cumulative[username] = {"votes": 0, "hits": 0, "points": 1.0}
                if voted_num == winner_num:
                    self.cumulative[username]["hits"] += 1
                    # 的中ポイント: オッズ × 1pt（小数点1桁で切り上げ）
                    gain = round(winner_odds, 1)
                    self.cumulative[username]["points"] = round(
                        self.cumulative[username]["points"] + gain, 1)

    # ── 入力 ─────────────────────────────────
    def _on_space(self, ev):
        if self.phase == "vote":
            self._end_vote()

    def _on_canvas_click(self, ev):
        # モーダル表示中の処理
        if self._modal_horse is not None:
            mx, my = _modal_pos(self._modal_horse_pos, self.win_w, self.win_h)
            mw, mh = 560, 460
            # ×ボタン
            cx1,cy1,cx2,cy2 = mx+mw-36, my+8, mx+mw-8, my+36
            if cx1<=ev.x<=cx2 and cy1<=ev.y<=cy2:
                self._close_modal()
                return
            # ヘッダー内（×以外）→ ドラッグ開始
            if mx<=ev.x<=mx+mw and my<=ev.y<=my+44:
                self._modal_drag = (ev.x, ev.y, mx, my)
                return
            # モーダル外クリックで閉じる
            if not (mx<=ev.x<=mx+mw and my<=ev.y<=my+mh):
                self._close_modal()
            return

        # 詳細ボタン（投票フェーズ）
        if self.phase == "vote":
            for num, x1, y1, x2, y2 in self._detail_rects:
                if x1<=ev.x<=x2 and y1<=ev.y<=y2:
                    h = next((h for h in self.horses if h["number"]==num), None)
                    if h:
                        self._modal_horse = h
                    return

        # メニューボタン（全フェーズ共通）
        bx = self.win_w - 116
        if bx <= ev.x <= bx+108 and 6 <= ev.y <= 36:
            self._go_menu()
            return
        # 最終結果画面ボタン
        if self.phase == "final" and self._final_btn:
            bx, by = self._final_btn
            if bx <= ev.x <= bx+130 and by <= ev.y <= by+38:
                self._go_menu()
                return
        # 結果画面ボタン
        if self.phase == "result" and self._result_btn:
            bx1, by, bx2 = self._result_btn
            if bx1 <= ev.x <= bx1+130 and by <= ev.y <= by+38:
                self._go_menu()
                return
            if bx2 <= ev.x <= bx2+150 and by <= ev.y <= by+38:
                self._next_race_or_end()
                return
        # 投票フェーズ中: 馬リストをクリックで投票
        if self.phase == "vote":
            for num, x1, y1, x2, y2 in self._vote_rects:
                if x1 <= ev.x <= x2 and y1 <= ev.y <= y2:
                    self._do_vote("[配信者]", num)
                    return
        # 結果画面は _draw_result 内で bind するため不要

    def _on_canvas_drag(self, ev):
        """B1-Motion: ドラッグ中の処理"""
        if self._modal_drag is not None:
            ox, oy, bmx, bmy = self._modal_drag
            self._modal_horse_pos = (bmx + ev.x - ox, bmy + ev.y - oy)
            # throttle: 50ms以内は再描画しない（_loop が次フレームで描画する）

    def _on_canvas_motion(self, ev):
        if self.phase != "vote":
            self.hover_horse = None
            return
        for num, x1, y1, x2, y2 in self._vote_rects:
            if x1 <= ev.x <= x2 and y1 <= ev.y <= y2:
                self.hover_horse = num
                return
        self.hover_horse = None

    def _on_canvas_release(self, ev):
        if self._modal_drag is not None:
            ox, oy, bmx, bmy = self._modal_drag
            self._modal_horse_pos = (bmx + ev.x - ox, bmy + ev.y - oy)
            self._modal_drag = None

    def _do_vote(self, username, num):
        """投票処理（チャット・クリック共通）"""
        if username not in self.voters:
            self.voters[username] = num
            self.votes[num] = self.votes.get(num, 0) + 1
            # 累積成績に投票を記録（初回は1pt付与）
            if username not in self.cumulative:
                self.cumulative[username] = {"votes": 0, "hits": 0, "points": 1.0}
            self.cumulative[username]["votes"] += 1
            if username == "[配信者]":
                self.my_vote = num
            else:
                self.danmaku.append(
                    DanmakuMsg(self.canvas, username, f"→ {num}番", self.win_w))

    def _on_cmd(self, username, col, row, is_flag):
        # コマンド形式（A1等）は無視、チャットで数字投票
        pass

    def _on_chat(self, username, text):
        text = text.strip()
        if self.phase == "vote" and text.isdigit():
            num = int(text)
            if 1 <= num <= len(self.horses):
                self._do_vote(username, num)
                return
        self.danmaku.append(DanmakuMsg(self.canvas, username, text, self.win_w))

    def _go_menu(self):
        self._running = False
        self.twitch.stop()
        for d in self.danmaku:
            try:
                self.canvas.delete(d.text_id)
                self.canvas.delete(d.shadow_id)
            except Exception:
                pass
        self.on_menu()

    # ── 描画 ─────────────────────────────────
    def _draw(self):
        self.canvas.delete("hr_bg","hr_header","hr_main","hr_overlay")
        # 背景
        self.canvas.create_rectangle(0,0,self.win_w,self.win_h,
            fill=BG, outline="", tags="hr_bg")

        if self.phase == "vote":
            self._draw_vote()
        elif self.phase == "gate":
            self._draw_gate()
        elif self.phase == "race":
            self._draw_race()
        elif self.phase == "goal":
            self._draw_goal_scene()
        elif self.phase == "result":
            self._draw_result()
        elif self.phase == "final":
            self._draw_final()

        # 弾幕
        for d in self.danmaku:
            self.canvas.tag_raise(d.shadow_id)
            self.canvas.tag_raise(d.text_id)

    def _draw_header(self, tag="hr_header"):
        c = self.canvas
        c.create_rectangle(0,0,self.win_w,70,
            fill=HEADER_BG, outline="", tags=tag)
        c.create_text(self.win_w//2, 20,
            text=f"🏇 {self.race['name']}",
            fill=ACCENT_COL, font=("Courier",16,"bold"), tags=tag)
        surface  = self.race["surface"]
        distance = self.race["distance"]
        surf_col = "#50E080" if surface == "芝" else "#C8A050"  # 芝=緑、ダート=茶
        dist_col = "#64C8FF" if distance <= 1400 else ("#FFFFFF" if distance <= 2000 else "#FFB060")
        # 芝/ダートと距離を別々に色付け
        # グレードバッジ
        grade_key = self.race.get("grade", "G3")
        grade_colors = {
            "未勝利": "#88aa88","G3":"#88aacc","G2":"#4488ff",
            "G1":"#ffcc44","特別G1":"#ff6644",
        }
        gc = grade_colors.get(grade_key, "#88aacc")
        c.create_text(self.win_w//2 - 110, 48,
            text=f"[{grade_key}]",
            fill=gc, font=("Courier",13,"bold"), tags=tag)
        cx_surf = self.win_w//2 - 20
        cx_dist = self.win_w//2 + 50
        c.create_text(cx_surf, 48,
            text=surface,
            fill=surf_col, font=("Courier",13,"bold"), tags=tag)
        c.create_text(cx_dist, 48,
            text=f"{distance}m",
            fill=dist_col, font=("Courier",13,"bold"), tags=tag)
        # メニューボタン
        bx = self.win_w - 116
        c.create_rectangle(bx,6,bx+108,36,
            fill=BTN_MENU, outline=CELL_BORDER, tags=tag)
        c.create_text(bx+54,21, text="◀ メニュー",
            fill=TEXT_W, font=("Courier",11,"bold"), tags=tag)
        # メニューボタンの判定は _on_canvas_click で行う（tag_bindは使わない）

    def _check_menu_click(self, ev):
        bx = self.win_w - 116
        if bx <= ev.x <= bx+108 and 6 <= ev.y <= 36:
            self._go_menu()

    def _draw_vote(self):
        c   = self.canvas
        tag = "hr_main"
        self._draw_header()

        # ── カラム境界 ──
        jx  = HR_HORSE_W          # 騎手カラム開始x
        vx  = HR_INFO_W           # 投票状況カラム開始x
        hdr = 70
        y0  = hdr + 2

        # 馬情報カラム背景
        c.create_rectangle(0, hdr, HR_HORSE_W, self.win_h,
            fill=SIDEBAR_BG, outline="", tags=tag)
        # 騎手カラム背景（少し明るく）
        c.create_rectangle(HR_HORSE_W, hdr, HR_INFO_W, self.win_h,
            fill="#13162A", outline="", tags=tag)
        # カラム区切り線
        for lx in [HR_HORSE_W, HR_INFO_W]:
            c.create_line(lx, hdr, lx, self.win_h,
                fill=CELL_BORDER, width=1, tags=tag)

        # カラムヘッダー
        c.create_text(HR_HORSE_W//2, y0+8,
            text="出走馬一覧", fill=ACCENT_COL,
            font=("Courier",12,"bold"), tags=tag)
        c.create_text(HR_HORSE_W + HR_JOCKEY_W//2, y0+8,
            text="騎手情報", fill=ACCENT_COL,
            font=("Courier",12,"bold"), tags=tag)
        c.create_text(vx + (self.win_w-vx)//2, y0+8,
            text="📊 投票状況", fill=ACCENT_COL,
            font=("Courier",12,"bold"), tags=tag)

        y   = y0 + 28
        n   = len(self.horses)
        row_h = (self.win_h - y - 56) // n
        row_h = min(row_h, 82)

        self._vote_rects   = []
        self._detail_rects = []
        for i, h in enumerate(self.horses):
            ry       = y + i * row_h
            col      = HR_COLORS[(h["number"]-1) % len(HR_COLORS)]
            votes_n  = self.votes.get(h["number"], 0)
            is_hover = (self.hover_horse == h["number"])
            is_voted = (self.my_vote == h["number"])
            odds_val = self.odds.get(h["number"], 0.0)
            half     = row_h // 2

            # クリック領域（詳細ボタン分を除いた左側）
            self._vote_rects.append((h["number"], 2, ry, HR_HORSE_W-36, ry+row_h-2))

            # ── 馬情報カラム背景 ──
            if is_voted:
                bg_col = "#1A3A2A"; outline = SAFE_COL
            elif is_hover:
                bg_col = BTN_DARK_H; outline = ACCENT_COL
            else:
                bg_col = BTN_DARK; outline = CELL_BORDER
            c.create_rectangle(2, ry, HR_HORSE_W-2, ry+row_h-2,
                fill=bg_col, outline=outline, tags=tag)
            # 馬番カラーバー
            c.create_rectangle(2, ry, 14, ry+row_h-2,
                fill=col, outline="", tags=tag)

            # 馬番・馬名（大きめ）
            c.create_text(22, ry+5,
                text=f"{h['number']}番  {h['name']}",
                fill=TEXT_W, anchor="nw",
                font=("Courier",11,"bold"), tags=tag)

            # ステータス
            # speed/staminaは1〜10スケール → 5段階表示（切り上げ）
            spd_s = min(5, max(0, round(h["speed"] / 2)))
            stm_s = min(5, max(0, round(h["stamina"] / 2)))
            stars_spd = "★"*spd_s + "☆"*(5-spd_s)
            stars_stm = "★"*stm_s + "☆"*(5-stm_s)
            c.create_text(22, ry+24,
                text=f"速{stars_spd}  耐{stars_stm}  調{h['condition']}",
                fill=TEXT_G, anchor="nw",
                font=("Courier",10), tags=tag)

            # 一言評価（枠内折り返し）
            comment  = h.get("comment","")
            max_c    = (HR_HORSE_W - 50) // 7
            line1    = comment[:max_c]
            line2    = comment[max_c:max_c*2]
            txt_y    = ry + min(42, row_h - 34)
            c.create_text(22, txt_y,
                text=line1,
                fill=FLAG_COL, anchor="nw",
                font=("Courier",9), tags=tag)
            if line2 and row_h >= 72:
                c.create_text(22, txt_y+13,
                    text=line2,
                    fill=FLAG_COL, anchor="nw",
                    font=("Courier",9), tags=tag)

            # 「詳」ボタン（馬カラム右下）
            dbx1 = HR_HORSE_W - 32
            dbx2 = HR_HORSE_W - 4
            dby1 = ry + row_h - 24
            dby2 = ry + row_h - 4
            db_tag = f"detail_{h['number']}"
            c.create_rectangle(dbx1, dby1, dbx2, dby2,
                fill=BTN_DARK_H, outline=ACCENT_COL, width=1, tags=(tag, db_tag))
            c.create_text((dbx1+dbx2)//2, (dby1+dby2)//2,
                text="詳", fill=ACCENT_COL,
                font=("Courier",9,"bold"), tags=(tag, db_tag))
            self._detail_rects.append((h["number"], dbx1, dby1, dbx2, dby2))

            # オッズ（馬カラム右上）
            odds_col = MINE_COL if odds_val < 3.0 else (FLAG_COL if odds_val < 6.0 else SAFE_COL)
            c.create_text(HR_HORSE_W-8, ry+5,
                text=f"{odds_val:.1f}倍",
                fill=odds_col, anchor="ne",
                font=("Courier",11,"bold"), tags=tag)

            # 投票済み / クリックヒント
            if is_voted:
                c.create_text(HR_HORSE_W-8, ry+row_h-10,
                    text="✅ 投票済",
                    fill=SAFE_COL, anchor="ne",
                    font=("Courier",10,"bold"), tags=tag)
            else:
                hint = " ←Click" if is_hover else ""
                c.create_text(HR_HORSE_W-8, ry+row_h-10,
                    text=f"{votes_n}票{hint}",
                    fill=SAFE_COL if votes_n>0 else TEXT_G,
                    anchor="ne", font=("Courier",10), tags=tag)

            # ── 騎手カラム ──
            jock    = h["jockey"]
            jname   = jock["name"]   # 苗字のみ（horserace.pyで制御）
            jskl    = "★"*jock["skill"] + "☆"*(5-jock["skill"])
            jstyle  = jock["style"]
            aff_sym = h["affinity"]
            aff_col = (SAFE_COL if aff_sym=="◎" else
                       ACCENT_COL if aff_sym=="○" else
                       FLAG_COL   if aff_sym=="△" else MINE_COL)

            jbg = "#1A1E34" if is_hover else "#13162A"
            c.create_rectangle(HR_HORSE_W+1, ry, HR_INFO_W-1, ry+row_h-2,
                fill=jbg, outline="", tags=tag)

            lh = max(16, row_h // 4)   # 行間（row_hに合わせて可変）

            c.create_text(HR_HORSE_W+8, ry+4,
                text=jname,
                fill=TEXT_W, anchor="nw",
                font=("Courier",11,"bold"), tags=tag)
            c.create_text(HR_HORSE_W+8, ry+4+lh,
                text=jskl,
                fill=TEXT_G, anchor="nw",
                font=("Courier",9), tags=tag)
            c.create_text(HR_HORSE_W+8, ry+4+lh*2,
                text=jstyle,
                fill=TEXT_G, anchor="nw",
                font=("Courier",9), tags=tag)
            c.create_text(HR_HORSE_W+8, ry+4+lh*3,
                text=f"相性 {aff_sym}",
                fill=aff_col, anchor="nw",
                font=("Courier",10,"bold"), tags=tag)

            # レーン区切り
            c.create_line(0, ry+row_h-1, HR_INFO_W, ry+row_h-1,
                fill=CELL_BORDER, width=1, tags=tag)

        # ── 投票状況カラム ──
        rx          = vx + 16
        vote_w      = self.win_w - vx - 20
        total_votes = sum(self.votes.values()) or 1
        bar_max_w   = vote_w - 80

        by = y
        for h in self.horses:
            num   = h["number"]
            cnt   = self.votes.get(num, 0)
            pct   = cnt / total_votes
            col   = HR_COLORS[(num-1) % len(HR_COLORS)]
            bar_w = int(bar_max_w * pct)
            odds_val = self.odds.get(num, 0.0)
            odds_col = MINE_COL if odds_val<3.0 else (FLAG_COL if odds_val<6.0 else SAFE_COL)

            c.create_text(rx, by+4,
                text=f"{num}番 {h['name'][:8]}",
                fill=TEXT_W, anchor="nw", font=("Courier",10,"bold"), tags=tag)
            c.create_text(rx+bar_max_w-4, by+4,
                text=f"{odds_val:.1f}倍",
                fill=odds_col, anchor="ne", font=("Courier",10,"bold"), tags=tag)
            c.create_rectangle(rx, by+20, rx+bar_max_w, by+32,
                fill=CELL_HID, outline="", tags=tag)
            if bar_w > 0:
                c.create_rectangle(rx, by+20, rx+bar_w, by+32,
                    fill=col, outline="", tags=tag)
            c.create_text(rx+bar_max_w+6, by+26,
                text=f"{cnt}票({pct*100:.0f}%)",
                fill=TEXT_G, anchor="w", font=("Courier",9), tags=tag)
            by += row_h

        # タイマー
        ratio   = max(0, self.vote_timer / self.vote_sec)
        bar_col = SAFE_COL if ratio>0.4 else FLAG_COL if ratio>0.15 else MINE_COL
        ty      = self.win_h - 50
        c.create_rectangle(rx, ty, rx+bar_max_w, ty+12,
            fill=CELL_HID, outline="", tags=tag)
        if ratio > 0:
            c.create_rectangle(rx, ty, rx+int(bar_max_w*ratio), ty+12,
                fill=bar_col, outline="", tags=tag)
        c.create_text(vx + vote_w//2, ty-18,
            text=f"投票受付中  残り {max(0,self.vote_timer):.0f}秒  [Spaceで締切]",
            fill=bar_col, font=("Courier",11,"bold"), tags=tag)

    def _draw_gate(self):
        c   = self.canvas
        tag = "hr_main"

        # ── 背景（芝/ダート共にCanvas描画） ──
        surf_col = "#2A4A1A" if self.race["surface"] == "芝" else "#4A3010"
        c.create_rectangle(0, 0, self.win_w, self.win_h,
            fill=surf_col, outline="", tags=tag)

        self._draw_header()

        # ── レイアウト ──
        n         = len(self.horses)
        track_h   = self.win_h - 80 - 60
        lane_h    = track_h // n
        img_h     = int(lane_h * 0.85)
        gate_x    = int(self.win_w * 0.38)   # ゲートバーのx位置
        label_x   = gate_x - 12              # 馬名ラベルの右端
        track_y   = 80

        # フェーズ内時間で演出を制御
        # 0〜1.0秒: ゲート待機（カウントダウン表示）
        # 1.0〜2.0秒: カウントダウン3→2→1
        # 2.0秒〜: ゲートオープン、馬が加速して右へ
        t = self.phase_t
        opened = t >= 2.0

        # カウントダウン表示
        if t < 2.0:
            cd_num = 3 - int(t)
            cd_col = [MINE_COL, FLAG_COL, SAFE_COL][max(0, cd_num - 1)]
            cd_size = 48 + int((t % 1.0) * 12)  # 脈動
            c.create_text(self.win_w // 2, self.win_h // 2,
                text=str(max(1, cd_num)),
                fill=cd_col, font=("Courier", cd_size, "bold"), tags=tag)
        else:
            elapsed = t - 2.0
            c.create_text(self.win_w // 2, track_y + track_h + 30,
                text="ゲートオープン！",
                fill=FLAG_COL, font=("Courier", 22, "bold"), tags=tag)

        for i, h in enumerate(self.horses):
            ry  = track_y + i * lane_h
            col = HR_COLORS[(h["number"] - 1) % len(HR_COLORS)]

            # レーン区切り線
            c.create_line(0, ry + lane_h - 1, self.win_w, ry + lane_h - 1,
                fill="#333333", width=1, tags=tag)

            # 馬番・馬名ラベル（ゲート左側）
            c.create_text(label_x, ry + lane_h // 2,
                text=f"{h['number']} {h['name'][:7]}",
                fill=col, anchor="e",
                font=("Courier", 11, "bold"), tags=tag)

            # ゲートバー（オープン前のみ）
            if not opened:
                c.create_rectangle(gate_x, ry, gate_x + 8, ry + lane_h - 2,
                    fill="#CCCCCC", outline="#888888", width=1, tags=tag)

            # 馬の位置計算
            if not opened:
                # 待機中：ゲート直前で微振動
                sway = int(math.sin(t * 6 + i) * 2)
                hx   = gate_x - img_h // 2 + sway
            else:
                # オープン後：加速して右へ飛び出す
                elapsed = t - 2.0
                # 加速度を持った移動（easeOut）
                accel = min(elapsed * elapsed * 180, self.win_w)
                hx = gate_x + int(accel)

            hy = ry + lane_h // 2

            self.renderers[i].clear(c)
            if self.use_images:
                self.renderers[i].draw(c, hx, hy, col,
                    horse_number=h["number"],
                    coat=h.get("coat", "brown"))
            else:
                self.renderers[i].draw(c, hx, hy, col,
                    frame=self.anim_frame if opened else 0,
                    scale=0.7)

        # phase_t >= 3.0 でレース開始（_update_phaseで制御）

    def _draw_race(self):
        c = self.canvas
        tag = "hr_main"
        self._draw_header()

        # コース背景
        track_y = 80
        track_h = self.win_h - track_y - 60
        surface = self.race["surface"]
        track_col = "#2A4A1A" if surface == "芝" else "#4A3010"
        c.create_rectangle(0, track_y, self.win_w, track_y+track_h,
            fill=track_col, outline="", tags=tag)

        # レーン
        n        = len(self.horses)
        lane_h   = track_h // n
        label_w  = 130  # 番号＋馬名エリア幅
        run_x    = label_w   # 走行エリア開始x
        run_w    = self.win_w - run_x - 40  # 走行エリア幅

        # ラベル背景（走行エリアと分離）
        c.create_rectangle(0, track_y, label_w, track_y+track_h,
            fill="#0D1A0D" if surface=="芝" else "#1A0D00",
            outline="", tags=tag)
        c.create_line(label_w, track_y, label_w, track_y+track_h,
            fill="#2A4A2A" if surface=="芝" else "#4A2A00",
            width=1, tags=tag)

        # ゴールライン
        gx = run_x + run_w
        c.create_line(gx, track_y, gx, track_y+track_h,
            fill="#FFFFFF", width=3, dash=(8,4), tags=tag)
        c.create_text(gx, track_y-10, text="GOAL",
            fill="#FFFFFF", font=("Courier",11,"bold"), tags=tag)

        for i, h in enumerate(self.horses):
            ry  = track_y + i * lane_h
            col = HR_COLORS[(h["number"]-1) % len(HR_COLORS)]
            pos = self.horse_pos[i] if self.horse_pos else 0.0

            # レーン区切り
            c.create_line(0, ry, self.win_w, ry,
                fill="#1A3A0A" if surface=="芝" else "#2A1A00",
                width=1, tags=tag)

            # 番号＋馬名（左ラベルエリア内）
            c.create_text(8, ry+lane_h//2,
                text=f"{h['number']}", fill=col,
                anchor="w", font=("Courier",12,"bold"), tags=tag)
            c.create_text(28, ry+lane_h//2,
                text=h["name"][:7], fill=TEXT_W,
                anchor="w", font=("Courier",10), tags=tag)

            # 馬の位置（走行エリア内のみ）
            hx = run_x + int(run_w * min(pos, 1.0))
            # sin波で上下揺れ（疾走感）
            sway = int(math.sin(self.phase_t * 8 + i) * 3) if pos > 0 else 0
            self.renderers[i].clear(c)
            if self.use_images:
                self.renderers[i].draw(c, hx, ry+lane_h//2+sway, col,
                                       horse_number=h["number"],
                                       coat=h.get("coat","brown"))
            else:
                self.renderers[i].draw(c, hx, ry+lane_h//2+sway, col,
                                       frame=self.anim_frame, scale=0.65)

        # 距離表示
        surf_col2 = "#50E080" if surface == "芝" else "#C8A050"
        dist      = self.race["distance"]
        dist_col2 = "#64C8FF" if dist <= 1400 else ("#FFFFFF" if dist <= 2000 else "#FFB060")
        dist_label = "短距離" if dist<=1400 else ("マイル" if dist<=1800 else
                     ("中距離" if dist<=2200 else ("中長距離" if dist<=2800 else "長距離")))
        c.create_text(self.win_w//2 - 50, self.win_h-30,
            text=surface,
            fill=surf_col2, font=("Courier",11,"bold"), tags=tag)
        c.create_text(self.win_w//2 + 10, self.win_h-30,
            text=f"{dist}m",
            fill=dist_col2, font=("Courier",11,"bold"), tags=tag)
        c.create_text(self.win_w//2 + 80, self.win_h-30,
            text=f"({dist_label})",
            fill=TEXT_G, font=("Courier",10), tags=tag)

    def _draw_goal_scene(self):
        """ゴール演出（5.5秒）
        0〜1.0s : レース画面継続、右端にゴールポスト出現
        1.0〜2.5s: ゴール瞬間フラッシュ、背景にゴール画像
        2.5〜5.5s: 勝ち馬スライドイン、順位表示、花吹雪
        """
        c   = self.canvas
        tag = "hr_main"
        t   = self.phase_t

        if not self.results:
            return
        winner = next((r for r in self.results if r["rank"]==1), None)
        if not winner:
            return
        col = HR_COLORS[(winner["horse"]["number"]-1) % len(HR_COLORS)]
        cx  = self.win_w // 2
        cy  = self.win_h // 2

        # ── フェーズ1(0〜1.5s): ゴール画像フル表示＋GOAL!!テキスト ──
        if t < 1.5:
            sub_t = t
            # ゴール背景画像
            if hasattr(self, "_goal_bg_img") and self._goal_bg_img:
                c.create_image(0, 0, image=self._goal_bg_img,
                    anchor="nw", tags=tag)
            else:
                c.create_rectangle(0, 0, self.win_w, self.win_h,
                    fill="#006600", outline="", tags=tag)
            # フラッシュ
            if sub_t < 0.5:
                stip = "gray75" if sub_t < 0.25 else "gray50"
                c.create_rectangle(0, 0, self.win_w, self.win_h,
                    fill="#FFFFFF", outline="", stipple=stip, tags=tag)
            # 「ゴール！」大テキスト
            scale_t = min(1.0, sub_t / 0.4)
            size    = int(28 + scale_t * 24)
            c.create_text(cx+3, cy+3,
                text="GOAL !!",
                fill="#000000", font=("Courier",size,"bold"), tags=tag)
            c.create_text(cx, cy,
                text="GOAL !!",
                fill=FLAG_COL, font=("Courier",size,"bold"), tags=tag)
            # 勝ち馬名
            if sub_t > 0.5:
                c.create_text(cx, cy+size+12,
                    text=f"{winner['horse']['number']}番  {winner['horse']['name']}",
                    fill=col, font=("Courier",20,"bold"), tags=tag)
            return

        # ── フェーズ2(1.5〜2.5s): 勝ち馬スライドイン ──
        if t < 2.5:
            sub_t = t - 1.5
            # ゴール背景（暗め）
            if hasattr(self, "_goal_bg_img") and self._goal_bg_img:
                c.create_image(0, 0, image=self._goal_bg_img,
                    anchor="nw", tags=tag)
                c.create_rectangle(0, 0, self.win_w, self.win_h,
                    fill=BG, outline="", stipple="gray50", tags=tag)
            else:
                c.create_rectangle(0, 0, self.win_w, self.win_h,
                    fill=BG, outline="", tags=tag)
            # 勝ち馬スライドイン（左から中央へ）
            if self.use_images and hasattr(self, "_goal_big_img") and self._goal_big_img:
                slide = min(1.0, sub_t / 0.6)
                ease  = 1 - (1 - slide) ** 3   # easeOutCubic
                img_x = int(-300 + ease * (cx * 0.5 + 300))
                c.create_image(img_x, cy + 10,
                    image=self._goal_big_img,
                    anchor="center", tags=tag)
            # 馬名テキスト
            if sub_t > 0.4:
                c.create_text(cx + 20, cy - 80,
                    text=f"🏆 {winner['horse']['number']}番  {winner['horse']['name']}",
                    fill=col, font=("Courier",22,"bold"), tags=tag)
            return

        # ── フェーズ3(2.5〜5.5s): 勝ち馬大表示＋順位＋花吹雪 ──
        sub_t = t - 2.5

        # 背景（ゴール画像を薄く）
        if hasattr(self, "_goal_bg_img") and self._goal_bg_img:
            c.create_image(0, 0, image=self._goal_bg_img,
                anchor="nw", tags=tag)
            # 暗幕
            c.create_rectangle(0, 0, self.win_w, self.win_h,
                fill=BG, outline="", stipple="gray75", tags=tag)
        else:
            c.create_rectangle(0, 0, self.win_w, self.win_h,
                fill=BG, outline="", tags=tag)

        # 勝ち馬画像スライドイン（左から）
        if self.use_images and hasattr(self, "_goal_big_img") and self._goal_big_img:
            slide = min(1.0, sub_t / 0.6)
            ease  = 1 - (1-slide)**3  # easeOutCubic
            img_x = int(-200 + ease * (cx * 0.55 + 200))
            c.create_image(img_x, cy + 20,
                image=self._goal_big_img,
                anchor="center", tags=tag)

        # 右側: 順位表
        rx = cx + 40
        c.create_text(rx, cy - 120,
            text="🏆 レース結果",
            fill=FLAG_COL, font=("Courier",16,"bold"),
            anchor="w", tags=tag)
        medals = ["🥇","🥈","🥉"] + [f"{r}位" for r in range(4,9)]
        row_y  = cy - 90
        for res in self.results[:5]:
            rank  = res["rank"]
            h     = res["horse"]
            hcol  = HR_COLORS[(h["number"]-1) % len(HR_COLORS)]
            rcol  = FLAG_COL if rank==1 else (ACCENT_COL if rank==2 else
                    SAFE_COL if rank==3 else TEXT_G)
            # 少し遅延して順に出現
            if sub_t > rank * 0.18:
                c.create_text(rx, row_y,
                    text=f"{medals[rank-1]}  {h['number']}番 {h['name']}",
                    fill=rcol, anchor="w",
                    font=("Courier",13,"bold" if rank<=3 else "normal"), tags=tag)
            row_y += 38

        # 花吹雪
        if hasattr(self, "_goal_particles"):
            for p in self._goal_particles:
                r = p["r"]
                c.create_oval(p["x"]-r, p["y"]-r, p["x"]+r, p["y"]+r,
                    fill=p["color"], outline="", tags=tag)

    def _draw_result(self):
        c = self.canvas
        tag = "hr_main"
        self._draw_header()

        if not self.results:
            return

        cx   = self.win_w // 2
        # 投票者を馬番ごとに整理
        voters_by_horse = {}
        for username, num in self.voters.items():
            voters_by_horse.setdefault(num, []).append(username)
        winner_num = self.results[0]["horse"]["number"]

        c.create_text(cx, 90, text="🏆 レース結果",
            fill=ACCENT_COL, font=("Courier",18,"bold"), tags=tag)

        # ── 左カラム: 順位表 ──
        lx   = 20
        row_h = min(48, (self.win_h - 200) // len(self.results))
        sy   = 120
        medals = ["🥇","🥈","🥉"] + [f"{r}位" for r in range(4,9)]

        for res in self.results:
            rank = res["rank"]
            h    = res["horse"]
            col  = HR_COLORS[(h["number"]-1) % len(HR_COLORS)]
            ry   = sy + (rank-1)*row_h
            rank_col = FLAG_COL if rank==1 else (ACCENT_COL if rank==2
                       else (SAFE_COL if rank==3 else TEXT_G))

            # 行背景（1〜3位は強調）
            if rank <= 3:
                c.create_rectangle(lx, ry, lx+560, ry+row_h-2,
                    fill=BTN_DARK, outline=rank_col, width=1, tags=tag)

            c.create_text(lx+4, ry+row_h//2,
                text=medals[rank-1], fill=rank_col, anchor="w",
                font=("Courier",13,"bold"), tags=tag)
            c.create_rectangle(lx+44, ry+4, lx+54, ry+row_h-4,
                fill=col, outline="", tags=tag)
            c.create_text(lx+60, ry+row_h//2,
                text=f"{h['number']}番 {h['name']}",
                fill=TEXT_W, anchor="w",
                font=("Courier",12,"bold" if rank<=3 else "normal"), tags=tag)
            c.create_text(lx+240, ry+row_h//2,
                text=f"調{h['condition']}",
                fill=TEXT_G, anchor="w", font=("Courier",10), tags=tag)

            # 投票者一覧（この馬に投票した人）
            vlist = voters_by_horse.get(h["number"], [])
            if vlist:
                # 画面幅に収まる文字数を計算（1文字≒7px想定）
                max_chars = (self.win_w - lx - 290) // 7
                joined = "  ".join(vlist)
                if len(joined) > max_chars:
                    # 収まる人数を探す
                    shown = []
                    used  = 0
                    for v in vlist:
                        if used + len(v) + 2 + 4 > max_chars:
                            break
                        shown.append(v)
                        used += len(v) + 2
                    display = "  ".join(shown) + f"  他{len(vlist)-len(shown)}人"
                else:
                    display = joined
                txt_col = SAFE_COL if h["number"] == winner_num else TEXT_G
                c.create_text(lx+290, ry+row_h//2,
                    text=display,
                    fill=txt_col, anchor="w",
                    font=("Courier",9), tags=tag)

        # ── 的中サマリー + 累積ランキング ──
        total   = len(self.voters)
        winners = voters_by_horse.get(winner_num, [])
        wy      = sy + len(self.results)*row_h + 14
        c.create_text(cx, wy,
            text=f"このレース: 投票者 {total}人  /  的中 {len(winners)}人",
            fill=TEXT_G, font=("Courier",11), tags=tag)

        # ── ボタン＋自動遷移カウントダウン（位置を先に確定）──
        by  = self.win_h - 56
        bx1 = cx - 160
        bx2 = cx + 20

        # 累積ランキング（ボタンエリアの上に収める）
        if self.current_race >= 2 and self.cumulative:
            rank_bottom = by - 52   # カウントダウン・進捗の分を確保
            ry2 = wy + 26
            if ry2 + 20 < rank_bottom:
                c.create_text(cx, ry2,
                    text=f"── 累積的中ランキング (全{self.current_race}レース) ──",
                    fill=ACCENT_COL, font=("Courier",11,"bold"), tags=tag)
                ry2 += 20
                ranked   = sorted(self.cumulative.items(),
                                  key=lambda x: (-x[1].get("points",1.0), -x[1]["hits"]))
                medals_r = ["🥇","🥈","🥉"] + ["  " for _ in range(20)]
                for ri, (uname, stat) in enumerate(ranked):
                    if ry2 + 18 > rank_bottom:
                        remaining = len(ranked) - ri
                        if remaining > 0:
                            c.create_text(cx, ry2,
                                text=f"他{remaining}人...",
                                fill=TEXT_G, font=("Courier",9), tags=tag)
                        break
                    medal  = medals_r[ri]
                    hits   = stat["hits"]
                    votes  = stat["votes"]
                    pts    = stat.get("points", 1.0)
                    col_u  = FLAG_COL if ri==0 else (ACCENT_COL if ri==1 else
                             (SAFE_COL if ri==2 else TEXT_W))
                    c.create_text(cx - 160, ry2,
                        text=f"{medal} {uname[:14]}",
                        fill=col_u, anchor="w", font=("Courier",10,"bold"), tags=tag)
                    c.create_text(cx + 80, ry2,
                        text=f"{pts:.1f}pt  {hits}/{votes}的中",
                        fill=col_u, anchor="w", font=("Courier",10), tags=tag)
                    ry2 += 18
        c.create_rectangle(bx1, by, bx1+130, by+38,
            fill=BTN_MENU, outline=CELL_BORDER, tags=tag)
        c.create_text(bx1+65, by+19, text="◀ メニュー",
            fill=TEXT_W, font=("Courier",11,"bold"), tags=tag)
        # レース数の残り表示とボタンラベル切り替え
        is_last = (self.race_count > 0 and self.current_race >= self.race_count)
        next_label = "🏆 最終結果へ" if is_last else "🔄 次のレース"
        next_col   = FLAG_COL if is_last else SAFE_COL
        c.create_rectangle(bx2, by, bx2+150, by+38,
            fill=next_col, outline="", tags=tag)
        c.create_text(bx2+75, by+19, text=next_label,
            fill=BG, font=("Courier",11,"bold"), tags=tag)
        # レース進捗
        if self.race_count > 0:
            progress = f"レース {self.current_race} / {self.race_count}"
        else:
            progress = f"レース {self.current_race} / ∞"
        c.create_text(cx, by-42,
            text=progress,
            fill=ACCENT_COL, font=("Courier",12,"bold"), tags=tag)

        # 自動遷移カウントダウン
        if self.auto_next_sec > 0:
            remain = max(0, self.auto_next_sec - self.result_timer)
            c.create_text(cx, by-20,
                text=f"{remain:.0f}秒後に自動で次のレースへ",
                fill=FLAG_COL, font=("Courier",11), tags=tag)

        # ボタン座標を保存してon_canvas_clickから使う
        self._result_btn = (bx1, by, bx2)

    def _draw_final(self):
        """全レース終了後の最終ランキング画面"""
        c   = self.canvas
        tag = "hr_main"
        c.create_rectangle(0,0,self.win_w,self.win_h, fill=BG, outline="", tags=tag)

        cx = self.win_w // 2
        c.create_text(cx, 50,
            text=f"🏆 全{self.race_count}レース 最終ランキング",
            fill=FLAG_COL, font=("Courier",20,"bold"), tags=tag)

        if not self.cumulative:
            c.create_text(cx, self.win_h//2,
                text="投票者がいませんでした",
                fill=TEXT_G, font=("Courier",14), tags=tag)
        else:
            ranked = sorted(self.cumulative.items(),
                            key=lambda x: (-x[1].get("points",1.0), -x[1]["hits"]))
            medals_f = ["🥇","🥈","🥉"] + [f"{i}位" for i in range(4, 50)]
            row_h_f  = min(54, (self.win_h - 180) // max(len(ranked), 1))
            sy       = 110

            # ヘッダー
            c.create_text(cx-220, sy-20, text="プレイヤー",
                fill=TEXT_G, anchor="w", font=("Courier",10), tags=tag)
            c.create_text(cx+60, sy-20, text="ポイント",
                fill=TEXT_G, anchor="w", font=("Courier",10), tags=tag)
            c.create_text(cx+160, sy-20, text="的中/投票",
                fill=TEXT_G, anchor="w", font=("Courier",10), tags=tag)

            for ri, (uname, stat) in enumerate(ranked):
                ry    = sy + ri * row_h_f
                if ry + row_h_f > self.win_h - 80:
                    remaining = len(ranked) - ri
                    c.create_text(cx, ry,
                        text=f"他{remaining}人...",
                        fill=TEXT_G, font=("Courier",11), tags=tag)
                    break
                medal = medals_f[ri]
                hits  = stat["hits"]
                votes = stat["votes"]
                pts   = stat.get("points", 1.0)
                pct   = int(hits/votes*100) if votes else 0
                col_u = FLAG_COL if ri==0 else (ACCENT_COL if ri==1 else
                        (SAFE_COL if ri==2 else TEXT_W))

                if ri < 3:
                    c.create_rectangle(cx-280, ry, cx+300, ry+row_h_f-2,
                        fill=BTN_DARK, outline=col_u, tags=tag)

                c.create_text(cx-270, ry+row_h_f//2,
                    text=medal, fill=col_u, anchor="w",
                    font=("Courier",14,"bold"), tags=tag)
                c.create_text(cx-220, ry+row_h_f//2,
                    text=uname[:16], fill=col_u, anchor="w",
                    font=("Courier",13,"bold" if ri<3 else "normal"), tags=tag)
                c.create_text(cx+60, ry+row_h_f//2,
                    text=f"{pts:.1f}pt",
                    fill=col_u, anchor="w", font=("Courier",13,"bold"), tags=tag)
                c.create_text(cx+160, ry+row_h_f//2,
                    text=f"{hits}/{votes} ({pct}%)",
                    fill=TEXT_G, anchor="w", font=("Courier",11), tags=tag)

        # メニューボタン
        by = self.win_h - 56
        bx = cx - 65
        c.create_rectangle(bx, by, bx+130, by+38,
            fill=SAFE_COL, outline="", tags=tag)
        c.create_text(bx+65, by+19, text="◀ メニューへ",
            fill=BG, font=("Courier",12,"bold"), tags=tag)

        self._final_btn = (bx, by)

    def _next_race_or_end(self):
        """次のレースへ、またはレース数に達したら最終結果へ"""
        if self._transitioning:   # 2重呼び出し防止
            return
        self._transitioning = True
        if self.race_count > 0 and self.current_race >= self.race_count:
            self.phase        = "final"
            self.phase_t      = 0.0
            self._final_btn   = None
        else:
            self._next_race()

    def _next_race(self):
        self._transitioning = False
        self._result_btn  = None
        self.current_race += 1
        # 育成馬の連続出走
        t_list = self.trained_list if self.keep_trained else []
        n_tr   = len(t_list)
        n_rnd  = max(0, 8 - n_tr)
        if n_tr > 0:
            _gkey = self.cfg.get("hr_grade", "G3")
            self.race       = generate_race(num_horses=n_rnd, grade_key=_gkey)
            rand_horses     = self.race["horses"]
            for i, h in enumerate(t_list):
                h["number"] = i + 1
            for i, h in enumerate(rand_horses):
                h["number"] = n_tr + i + 1
            self.race["horses"] = t_list + rand_horses
            from horserace import calc_odds
            self.odds = calc_odds(
                self.race["horses"], self.race["surface"], self.race["distance"])
        else:
            _gkey = self.cfg.get("hr_grade", "G3")
            self.race       = generate_race(num_horses=8, grade_key=_gkey)
            self.odds       = self.race["odds"]
        self.horses       = self.race["horses"]
        self.results      = None
        self.votes        = {}
        self.voters       = {}
        self.vote_timer   = float(self.vote_sec)
        self.horse_pos    = []
        self.phase        = "vote"
        self.phase_t      = 0.0
        self.finish_flash = 0.0
        self.result_timer = 0.0
        self.my_vote      = None
        self.hover_horse  = None
        self._vote_rects  = []
        self._goal_particles  = []
        self._goal_triggered  = False
        self._modal_horse     = None
        self._modal_close     = None
        self._detail_rects    = []
        # ゴール演出キャッシュをクリア（次レースの勝ち馬に備える）
        if hasattr(self, "_goal_big_img"):
            del self._goal_big_img
        if hasattr(self, "_goal_bg_img"):
            del self._goal_bg_img
        # レンダラーも新しい馬に合わせて再生成
        if self.use_images:
            self.renderers = [
                ImageHorseRenderer(self.horse_sprites, f"horse_{i}")
                for i in range(len(self.horses))
            ]
        else:
            self.renderers = [IconHorseRenderer(f"horse_{i}") for i in range(len(self.horses))]

class PaintScreen:
    def __init__(self, root, cfg, on_menu):
        self.root    = root
        self.cfg     = cfg
        self.on_menu = on_menu

        root.title("ChatViewPlayGame - ペイント")
        root.configure(bg=BG)

        res_name = cfg.get("resolution", DEFAULT_RES)
        self.win_w, self.win_h = RESOLUTIONS.get(res_name, RESOLUTIONS[DEFAULT_RES])

        # 描画エリアサイズ
        self.draw_w = self.win_w - PT_PANEL_W
        self.draw_h = self.win_h

        # ツール状態
        self.tool    = "pen"     # pen / line / rect / oval / eraser
        self.color   = "#000000"
        self.width   = 3
        self.prev_x  = None
        self.prev_y  = None
        self.start_x = None
        self.start_y = None
        self.temp_id = None      # ゴムバンドプレビュー用

        # 描画オブジェクトIDスタック（undo用）
        self.draw_ids = []

        # 弾幕
        self.danmaku   = []
        self._running  = True
        self.prev_time = time.time()

        # Canvas（全体）
        self.canvas = tk.Canvas(root, width=self.win_w, height=self.win_h,
                                bg="#1A1A2A", highlightthickness=0, cursor="crosshair")
        self.canvas.pack()

        # 描画エリア背景（白いキャンバス）
        self.canvas.create_rectangle(0, 0, self.draw_w, self.draw_h,
                                     fill="#FFFFFF", outline="", tags="canvas_bg")

        # Twitch
        self.online_mode = cfg.get("online_mode", True)
        self.twitch = TwitchClient(
            cfg.get("channel",""), cfg.get("token",""),
            on_command=lambda *a: None,
            on_chat=self._on_chat,
        )
        if self.online_mode:
            threading.Thread(
                target=lambda: asyncio.run(self.twitch.connect()), daemon=True
            ).start()

        # イベントバインド
        self.canvas.bind("<ButtonPress-1>",   self._on_press)
        self.canvas.bind("<B1-Motion>",       self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

        self._build_panel()
        self._loop()

    # ── ツールパネル ──────────────────────────
    def _build_panel(self):
        px = self.draw_w
        c  = self.canvas
        pw = PT_PANEL_W

        # パネル背景
        c.create_rectangle(px, 0, self.win_w, self.win_h,
                           fill=SIDEBAR_BG, outline="", tags="pt_panel")
        c.create_line(px, 0, px, self.win_h,
                      fill=CELL_BORDER, width=1, tags="pt_panel")

        # タイトル
        c.create_text(px+pw//2, 18, text="🎨 ペイント",
                      fill=ACCENT_COL, font=("Courier",11,"bold"), tags="pt_panel")

        # ── ツール選択ボタン ──
        tools = [
            ("pen",    "✏ ペン"),
            ("line",   "／ 直線"),
            ("rect",   "□ 四角"),
            ("oval",   "○ 円"),
            ("eraser", "✦ 消しゴム"),
        ]
        self._tool_btns = {}
        ty = 44
        for tid, tlabel in tools:
            bid = c.create_rectangle(px+8, ty, px+pw-8, ty+26,
                fill=ACCENT_COL if tid==self.tool else BTN_DARK,
                outline=CELL_BORDER, tags="pt_panel")
            txt = c.create_text(px+pw//2, ty+13, text=tlabel,
                fill=BG if tid==self.tool else TEXT_W,
                font=("Courier",10,"bold"), tags="pt_panel")
            self._tool_btns[tid] = (bid, txt, ty)
            # クリックバインド
            for item in (bid, txt):
                c.tag_bind(item, "<Button-1>",
                           lambda e, t=tid: self._set_tool(t))
            ty += 32

        # ── 線の太さ ──
        c.create_text(px+pw//2, ty+8, text="── 太さ ──",
                      fill=TEXT_G, font=("Courier",9), tags="pt_panel")
        ty += 22
        widths = [1, 3, 5, 8]
        self._width_btns = {}
        wx = px + 8
        for w in widths:
            ww = (pw - 16) // 4
            bid = c.create_rectangle(wx, ty, wx+ww-2, ty+24,
                fill=ACCENT_COL if w==self.width else BTN_DARK,
                outline=CELL_BORDER, tags="pt_panel")
            txt = c.create_text(wx+ww//2-1, ty+12, text=str(w),
                fill=BG if w==self.width else TEXT_W,
                font=("Courier",10,"bold"), tags="pt_panel")
            self._width_btns[w] = (bid, txt)
            for item in (bid, txt):
                c.tag_bind(item, "<Button-1>",
                           lambda e, wv=w: self._set_width(wv))
            wx += ww
        ty += 30

        # ── カラーパレット ──
        c.create_text(px+pw//2, ty+8, text="── 色 ──",
                      fill=TEXT_G, font=("Courier",9), tags="pt_panel")
        ty += 22
        self._color_btns = {}
        cols_per_row = 4
        cell_w = (pw - 16) // cols_per_row
        for idx, col in enumerate(PT_COLORS):
            cx2 = px + 8 + (idx % cols_per_row) * cell_w
            cy2 = ty + (idx // cols_per_row) * (cell_w - 2)
            bid = c.create_rectangle(cx2, cy2, cx2+cell_w-3, cy2+cell_w-3,
                fill=col, outline=SAFE_COL if col==self.color else "#444466",
                width=2 if col==self.color else 1, tags="pt_panel")
            self._color_btns[col] = bid
            c.tag_bind(bid, "<Button-1>",
                       lambda e, cl=col: self._set_color(cl))
        ty += (len(PT_COLORS) // cols_per_row) * (cell_w - 2) + 8

        # カスタムカラーボタン
        bid = c.create_rectangle(px+8, ty, px+pw-8, ty+24,
            fill=BTN_DARK, outline=CELL_BORDER, tags="pt_panel")
        txt = c.create_text(px+pw//2, ty+12, text="🎨 カスタム",
            fill=TEXT_W, font=("Courier",9,"bold"), tags="pt_panel")
        for item in (bid, txt):
            c.tag_bind(item, "<Button-1>", self._pick_custom_color)
        ty += 32

        # ── 現在色プレビュー ──
        self._cur_color_box = c.create_rectangle(px+8, ty, px+pw-8, ty+28,
            fill=self.color, outline=CELL_BORDER, width=2, tags="pt_panel")
        ty += 36

        # ── 操作ボタン ──
        # 保存
        y_save = self.win_h - 132
        bid = c.create_rectangle(px+8, y_save, px+pw-8, y_save+26,
            fill=ACCENT_COL, outline="", tags="pt_panel")
        txt = c.create_text(px+pw//2, y_save+13, text="💾 保存",
            fill=BG, font=("Courier",10,"bold"), tags="pt_panel")
        for item in (bid, txt):
            c.tag_bind(item, "<Button-1>", self._save_image)
        self._save_flash_id  = None   # 保存完了メッセージ用
        self._save_flash_txt = c.create_text(px+pw//2, y_save-10,
            text="", fill=SAFE_COL,
            font=("Courier",8,"bold"), tags="pt_panel")

        # 全消し
        y_clear = self.win_h - 100
        bid = c.create_rectangle(px+8, y_clear, px+pw-8, y_clear+28,
            fill=MINE_COL, outline="", tags="pt_panel")
        txt = c.create_text(px+pw//2, y_clear+14, text="🗑 全消し",
            fill="#FFFFFF", font=("Courier",10,"bold"), tags="pt_panel")
        for item in (bid, txt):
            c.tag_bind(item, "<Button-1>", self._clear_canvas)

        # undo
        y_undo = self.win_h - 64
        bid = c.create_rectangle(px+8, y_undo, px+pw-8, y_undo+24,
            fill=BTN_DARK, outline=CELL_BORDER, tags="pt_panel")
        txt = c.create_text(px+pw//2, y_undo+12, text="↩ 元に戻す",
            fill=TEXT_W, font=("Courier",9,"bold"), tags="pt_panel")
        for item in (bid, txt):
            c.tag_bind(item, "<Button-1>", self._undo)

        # メニュー
        y_menu = self.win_h - 34
        bid = c.create_rectangle(px+8, y_menu, px+pw-8, y_menu+26,
            fill=BTN_MENU, outline=CELL_BORDER, tags="pt_panel")
        txt = c.create_text(px+pw//2, y_menu+13, text="◀ メニュー",
            fill=TEXT_W, font=("Courier",10,"bold"), tags="pt_panel")
        for item in (bid, txt):
            c.tag_bind(item, "<Button-1>", lambda e: self._go_menu())

    # ── ツール・色・太さ変更 ─────────────────
    def _set_tool(self, tool):
        self.tool = tool
        self._refresh_panel()

    def _set_width(self, w):
        self.width = w
        self._refresh_panel()

    def _set_color(self, col):
        self.color = col
        self._refresh_panel()

    def _pick_custom_color(self, e=None):
        import tkinter.colorchooser as cc
        result = cc.askcolor(color=self.color, title="色を選択")
        if result and result[1]:
            self.color = result[1]
            self._refresh_panel()

    def _refresh_panel(self):
        c = self.canvas
        # ツールボタン更新
        for tid, (bid, txt, _) in self._tool_btns.items():
            active = (tid == self.tool)
            c.itemconfig(bid, fill=ACCENT_COL if active else BTN_DARK)
            c.itemconfig(txt, fill=BG if active else TEXT_W)
        # 太さボタン更新
        for w, (bid, txt) in self._width_btns.items():
            active = (w == self.width)
            c.itemconfig(bid, fill=ACCENT_COL if active else BTN_DARK)
            c.itemconfig(txt, fill=BG if active else TEXT_W)
        # カラーパレット更新
        for col, bid in self._color_btns.items():
            active = (col == self.color)
            c.itemconfig(bid,
                outline=SAFE_COL if active else "#444466",
                width=2 if active else 1)
        # 現在色プレビュー更新
        c.itemconfig(self._cur_color_box, fill=self.color)

    # ── 描画イベント ──────────────────────────
    def _in_draw_area(self, x, y):
        return 0 <= x < self.draw_w and 0 <= y < self.draw_h

    def _on_press(self, ev):
        if not self._in_draw_area(ev.x, ev.y):
            return
        self.start_x = ev.x
        self.start_y = ev.y
        self.prev_x  = ev.x
        self.prev_y  = ev.y

    def _on_drag(self, ev):
        if self.start_x is None:
            return
        x = min(max(ev.x, 0), self.draw_w - 1)
        y = min(max(ev.y, 0), self.draw_h - 1)
        c = self.canvas

        if self.tool == "pen":
            if self.prev_x is not None:
                iid = c.create_line(
                    self.prev_x, self.prev_y, x, y,
                    fill=self.color, width=self.width,
                    capstyle="round", smooth=True)
                self.draw_ids.append(iid)
            self.prev_x, self.prev_y = x, y

        elif self.tool == "eraser":
            r = self.width * 4
            iid = c.create_oval(x-r, y-r, x+r, y+r,
                fill="#FFFFFF", outline="#FFFFFF")
            self.draw_ids.append(iid)
            self.prev_x, self.prev_y = x, y

        else:
            # ゴムバンドプレビュー
            if self.temp_id:
                c.delete(self.temp_id)
            if self.tool == "line":
                self.temp_id = c.create_line(
                    self.start_x, self.start_y, x, y,
                    fill=self.color, width=self.width,
                    capstyle="round", dash=(4,4))
            elif self.tool == "rect":
                self.temp_id = c.create_rectangle(
                    self.start_x, self.start_y, x, y,
                    outline=self.color, width=self.width, fill="")
            elif self.tool == "oval":
                self.temp_id = c.create_oval(
                    self.start_x, self.start_y, x, y,
                    outline=self.color, width=self.width, fill="")

    def _on_release(self, ev):
        if self.start_x is None:
            return
        x = min(max(ev.x, 0), self.draw_w - 1)
        y = min(max(ev.y, 0), self.draw_h - 1)
        c = self.canvas

        # tempを削除して正式描画
        if self.temp_id:
            c.delete(self.temp_id)
            self.temp_id = None

        if self.tool == "line":
            iid = c.create_line(
                self.start_x, self.start_y, x, y,
                fill=self.color, width=self.width, capstyle="round")
            self.draw_ids.append(iid)
        elif self.tool == "rect":
            iid = c.create_rectangle(
                self.start_x, self.start_y, x, y,
                outline=self.color, width=self.width, fill="")
            self.draw_ids.append(iid)
        elif self.tool == "oval":
            iid = c.create_oval(
                self.start_x, self.start_y, x, y,
                outline=self.color, width=self.width, fill="")
            self.draw_ids.append(iid)

        self.start_x = self.start_y = None
        self.prev_x  = self.prev_y  = None

    # ── 保存 ─────────────────────────────────
    def _save_image(self, e=None):
        import datetime, os
        try:
            from PIL import ImageGrab
        except ImportError:
            self.canvas.itemconfig(self._save_flash_txt, text="Pillowが必要です")
            return

        # 保存先: exe/スクリプトと同じディレクトリ
        if getattr(sys, "frozen", False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))

        ts       = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = os.path.join(base_dir, f"paint_{ts}.png")

        try:
            # ウィンドウ上のCanvas描画エリアの絶対座標を取得してスクリーンショット
            self.root.update_idletasks()
            x = self.root.winfo_rootx()
            y = self.root.winfo_rooty()
            img = ImageGrab.grab(bbox=(
                x, y,
                x + self.draw_w,
                y + self.draw_h
            ))
            img.save(out_path, "PNG")

            # 完了メッセージ（2秒表示）
            self.canvas.itemconfig(self._save_flash_txt, text="saved!")
            self.root.after(2000, lambda:
                self.canvas.itemconfig(self._save_flash_txt, text=""))
        except Exception as err:
            self.canvas.itemconfig(self._save_flash_txt, text="保存失敗")
            print(f"[PaintSave] {err}")

    # ── キャンバス操作 ────────────────────────
    def _clear_canvas(self, e=None):
        for iid in self.draw_ids:
            self.canvas.delete(iid)
        self.draw_ids.clear()

    def _undo(self, e=None):
        if self.draw_ids:
            self.canvas.delete(self.draw_ids.pop())

    # ── Twitch ───────────────────────────────
    def _on_chat(self, username, text):
        self.danmaku.append(DanmakuMsg(self.canvas, username, text, self.draw_w))

    # ── ループ ───────────────────────────────
    def _loop(self):
        if not self._running:
            return
        now = time.time()
        dt  = now - self.prev_time
        self.prev_time = now

        for d in self.danmaku:
            d.update(dt)
        self.danmaku = [d for d in self.danmaku if d.alive]

        for d in self.danmaku:
            self.canvas.tag_raise(d.shadow_id)
            self.canvas.tag_raise(d.text_id)

        # パネルを常に最前面に
        self.canvas.tag_raise("pt_panel")

        self.root.after(FPS_INTERVAL, self._loop)

    # ── 終了 ─────────────────────────────────
    def _go_menu(self):
        self._running = False
        self.twitch.stop()
        for d in self.danmaku:
            try:
                self.canvas.delete(d.text_id)
                self.canvas.delete(d.shadow_id)
            except Exception:
                pass
        self.on_menu()
class TrainingScreen:
    def __init__(self, root, cfg, on_back, on_race):
        self.root    = root
        self.cfg     = cfg
        self.on_back = on_back
        self.on_race = on_race
        self._tr     = __import__("training")
        self.name    = ""
        self.seed    = self._tr.generate_birth_seed()
        self.stats   = None
        self.fatigue = 0
        self.month   = 0
        self.history = []
        self.choices = []
        self.trial_available = False   # 試走可能フラグ（6ヶ月完了後）
        self.trial_done      = False   # 今周期の試走消化フラグ
        # 演出用スプライト（起動時に1回読み込み）
        self._sprites    = None
        self._anim_job   = None   # after() ジョブID
        self._anim_frame = 0
        self._load_sprites()
        root.title("ChatViewPlayGame - 馬育成")
        root.configure(bg=BG)
        self._build_name_screen()

    # ── 馬名入力 ──────────────────────────────
    def _build_name_screen(self):
        for w in self.root.winfo_children(): w.destroy()
        make_label(self.root, "🐴 馬を育てる",
                   fg=ACCENT_COL, font=("Courier",20,"bold")).pack(pady=(28,4))
        make_label(self.root, "育てる馬の名前を入力してください（カタカナ・最大8文字）",
                   fg=TEXT_G, font=("Courier",11)).pack(pady=(0,20))
        frame = tk.Frame(self.root, bg=BG)
        frame.pack(padx=40)
        make_label(frame, "馬名:", font=("Courier",12,"bold"), anchor="w").pack(fill="x")
        self._name_var = tk.StringVar()
        tk.Entry(frame, textvariable=self._name_var, width=20,
                 bg=CELL_HID, fg=TEXT_W, insertbackground=TEXT_W,
                 relief="flat", font=("Courier",16), bd=8).pack(fill="x", pady=(4,0))
        self._err_var = tk.StringVar()
        tk.Label(frame, textvariable=self._err_var,
                 bg=BG, fg=MINE_COL, font=("Courier",11)).pack(pady=(8,0))
        make_label(frame, f"誕生シード: {self.seed:08X}",
                   fg=TEXT_G, font=("Courier",9)).pack(anchor="w", pady=(8,0))
        bf = tk.Frame(frame, bg=BG)
        bf.pack(fill="x", pady=(24,0))
        make_btn(bf, "◀  戻る", self.on_back).pack(side="left")
        make_btn(bf, "育成開始 ▶", self._start_training,
                 bg=SAFE_COL, fg=BG).pack(side="right")

    def _validate_name(self, name):
        import unicodedata
        if not name: return "馬名を入力してください"
        if len(name) > 8: return "馬名は8文字以内にしてください"
        for ch in name:
            if "KATAKANA" not in unicodedata.name(ch, "") and "MIDDLE DOT" not in unicodedata.name(ch, ""):
                return f"カタカナで入力してください（'{ch}'は使用不可）"
        return None

    def _start_training(self):
        name = self._name_var.get().strip()
        err  = self._validate_name(name)
        if err:
            self._err_var.set(f"⚠ {err}")
            return
        self.name         = name
        self.stats        = self._tr.generate_initial_stats(self.seed)
        self.fatigue      = 0
        self.month        = 0
        self.history      = []
        self.trial_available = False
        self.trial_done      = False
        self._next_month()

    # ── 月次育成 ──────────────────────────────
    def _next_month(self):
        if self.month >= self._tr.TRAINING_MONTHS:
            self._show_complete()
            return
        # 6ヶ月完了タイミングで試走を解放（1回限り）
        if self.month == 6 and not self.trial_done:
            self.trial_available = True
        self.choices = self._tr.get_monthly_choices(
            self.month + 1, self.fatigue, self.seed, self.history)
        self._build_training_screen()

    def _draw_pentagon(self, canvas, stats, cx, cy, r):
        """五角形レーダーチャート"""
        import math
        keys   = ["speed","stamina","corner","mental","adaptability"]
        labels = ["速度","スタミナ","コーナー","精神力","適応力"]
        n      = len(keys)
        # 背景グリッド
        for level in [0.25, 0.5, 0.75, 1.0]:
            pts = []
            for i in range(n):
                angle = math.pi/2 + 2*math.pi*i/n
                px = cx + r * level * math.cos(angle)
                py = cy - r * level * math.sin(angle)
                pts.extend([px, py])
            canvas.create_polygon(pts, fill="", outline="#333355", width=1)
        # 軸線
        for i in range(n):
            angle = math.pi/2 + 2*math.pi*i/n
            canvas.create_line(cx, cy,
                cx + r * math.cos(angle),
                cy - r * math.sin(angle),
                fill="#333355", width=1)
        # ステータス多角形
        pts = []
        for i, key in enumerate(keys):
            val   = stats.get(key, 0) / self._tr.STAT_MAX
            angle = math.pi/2 + 2*math.pi*i/n
            px    = cx + r * val * math.cos(angle)
            py    = cy - r * val * math.sin(angle)
            pts.extend([px, py])
        canvas.create_polygon(pts, fill="#2244AA", outline=ACCENT_COL,
                              width=2)
        # 頂点ドット
        for i, key in enumerate(keys):
            val   = stats.get(key, 0) / self._tr.STAT_MAX
            angle = math.pi/2 + 2*math.pi*i/n
            px    = cx + r * val * math.cos(angle)
            py    = cy - r * val * math.sin(angle)
            canvas.create_oval(px-4, py-4, px+4, py+4,
                               fill=ACCENT_COL, outline="")
        # ラベル
        for i, (key, lbl) in enumerate(zip(keys, labels)):
            angle = math.pi/2 + 2*math.pi*i/n
            lx    = cx + (r+22) * math.cos(angle)
            ly    = cy - (r+22) * math.sin(angle)
            stars = self._tr.to_stars(stats.get(key, 0))
            canvas.create_text(lx, ly-6, text=lbl,
                fill=TEXT_G, font=("Courier",9), anchor="center")
            canvas.create_text(lx, ly+6, text=stars,
                fill=FLAG_COL, font=("Courier",9), anchor="center")

    def _build_training_screen(self):
        for w in self.root.winfo_children(): w.destroy()
        tr    = self._tr
        month = self.month + 1

        make_label(self.root, f"🐴 {self.name}  第{month}月  / 全12月",
                   fg=ACCENT_COL, font=("Courier",16,"bold")).pack(pady=(16,4))

        # ── 素質ヒント（月ごとに調教師がそっとつぶやく） ──
        hint = tr.get_aptitude_hint(self.seed, month)
        hint_frame = tk.Frame(self.root, bg=BTN_DARK)
        hint_frame.pack(fill="x", padx=28, pady=(0,6))
        make_label(hint_frame, f"調教師の目: 「{hint}」",
                   fg=TEXT_G, font=("Courier",10)).pack(anchor="w", padx=12, pady=4)

        # 上部: グラフ + 右側情報
        top = tk.Frame(self.root, bg=BG)
        top.pack(fill="x", padx=28)

        # 五角形グラフ
        graph_size = 220
        cv = tk.Canvas(top, width=graph_size, height=graph_size,
                       bg=SIDEBAR_BG, highlightthickness=0)
        cv.pack(side="left", padx=(0,16), pady=4)
        self._draw_pentagon(cv, self.stats, graph_size//2, graph_size//2, 75)

        # 右側: 疲労・全盛期・進捗
        info = tk.Frame(top, bg=BG)
        info.pack(side="left", fill="both", expand=True)

        fat_col = MINE_COL if self.fatigue >= 60 else (FLAG_COL if self.fatigue >= 40 else SAFE_COL)
        make_label(info, f"疲労: {self.fatigue}/100",
                   fg=fat_col, font=("Courier",12,"bold")).pack(anchor="w")
        peak = self.stats["peak_month"]
        peak_col = SAFE_COL if month == peak else TEXT_G
        peak_txt = "【全盛期！】" if month == peak else f"全盛期: 第{peak}月"
        make_label(info, peak_txt, fg=peak_col,
                   font=("Courier",11,"bold" if month==peak else "normal")).pack(anchor="w", pady=(4,0))

        # 進捗ドット
        prog = tk.Frame(info, bg=BG)
        prog.pack(anchor="w", pady=(12,0))
        for m in range(tr.TRAINING_MONTHS):
            col = SAFE_COL if m < self.month else (ACCENT_COL if m == self.month else CELL_HID)
            tk.Label(prog, text="●", bg=BG, fg=col,
                     font=("Courier",11)).pack(side="left")

        # メニュー
        make_label(self.root, "今月のメニューを選んでください",
                   fg=TEXT_W, font=("Courier",12,"bold")).pack(pady=(8,4))

        for menu in self.choices:
            ef   = menu["effects"]
            parts = []
            for k, v in ef.items():
                lbl = tr.STAT_LABELS.get(k, k)
                parts.append(f"{lbl}{'+'if v>0 else ''}{v}")
            eff_str = "  ".join(parts)

            mf = tk.Frame(self.root, bg=BTN_DARK,
                          highlightbackground=CELL_BORDER, highlightthickness=1)
            mf.pack(fill="x", padx=28, pady=3)
            mf.configure(cursor="hand2")
            tk.Label(mf, text=f"  {menu['label']}",
                     bg=BTN_DARK, fg=TEXT_W,
                     font=("Courier",13,"bold"), anchor="w").pack(fill="x", padx=8, pady=(6,0))
            tk.Label(mf, text=f"  {menu['desc']}",
                     bg=BTN_DARK, fg=TEXT_G,
                     font=("Courier",10), anchor="w").pack(fill="x", padx=8)
            tk.Label(mf, text=f"  効果: {eff_str}",
                     bg=BTN_DARK, fg=ACCENT_COL,
                     font=("Courier",9), anchor="w").pack(fill="x", padx=8, pady=(0,6))
            mf.bind("<Button-1>", lambda e, m=menu: self._select_menu(m))
            for child in mf.winfo_children():
                child.bind("<Button-1>", lambda e, m=menu: self._select_menu(m))
            mf.bind("<Enter>", lambda e, f=mf: f.configure(bg=BTN_DARK_H))
            mf.bind("<Leave>", lambda e, f=mf: f.configure(bg=BTN_DARK))

        # ── 試走ボタン（6ヶ月完了後、1回だけ表示） ──
        if self.trial_available and not self.trial_done:
            tf = tk.Frame(self.root, bg="#1A1000",
                          highlightbackground=FLAG_COL, highlightthickness=1)
            tf.pack(fill="x", padx=28, pady=(8,2))
            make_label(tf, "  ⚡ 試走レースに出走する（この月の調教の代わりに）",
                       fg=FLAG_COL, font=("Courier",12,"bold")).pack(anchor="w", padx=8, pady=(6,0))
            make_label(tf, "  疲労+10〜20。勝てば経験ボーナス、負ければ次月に悔しさ補正。",
                       fg=TEXT_G, font=("Courier",9)).pack(anchor="w", padx=8, pady=(0,6))
            tf.configure(cursor="hand2")
            tf.bind("<Button-1>", lambda e: self._select_trial())
            for child in tf.winfo_children():
                child.bind("<Button-1>", lambda e: self._select_trial())
            tf.bind("<Enter>", lambda e: tf.configure(bg="#2A1A00"))
            tf.bind("<Leave>", lambda e: tf.configure(bg="#1A1000"))

    # ── スプライト読み込み ──────────────────────
    def _load_sprites(self):
        """育成演出用スプライトを読み込む（Pillow必須）"""
        import os
        self._img_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")
        img_dir = self._img_dir
        try:
            from horserace import load_horse_sprites
            self._sprites = load_horse_sprites(img_dir, target_h=160)
        except Exception:
            self._sprites = None
        # 背景画像をキャッシュ（Pillowが使えるときだけ）
        self._bg_cache = {}
        try:
            from PIL import Image, ImageTk as _ITk
            # haikei02=厩舎, haikei03=ウッドチップ, haikei04=坂路, haikei05=試走レース
            _load_map = {
                "mental":  "haikei02.png",
                "pasture": "haikei02.png",
                "speed":   "haikei03.png",
                "balance": "haikei03.png",
                "adapt":   "haikei03.png",
                "special": "haikei03.png",
                "stamina": "haikei04.png",
                "corner":  "haikei04.png",
                "trial":   "haikei05.png",
            }
            _loaded = {}
            for kind, fname in _load_map.items():
                if fname not in _loaded:
                    p = os.path.join(img_dir, fname)
                    if os.path.exists(p):
                        _loaded[fname] = Image.open(p).convert("RGBA")
                    else:
                        _loaded[fname] = None
                self._bg_cache[kind] = _loaded[fname]
        except Exception:
            pass

        # 試走用: 4頭分のスプライトを小さいサイズで用意
        self._trial_sprites = None
        try:
            from horserace import load_horse_sprites
            self._trial_sprites = load_horse_sprites(img_dir, target_h=120)
        except Exception:
            pass

    # ── メニュー演出 ─────────────────────────────
    # メニューID → (演出種類, 色, ラベル)
    _ANIM_MAP = {
        0: ("speed",   "#FF5533", "スピード特訓"),
        1: ("stamina", "#4488FF", "スタミナ調教"),
        2: ("corner",  "#44CCAA", "コーナー練習"),
        3: ("mental",  "#AA66FF", "メンタルケア"),
        4: ("pasture", "#44BB44", "放牧"),
        5: ("adapt",   "#FFAA22", "適応力強化"),
        6: ("balance", "#88CCFF", "総合調教"),
        7: ("special", "#FFAA00", "特別特訓"),
    }

    def _play_anim(self, menu_id, on_done):
        """演出Canvasを表示してアニメを再生、完了後 on_done を呼ぶ"""
        for w in self.root.winfo_children():
            w.destroy()

        kind, color, label = self._ANIM_MAP.get(menu_id, ("speed","#FF5533","調教"))
        res_name = self.cfg.get("resolution", DEFAULT_RES)
        win_w, win_h = RESOLUTIONS.get(res_name, RESOLUTIONS[DEFAULT_RES])

        cv = tk.Canvas(self.root, width=win_w, height=win_h,
                       bg=BG, highlightthickness=0)
        cv.pack()

        # コート選択（seedベース）
        coat = "brown" if self.seed % 2 == 0 else "white"
        sprite_num = 1  # スプライト番号（1〜8）

        self._anim_frame = 0
        DURATION = 90   # フレーム数（約3秒 @30fps）
        FPS_MS   = 33

        def loop():
            f = self._anim_frame
            if f >= DURATION:
                if self._anim_job:
                    self.root.after_cancel(self._anim_job)
                    self._anim_job = None
                on_done()
                return

            cv.delete("all")
            self._draw_anim_frame(cv, kind, color, label, f,
                                  win_w, win_h, coat, sprite_num)
            self._anim_frame += 1
            self._anim_job = self.root.after(FPS_MS, loop)

        # スキップボタン
        skip_f = tk.Frame(self.root, bg=BG)
        skip_f.place(x=win_w-120, y=win_h-50)
        make_btn(skip_f, "▶ スキップ", lambda: self._skip_anim(on_done),
                 bg=BTN_DARK).pack()

        loop()

    def _skip_anim(self, on_done):
        if self._anim_job:
            self.root.after_cancel(self._anim_job)
            self._anim_job = None
        on_done()

    def _draw_anim_frame(self, cv, kind, color, label, f,
                         W, H, coat, sprite_num):
        """1フレーム分の演出を描画"""
        import math

        # ── 背景 ──
        # 背景画像キャッシュから取得し、なければフォールバックカラーで描画
        bg_colors = {
            "speed":   "#0A0500",
            "stamina": "#00050A",
            "corner":  "#00080A",
            "mental":  "#04000A",
            "pasture": "#000A02",
            "adapt":   "#080600",
            "balance": "#040408",
            "special": "#0A0600",
        }
        # PhotoImage キャッシュ（解像度変化に対応）
        _pimg_key = f"_bgpimg_{kind}_{W}x{H}"
        _bg_pimg = getattr(self, _pimg_key, None)
        if _bg_pimg is None:
            _raw = self._bg_cache.get(kind) if hasattr(self, "_bg_cache") else None
            if _raw is not None:
                try:
                    from PIL import Image as _PILImg, ImageTk as _ITk
                    _resized = _raw.resize((W, H), _PILImg.LANCZOS)
                    _bg_pimg = _ITk.PhotoImage(_resized)
                    setattr(self, _pimg_key, _bg_pimg)
                except Exception:
                    _bg_pimg = None

        if _bg_pimg is not None:
            cv.create_image(0, 0, image=_bg_pimg, anchor="nw")
        else:
            cv.create_rectangle(0, 0, W, H,
                fill=bg_colors.get(kind, BG), outline="")

        GY = H - 120  # 地面 y

        # ── 種類別オーバーレイ演出（背景画像の上に重ねる） ──
        if kind == "speed":
            # 速度線（半透明風に細めの線を重ねる）
            for i in range(10):
                lx = int((f * 8 + i * 90) % (W + 150)) - 150
                ly = GY - 60 + i * 8
                ln = 50 + i * 6
                cv.create_line(lx, ly, lx+ln, ly,
                    fill=color, width=2)

        elif kind == "corner":
            # コースライン強調
            cv.create_arc(W//2-250, GY-100, W//2+250, GY+300,
                start=30, extent=120, style="arc",
                outline=color, width=3)

        elif kind == "mental":
            # 星のオーバーレイ
            for i in range(25):
                sx = int((i * 139 + f * 0.3) % W)
                sy = int((i * 67 + f * 0.7) % (GY - 20))
                sr = 1 + int(math.sin(f * 0.05 + i) + 1)
                cv.create_oval(sx-sr, sy-sr, sx+sr, sy+sr,
                    fill=color, outline="")

        elif kind == "special":
            # 炎パーティクルオーバーレイ
            mid_x = W // 2
            for i in range(30):
                fx2 = mid_x - 50 + (i * 31) % 100 + int(math.sin(f*0.1+i)*10)
                fy2 = GY - int((f * 3 + i * 17) % 90)
                fc  = ["#FF6600","#FF3300","#FFAA00"][i % 3]
                r   = max(1, 4 - (GY - fy2) // 25)
                cv.create_oval(fx2-r, fy2-r, fx2+r, fy2+r,
                    fill=fc, outline="")

        # 背景画像がない場合のみ地面を描画（画像あり時は画像内の地面を使う）
        if _bg_pimg is None:
            cv.create_rectangle(0, GY, W, H, fill="#101018", outline="")
            cv.create_line(0, GY, W, GY, fill="#333344", width=1)

        # ── 馬画像 or フォールバック図形 ──
        if kind == "special":
            shake = int(math.sin(f * 0.4) * 4)
        else:
            shake = 0

        if kind == "pasture":
            # 放牧: 画面中央付近でゆったり小さく揺れるだけ
            import math as _m
            horse_x  = W // 2 + int(_m.sin(f * 0.025) * 60)
            horse_y  = GY - 10
            speed_mult = 0.01
        elif kind == "mental":
            # ゆらゆら
            horse_x  = W // 2 + int(math.sin(f * 0.04) * 20) + shake
            horse_y  = GY - 10
            speed_mult = 0.02
        elif kind == "stamina":
            # 坂を登る
            prog     = (f * 0.6) % W
            horse_x  = int(prog) + shake
            horse_y  = int(GY - prog * 0.04) - 10
            speed_mult = 0.07
        elif kind == "corner":
            # 弧を描く
            angle    = f * 0.04 + math.pi * 1.2
            horse_x  = int(W//2 + math.cos(angle) * 220) + shake
            horse_y  = int(GY - 40 + math.sin(angle) * 30)
            speed_mult = 0.10
        elif kind == "speed":
            # 速く走る
            horse_x  = int((f * 6) % (W + 200)) - 100 + shake
            horse_y  = GY - 10
            speed_mult = 0.18
        else:
            # balance / adapt / special
            horse_x  = int((f * 3) % (W + 150)) - 75 + shake
            horse_y  = GY - 10
            speed_mult = 0.12

        # 画像があれば表示
        sprite = None
        if self._sprites:
            # スプライト番号は1〜8のうち seed%8+1 を使用
            snum = (self.seed % 8) + 1
            sprite = self._sprites.get((coat, snum))

        if sprite:
            cv.create_image(horse_x, horse_y, image=sprite, anchor="s")
        else:
            # フォールバック: 図形の馬
            self._draw_fallback_horse(cv, horse_x, horse_y, color, f * speed_mult)

        # ── テキスト演出 ──
        # メニュー名（大きく点滅）
        alpha_pulse = 0.6 + math.sin(f * 0.1) * 0.4
        cv.create_text(40, 60, text=label,
            fill=color, anchor="w",
            font=("Courier", 28, "bold"))

        # 進捗バー
        prog_w = int((f / 90) * (W - 80))
        cv.create_rectangle(40, H-30, W-40, H-14,
            fill="#1A1A2A", outline="#333344")
        cv.create_rectangle(40, H-30, 40+prog_w, H-14,
            fill=color, outline="")
        cv.create_text(W//2, H-22, text="調教中...",
            fill=TEXT_G, font=("Courier", 10))

    def _draw_fallback_horse(self, cv, x, y, color, leg_phase):
        """Pillowなし時の図形馬"""
        import math
        lp = leg_phase
        # 胴体
        cv.create_oval(x-28, y-26, x+28, y, fill=color, outline="")
        # 首・頭
        cv.create_oval(x+10, y-42, x+34, y-16, fill=color, outline="")
        # 脚
        for i, (ox, phase) in enumerate([(-15,0),(5,math.pi),(0,math.pi/2),(15,math.pi*1.5)]):
            a = math.sin(lp + phase) * 0.5
            x1 = x + ox
            y1 = y
            x2 = x1 + int(math.sin(a) * 8)
            y2 = y1 + int(math.cos(a) * 14) + 2
            cv.create_line(x1, y1, x2, y2, fill=color, width=3)

    def _select_menu(self, menu):
        import random as _r
        tr = self._tr
        new_stats, new_fat, event = tr.apply_training(
            self.stats, self.fatigue, menu["id"],
            self.month + 1,
            self.stats["growth_rate"],
            self.stats["peak_month"],
            seed=self.seed
        )
        self.stats   = new_stats
        self.fatigue = new_fat
        self.history.append(menu["id"])
        self.month  += 1

        # コーチメッセージ（演出後に表示）
        coach_msg = tr.get_coach_message(menu["id"], _r)
        # 演出を再生してから次へ
        self._play_anim(
            menu["id"],
            on_done=lambda: self._show_coach_message(menu, coach_msg, event)
        )

    def _select_trial(self):
        """試走レースを実行"""
        tr = self._tr
        new_stats, new_fat, event = tr.apply_trial_race(
            self.stats, self.fatigue, self.month + 1, self.seed,
            my_name=self.name)
        self.stats        = new_stats
        self.fatigue      = new_fat
        self.history.append(tr.TRIAL_MENU_ID)
        self.month       += 1
        self.trial_done   = True
        self.trial_available = False
        outcome = event.get("outcome", "mid")
        # 試走専用アニメ（haikei05背景 + 4頭レース演出）
        self._play_trial_anim(
            on_done=lambda: self._show_trial_result(event, outcome),
            outcome=outcome
        )

    def _play_trial_anim(self, on_done, outcome="mid"):
        """試走レース専用演出: haikei05背景 + 4頭走行アニメ"""
        for w in self.root.winfo_children():
            w.destroy()

        res_name = self.cfg.get("resolution", DEFAULT_RES)
        W, H = RESOLUTIONS.get(res_name, RESOLUTIONS[DEFAULT_RES])

        cv = tk.Canvas(self.root, width=W, height=H,
                       bg=BG, highlightthickness=0)
        cv.pack()

        # スキップボタン
        skip_f = tk.Frame(self.root, bg=BG)
        skip_f.place(x=W-120, y=H-50)
        make_btn(skip_f, "▶ スキップ", lambda: self._skip_anim(on_done),
                 bg=BTN_DARK).pack()

        self._anim_frame = 0
        DURATION = 210   # 約7秒
        FPS_MS   = 33

        # 背景PhotoImageキャッシュ
        _bg_key = f"_trial_bg_{W}x{H}"
        _bg_pimg = getattr(self, _bg_key, None)
        if _bg_pimg is None:
            _raw = self._bg_cache.get("trial") if hasattr(self, "_bg_cache") else None
            if _raw is not None:
                try:
                    from PIL import Image as _PI, ImageTk as _ITk
                    _bg_pimg = _ITk.PhotoImage(_raw.resize((W, H), _PI.LANCZOS))
                    setattr(self, _bg_key, _bg_pimg)
                except Exception:
                    _bg_pimg = None

        # 4頭の設定（seed由来で毎回同じ組み合わせ）
        import random as _rr
        _rng = _rr.Random(self.seed ^ 0xF00D)
        _coats  = ["brown","white","brown","brown"]
        _snums  = [((self.seed+i) % 8)+1 for i in range(4)]
        # レーンのy比率（haikei05実測ベース: 奥芝→ダート→手前芝）
        # 奥の芝コース: y_img≈440〜480/768 → ratio 0.580〜0.625
        # ダートコース: y_img≈490〜515/768 → ratio 0.638〜0.671
        # 奥側は小さく(scale小)、手前は大きく(scale=1.0)
        _lanes = [
            {"y_ratio": 0.575, "scale": 0.45, "speed": 4.6, "offset": W*0.08},
            {"y_ratio": 0.600, "scale": 0.58, "speed": 4.2, "offset": W*0.30},
            {"y_ratio": 0.645, "scale": 0.82, "speed": 5.0, "offset": W*0.00},
            {"y_ratio": 0.668, "scale": 1.00, "speed": 4.8, "offset": W*0.18},
        ]
        # 自馬（seed由来）は手前レーン(index 3)を使用
        _my_coat = "brown" if self.seed % 2 == 0 else "white"
        _my_snum = (self.seed % 8) + 1
        _coats[3] = _my_coat
        _snums[3] = _my_snum

        # 結果に応じた自馬スピード補正
        speed_bonus = {"victory": 1.25, "mid": 1.0, "defeat": 0.72}.get(outcome, 1.0)
        _lanes[3]["speed"] *= speed_bonus

        # 競争馬カラー（背番号色）
        _jockey_colors = ["#FF4444","#4488FF","#44CC66","#FFCC00"]

        def loop():
            f = self._anim_frame
            if f >= DURATION:
                if self._anim_job:
                    self.root.after_cancel(self._anim_job)
                    self._anim_job = None
                on_done()
                return

            cv.delete("all")

            # 背景
            if _bg_pimg:
                cv.create_image(0, 0, image=_bg_pimg, anchor="nw")
            else:
                cv.create_rectangle(0, 0, W, H, fill="#5A8A3A", outline="")

            # 4頭を奥→手前の順で描画（奥が先に描かれ手前が上に重なる）
            import math
            for idx in range(4):
                lane  = _lanes[idx]
                hy    = int(lane["y_ratio"] * H)
                sc    = lane["scale"]
                spd   = lane["speed"]
                off   = lane["offset"]
                # 右から左へ流れる（ゲートが左にあるので右→左）
                # ただし画像を見ると馬は右方向へ走るので左→右
                hx = int((f * spd + off) % (W + 200)) - 60

                coat = _coats[idx]
                snum = _snums[idx]
                jcol = _jockey_colors[idx]

                # 奥の馬は薄く（遠近感）
                drawn = False
                sprites = self._trial_sprites
                if sprites:
                    sp_key = (coat, snum)
                    base_sp = sprites.get(sp_key)
                    if base_sp:
                        # スケール別キャッシュ
                        sp_cache_key = f"_tsp_{coat}_{snum}_{sc:.2f}"
                        scaled_sp = getattr(self, sp_cache_key, None)
                        if scaled_sp is None:
                            try:
                                from PIL import Image as _PI, ImageTk as _ITk
                                from horserace import SPRITE_CROPS
                                import numpy as np
                                path = self._img_dir + f"/rdesign_19914.png" if coat=="brown" else self._img_dir + f"/rdesign_19916.png"
                                import os
                                sheet = _PI.open(os.path.join(self._img_dir,
                                    "rdesign_19914.png" if coat=="brown" else "rdesign_19916.png")).convert("RGBA")
                                arr = np.array(sheet)
                                mask = (arr[:,:,0].astype(int)+arr[:,:,1].astype(int)+arr[:,:,2].astype(int))<=30
                                arr[mask,3]=0
                                x1,y1,x2,y2 = SPRITE_CROPS[snum]
                                crop = _PI.fromarray(arr,"RGBA").crop((x1,y1,x2,y2))
                                crop = crop.transpose(_PI.FLIP_LEFT_RIGHT)
                                th = int(120 * sc)
                                tw = int(crop.width * th / crop.height)
                                if th > 0 and tw > 0:
                                    crop = crop.resize((tw, th), _PI.LANCZOS)
                                    scaled_sp = _ITk.PhotoImage(crop)
                                    setattr(self, sp_cache_key, scaled_sp)
                            except Exception:
                                scaled_sp = None
                        if scaled_sp:
                            cv.create_image(hx, hy, image=scaled_sp, anchor="s")
                            # 勝負服（騎手カラーの丸: 馬の背〜頭あたりに重ねる）
                            jr = max(4, int(10 * sc))
                            jy = int(hy - 100 * sc)
                            cv.create_oval(hx-jr, jy-jr, hx+jr, jy+jr,
                                fill=jcol, outline="white", width=1)
                            drawn = True

                if not drawn:
                    # フォールバック図形馬
                    s = sc
                    cv.create_oval(hx-18*s, hy-16*s, hx+18*s, hy,
                        fill=jcol, outline="")
                    cv.create_oval(hx+8*s, hy-28*s, hx+22*s, hy-10*s,
                        fill=jcol, outline="")

            # テキストオーバーレイ
            outcome_txt = {"victory":"⚡ 試走レース中... 快走！",
                           "mid":    "⚡ 試走レース中...",
                           "defeat": "⚡ 試走レース中... 苦戦..."}
            txt_col = {"victory": SAFE_COL, "mid": FLAG_COL, "defeat": MINE_COL}.get(outcome, TEXT_W)
            cv.create_text(W//2, 36,
                text=outcome_txt.get(outcome,"⚡ 試走レース中..."),
                fill=txt_col, font=("Courier", 20, "bold"),
                anchor="center")

            # 進捗バー
            prog_w = int((f / DURATION) * (W - 80))
            cv.create_rectangle(40, H-28, W-40, H-12,
                fill="#1A1A2A", outline="#445566")
            cv.create_rectangle(40, H-28, 40+prog_w, H-12,
                fill=txt_col, outline="")
            cv.create_text(W//2, H-20, text=f"🐴 {self.name}  試走中...",
                fill=TEXT_G, font=("Courier", 10))

            self._anim_frame += 1
            self._anim_job = self.root.after(FPS_MS, loop)

        loop()

    def _show_trial_result(self, event, outcome):
        """試走結果画面"""
        for w in self.root.winfo_children(): w.destroy()
        tr = self._tr

        outcome_colors = {"victory": SAFE_COL, "mid": FLAG_COL, "defeat": MINE_COL}
        outcome_labels = {"victory": "🏆 勝利！", "mid": "📊 中位", "defeat": "💔 惨敗"}
        col   = outcome_colors.get(outcome, TEXT_W)
        label = outcome_labels.get(outcome, "試走完了")

        make_label(self.root, f"⚡ 試走レース結果 — {label}",
                   fg=col, font=("Courier",18,"bold")).pack(pady=(28,8))
        make_label(self.root, f"🐴 {self.name}  第{self.month}月 完了（試走）",
                   fg=ACCENT_COL, font=("Courier",13)).pack(pady=(0,16))

        res_frame = tk.Frame(self.root, bg=SIDEBAR_BG)
        res_frame.pack(fill="x", padx=40, pady=(0,12))
        make_label(res_frame, event["message_prefix"],
                   fg=col, font=("Courier",12,"bold")).pack(anchor="w", padx=12, pady=(8,0))
        make_label(res_frame, event["message"],
                   fg=TEXT_W, font=("Courier",11)).pack(anchor="w", padx=20)
        make_label(res_frame, event["sub"],
                   fg=TEXT_G, font=("Courier",10)).pack(anchor="w", padx=20, pady=(0,8))

        # ── 順位表示 ──
        ranking = event.get("ranking", [])
        my_rank = event.get("my_rank", "-")
        if ranking:
            rank_frame = tk.Frame(self.root, bg="#0A1A0A")
            rank_frame.pack(fill="x", padx=40, pady=(0,10))
            make_label(rank_frame, "── レース順位 ──",
                       fg=TEXT_G, font=("Courier",10,"bold")).pack(anchor="w", padx=12, pady=(6,2))
            medals = ["🥇","🥈","🥉","4"]
            for i, horse_nm in enumerate(ranking):
                is_my = (horse_nm == self.name)
                nm_col = col if is_my else TEXT_W
                nm_bold = "bold" if is_my else "normal"
                tag = " ◀ 我が馬" if is_my else ""
                make_label(rank_frame,
                           f"  {medals[i]}  {horse_nm}{tag}",
                           fg=nm_col, font=("Courier",11,nm_bold)
                           ).pack(anchor="w", padx=16)
            tk.Label(rank_frame, text="", bg="#0A1A0A").pack(pady=2)

        # 試走実績
        results = self.stats.get("_trial_result", [])
        if results:
            rlabels = {"victory":"勝", "mid":"中", "defeat":"敗"}
            r_str = " ".join(rlabels.get(r,"?") for r in results)
            make_label(self.root, f"試走実績: {r_str}",
                       fg=TEXT_G, font=("Courier",10)).pack(pady=(4,0))

        bf = tk.Frame(self.root, bg=BG)
        bf.pack(pady=(20,0))
        if self.month >= tr.TRAINING_MONTHS:
            make_btn(bf, "育成完了へ ▶", self._show_complete,
                     bg=SAFE_COL, fg=BG).pack()
        else:
            make_btn(bf, f"第{self.month+1}月へ ▶", self._next_month,
                     bg=SAFE_COL, fg=BG).pack()

    def _show_coach_message(self, menu, coach_msg, event):
        for w in self.root.winfo_children(): w.destroy()
        make_label(self.root, f"🐴 {self.name}  第{self.month}月 完了",
                   fg=ACCENT_COL, font=("Courier",16,"bold")).pack(pady=(28,16))

        # 通常コーチメッセージ
        msg_frame = tk.Frame(self.root, bg=SIDEBAR_BG)
        msg_frame.pack(fill="x", padx=40, pady=(0,12))
        make_label(msg_frame, "調教師:",
                   fg=FLAG_COL, font=("Courier",10,"bold")).pack(anchor="w", padx=12, pady=(8,0))
        make_label(msg_frame, f"「{coach_msg}」",
                   fg=TEXT_W, font=("Courier",11)).pack(anchor="w", padx=20, pady=(0,8))

        # イベントメッセージ
        if event:
            ev_frame = tk.Frame(self.root, bg="#1A0A00" if "アクシデント" in event["message_prefix"] else "#0A1A00")
            ev_frame.pack(fill="x", padx=40, pady=(0,12))
            make_label(ev_frame, event["message_prefix"],
                       fg=MINE_COL if "アクシデント" in event["message_prefix"] else SAFE_COL,
                       font=("Courier",12,"bold")).pack(anchor="w", padx=12, pady=(8,0))
            make_label(ev_frame, event["message"],
                       fg=TEXT_W, font=("Courier",11)).pack(anchor="w", padx=20)
            if event.get("sub"):
                make_label(ev_frame, event["sub"],
                           fg=FLAG_COL, font=("Courier",10)).pack(anchor="w", padx=20, pady=(0,8))

        bf = tk.Frame(self.root, bg=BG)
        bf.pack(pady=(16,0))
        if self.month >= self._tr.TRAINING_MONTHS:
            make_btn(bf, "育成完了へ ▶", self._show_complete,
                     bg=SAFE_COL, fg=BG).pack()
        else:
            # extra_trial_pending: 特別招待レースボタンを追加表示
            if self.stats.get("_extra_trial_pending"):
                make_btn(bf, "⚡ 特別招待レースに参加する！",
                         self._select_extra_trial,
                         bg=FLAG_COL, fg=BG).pack(pady=(0,6))
            make_btn(bf, f"第{self.month+1}月へ ▶", self._next_month,
                     bg=SAFE_COL, fg=BG).pack()

    def _select_extra_trial(self):
        """特別招待レース（追加試走）を実行"""
        # pending フラグをクリア
        self.stats["_extra_trial_pending"] = False
        tr = self._tr
        new_stats, new_fat, event = tr.apply_trial_race(
            self.stats, self.fatigue, self.month, self.seed ^ 0xEEEE,
            my_name=self.name)
        self.stats   = new_stats
        self.fatigue = new_fat
        # history には記録せず（月消費なし）、trial_count/resultは加算される
        outcome = event.get("outcome", "mid")
        self._play_trial_anim(
            on_done=lambda: self._show_extra_trial_result(event, outcome),
            outcome=outcome
        )

    def _show_extra_trial_result(self, event, outcome):
        """特別招待レース結果画面（_show_trial_result の軽量版）"""
        for w in self.root.winfo_children(): w.destroy()
        tr = self._tr
        outcome_colors = {"victory": SAFE_COL, "mid": FLAG_COL, "defeat": MINE_COL}
        outcome_labels = {"victory": "🏆 勝利！", "mid": "📊 中位", "defeat": "💔 惨敗"}
        col   = outcome_colors.get(outcome, TEXT_W)
        label = outcome_labels.get(outcome, "完走")

        make_label(self.root, f"⚡ 特別招待レース結果 — {label}",
                   fg=col, font=("Courier",18,"bold")).pack(pady=(28,8))
        make_label(self.root, f"🐴 {self.name}  特別試走",
                   fg=ACCENT_COL, font=("Courier",13)).pack(pady=(0,12))

        res_frame = tk.Frame(self.root, bg=SIDEBAR_BG)
        res_frame.pack(fill="x", padx=40, pady=(0,10))
        make_label(res_frame, event["message_prefix"],
                   fg=col, font=("Courier",12,"bold")).pack(anchor="w", padx=12, pady=(8,0))
        make_label(res_frame, event["message"],
                   fg=TEXT_W, font=("Courier",11)).pack(anchor="w", padx=20, pady=(0,8))

        # 順位表示
        ranking = event.get("ranking", [])
        if ranking:
            rank_frame = tk.Frame(self.root, bg="#0A1A0A")
            rank_frame.pack(fill="x", padx=40, pady=(0,10))
            make_label(rank_frame, "── レース順位 ──",
                       fg=TEXT_G, font=("Courier",10,"bold")).pack(anchor="w", padx=12, pady=(6,2))
            medals = ["🥇","🥈","🥉","4"]
            for i, horse_nm in enumerate(ranking):
                is_my = (horse_nm == self.name)
                nm_col = col if is_my else TEXT_W
                nm_bold = "bold" if is_my else "normal"
                tag = " ◀ 我が馬" if is_my else ""
                make_label(rank_frame,
                           f"  {medals[i]}  {horse_nm}{tag}",
                           fg=nm_col, font=("Courier",11,nm_bold)).pack(anchor="w", padx=16)
            tk.Label(rank_frame, text="", bg="#0A1A0A").pack(pady=2)

        # 実績
        results = self.stats.get("_trial_result", [])
        if results:
            rlabels = {"victory":"勝", "mid":"中", "defeat":"敗"}
            r_str = " ".join(rlabels.get(r,"?") for r in results)
            make_label(self.root, f"試走実績: {r_str}",
                       fg=TEXT_G, font=("Courier",10)).pack(pady=(4,0))

        bf = tk.Frame(self.root, bg=BG)
        bf.pack(pady=(20,0))
        if self.month >= tr.TRAINING_MONTHS:
            make_btn(bf, "育成完了へ ▶", self._show_complete,
                     bg=SAFE_COL, fg=BG).pack()
        else:
            make_btn(bf, f"第{self.month+1}月へ ▶", self._next_month,
                     bg=SAFE_COL, fg=BG).pack()

    # ── 育成完了 ──────────────────────────────
    def _show_complete(self):
        for w in self.root.winfo_children(): w.destroy()
        tr = self._tr
        traits = tr.determine_traits(self.stats)
        self.stats["traits"] = traits
        code     = tr.encode_horse_code(self.name, self.seed, self.history)
        eval_msg = tr.get_completion_message(self.stats)
        # コンボ特性を分けて表示用に取得
        single_names = {t["name"] for t in tr.TRAITS}
        combo_traits  = [t for t in traits if t not in single_names]
        base_traits   = [t for t in traits if t in single_names]

        apt = tr.get_aptitude_type(self.seed)

        make_label(self.root, "🏆 育成完了！",
                   fg=FLAG_COL, font=("Courier",22,"bold")).pack(pady=(20,4))
        make_label(self.root, f"「{self.name}」が育成を終えました！",
                   fg=TEXT_W, font=("Courier",13)).pack(pady=(0,4))
        # 素質タイプ開示
        make_label(self.root, f"素質: 【{apt['name']}】  {apt['desc']}",
                   fg=ACCENT_COL, font=("Courier",11)).pack(pady=(0,10))

        # 調教師の評価
        ev_frame = tk.Frame(self.root, bg=SIDEBAR_BG)
        ev_frame.pack(fill="x", padx=40, pady=(0,12))
        make_label(ev_frame, "調教師の評価:",
                   fg=FLAG_COL, font=("Courier",10,"bold")).pack(anchor="w", padx=12, pady=(8,0))
        for line in eval_msg.splitlines():
            make_label(ev_frame, f"  {line}",
                       fg=TEXT_W, font=("Courier",11)).pack(anchor="w", padx=20)
        tk.Label(ev_frame, text="", bg=SIDEBAR_BG).pack(pady=4)

        # 五角形グラフ（最終）
        graph_size = 200
        cv = tk.Canvas(self.root, width=graph_size, height=graph_size,
                       bg=SIDEBAR_BG, highlightthickness=0)
        cv.pack(pady=(0,8))
        self._draw_pentagon(cv, self.stats, graph_size//2, graph_size//2, 68)

        # 試走実績
        results = self.stats.get("_trial_result", [])
        if results:
            rlabels = {"victory": "🏆勝", "mid": "📊中", "defeat": "💔敗"}
            r_str = "  ".join(rlabels.get(r, "?") for r in results)
            make_label(self.root, f"試走実績: {r_str}",
                       fg=TEXT_G, font=("Courier",10)).pack(pady=(0,4))

        # 特性表示（単体 + コンボ）
        if base_traits:
            make_label(self.root, "特性: " + "  ".join(base_traits),
                       fg=TEXT_G, font=("Courier",11)).pack(pady=(0,2))
        if combo_traits:
            make_label(self.root, "✨ コンボ: " + "  ".join(combo_traits),
                       fg=FLAG_COL, font=("Courier",12,"bold")).pack(pady=(0,8))
        elif base_traits:
            tk.Label(self.root, text="", bg=BG).pack(pady=4)

        # コード
        make_label(self.root, "馬コード（コピーして保存）:",
                   fg=TEXT_G, font=("Courier",11)).pack(pady=(4,2))
        code_var   = tk.StringVar(value=code)
        code_entry = tk.Entry(self.root, textvariable=code_var, width=56,
                              bg=CELL_HID, fg=SAFE_COL,
                              relief="flat", font=("Courier",10), bd=6, state="readonly")
        code_entry.pack(padx=40, pady=(0,4))
        copy_lbl = tk.Label(self.root, text="", bg=BG, fg=SAFE_COL, font=("Courier",10))
        copy_lbl.pack()

        def copy_code():
            self.root.clipboard_clear()
            self.root.clipboard_append(code)
            copy_lbl.config(text="✅ コピーしました！")
            self.root.after(2000, lambda: copy_lbl.config(text=""))

        bf = tk.Frame(self.root, bg=BG)
        bf.pack(pady=(8,24))
        make_btn(bf, "📋 コードをコピー", copy_code, bg=BTN_DARK).pack(side="left")
        make_btn(bf, "◀  ロビーへ", self.on_back).pack(side="left", padx=(8,0))
        make_btn(bf, "🏇  すぐレースへ", lambda: self._go_race(code),
                 bg=SAFE_COL, fg=BG).pack(side="left", padx=(8,0))

    def _go_race(self, code):
        tr = self._tr
        name, seed, history = tr.decode_horse_code(code)
        trained    = tr.trained_to_race_horse(name, seed, history, 1, "芝")
        vote_sec   = self.cfg.get("hr_vote_sec", 60)
        race_count = int(self.cfg.get("hr_race_count", "3"))
        self.on_race(self.cfg, vote_sec, race_count, trained)

class CodeEntryScreen:
    """最大8頭の育成馬コードを入力してレースに参加する画面"""
    MAX_HORSES = 8

    def __init__(self, root, cfg, on_back, on_race):
        self.root       = root
        self.cfg        = cfg
        self.on_back    = on_back
        self.on_race    = on_race
        self._entries   = []
        self._parsed    = {}
        self._modal_cv  = None
        self._modal_horse     = None
        self._modal_horse_pos = None
        self._modal_drag      = None
        self._modal_last_draw = 0.0

        res_name = cfg.get("resolution", DEFAULT_RES)
        self.win_w, self.win_h = RESOLUTIONS.get(res_name, RESOLUTIONS[DEFAULT_RES])

        root.title("ChatViewPlayGame - コードで参戦")
        root.configure(bg=BG)

        make_label(root, "📋 コードで参戦",
                   fg=ACCENT_COL, font=("Courier",20,"bold")).pack(pady=(20,2))
        make_label(root, "育成馬コードを入力（最大8頭・空欄はランダム馬で補完）",
                   fg=TEXT_G, font=("Courier",10)).pack(pady=(0,4))

        # 現在の設定を簡易表示
        from horserace import GRADE_DEFS, DEFAULT_GRADE
        grade_key  = cfg.get("hr_grade", DEFAULT_GRADE)
        gdef       = GRADE_DEFS.get(grade_key, GRADE_DEFS[DEFAULT_GRADE])
        vote_sec   = cfg.get("hr_vote_sec", 60)
        race_count = cfg.get("hr_race_count", "3")
        keep       = "有効" if cfg.get("hr_keep_trained", False) else "無効"
        grade_colors = {"未勝利":"#88aa88","G3":"#88aacc","G2":"#4488ff","G1":"#ffcc44","特別G1":"#ff6644"}
        gcol = grade_colors.get(grade_key, "#88aacc")

        info_frame = tk.Frame(root, bg=SIDEBAR_BG)
        info_frame.pack(fill="x", padx=28, pady=(0,8))
        info_inner = tk.Frame(info_frame, bg=SIDEBAR_BG)
        info_inner.pack(padx=12, pady=6)

        items = [
            ("グレード",   f"{grade_key}  （ランダム馬: {gdef['stat_min']}〜{gdef['stat_max']}）", gcol),
            ("投票時間",   f"{vote_sec}秒",                                                          TEXT_G),
            ("レース数",   f"{race_count}レース" if race_count != "0" else "無限",                   TEXT_G),
            ("連続出走",   keep,                                                                       TEXT_G),
        ]
        for label, val, col in items:
            row = tk.Frame(info_inner, bg=SIDEBAR_BG)
            row.pack(side="left", padx=(0,20))
            tk.Label(row, text=label, bg=SIDEBAR_BG, fg="#445",
                     font=("Courier",9)).pack(anchor="w")
            tk.Label(row, text=val, bg=SIDEBAR_BG, fg=col,
                     font=("Courier",10,"bold")).pack(anchor="w")

        inner = tk.Frame(root, bg=BG)
        inner.pack(fill="both", expand=True, padx=28)

        for i in range(self.MAX_HORSES):
            row = tk.Frame(inner, bg=BG)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=f"{i+1}番:",
                     bg=BG, fg=HR_COLORS[i % len(HR_COLORS)],
                     font=("Courier",11,"bold"), width=4).pack(side="left")
            var = tk.StringVar()
            tk.Entry(row, textvariable=var, width=44,
                     bg=CELL_HID, fg=SAFE_COL, insertbackground=TEXT_W,
                     relief="flat", font=("Courier",10), bd=4).pack(side="left", padx=(4,4))
            status_lbl = tk.Label(row, text="", bg=BG, fg=TEXT_G,
                                   font=("Courier",9), width=18, anchor="w")
            status_lbl.pack(side="left")
            idx = i
            detail_btn = tk.Button(row, text="詳細",
                                   bg=BTN_DARK, fg=TEXT_G,
                                   activebackground=ACCENT_COL, activeforeground=BG,
                                   relief="groove", bd=1,
                                   font=("Courier",9,"bold"),
                                   state="disabled", cursor="hand2",
                                   command=lambda i=idx: self._show_profile(i))
            detail_btn.pack(side="left", padx=(2,0))
            var.trace_add("write", lambda *a, i=idx: self._on_code_change(i))
            self._entries.append((var, status_lbl, detail_btn))

        self._err_var = tk.StringVar()
        tk.Label(root, textvariable=self._err_var,
                 bg=BG, fg=MINE_COL, font=("Courier",11)).pack(pady=(8,0))

        bf = tk.Frame(root, bg=BG)
        bf.pack(pady=(8,16))
        make_btn(bf, "◀  戻る", self.on_back).pack(side="left")
        make_btn(bf, "🏇  参戦する", self._go_race,
                 bg=SAFE_COL, fg=BG).pack(side="left", padx=(12,0))

    def _on_code_change(self, idx):
        var, lbl, btn = self._entries[idx]
        code = var.get().strip()
        if not code:
            lbl.config(text="（ランダム馬）", fg=TEXT_G)
            btn.config(state="disabled", bg=BTN_DARK, fg=TEXT_G)
            self._parsed.pop(idx, None)
            return
        try:
            from training import decode_horse_code, replay_training
            name, seed, history = decode_horse_code(code)
            stats  = replay_training(seed, history)
            traits = stats.get("traits", [])
            self._parsed[idx] = (name, seed, history, stats)
            from training import COMBO_TRAITS as _CT
            combo_names = {c["name"] for c in _CT}
            combos = [t for t in traits if t in combo_names]
            trait_str = f" [{'・'.join(combos[:2])}]" if combos else (
                        f" [{traits[0]}]" if traits else "")
            lbl.config(text=f"✅ {name}{trait_str}", fg=SAFE_COL)
            btn.config(state="normal", bg=ACCENT_COL, fg=BG,
                       activebackground=BTN_DARK_H, activeforeground=TEXT_W)
            self._err_var.set("")
        except Exception:
            self._parsed.pop(idx, None)
            lbl.config(text="⚠ 無効なコード", fg=MINE_COL)
            btn.config(state="disabled", bg=BTN_DARK, fg=TEXT_G)

    def _show_profile(self, idx):
        """モーダルCanvasをモーダルサイズ分だけ生成して馬プロフィールを表示"""
        if idx not in self._parsed:
            return
        data  = self._parsed[idx]
        stats = data[3] if len(data) > 3 else None
        if stats is None:
            from training import replay_training
            stats = replay_training(data[1], data[2])

        # コメント生成
        comment = ""
        try:
            from horserace import make_comment
            import random as _r
            surface = _r.choice(["芝", "ダート"])
            horse_tmp = {
                "speed":        min(10, max(1, round(stats.get("speed",   50)/10))),
                "stamina":      min(10, max(1, round(stats.get("stamina", 50)/10))),
                "corner":       min(10, max(1, round(stats.get("corner",  50)/10))),
                "mental":       min(10, max(1, round(stats.get("mental",  50)/10))),
                "adaptability": min(10, max(1, round(stats.get("adaptability",50)/10))),
                "apt_turf":     stats.get("apt_turf","○"),
                "apt_dirt":     stats.get("apt_dirt","○"),
                "condition":    "○",
                "cond_mult":    1.0,
                "jockey":       {"skill":3,"style":"先行"},
                "affinity":     "○",
                "aff_mult":     1.0,
                "traits":       stats.get("traits",[]),
            }
            comment = make_comment(horse_tmp, surface, 2000)
        except Exception:
            pass

        horse = {
            "number":       idx + 1,
            "name":         data[0],
            "speed":        min(10, max(1, round(stats.get("speed",   50)/10))),
            "stamina":      min(10, max(1, round(stats.get("stamina", 50)/10))),
            "corner":       min(10, max(1, round(stats.get("corner",  50)/10))),
            "mental":       min(10, max(1, round(stats.get("mental",  50)/10))),
            "adaptability": min(10, max(1, round(stats.get("adaptability",50)/10))),
            "apt_turf":     stats.get("apt_turf","○"),
            "apt_dirt":     stats.get("apt_dirt","○"),
            "condition":    "○",
            "traits":       stats.get("traits", []),
            "is_trained":   True,
            "comment":      comment,
        }
        self._modal_horse     = horse
        self._modal_horse_pos = None
        self._modal_drag      = None

        # 既存のモーダルCanvasがあれば破棄
        if self._modal_cv is not None:
            try: self._modal_cv.destroy()
            except Exception: pass
            self._modal_cv = None

        # ── Canvas をモーダルサイズ分だけ生成して中央に配置 ──
        # 全画面Canvasにすると他ウィジェットを覆いフリーズするため
        mw, mh   = 560, 460
        px = max(0, (self.win_w - mw) // 2)
        py = max(0, (self.win_h - mh) // 2)
        cv = tk.Canvas(self.root, width=mw, height=mh,
                       bg="#0D1025", highlightthickness=0)
        cv.place(x=px, y=py)
        self._modal_cv = cv
        self._modal_px = px
        self._modal_py = py

        cv.bind("<Button-1>",        self._modal_click)
        cv.bind("<B1-Motion>",       self._modal_b1motion)
        cv.bind("<ButtonRelease-1>", self._modal_release)

        # モーダルサイズのCanvas内に直接描画（座標はCanvas内相対）
        self._draw_modal_on_cv(cv, horse, mw, mh)

    def _draw_modal_on_cv(self, cv, h, mw, mh):
        """Canvas内（0,0起点）にモーダルを描画"""
        import math
        cv.delete("all")
        col = HR_COLORS[(h.get("number",1)-1) % len(HR_COLORS)]

        # 外枠
        cv.create_rectangle(0, 0, mw-1, mh-1, fill="", outline=col, width=2)
        # ヘッダー
        cv.create_rectangle(0, 0, mw, 44, fill=BTN_DARK, outline="")
        mark = "🐴 " if h.get("is_trained") else ""
        cv.create_text(16, 22,
            text=f"{mark}{h.get('number','')}番  {h.get('name','')}",
            fill=col, anchor="w", font=("Courier",14,"bold"))
        cv.create_text(mw//2, 22, text="⠿ ドラッグで移動",
            fill=TEXT_G, anchor="center", font=("Courier",8))
        # ×ボタン
        cv.create_rectangle(mw-36, 8, mw-8, 36,
            fill="#2A1A1A", outline=MINE_COL, width=1)
        cv.create_text(mw-22, 22, text="×",
            fill=MINE_COL, font=("Courier",13,"bold"))

        # 五角形グラフ（Canvas内座標）
        keys   = ["speed","stamina","corner","mental","adaptability"]
        labels = ["速度","スタミナ","コーナー","精神力","適応力"]
        cx_g, cy_g, r = 110, 195, 85
        for level in [0.25,0.5,0.75,1.0]:
            pts = []
            for i in range(5):
                a = math.pi/2 + 2*math.pi*i/5
                pts.extend([cx_g+r*level*math.cos(a), cy_g-r*level*math.sin(a)])
            cv.create_polygon(pts, fill="", outline="#222244", width=1)
        for i in range(5):
            a = math.pi/2 + 2*math.pi*i/5
            cv.create_line(cx_g, cy_g, cx_g+r*math.cos(a), cy_g-r*math.sin(a),
                           fill="#222244", width=1)
        pts = []
        for i, key in enumerate(keys):
            val = h.get(key, 0) / 10.0
            a   = math.pi/2 + 2*math.pi*i/5
            pts.extend([cx_g+r*val*math.cos(a), cy_g-r*val*math.sin(a)])
        cv.create_polygon(pts, fill=col, outline=col, width=2)
        cv.create_polygon(pts, fill="", outline=col, width=2)
        for i, key in enumerate(keys):
            val = h.get(key, 0) / 10.0
            a   = math.pi/2 + 2*math.pi*i/5
            px2, py2 = cx_g+r*val*math.cos(a), cy_g-r*val*math.sin(a)
            cv.create_oval(px2-4, py2-4, px2+4, py2+4, fill=col, outline="")
        for i, (key, lbl) in enumerate(zip(keys, labels)):
            a  = math.pi/2 + 2*math.pi*i/5
            lx = cx_g+(r+26)*math.cos(a)
            ly = cy_g-(r+26)*math.sin(a)
            sn = min(5, max(0, round(h.get(key,0)/2)))
            cv.create_text(lx, ly-7, text=lbl,
                fill=TEXT_G, font=("Courier",9), anchor="center")
            cv.create_text(lx, ly+7, text="★"*sn+"☆"*(5-sn),
                fill=FLAG_COL, font=("Courier",9), anchor="center")

        # 右側ステータス
        rx, ry2 = 240, 56
        for lbl, key in [("速度","speed"),("スタミナ","stamina"),("コーナー","corner"),
                         ("精神力","mental"),("適応力","adaptability")]:
            val = h.get(key, 0)
            sn  = min(5, max(0, round(val/2)))
            cv.create_text(rx, ry2, text=f"{lbl}:",
                fill=TEXT_G, anchor="w", font=("Courier",10))
            cv.create_text(rx+80, ry2, text="★"*sn+"☆"*(5-sn),
                fill=FLAG_COL, anchor="w", font=("Courier",10))
            ry2 += 22
        ry2 += 4
        apt_t = h.get("apt_turf","○")
        apt_d = h.get("apt_dirt","○")
        cv.create_text(rx, ry2, text=f"芝:{apt_t}  ダート:{apt_d}",
            fill=TEXT_G, anchor="w", font=("Courier",10))
        ry2 += 22
        cond = h.get("condition","○")
        cond_col = SAFE_COL if cond=="◎" else (FLAG_COL if cond=="○" else
                   (TEXT_G if cond=="△" else MINE_COL))
        cv.create_text(rx, ry2, text=f"調子: {cond}",
            fill=cond_col, anchor="w", font=("Courier",11,"bold"))

        # 特性
        traits = h.get("traits", [])
        if traits:
            try:
                from training import COMBO_TRAITS as _CT
                combo_names = {c["name"] for c in _CT}
            except Exception:
                combo_names = set()
            base_t  = [t for t in traits if t not in combo_names]
            combo_t = [t for t in traits if t in combo_names]
            ty = mh - 80
            cv.create_line(10, ty-6, mw-10, ty-6, fill=CELL_BORDER, width=1)
            if base_t:
                cv.create_text(16, ty, text="特性: "+"  ".join(base_t),
                    fill=TEXT_G, anchor="w", font=("Courier",10))
                ty += 18
            if combo_t:
                cv.create_text(16, ty, text="✨ "+"  ".join(combo_t),
                    fill=FLAG_COL, anchor="w", font=("Courier",11,"bold"))

        # コメント
        cy_com = mh - 24
        cv.create_line(10, cy_com-12, mw-10, cy_com-12, fill=CELL_BORDER, width=1)
        comment = h.get("comment","")
        cv.create_text(16, cy_com, text=f"「{comment[:52]}」" if comment else "（コメントなし）",
            fill=FLAG_COL, anchor="w", font=("Courier",9))

    def _modal_click(self, ev):
        mw, mh = 560, 460
        # ×ボタン（Canvas内座標）
        if mw-36<=ev.x<=mw-8 and 8<=ev.y<=36:
            self._close_modal()
            return
        # ヘッダー内（×以外）でドラッグ開始
        if ev.x <= mw-36 and ev.y <= 44:
            px = getattr(self, "_modal_px", 0)
            py = getattr(self, "_modal_py", 0)
            self._modal_drag = (ev.x, ev.y, px, py)

    def _modal_b1motion(self, ev):
        if self._modal_drag is None or self._modal_cv is None:
            return
        ox, oy, bpx, bpy = self._modal_drag
        mw, mh = 560, 460
        new_px = max(0, min(self.win_w - mw, bpx + ev.x - ox))
        new_py = max(0, min(self.win_h - mh, bpy + ev.y - oy))
        self._modal_px = new_px
        self._modal_py = new_py
        # place() はCanvas中身を再描画しないので毎回呼んでよい
        self._modal_cv.place(x=new_px, y=new_py)

    def _modal_release(self, ev):
        self._modal_drag = None

    def _close_modal(self):
        self._modal_horse     = None
        self._modal_horse_pos = None
        self._modal_drag      = None
        if self._modal_cv is not None:
            try: self._modal_cv.destroy()
            except Exception: pass
            self._modal_cv = None

    def _go_race(self):
        from training import decode_horse_code, trained_to_race_horse
        trained_list = []
        for idx, (var, lbl, btn) in enumerate(self._entries):
            code = var.get().strip()
            if not code:
                continue
            if idx not in self._parsed:
                self._err_var.set(f"⚠ {idx+1}番のコードが無効です")
                return
            data = self._parsed[idx]
            name, seed, history = data[0], data[1], data[2]
            horse = trained_to_race_horse(name, seed, history, idx+1, "芝")
            trained_list.append(horse)
        if not trained_list:
            self._err_var.set("⚠ 少なくとも1頭のコードを入力してください")
            return
        self._close_modal()
        vote_sec   = self.cfg.get("hr_vote_sec", 60)
        race_count = int(self.cfg.get("hr_race_count", "3"))
        self.on_race(self.cfg, vote_sec, race_count,
                     trained_list[0], trained_list)


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.cfg  = load_config()
        apply_theme(self.cfg.get("theme", "NightBlue"))
        _apply_icon(self.root)
        # ウィンドウサイズを設定から読み込み、起動時に一度だけ固定
        res_name = self.cfg.get("resolution", DEFAULT_RES)
        win_w, win_h = RESOLUTIONS.get(res_name, RESOLUTIONS[DEFAULT_RES])
        self.root.geometry(f"{win_w}x{win_h}")
        self.root.resizable(False, False)
        self._show_top_menu()
        self.root.mainloop()

    def _clear(self):
        clear_root(self.root)

    def _show_top_menu(self):
        self._clear()
        TopMenuScreen(self.root, self.cfg,
                      on_select_game=self._on_select_game,
                      on_settings=self._show_settings)

    def _show_settings(self):
        self._clear()
        SettingsScreen(self.root, self.cfg,
                       on_back=self._show_top_menu)

    def _on_select_game(self, game_id):
        if game_id == "minesweeper":
            self._show_ms_lobby()
        elif game_id == "reversi":
            self._show_reversi_lobby()
        elif game_id == "horserace":
            self._show_horse_lobby()
        elif game_id == "paint":
            self._show_paint()

    def _show_ms_lobby(self):
        self._clear()
        MinesweeperLobby(self.root, self.cfg,
                         on_start=self._start_minesweeper,
                         on_back=self._show_top_menu)

    def _start_minesweeper(self, cfg, cols, rows, mines, mode):
        self.cfg = cfg
        self._clear()
        GameScreen(self.root, cfg, cols, rows, mines, mode,
                   on_menu=self._show_top_menu)

    def _show_reversi_lobby(self):
        self._clear()
        ReversiLobby(self.root, self.cfg,
                     on_start=self._start_reversi,
                     on_back=self._show_top_menu)

    def _start_reversi(self, cfg, max_vote_sec, tiebreak):
        self.cfg = cfg
        self._clear()
        ReversiGameScreen(self.root, cfg, max_vote_sec, tiebreak,
                          on_menu=self._show_top_menu)

    def _show_horse_lobby(self):
        self._clear()
        HorseLobby(self.root, self.cfg,
                   on_start=self._start_horse,
                   on_back=self._show_top_menu,
                   on_train=self._show_training,
                   on_code=self._show_code_entry)

    def _start_horse(self, cfg, vote_sec, race_count=0):
        self.cfg = cfg
        self._clear()
        HorseRaceScreen(self.root, cfg, vote_sec, race_count,
                        on_menu=self._show_top_menu)

    def _show_paint(self):
        self._clear()
        PaintScreen(self.root, self.cfg,
                    on_menu=self._show_top_menu)

    def _show_training(self):
        self._clear()
        TrainingScreen(self.root, self.cfg,
                       on_back=self._show_horse_lobby,
                       on_race=self._start_horse_with_trained)

    def _show_code_entry(self):
        self._clear()
        CodeEntryScreen(self.root, self.cfg,
                        on_back=self._show_horse_lobby,
                        on_race=self._start_horse_with_trained)

    def _start_horse_with_trained(self, cfg, vote_sec, race_count, trained_horse, trained_list=None):
        self.cfg = cfg
        self._clear()
        HorseRaceScreen(self.root, cfg, vote_sec, race_count,
                        trained_horse=trained_horse,
                        trained_list=trained_list,
                        on_menu=self._show_top_menu)


if __name__ == "__main__":
    App()

# ══════════════════════════════════════════════
#  リバーシ ロビー画面
# ══════════════════════════════════════════════

# ══════════════════════════════════════════════
#  競馬 ロビー画面
# ══════════════════════════════════════════════

# ══════════════════════════════════════════════
#  ペイント画面
# ══════════════════════════════════════════════

# ══════════════════════════════════════════════
#  育成画面
# ══════════════════════════════════════════════


