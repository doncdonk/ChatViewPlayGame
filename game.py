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

from config import load_config, save_config
from minesweeper import Minesweeper
from twitch_client import TwitchClient
from reversi import Reversi, BLACK, WHITE, EMPTY
from horserace import generate_race, run_race, IconHorseRenderer

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
                   font=("Courier", 10)).pack(pady=(0, 18))

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

        self.twitch = TwitchClient(
            cfg["channel"], cfg["token"],
            on_command=self._on_command,
            on_chat=self._on_chat,
        )
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
        if not channel or not token.startswith("oauth:"):
            self.err_var.set("⚠ Settings not configured")
            return
        self.cfg["rv_vote_sec"]  = self.vote_var.get()
        self.cfg["rv_tiebreak"]  = self.tie_var.get()
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

        # Twitch接続
        self.twitch = TwitchClient(
            cfg["channel"], cfg["token"],
            on_command=self._on_vote,
            on_chat=self._on_chat,
        )
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
        if self.rv.turn == BLACK:
            self.voting    = False
            self.status_msg = "Your turn — click to place"
        else:
            self.voting    = True
            self.vote_timer = float(self.max_vote_sec)
            self.votes     = {}
            self.vote_order = []
            self.status_msg = f"Chat voting...  [{self.max_vote_sec}s]  Space = close"

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
        legal = self.rv.legal_moves(WHITE)
        if not self.votes:
            # 投票なし → ランダムに合法手から選ぶ
            if legal:
                import random as _r
                row, col = _r.choice(legal)
                self.rv.place(row, col)
        else:
            # 最多得票を選ぶ
            if self.tiebreak == "first":
                # 早着順: vote_orderから合法手の最初を選ぶ
                chosen = None
                for rc in self.vote_order:
                    if rc in legal:
                        chosen = rc
                        break
                if chosen is None and legal:
                    chosen = legal[0]
            else:
                # ランダム（同票の場合はランダム）
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
        if self.rv.turn == BLACK and not self.voting and not self.rv.game_over:
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
                if is_legal and self.rv.turn == BLACK and not self.voting:
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
class HorseLobby:
    def __init__(self, root, cfg, on_start, on_back):
        self.root     = root
        self.cfg      = cfg
        self.on_start = on_start
        self.on_back  = on_back

        root.title("ChatViewPlayGame - 競馬")
        root.configure(bg=BG)

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

        bf = tk.Frame(frame, bg=BG)
        bf.pack(fill="x", pady=(14,24))
        make_btn(bf, "◀  戻る", self.on_back).pack(side="left")
        make_btn(bf, "▶  レース開始", self._start,
                 bg=SAFE_COL, fg=BG).pack(side="right")

    def _start(self):
        if not self.cfg.get("channel") or not self.cfg.get("token","").startswith("oauth:"):
            self.err_var.set("⚠ Settings not configured")
            return
        self.cfg["hr_vote_sec"]    = self.vote_var.get()
        self.cfg["hr_auto_next"]   = self.auto_var.get()
        self.cfg["hr_race_count"]  = self.race_count_var.get()
        save_config(self.cfg)
        race_count = int(self.race_count_var.get())
        self.on_start(self.cfg, self.vote_var.get(), race_count)


# ══════════════════════════════════════════════
#  競馬 メイン画面
#  フェーズ: vote → gate → race → goal → result
# ══════════════════════════════════════════════
HR_COLORS = [
    "#FF4466","#4488FF","#44DD88","#FFCC00",
    "#FF8800","#AA44FF","#00CCFF","#FF66AA",
]
HR_LANE_H  = 68   # 1レーンの高さ
HR_INFO_W  = 320  # 左側馬情報パネル幅
HR_FPS     = 30

class HorseRaceScreen:
    PHASES = ["vote", "gate", "race", "goal", "result"]

    def __init__(self, root, cfg, vote_sec, race_count, on_menu):
        self.root     = root
        self.cfg      = cfg
        self.vote_sec   = vote_sec
        self.race_count = race_count   # 0=無限
        self.on_menu    = on_menu

        root.title("ChatViewPlayGame - 競馬")
        root.configure(bg=BG)

        res_name = cfg.get("resolution", DEFAULT_RES)
        self.win_w, self.win_h = RESOLUTIONS.get(res_name, RESOLUTIONS[DEFAULT_RES])

        self.canvas = tk.Canvas(root, width=self.win_w, height=self.win_h,
                                bg=BG, highlightthickness=0)
        self.canvas.pack()

        # レース生成
        self.race    = generate_race(num_horses=8)
        self.horses  = self.race["horses"]
        self.results = None   # run_race後に設定

        # 投票
        self.votes      = {}   # {horse_number: count}
        self.vote_timer = float(vote_sec)
        self.voters     = {}   # {username: horse_number} 1人1票

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

        # 馬描画レンダラー（馬ごとに個別タグ）
        self.renderers = [IconHorseRenderer(f"horse_{i}") for i in range(len(self.horses))]

        # Twitch
        self.twitch = TwitchClient(
            cfg["channel"], cfg["token"],
            on_command=self._on_cmd,
            on_chat=self._on_chat,
        )
        threading.Thread(
            target=lambda: asyncio.run(self.twitch.connect()), daemon=True
        ).start()

        root.bind("<space>", self._on_space)
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<Motion>",   self._on_canvas_motion)
        self.hover_horse   = None   # ホバー中の馬番号
        self.my_vote       = None   # 配信者の投票番号（[配信者]）
        self._vote_rects   = []     # [(num, x1,y1,x2,y2), ...]
        self._result_btn   = None   # 結果画面ボタン座標
        self._final_btn    = None   # 最終結果ボタン座標
        self._transitioning = False  # 遷移中フラグ（2重防止）
        self.auto_next_sec  = float(cfg.get("hr_auto_next", 0))
        self.result_timer   = 0.0
        self.current_race   = 1          # 現在のレース番号
        # 累積成績: {username: {"votes": N, "hits": N}}
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

        self._update_phase(dt)
        self._draw()
        self.root.after(1000 // HR_FPS, self._loop)

    def _update_phase(self, dt):
        if self.phase == "vote":
            self.vote_timer -= dt
            if self.vote_timer <= 0:
                self._end_vote()

        elif self.phase == "gate":
            if self.phase_t >= 3.0:
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

            # 全馬ゴールしたら次フェーズ
            if all(p >= 1.0 for p in self.horse_pos):
                self._start_goal()

        elif self.phase == "goal":
            self.finish_flash = 1.5
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
        self.phase      = "race"
        self.phase_t    = 0.0
        self.results    = run_race(self.horses, self.race["surface"], self.race["distance"])
        self.horse_pos  = [0.0] * len(self.horses)

    def _start_goal(self):
        self.phase        = "goal"
        self.phase_t      = 0.0
        self.finish_flash = 2.0
        # 的中を累積成績に反映
        if self.results:
            winner_num = self.results[0]["horse"]["number"]
            for username, voted_num in self.voters.items():
                if username not in self.cumulative:
                    self.cumulative[username] = {"votes": 0, "hits": 0}
                if voted_num == winner_num:
                    self.cumulative[username]["hits"] += 1

    # ── 入力 ─────────────────────────────────
    def _on_space(self, ev):
        if self.phase == "vote":
            self._end_vote()

    def _on_canvas_click(self, ev):
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

    def _on_canvas_motion(self, ev):
        if self.phase != "vote":
            self.hover_horse = None
            return
        for num, x1, y1, x2, y2 in self._vote_rects:
            if x1 <= ev.x <= x2 and y1 <= ev.y <= y2:
                self.hover_horse = num
                return
        self.hover_horse = None

    def _do_vote(self, username, num):
        """投票処理（チャット・クリック共通）"""
        if username not in self.voters:
            self.voters[username] = num
            self.votes[num] = self.votes.get(num, 0) + 1
            # 累積成績に投票を記録
            if username not in self.cumulative:
                self.cumulative[username] = {"votes": 0, "hits": 0}
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
            self._draw_race()
            self._draw_goal_overlay()
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
        cx_surf = self.win_w//2 - 40
        cx_dist = self.win_w//2 + 30
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
        self.canvas.tag_bind(tag, "<Button-1>", self._check_menu_click)

    def _check_menu_click(self, ev):
        bx = self.win_w - 116
        if bx <= ev.x <= bx+108 and 6 <= ev.y <= 36:
            self._go_menu()

    def _draw_vote(self):
        c = self.canvas
        tag = "hr_main"
        self._draw_header()

        # 左パネル: 馬情報
        panel_h = self.win_h - 70
        c.create_rectangle(0,70,HR_INFO_W,self.win_h,
            fill=SIDEBAR_BG, outline="", tags=tag)
        c.create_line(HR_INFO_W,70,HR_INFO_W,self.win_h,
            fill=CELL_BORDER, width=1, tags=tag)

        y = 82
        c.create_text(HR_INFO_W//2, y, text="出走馬一覧",
            fill=ACCENT_COL, font=("Courier",13,"bold"), tags=tag)
        y += 24

        row_h = (self.win_h - y - 60) // len(self.horses)
        row_h = min(row_h, 72)

        self._vote_rects = []
        for i, h in enumerate(self.horses):
            ry  = y + i * row_h
            col = HR_COLORS[i % len(HR_COLORS)]
            votes_n  = self.votes.get(h["number"], 0)
            is_hover = (self.hover_horse == h["number"])
            is_voted = (self.my_vote == h["number"])

            # クリック領域を記録
            self._vote_rects.append((h["number"], 4, ry, HR_INFO_W-4, ry+row_h-2))

            # 行背景（ホバー・投票済みで色変え）
            if is_voted:
                bg_col  = "#1A3A2A"
                outline = SAFE_COL
            elif is_hover:
                bg_col  = BTN_DARK_H
                outline = ACCENT_COL
            else:
                bg_col  = BTN_DARK
                outline = CELL_BORDER
            c.create_rectangle(4, ry, HR_INFO_W-4, ry+row_h-2,
                fill=bg_col, outline=outline, tags=tag)
            # 馬番カラーバー
            c.create_rectangle(4, ry, 18, ry+row_h-2,
                fill=col, outline="", tags=tag)
            # 馬名・番号
            c.create_text(26, ry+8,
                text=f"{h['number']}番 {h['name']}",
                fill=TEXT_W, anchor="nw", font=("Courier",11,"bold"), tags=tag)
            # ステータス
            stars_spd = "★"*h["speed"]  + "☆"*(5-h["speed"])
            stars_stm = "★"*h["stamina"]+ "☆"*(5-h["stamina"])
            c.create_text(26, ry+26,
                text=f"速{stars_spd} 耐{stars_stm} 調{h['condition']}",
                fill=TEXT_G, anchor="nw", font=("Courier",9), tags=tag)
            # 一言評価
            comment = h.get("comment","")[:28]
            c.create_text(26, ry+42,
                text=comment,
                fill=FLAG_COL, anchor="nw", font=("Courier",8), tags=tag)
            # 投票済みマーク or クリックヒント
            if is_voted:
                c.create_text(HR_INFO_W-10, ry+row_h//2,
                    text="✅ 投票済",
                    fill=SAFE_COL, anchor="e", font=("Courier",10,"bold"), tags=tag)
            else:
                c.create_text(HR_INFO_W-10, ry+row_h//2,
                    text=f"{votes_n}票" + (" ←Click" if is_hover else ""),
                    fill=SAFE_COL if votes_n>0 else TEXT_G,
                    anchor="e", font=("Courier",10,"bold"), tags=tag)

        # 右パネル: 投票状況
        rx = HR_INFO_W + 20
        c.create_text(rx, 90, text="📊 投票状況",
            fill=ACCENT_COL, anchor="nw", font=("Courier",14,"bold"), tags=tag)

        total_votes = sum(self.votes.values()) or 1
        bar_max_w   = self.win_w - HR_INFO_W - 40
        by = 126
        for h in self.horses:
            num   = h["number"]
            cnt   = self.votes.get(num, 0)
            pct   = cnt / total_votes
            col   = HR_COLORS[(num-1) % len(HR_COLORS)]
            bar_w = int(bar_max_w * pct)

            c.create_text(rx, by, text=f"{num}番 {h['name'][:8]}",
                fill=TEXT_W, anchor="nw", font=("Courier",10), tags=tag)
            c.create_rectangle(rx, by+16, rx+bar_max_w, by+28,
                fill=CELL_HID, outline="", tags=tag)
            if bar_w > 0:
                c.create_rectangle(rx, by+16, rx+bar_w, by+28,
                    fill=col, outline="", tags=tag)
            c.create_text(rx+bar_max_w+6, by+22,
                text=f"{cnt}票 ({pct*100:.0f}%)",
                fill=TEXT_G, anchor="w", font=("Courier",9), tags=tag)
            by += 42

        # タイマー
        ratio = max(0, self.vote_timer / self.vote_sec)
        bar_col = SAFE_COL if ratio > 0.4 else FLAG_COL if ratio > 0.15 else MINE_COL
        tw = self.win_w - HR_INFO_W - 40
        ty = self.win_h - 50
        c.create_rectangle(rx, ty, rx+tw, ty+14,
            fill=CELL_HID, outline="", tags=tag)
        if ratio > 0:
            c.create_rectangle(rx, ty, rx+int(tw*ratio), ty+14,
                fill=bar_col, outline="", tags=tag)
        c.create_text(self.win_w//2, ty-16,
            text=f"投票受付中  残り {max(0,self.vote_timer):.0f}秒  [Spaceで締切]",
            fill=bar_col, font=("Courier",12,"bold"), tags=tag)

    def _draw_gate(self):
        c = self.canvas
        tag = "hr_main"
        self._draw_header()

        cy = self.win_h // 2
        c.create_text(self.win_w//2, cy - 60,
            text="🏇 出走準備",
            fill=ACCENT_COL, font=("Courier",24,"bold"), tags=tag)

        # ゲート描画
        gate_x  = self.win_w // 2 - 200
        lane_h  = 44
        n       = len(self.horses)
        total_h = n * lane_h
        start_y = cy - total_h // 2

        # ゲートオープン演出（phase_t > 1.5 で開く）
        opened = self.phase_t > 1.5

        for i, h in enumerate(self.horses):
            ry  = start_y + i * lane_h
            col = HR_COLORS[(h['number']-1) % len(HR_COLORS)]

            # レーン背景
            c.create_rectangle(gate_x-10, ry, self.win_w-40, ry+lane_h-2,
                fill=CELL_HID if not opened else "#1A2A1A",
                outline=CELL_BORDER, tags=tag)

            # 馬番
            c.create_text(gate_x, ry+lane_h//2,
                text=f"{h['number']}", fill=col,
                font=("Courier",14,"bold"), tags=tag)

            # 馬（ゲート前に待機）
            hx = gate_x + 60 if not opened else gate_x + 60 + int(self.phase_t * 80)
            self.renderers[i].clear(c)
            self.renderers[i].draw(c, hx, ry+lane_h//2, col,
                                   frame=self.anim_frame if opened else 0,
                                   scale=0.7)

            # 馬名
            c.create_text(gate_x - 80, ry+lane_h//2,
                text=h["name"][:8], fill=TEXT_W,
                anchor="e", font=("Courier",10), tags=tag)

            # ゲートバー（開く演出）
            if not opened:
                c.create_rectangle(gate_x+40, ry, gate_x+46, ry+lane_h-2,
                    fill="#888888", outline="", tags=tag)

        if opened:
            c.create_text(self.win_w//2, cy + total_h//2 + 30,
                text="ゲートオープン！",
                fill=FLAG_COL, font=("Courier",20,"bold"), tags=tag)

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
            self.renderers[i].clear(c)
            self.renderers[i].draw(c, hx, ry+lane_h//2, col,
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

    def _draw_goal_overlay(self):
        c = self.canvas
        tag = "hr_overlay"
        if not self.results:
            return
        winner = next((r for r in self.results if r["rank"]==1), None)
        if not winner:
            return

        # フラッシュ
        if self.finish_flash > 0:
            alpha_stip = "gray75" if self.finish_flash > 1.0 else "gray50"
            c.create_rectangle(0,0,self.win_w,self.win_h,
                fill=FLAG_COL, outline="", stipple=alpha_stip, tags=tag)

        cx = self.win_w // 2
        cy = self.win_h // 2
        c.create_rectangle(cx-260,cy-60,cx+260,cy+60,
            fill=BG, outline=FLAG_COL, width=3, tags=tag)
        col = HR_COLORS[(winner["horse"]["number"]-1) % len(HR_COLORS)]
        c.create_text(cx, cy-20,
            text=f"🏆 {winner['horse']['number']}番  {winner['horse']['name']}",
            fill=col, font=("Courier",22,"bold"), tags=tag)
        c.create_text(cx, cy+20,
            text="ゴール！",
            fill=FLAG_COL, font=("Courier",16,"bold"), tags=tag)

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
                                  key=lambda x: (-x[1]["hits"], -x[1]["votes"]))
                medals_r = ["🥇","🥈","🥉"] + ["  " for _ in range(20)]
                for ri, (uname, stat) in enumerate(ranked):
                    if ry2 + 18 > rank_bottom:
                        remaining = len(ranked) - ri
                        if remaining > 0:
                            c.create_text(cx, ry2,
                                text=f"他{remaining}人...",
                                fill=TEXT_G, font=("Courier",9), tags=tag)
                        break
                    medal = medals_r[ri]
                    hits  = stat["hits"]
                    votes = stat["votes"]
                    col_u = FLAG_COL if ri==0 else (ACCENT_COL if ri==1 else
                            (SAFE_COL if ri==2 else TEXT_W))
                    c.create_text(cx - 160, ry2,
                        text=f"{medal} {uname[:14]}",
                        fill=col_u, anchor="w", font=("Courier",10,"bold"), tags=tag)
                    c.create_text(cx + 100, ry2,
                        text=f"{hits}/{votes}票的中",
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
                            key=lambda x: (-x[1]["hits"], -x[1]["votes"]))
            medals_f = ["🥇","🥈","🥉"] + [f"{i}位" for i in range(4, 50)]
            row_h_f  = min(54, (self.win_h - 160) // max(len(ranked), 1))
            sy       = 100

            for ri, (uname, stat) in enumerate(ranked):
                ry     = sy + ri * row_h_f
                if ry + row_h_f > self.win_h - 80:
                    remaining = len(ranked) - ri
                    c.create_text(cx, ry,
                        text=f"他{remaining}人...",
                        fill=TEXT_G, font=("Courier",11), tags=tag)
                    break
                medal  = medals_f[ri]
                hits   = stat["hits"]
                votes  = stat["votes"]
                pct    = int(hits/votes*100) if votes else 0
                col_u  = FLAG_COL if ri==0 else (ACCENT_COL if ri==1 else
                         (SAFE_COL if ri==2 else TEXT_W))

                if ri < 3:
                    c.create_rectangle(cx-280, ry, cx+280, ry+row_h_f-2,
                        fill=BTN_DARK, outline=col_u, tags=tag)

                c.create_text(cx-270, ry+row_h_f//2,
                    text=medal, fill=col_u, anchor="w",
                    font=("Courier",14,"bold"), tags=tag)
                c.create_text(cx-220, ry+row_h_f//2,
                    text=uname[:16], fill=col_u, anchor="w",
                    font=("Courier",13,"bold" if ri<3 else "normal"), tags=tag)
                c.create_text(cx+80, ry+row_h_f//2,
                    text=f"{hits} / {votes}票",
                    fill=col_u, anchor="w", font=("Courier",12), tags=tag)
                c.create_text(cx+200, ry+row_h_f//2,
                    text=f"({pct}%)",
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
        self.race         = generate_race(num_horses=8)
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
                   on_back=self._show_top_menu)

    def _start_horse(self, cfg, vote_sec, race_count=0):
        self.cfg = cfg
        self._clear()
        HorseRaceScreen(self.root, cfg, vote_sec, race_count,
                        on_menu=self._show_top_menu)


if __name__ == "__main__":
    App()

# ══════════════════════════════════════════════
#  リバーシ ロビー画面
# ══════════════════════════════════════════════

# ══════════════════════════════════════════════
#  競馬 ロビー画面
# ══════════════════════════════════════════════
