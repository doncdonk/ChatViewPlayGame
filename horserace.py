"""
競馬ロジック v2
- 馬名・騎手名・レース名・コース生成
- ステータス・調子・相性ボーナス生成
- オッズ計算（全ステータス考慮）
- レース結果計算
- 描画抽象クラス
"""
import random
import math

# ── 馬名ワードテーブル（最長8文字に統一） ──────
# PREFIX最長4文字 + SUFFIX最長4文字 = 最大8文字
PREFIX = [
    "シン","メイ","ダイ","サン","フジ","キング","クイーン",
    "レッド","ブルー","スカイ","ゴール","スター","ソード",
    "ドリーム","ライジング"[:4],  # 4文字上限
]
PREFIX = [p[:4] for p in PREFIX]  # 上限4文字

SUFFIX = [
    "ボルト","フレア","スター","ウイング"[:4],"ストーム"[:4],"ブレイズ"[:4],
    "ライト","ランナー"[:4],"ビート","シャイン"[:4],"フォース"[:4],"ブレード"[:4],
    "ホーク","アロー","ヒーロー"[:4],"クロス","バード","ウェーブ"[:4],
    "ダッシュ"[:4],"ソウル","ハート","ドーン",
]
SUFFIX = [s[:4] for s in SUFFIX]

MAX_HORSE_NAME = 8  # PREFIX最大4 + SUFFIX最大4

# ── 騎手名ワードテーブル ───────────────────────
FOREIGN_JOCKEYS = [
    "ルメール","デムーロ","シュタルケ","モレイラ","ビュイック",
    "レーン","フォード","マーカンド","ドイル","ヘファーナン",
]

JOCKEY_FIRST = ["田中","佐藤","鈴木","高橋","伊藤","渡辺","山本","中村","小林","加藤",
                "松本","井上","木村","林","清水","山田","石川","橋本","阿部","長谷川"]
JOCKEY_LAST  = ["剛","誠","翔","大輝","健","勇","颯","輝","蓮","陸",
                "太郎","次郎","一馬","竜也","昌弘","義弘","正樹","和也","雅人","浩二"]

# ── レース名ワードテーブル ──────────────────────
RACE_PLACE  = ["東京","京都","阪神","中山","札幌","函館","新潟","小倉","中京","福島"]
RACE_SUFFIX = ["記念","ステークス","カップ","賞","トロフィー","チャレンジカップ","ターフ"]
RACE_GRADE  = ["G1","G2","G3","OP","L"]

# ── レースグレード定義 ──────────────────────────────
# stat_min/max: ランダム馬のステータス範囲(1〜10スケール)
# jockey_min/max: 騎手技術範囲
# suffixes: このグレードで使うレース名サフィックス
GRADE_DEFS = {
    "未勝利": {
        "stat_min": 1, "stat_max": 3,
        "jockey_min": 1, "jockey_max": 2,
        "suffixes": ["新馬戦", "未勝利戦"],
        "grades":   ["未勝利"],
        "label":    "未勝利  ★☆☆☆☆  入門",
    },
    "G3": {
        "stat_min": 1, "stat_max": 5,
        "jockey_min": 1, "jockey_max": 3,
        "suffixes": ["賞", "特別", "オープン"],
        "grades":   ["G3", "L"],
        "label":    "G3      ★★☆☆☆  標準",
    },
    "G2": {
        "stat_min": 3, "stat_max": 7,
        "jockey_min": 2, "jockey_max": 4,
        "suffixes": ["ステークス", "チャレンジカップ", "トロフィー"],
        "grades":   ["G2"],
        "label":    "G2      ★★★☆☆  やや難",
    },
    "G1": {
        "stat_min": 5, "stat_max": 9,
        "jockey_min": 3, "jockey_max": 5,
        "suffixes": ["記念", "カップ", "ターフ"],
        "grades":   ["G1"],
        "label":    "G1      ★★★★☆  難しい",
    },
    "特別G1": {
        "stat_min": 7, "stat_max": 10,
        "jockey_min": 4, "jockey_max": 5,
        "suffixes": ["記念", "カップ", "グランプリ"],
        "grades":   ["G1"],
        "label":    "特別G1  ★★★★★  最高峰",
    },
}
DEFAULT_GRADE = "G3"

# ── コース・距離 ────────────────────────────────
COURSES = {
    "芝":    [1200, 1400, 1600, 1800, 2000, 2200, 2400, 3000, 3200],
    "ダート": [1000, 1200, 1400, 1700, 1800, 2100, 2400],
}

# ── 調子 ────────────────────────────────────────
CONDITIONS = [
    ("◎", 1.15, "絶好調"),
    ("○", 1.05, "好調"),
    ("△", 0.95, "平凡"),
    ("×", 0.80, "不調"),
]
CONDITION_WEIGHTS = [15, 35, 35, 15]

# ── 馬場適性 ────────────────────────────────────
APTITUDE = ["◎", "○", "△"]

# ── 騎手×馬 相性テーブル ─────────────────────────
AFFINITY_LABELS = {
    2: ("◎", 1.15, "相性抜群"),
    1: ("○", 1.05, "相性良好"),
    0: ("△", 1.00, "普通"),
   -1: ("×", 0.92, "相性難"),
}


def make_horse_name():
    name = random.choice(PREFIX) + random.choice(SUFFIX)
    return name[:MAX_HORSE_NAME]


def make_jockey_name():
    # 10%の確率で外国人騎手
    if random.random() < 0.10:
        return random.choice(FOREIGN_JOCKEYS)
    return random.choice(JOCKEY_FIRST)  # 苗字のみ


def make_race_name():
    place  = random.choice(RACE_PLACE)
    suffix = random.choice(RACE_SUFFIX)
    grade  = random.choice(RACE_GRADE)
    return f"{place}{suffix} ({grade})"


def make_course():
    surface  = random.choices(list(COURSES.keys()), weights=[70, 30])[0]
    distance = random.choice(COURSES[surface])
    return surface, distance


def make_jockey(skill_min=1, skill_max=5):
    name  = make_jockey_name()
    skill = random.randint(skill_min, skill_max)
    style = random.choice(["逃げ","先行","差し","追込"])
    return {"name": name, "skill": skill, "style": style}


def make_horse(number, surface, jockey, stat_min=1, stat_max=5):
    name    = make_horse_name()
    speed   = random.randint(stat_min, stat_max)
    stamina = random.randint(stat_min, stat_max)
    corner  = random.randint(stat_min, stat_max)
    apt_turf  = random.choices(APTITUDE, weights=[50,35,15])[0] if surface=="芝" \
                else random.choices(APTITUDE, weights=[15,35,50])[0]
    apt_dirt  = random.choices(APTITUDE, weights=[50,35,15])[0] if surface=="ダート" \
                else random.choices(APTITUDE, weights=[15,35,50])[0]
    cond_sym, cond_mult, cond_label = random.choices(CONDITIONS, weights=CONDITION_WEIGHTS)[0]

    # 騎手との相性（-1, 0, 1, 2）
    affinity_val = random.choices([-1, 0, 1, 2], weights=[10, 40, 35, 15])[0]
    aff_sym, aff_mult, aff_label = AFFINITY_LABELS[affinity_val]

    # 馬の毛色（茶色 or 白）
    coat = random.choice(["brown", "white"])

    mental       = random.randint(stat_min, stat_max)
    adaptability = random.randint(stat_min, stat_max)
    return {
        "number":       number,
        "name":         name,
        "speed":        speed,
        "stamina":      stamina,
        "corner":       corner,
        "mental":       mental,
        "adaptability": adaptability,
        "apt_turf":   apt_turf,
        "apt_dirt":   apt_dirt,
        "condition":  cond_sym,
        "cond_mult":  cond_mult,
        "cond_label": cond_label,
        "jockey":     jockey,
        "affinity":   aff_sym,
        "aff_mult":   aff_mult,
        "aff_label":  aff_label,
        "coat":       coat,
    }


def aptitude_score(apt):
    return {"◎": 1.2, "○": 1.0, "△": 0.75}.get(apt, 1.0)


def calc_base_score(horse, surface, distance):
    spd = horse["speed"]
    stm = horse["stamina"]
    cor = horse["corner"]
    jsk = horse["jockey"]["skill"]

    if distance <= 1400:
        score = spd * 2.0 + stm * 0.8 + cor * 0.5
    elif distance <= 1800:
        score = spd * 1.5 + stm * 1.2 + cor * 0.8
    elif distance <= 2200:
        score = spd * 1.0 + stm * 1.8 + cor * 1.0
    else:
        score = spd * 0.7 + stm * 2.2 + cor * 0.8

    # 騎手スキル補正（+最大10%）
    score *= (1.0 + (jsk - 1) * 0.025)

    # 馬場適性補正
    apt = horse["apt_turf"] if surface == "芝" else horse["apt_dirt"]
    score *= aptitude_score(apt)

    # 調子補正
    score *= horse["cond_mult"]

    # 騎手×馬相性補正
    score *= horse["aff_mult"]

    # ── 育成馬のコンボ特性ボーナス ──
    tb = horse.get("trait_bonus", {})
    if tb:
        # 全体ボーナス
        if "all_bonus" in tb:
            score *= tb["all_bonus"]
        # 距離別ボーナス
        if "speed_race" in tb and distance <= 1800:
            score *= tb["speed_race"]
        if "stamina_race" in tb and distance >= 2000:
            score *= tb["stamina_race"]
        # 馬場別ボーナス
        if "turf_bonus" in tb and surface == "芝":
            score *= tb["turf_bonus"]
        if "dirt_bonus" in tb and surface == "ダート":
            score *= tb["dirt_bonus"]
        # コンディション保護（不調時の減少を緩和）
        if tb.get("cond_protect") and horse["cond_mult"] < 1.0:
            score /= horse["cond_mult"]          # 一旦戻す
            score *= max(0.95, horse["cond_mult"])  # 軽微な減少に
        # 幸運バイアス（ランダムブレをプラス方向へ）
        if "luck_bias" in tb:
            score *= (1.0 + tb["luck_bias"])

    return score


def calc_odds(horses, surface, distance):
    """
    全ステータスを考慮したオッズを計算
    returns: {horse_number: odds_float}
    """
    scores = {h["number"]: calc_base_score(h, surface, distance) for h in horses}
    total  = sum(scores.values())
    # 勝率に変換してオッズを計算（控除率15%を設定）
    deduction = 0.85
    odds = {}
    for num, score in scores.items():
        win_rate = score / total
        raw_odds = deduction / win_rate
        # 切り上げて0.1刻みに
        odds[num] = max(1.1, round(raw_odds * 10) / 10)
    return odds


def run_race(horses, surface, distance):
    results = []
    for h in horses:
        base   = calc_base_score(h, surface, distance)
        rand   = random.uniform(0.80, 1.20)
        final  = base * rand
        results.append((h, final))

    results.sort(key=lambda x: -x[1])

    scores = [r[1] for r in results]
    mn, mx = min(scores), max(scores)
    rng    = mx - mn if mx != mn else 1.0

    ranked = []
    for rank, (horse, score) in enumerate(results):
        norm = (score - mn) / rng
        ranked.append({
            "rank":  rank + 1,
            "horse": horse,
            "score": score,
            "norm":  norm,
        })
    return ranked


# ── コメント生成（バリエーション強化版） ──────────
COMMENT_TEMPLATES_STRONG = [
    "実力最上位、素直に信頼",
    "文句なしの本命候補",
    "総合力が抜けており外せない",
    "能力値トップ、信頼度高い",
]
COMMENT_TEMPLATES_WEAK = [
    "実力差あり、大穴狙いか",
    "厳しい条件、激走あるか",
    "苦しい戦い、展開頼み",
    "前走大敗、変わり身期待",
]
COMMENT_COND_GOOD = [
    "絶好調の今、狙い目",
    "状態は上々、今日が勝負",
    "仕上がり抜群、買い時",
]
COMMENT_COND_BAD = [
    "調子に難、今回は静観か",
    "体調面に不安、割引必要",
    "状態下降気味で信頼薄",
]
COMMENT_DIST_GOOD = [
    "距離は絶好の条件",
    "この距離は得意舞台",
    "距離適性◎で力を出せる",
]
COMMENT_DIST_BAD = [
    "距離がカギ、折り合い注意",
    "距離不安、消耗戦は厳しい",
]
COMMENT_SURF_GOOD = [
    "馬場適性は申し分なし",
    "得意の馬場でベスト発揮",
]
COMMENT_SURF_BAD = [
    "馬場が苦手、大幅割引",
    "不得意馬場で苦戦必至",
]
COMMENT_JOCKEY_AFF = [
    "名手とのコンビで上積み期待",
    "騎手との相性も良く怖い",
]
COMMENT_JOCKEY_BAD = [
    "騎手との相性に不安あり",
    "コンビ面での減点要素",
]
COMMENT_MID = [
    "展開次第で一発も",
    "人気薄で警戒必要",
    "混戦なら浮上の余地",
    "実力は中位、侮れない",
    "堅実な走りが持ち味",
]


def make_comment(horse, surface, distance):
    spd = horse["speed"]
    stm = horse["stamina"]
    apt = horse["apt_turf"] if surface == "芝" else horse["apt_dirt"]
    cond = horse["condition"]
    aff  = horse["affinity"]
    total = spd + stm + horse["corner"] + horse["jockey"]["skill"]

    parts = []

    # 総合力コメント
    if total >= 16:
        parts.append(random.choice(COMMENT_TEMPLATES_STRONG))
    elif total <= 9:
        parts.append(random.choice(COMMENT_TEMPLATES_WEAK))

    # 調子コメント
    if cond == "◎":
        parts.append(random.choice(COMMENT_COND_GOOD))
    elif cond == "×":
        parts.append(random.choice(COMMENT_COND_BAD))

    # 距離適性
    if distance <= 1400 and spd >= 4:
        parts.append(random.choice(COMMENT_DIST_GOOD))
    elif distance >= 2400 and stm >= 4:
        parts.append(random.choice(COMMENT_DIST_GOOD))
    elif distance >= 2400 and stm <= 2:
        parts.append(random.choice(COMMENT_DIST_BAD))

    # 馬場適性
    if apt == "◎":
        parts.append(random.choice(COMMENT_SURF_GOOD))
    elif apt == "△":
        parts.append(random.choice(COMMENT_SURF_BAD))

    # 騎手相性
    if aff == "◎":
        parts.append(random.choice(COMMENT_JOCKEY_AFF))
    elif aff == "×":
        parts.append(random.choice(COMMENT_JOCKEY_BAD))

    if not parts:
        parts.append(random.choice(COMMENT_MID))

    # 最大2つ選んで返す
    selected = random.sample(parts, min(2, len(parts)))
    return "。".join(selected)


def generate_race(num_horses=8, grade_key=None):
    """
    grade_key: GRADE_DEFS のキー（None のときは DEFAULT_GRADE）
    """
    gkey  = grade_key if grade_key in GRADE_DEFS else DEFAULT_GRADE
    gdef  = GRADE_DEFS[gkey]
    smin  = gdef["stat_min"]
    smax  = gdef["stat_max"]
    jmin  = gdef["jockey_min"]
    jmax  = gdef["jockey_max"]

    surface, distance = make_course()

    # グレードに応じたレース名
    place   = random.choice(RACE_PLACE)
    suffix  = random.choice(gdef["suffixes"])
    grade   = random.choice(gdef["grades"])
    race_name = f"{place}{suffix}  [{grade}]"

    jockeys = [make_jockey(skill_min=jmin, skill_max=jmax) for _ in range(num_horses)]
    horses  = [make_horse(i+1, surface, jockeys[i],
                           stat_min=smin, stat_max=smax)
               for i in range(num_horses)]

    for h in horses:
        h["comment"] = make_comment(h, surface, distance)

    odds = calc_odds(horses, surface, distance)
    return {
        "name":     race_name,
        "surface":  surface,
        "distance": distance,
        "horses":   horses,
        "odds":     odds,
        "grade":    gkey,
    }


# ── スプライト切り出し座標 ────────────────────────
# 800x600の画像から各馬をクロップする座標 (x1,y1,x2,y2)
SPRITE_CROPS = {
    1: (0,   0,   400, 200),
    2: (400, 0,   800, 200),
    3: (0,   200, 266, 400),
    4: (266, 200, 533, 400),
    5: (533, 200, 800, 400),
    6: (0,   400, 266, 600),
    7: (266, 400, 533, 600),
    8: (533, 400, 800, 600),
}

def load_horse_sprites(img_dir, target_h):
    """
    スプライト画像を切り出し・透過・反転・リサイズしてPhotoImageを返す
    returns: {("brown", num): PhotoImage, ("white", num): PhotoImage}
             失敗時は None
    """
    import os
    try:
        from PIL import Image, ImageTk
    except ImportError:
        return None

    path_brown = os.path.join(img_dir, "rdesign_19914.png")
    path_white = os.path.join(img_dir, "rdesign_19916.png")

    if not os.path.exists(path_brown) or not os.path.exists(path_white):
        return None

    try:
        sheets = {
            "brown": Image.open(path_brown).convert("RGBA"),
            "white": Image.open(path_white).convert("RGBA"),
        }
    except Exception:
        return None

    import numpy as np
    result = {}

    for coat, sheet in sheets.items():
        arr = np.array(sheet)
        # 黒背景透過（RGB合計30以下をα=0）
        mask = (arr[:,:,0].astype(int)
              + arr[:,:,1].astype(int)
              + arr[:,:,2].astype(int)) <= 30
        arr[mask, 3] = 0
        sheet_tr = Image.fromarray(arr, "RGBA")

        for num, (x1, y1, x2, y2) in SPRITE_CROPS.items():
            crop = sheet_tr.crop((x1, y1, x2, y2))
            # 左右反転（右向きに）
            crop = crop.transpose(Image.FLIP_LEFT_RIGHT)
            # リサイズ（アスペクト比維持）
            ratio    = target_h / crop.height
            target_w = int(crop.width * ratio)
            crop     = crop.resize((target_w, target_h), Image.LANCZOS)
            result[(coat, num)] = ImageTk.PhotoImage(crop)

    return result if result else None


def load_gate_image(img_dir, win_w, win_h):
    """ゲート背景画像を読み込んでPhotoImageを返す。失敗時はNone"""
    import os
    try:
        from PIL import Image, ImageTk
    except ImportError:
        return None

    path = os.path.join(img_dir, "rdesign_19917.png")
    if not os.path.exists(path):
        return None

    try:
        img = Image.open(path).convert("RGB")
        img = img.resize((win_w, win_h), Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None


# ── 描画抽象クラス ────────────────────────────────
class HorseRenderer:
    def draw(self, canvas, x, y, color, frame=0, scale=1.0):
        raise NotImplementedError
    def clear(self, canvas):
        pass


class IconHorseRenderer(HorseRenderer):
    def __init__(self, tag_prefix):
        self.tag = tag_prefix

    def draw(self, canvas, x, y, color, frame=0, scale=1.0):
        tag = self.tag
        s   = scale
        canvas.create_oval(
            x-22*s, y-10*s, x+22*s, y+10*s,
            fill=color, outline="", tags=tag)
        canvas.create_polygon(
            x+14*s, y-8*s, x+24*s, y-22*s,
            x+32*s, y-18*s, x+20*s, y-4*s,
            fill=color, outline="", tags=tag)
        canvas.create_oval(
            x+22*s, y-30*s, x+38*s, y-14*s,
            fill=color, outline="", tags=tag)
        canvas.create_polygon(
            x+28*s, y-30*s, x+26*s, y-38*s,
            x+31*s, y-30*s,
            fill=color, outline="", tags=tag)
        leg_offset = [0, 4, 0, -4][frame % 4]
        legs = [
            (x-14*s, y+10*s, x-14*s, y+26*s+leg_offset),
            (x- 4*s, y+10*s, x- 4*s, y+26*s-leg_offset),
            (x+ 6*s, y+10*s, x+ 6*s, y+26*s+leg_offset),
            (x+16*s, y+10*s, x+16*s, y+26*s-leg_offset),
        ]
        for lx1,ly1,lx2,ly2 in legs:
            canvas.create_line(lx1,ly1,lx2,ly2,
                fill=color, width=max(2,int(3*s)), tags=tag)
        canvas.create_line(
            x+16*s, y-10*s, x+24*s, y-24*s,
            fill="#FFFFFF", width=max(1,int(2*s)), tags=tag)
        canvas.create_oval(
            x+30*s, y-26*s, x+34*s, y-22*s,
            fill="#000000", outline="", tags=tag)

    def clear(self, canvas):
        canvas.delete(self.tag)

# ══════════════════════════════════════════════
#  文字実況生成
# ══════════════════════════════════════════════

# ── フェーズ別テンプレート ──────────────────────
_C_GATE_WAIT = [
    "各馬ゲートに収まった。さあスタートを待つ！",
    "今日のレースはいよいよ始まる！",
    "好スタートを切れるか、注目の一戦だ！",
]
_C_GATE_OPEN = [
    "ゲートオープン！{lead}が飛び出した！",
    "スタート！{lead}がいい出だし！",
    "一斉にスタート！{lead}が先頭に立つ！",
    "ゲート解放！{lead}がいきなり前へ！",
]
_C_GATE_SLOW = [
    "{slow}がやや出遅れた！挽回なるか！",
    "{slow}、スタートで後手を踏んだ！",
]

_C_EARLY = [   # pos 0〜0.30
    "{lead}が先頭、{second}が続く！",
    "前半は{lead}がリード、まだまだ序盤だ！",
    "{lead}が飛ばす！ペースはどうか！",
    "序盤から{lead}が積極的に前を主張！",
    "{second}が{lead}を追う展開！",
]
_C_MID = [     # pos 0.30〜0.60
    "中間点！{lead}が先頭、{second}と{gap}差！",
    "{lead}、まだ脚がある！",
    "ここで{rising}が上がってきた！",
    "{lead}が粘る！{second}が迫る！",
    "レースは折り返し！{lead}がリード！",
    "{lead}と{second}、並んで直線を目指す！",
]
_C_LATE = [    # pos 0.60〜0.90
    "直線に入った！{lead}が抜け出す！",
    "{lead}、脚色が違う！これは決まりか！",
    "{second}が猛追！{lead}に並びかける！",
    "残り僅か！{lead}か！{second}か！",
    "{lead}が先頭！ゴールまであとわずか！",
    "{rising}がごぼう抜き！一体何位まで上がるか！",
]
_C_FINAL = [   # pos 0.90〜
    "ゴール前！{lead}が先頭で突っ込む！",
    "{lead}、粘れ！{second}が迫ってきた！",
    "あとわずか！{lead}か！{second}か！",
    "最後の直線！{lead}が力を振り絞る！",
]
_C_GOAL = [
    "{winner}がゴールイン！見事な走りだ！",
    "{winner}が先着！{winner}の勝利！",
    "1着は{winner}！強い走りを見せた！",
    "{winner}、ゴール！この馬が一番強かった！",
]
_C_UPSET = [
    "これは波乱！{winner}がまさかの先頭！",
    "大穴{winner}が先頭でゴール！信じられない！",
    "{winner}、大逆転！誰が予想しただろうか！",
]
_C_FAVORITE = [
    "本命{winner}が貫録の勝利！",
    "{winner}、さすがの強さだ！順当な結果！",
    "人気通り！{winner}がきっちり仕事をした！",
]
_C_TRAINED = [
    "育てた{winner}が勝利！この喜びはひとしおだ！",
    "{winner}、育成の成果を見せた！",
    "我が馬{winner}が先頭でゴール！素晴らしい！",
]
_C_TIRED = [
    "{horse}、脚が上がってきた！苦しい！",
    "{horse}が失速！後続に交わされる！",
]
_C_COND_GOOD = [
    "絶好調の{horse}、まだ余裕の走りだ！",
    "{horse}、今日は状態がいい！",
]
_C_TRAIT = {
    "快速型":    ["{horse}の快速が炸裂する！"],
    "鉄人":      ["{horse}、スタミナが切れない！"],
    "芝の帝王":  ["{horse}、芝で本領発揮か！"],
    "孤高の怪物":["{horse}、圧倒的な強さを見せる！"],
    "末脚怪物":  ["{horse}、末脚が炸裂！後ろから来る！"],
}

def _horse_name(h):
    return h["name"]

def make_commentary(horses, positions, surface, distance,
                    phase, phase_t, prev_rank, odds,
                    rng_seed=0):
    """
    現在のレース状況から実況テキストを1本生成して返す。
    返り値: str  （生成できない場合は None）

    horses    : レース馬リスト
    positions : horse_pos リスト（0.0〜1.0）
    phase     : "gate" / "race" / "goal"
    phase_t   : フェーズ内経過秒
    prev_rank : 前回の順位リスト（horse index順）、初回は None
    odds      : {horse_number: float}
    rng_seed  : ランダム選択用シード
    """
    import random as _r
    rng = _r.Random(rng_seed)

    n = len(horses)
    if n == 0:
        return None

    # ── gate フェーズ ──
    if phase == "gate":
        if phase_t < 1.5:
            return rng.choice(_C_GATE_WAIT)
        # ゲートオープン直後: 先頭に立ちそうな馬（速度が高い）
        fast = max(horses, key=lambda h: h.get("speed", 1))
        slow_candidates = sorted(horses, key=lambda h: h.get("speed",1))[:2]
        slow = rng.choice(slow_candidates)
        if rng.random() < 0.5:
            return rng.choice(_C_GATE_OPEN).format(lead=_horse_name(fast))
        else:
            return rng.choice(_C_GATE_SLOW).format(slow=_horse_name(slow))

    # ── race フェーズ ──
    if phase == "race" and positions:
        # 現在の順位（positionで降順ソート）
        order = sorted(range(n), key=lambda i: -positions[i])
        lead_h   = horses[order[0]]
        second_h = horses[order[1]] if n > 1 else lead_h
        lead_pos = positions[order[0]]

        # ギャップ
        gap_raw = positions[order[0]] - positions[order[1]] if n > 1 else 0
        if gap_raw < 0.05:
            gap_str = "ハナ差"
        elif gap_raw < 0.10:
            gap_str = "半馬身"
        elif gap_raw < 0.20:
            gap_str = "1馬身"
        else:
            gap_str = "大きな差"

        # 順位変動馬（前回と比べて上昇した馬）
        rising_h = None
        if prev_rank:
            for new_pos_idx, horse_idx in enumerate(order):
                old_pos_idx = prev_rank.index(horse_idx) if horse_idx in prev_rank else new_pos_idx
                if new_pos_idx < old_pos_idx - 1:
                    rising_h = horses[horse_idx]
                    break

        fmt = dict(
            lead   = _horse_name(lead_h),
            second = _horse_name(second_h),
            gap    = gap_str,
            rising = _horse_name(rising_h) if rising_h else _horse_name(second_h),
        )

        # 疲労/好調チェック（育成馬）
        if rng.random() < 0.15:
            for h in horses:
                if h.get("condition") == "◎":
                    return rng.choice(_C_COND_GOOD).format(horse=_horse_name(h))
            for h in horses:
                if h.get("condition") == "×" and positions[horses.index(h)] < 0.5:
                    return rng.choice(_C_TIRED).format(horse=_horse_name(h))

        # 特性コメント（育成馬のみ、低確率）
        if rng.random() < 0.12:
            for h in horses:
                traits = h.get("traits", [])
                for trait_name, msgs in _C_TRAIT.items():
                    if trait_name in traits:
                        return rng.choice(msgs).format(horse=_horse_name(h))

        # 位置によってテンプレートを選ぶ
        if lead_pos < 0.30:
            tmpl = rng.choice(_C_EARLY)
        elif lead_pos < 0.60:
            tmpl = rng.choice(_C_MID)
        elif lead_pos < 0.90:
            # 直線: 順位変動があれば rising 優先
            if rising_h and rng.random() < 0.4:
                tmpl = "{rising}がごぼう抜き！一体何位まで上がるか！"
            else:
                tmpl = rng.choice(_C_LATE)
        else:
            tmpl = rng.choice(_C_FINAL)

        return tmpl.format(**fmt)

    # ── goal フェーズ ──
    if phase == "goal":
        if not horses:
            return None
        winner = horses[0]  # 呼び出し側で1着を渡す想定
        winner_odds = odds.get(winner["number"], 5.0)
        is_trained  = winner.get("is_trained", False)

        if is_trained:
            return rng.choice(_C_TRAINED).format(winner=_horse_name(winner))
        elif winner_odds <= 3.0:
            return rng.choice(_C_FAVORITE).format(winner=_horse_name(winner))
        elif winner_odds >= 10.0:
            return rng.choice(_C_UPSET).format(winner=_horse_name(winner))
        else:
            return rng.choice(_C_GOAL).format(winner=_horse_name(winner))

    return None



class ImageHorseRenderer(HorseRenderer):
    """画像スプライトを使った描画"""
    def __init__(self, sprites, tag_prefix):
        # sprites: {("brown", num): PhotoImage, ("white", num): PhotoImage}
        self.sprites = sprites
        self.tag     = tag_prefix

    def draw(self, canvas, x, y, color, frame=0, scale=1.0,
             horse_number=1, coat="brown"):
        key = (coat, horse_number)
        img = self.sprites.get(key)
        if img is None:
            return
        canvas.create_image(x, y, image=img, anchor="center", tags=self.tag)

    def clear(self, canvas):
        canvas.delete(self.tag)
