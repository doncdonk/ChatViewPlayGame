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

# 固定難易度プリセット
PRESET_DIFFICULTIES = {
    "小  9×9   地雷10":  (9,  9,  10),
    "中  16×16  地雷40": (16, 16, 40),
    "大  30×16  地雷99": (30, 16, 99),
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
        root.resizable(False, False)

        make_label(root, "⚙  設定", fg=ACCENT_COL,
                   font=("Courier", 20, "bold")).pack(pady=(24, 4))
        make_label(root, "Twitch connection settings",
                   fg=TEXT_G, font=("Courier", 11)).pack(pady=(0, 20))

        frame = tk.Frame(root, bg=BG)
        frame.pack(padx=36)

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
        self.cfg["channel"] = channel
        self.cfg["token"]   = token
        self.cfg["theme"]   = self.theme_var.get()
        apply_theme(self.cfg["theme"])
        save_config(self.cfg)
        self.on_back()

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
        "ready":   False,
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
        root.resizable(False, False)

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
        root.resizable(False, False)

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
        if not (2 <= cols <= 30 and 2 <= rows <= 30):
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
            self.err_var.set("⚠ Invalid custom values (cols/rows: 2-30, mines: 1+)")
            return

        self.cfg["ms_mode"]       = mode
        self.cfg["ms_difficulty"] = self.diff_var.get()
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

        self.board_w = cols * CELL
        self.board_h = rows * CELL
        self.win_w   = self.board_w + SIDEBAR_W
        self.win_h   = self.board_h + HEADER_H

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
        bx = self.board_w - 112
        return bx, 6, bx + 104, 36

    def _copy_btn_rect(self):
        """サイドバー内のコピーボタン領域"""
        sx = self.board_w
        return sx + 8, self.win_h - 58, self.win_w - 8, self.win_h - 8

    def _cell_at(self, x, y):
        col = x // CELL
        row = (y - HEADER_H) // CELL
        if 0 <= col < self.cols and 0 <= row < self.rows and y > HEADER_H:
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
        cx = col * CELL + CELL // 2
        cy = row * CELL + HEADER_H + CELL // 2

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
                x1 = col * CELL
                y1 = row * CELL + HEADER_H
                x2, y2 = x1 + CELL, y1 + CELL
                cell  = self.ms.get_cell(col, row)
                hover = (self.hover == (col, row))
                tag   = f"cell_{col}_{row}"
                c.delete(tag)

                if cell["open"]:
                    c.create_rectangle(x1,y1,x2,y2,
                        fill=CELL_OPEN, outline=CELL_BORDER, tags=tag)
                    if cell["mine"] and self.ms.game_over:
                        c.create_oval(x1+6,y1+6,x2-6,y2-6,
                            fill=MINE_COL, outline="", tags=tag)
                    elif cell["number"] and cell["number"] > 0:
                        c.create_text(x1+CELL//2, y1+CELL//2,
                            text=str(cell["number"]),
                            fill=NUM_COLORS[cell["number"]],
                            font=("Courier",16,"bold"), tags=tag)
                else:
                    bg = CELL_HOV if hover else CELL_HID
                    c.create_rectangle(x1,y1,x2,y2,
                        fill=bg, outline=CELL_BORDER, tags=tag)
                    if cell["flag"]:
                        c.create_text(x1+CELL//2, y1+CELL//2,
                            text="🚩", font=("Courier",14), tags=tag)
                    else:
                        lbl = chr(ord('A')+col) + str(row+1)
                        c.create_text(x1+4, y1+3, text=lbl, anchor="nw",
                            fill="#6878A8", font=("Courier",11), tags=tag)

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
        c.create_text(self.board_w - 10, 74, text=guide,
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
        sx = self.board_w
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
            bx1, by1 = sx+8, self.win_h-138
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
        bx, by = self.board_w // 2, HEADER_H + self.board_h // 2

        if self.ms.game_over:
            c.create_rectangle(0,HEADER_H,self.board_w,self.win_h,
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
        root.resizable(False, False)

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
RV_CELL      = 56      # 1マスのサイズ
RV_LABEL_W   = 24      # 座標ラベル幅
RV_BOARD_OFF = 8       # 盤面の左上オフセット（盤面枠）
RV_SIDEBAR_W = 280
RV_HEADER_H  = 80
RV_WIN_W     = 8*RV_CELL + RV_BOARD_OFF*2 + RV_LABEL_W*2 + RV_SIDEBAR_W
RV_WIN_H     = 8*RV_CELL + RV_BOARD_OFF*2 + RV_LABEL_W*2 + RV_HEADER_H

class ReversiGameScreen:
    def __init__(self, root, cfg, max_vote_sec, tiebreak, on_menu):
        self.root         = root
        self.cfg          = cfg
        self.max_vote_sec = max_vote_sec
        self.tiebreak     = tiebreak
        self.on_menu      = on_menu

        root.title("ChatViewPlayGame - チャットvsリバーシ")
        root.configure(bg=BG)
        root.resizable(False, False)

        self.canvas = tk.Canvas(root, width=RV_WIN_W, height=RV_WIN_H,
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
        return RV_BOARD_OFF + RV_LABEL_W, RV_HEADER_H + RV_BOARD_OFF + RV_LABEL_W

    def _cell_at(self, mx, my):
        bx, by = self._board_xy()
        col = (mx - bx) // RV_CELL
        row = (my - by) // RV_CELL
        if 0 <= col < 8 and 0 <= row < 8:
            return col, row
        return None, None

    def _menu_btn_rect(self):
        bx = RV_WIN_W - RV_SIDEBAR_W - 116
        return bx, 6, bx+108, 36

    def _copy_btn_rect(self):
        sx = RV_WIN_W - RV_SIDEBAR_W
        return sx+8, RV_WIN_H-58, RV_WIN_W-8, RV_WIN_H-8

    def _sidebar_x(self):
        return RV_WIN_W - RV_SIDEBAR_W

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
        board_px = 8*RV_CELL + RV_BOARD_OFF*2
        c.create_rectangle(0,0,RV_WIN_W,RV_HEADER_H,
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
        c.create_text(cx, 50, text=self.status_msg,
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

        # 盤面背景
        c.create_rectangle(bx-RV_BOARD_OFF, by-RV_BOARD_OFF,
            bx+8*RV_CELL+RV_BOARD_OFF, by+8*RV_CELL+RV_BOARD_OFF,
            fill="#1A3A1A", outline=CELL_BORDER, width=2, tags="rv_board")

        for row in range(8):
            for col in range(8):
                x1 = bx + col*RV_CELL
                y1 = by + row*RV_CELL
                x2, y2 = x1+RV_CELL, y1+RV_CELL
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
                    r = RV_CELL//6
                    cx2 = x1+RV_CELL//2
                    cy2 = y1+RV_CELL//2
                    c.create_oval(cx2-r,cy2-r,cx2+r,cy2+r,
                        fill="#4A9A4A", outline="", tags="rv_board")

                # 石
                stone = self.rv.board[row][col]
                if stone != EMPTY:
                    pad = 6
                    scx = x1+RV_CELL//2
                    scy = y1+RV_CELL//2
                    sr  = RV_CELL//2 - pad
                    col_fill = "#111111" if stone == BLACK else "#EEEEEE"
                    outline_c = "#444444" if stone == BLACK else "#AAAAAA"
                    if is_last:
                        outline_c = ACCENT_COL
                    c.create_oval(scx-sr,scy-sr,scx+sr,scy+sr,
                        fill=col_fill, outline=outline_c, width=2, tags="rv_board")

                # マス内座標
                if stone == EMPTY:
                    coord = chr(65+col) + str(row+1)
                    if is_legal and self.voting:
                        # チャットターン：合法手は白でくっきり強調
                        c.create_text(x1+5, y1+4, text=coord, anchor="nw",
                            fill="#FFFFFF", font=("Courier",11,"bold"), tags="rv_board")
                    elif not is_legal:
                        # 置けないマスは薄く
                        c.create_text(x1+5, y1+4, text=coord, anchor="nw",
                            fill="#3A6A3A", font=("Courier",9), tags="rv_board")
                    # 配信者ターンの合法手マスは丸ヒントのみで座標は非表示

        # ── 外周座標ラベル ──────────────────────
        # 列ラベル（A〜H）上下
        for col in range(8):
            lx = bx + col*RV_CELL + RV_CELL//2
            lbl = chr(65+col)
            # 上
            c.create_text(lx, by - RV_LABEL_W//2,
                text=lbl, fill=ACCENT_COL,
                font=("Courier",13,"bold"), tags="rv_board")
            # 下
            c.create_text(lx, by + 8*RV_CELL + RV_LABEL_W//2,
                text=lbl, fill=ACCENT_COL,
                font=("Courier",13,"bold"), tags="rv_board")

        # 行ラベル（1〜8）左右
        for row in range(8):
            ly = by + row*RV_CELL + RV_CELL//2
            lbl = str(row+1)
            # 左
            c.create_text(bx - RV_LABEL_W//2, ly,
                text=lbl, fill=ACCENT_COL,
                font=("Courier",13,"bold"), tags="rv_board")
            # 右
            c.create_text(bx + 8*RV_CELL + RV_LABEL_W//2, ly,
                text=lbl, fill=ACCENT_COL,
                font=("Courier",13,"bold"), tags="rv_board")

        # ゲームオーバー表示
        if self.rv.game_over:
            board_cx = bx + 4*RV_CELL
            board_cy = by + 4*RV_CELL
            c.create_rectangle(bx+20, board_cy-50, bx+8*RV_CELL-20, board_cy+60,
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

        c.create_rectangle(sx,0,RV_WIN_W,RV_WIN_H,
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
            c.create_rectangle(sx+12, RV_WIN_H-90, sx+12+bar_full, RV_WIN_H-76,
                fill=CELL_HID, outline="", tags="rv_sidebar")
            if bar_now > 0:
                c.create_rectangle(sx+12, RV_WIN_H-90, sx+12+bar_now, RV_WIN_H-76,
                    fill=bar_col, outline="", tags="rv_sidebar")
            c.create_text(sx+RV_SIDEBAR_W//2, RV_WIN_H-100,
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
class App:
    def __init__(self):
        self.root = tk.Tk()
        self.cfg  = load_config()
        apply_theme(self.cfg.get("theme", "NightBlue"))
        _apply_icon(self.root)
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


if __name__ == "__main__":
    App()

# ══════════════════════════════════════════════
#  リバーシ ロビー画面
# ══════════════════════════════════════════════
