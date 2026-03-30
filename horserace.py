"""
競馬ロジック
- 馬名・レース名・コース生成
- ステータス・調子生成
- レース結果計算（ステータス反映＋ランダム要素）
"""
import random

# ── 馬名ワードテーブル ──────────────────────────
PREFIX = [
    "シン","メイ","ダイ","ゴール","サン","ブラック","ホワイト",
    "スター","ソード","フラッシュ","ドリーム","ライジング",
    "ファイア","サイレント","ミラクル","フジ","キング","クイーン",
    "レッド","ブルー","スカイ","サンダー","ウィンド","オーシャン",
]
SUFFIX = [
    "ボルト","フレア","スター","ウイング","ストーム","ブレイズ",
    "ライト","ランナー","ビート","シャイン","フォース","ブレード",
    "ホーク","アロー","スピード","ヒーロー","レジェンド","クロス",
    "バード","ウェーブ","ダッシュ","ソウル","ハート","ドーン",
]

# ── レース名ワードテーブル ──────────────────────
RACE_PLACE  = ["東京","京都","阪神","中山","札幌","函館","新潟","小倉","中京","福島"]
RACE_SUFFIX = ["記念","ステークス","カップ","賞","トロフィー","チャレンジカップ","ターフ"]
RACE_GRADE  = ["G1","G2","G3","OP","L"]

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


def make_horse_name():
    return random.choice(PREFIX) + random.choice(SUFFIX)


def make_race_name():
    place  = random.choice(RACE_PLACE)
    suffix = random.choice(RACE_SUFFIX)
    grade  = random.choice(RACE_GRADE)
    return f"{place}{suffix} ({grade})"


def make_course():
    surface  = random.choice(list(COURSES.keys()))
    distance = random.choice(COURSES[surface])
    return surface, distance


def make_horse(number, surface):
    """1頭の馬データを生成"""
    name    = make_horse_name()
    speed   = random.randint(1, 5)
    stamina = random.randint(1, 5)
    corner  = random.randint(1, 5)
    # 馬場適性（メインコースは高めに）
    apt_turf  = random.choices(APTITUDE, weights=[50, 35, 15])[0] if surface == "芝" \
                else random.choices(APTITUDE, weights=[15, 35, 50])[0]
    apt_dirt  = random.choices(APTITUDE, weights=[50, 35, 15])[0] if surface == "ダート" \
                else random.choices(APTITUDE, weights=[15, 35, 50])[0]
    cond_sym, cond_mult, cond_label = random.choices(CONDITIONS, weights=CONDITION_WEIGHTS)[0]

    return {
        "number":     number,
        "name":       name,
        "speed":      speed,
        "stamina":    stamina,
        "corner":     corner,
        "apt_turf":   apt_turf,
        "apt_dirt":   apt_dirt,
        "condition":  cond_sym,
        "cond_mult":  cond_mult,
        "cond_label": cond_label,
    }


def aptitude_score(apt):
    return {"◎": 1.2, "○": 1.0, "△": 0.75}.get(apt, 1.0)


def calc_base_score(horse, surface, distance):
    """ステータスからベーススコアを計算"""
    spd = horse["speed"]
    stm = horse["stamina"]
    cor = horse["corner"]

    # 距離補正（短距離は速度重視、長距離はスタミナ重視）
    if distance <= 1400:
        score = spd * 2.0 + stm * 0.8 + cor * 0.5
    elif distance <= 1800:
        score = spd * 1.5 + stm * 1.2 + cor * 0.8
    elif distance <= 2200:
        score = spd * 1.0 + stm * 1.8 + cor * 1.0
    else:
        score = spd * 0.7 + stm * 2.2 + cor * 0.8

    # 馬場適性補正
    apt = horse["apt_turf"] if surface == "芝" else horse["apt_dirt"]
    score *= aptitude_score(apt)

    # 調子補正
    score *= horse["cond_mult"]

    return score


def run_race(horses, surface, distance):
    """
    レースを実行してスコアリスト・順位リストを返す
    returns: [(horse, score, final_pos), ...]  順位順
    """
    results = []
    for h in horses:
        base   = calc_base_score(h, surface, distance)
        # ランダム要素 ±20%
        rand   = random.uniform(0.80, 1.20)
        final  = base * rand
        results.append((h, final))

    results.sort(key=lambda x: -x[1])

    # 走行位置データを生成（アニメーション用）
    # 各馬の「最終スコア正規化値」= 0.0〜1.0
    scores = [r[1] for r in results]
    mn, mx = min(scores), max(scores)
    rng    = mx - mn if mx != mn else 1.0

    ranked = []
    for rank, (horse, score) in enumerate(results):
        norm = (score - mn) / rng   # 0〜1
        ranked.append({
            "rank":  rank + 1,
            "horse": horse,
            "score": score,
            "norm":  norm,
        })
    return ranked


def make_comment(horse, surface, distance):
    """ステータスとレース条件から一言評価を生成"""
    spd = horse["speed"]
    stm = horse["stamina"]
    apt = horse["apt_turf"] if surface == "芝" else horse["apt_dirt"]
    cond = horse["condition"]

    comments = []

    # 距離適性コメント
    if distance <= 1400:
        if spd >= 4:
            comments.append("短距離巧者、スピードは上位")
        elif spd <= 2:
            comments.append("スピード不足、距離が忙しい")
    elif distance >= 2400:
        if stm >= 4:
            comments.append("スタミナ豊富、長丁場で本領発揮")
        elif stm <= 2:
            comments.append("長距離は疑問、スタミナ不安")
    else:
        if spd >= 4 and stm >= 4:
            comments.append("バランス型、どの展開でも対応可")
        elif spd >= 4:
            comments.append("先行力あり、逃げ粘り期待")

    # 馬場適性コメント
    if apt == "◎":
        comments.append(f"{surface}は得意コース")
    elif apt == "△":
        comments.append(f"{surface}は苦手、割引が必要")

    # 調子コメント
    if cond == "◎":
        comments.append("今日の状態は抜群、本命候補")
    elif cond == "×":
        comments.append("調子に難あり、過信は禁物")

    # 総合評価
    total = horse["speed"] + horse["stamina"] + horse["corner"]
    if total >= 12:
        comments.append("総合力は高く実力上位")
    elif total <= 7:
        comments.append("実力は下位、大穴狙いか")

    if not comments:
        comments.append("実力は中位、展開次第で一発も")

    return "。".join(comments[:2])


def generate_race(num_horses=8):
    """レース全体を生成して返す"""
    race_name       = make_race_name()
    surface, distance = make_course()
    horses          = [make_horse(i+1, surface) for i in range(num_horses)]
    for h in horses:
        h["comment"] = make_comment(h, surface, distance)
    return {
        "name":     race_name,
        "surface":  surface,
        "distance": distance,
        "horses":   horses,
    }


# ── 描画抽象クラス ────────────────────────────────
class HorseRenderer:
    """将来の画像差し替えに備えた描画インターフェース"""
    def draw(self, canvas, x, y, color, frame=0, scale=1.0):
        raise NotImplementedError

    def clear(self, canvas):
        pass


class IconHorseRenderer(HorseRenderer):
    """
    現在の実装: Canvas図形で馬シルエットを描画
    将来 ImageHorseRenderer に差し替え可能
    """
    def __init__(self, tag_prefix):
        self.tag = tag_prefix

    def draw(self, canvas, x, y, color, frame=0, scale=1.0):
        """
        x, y: 馬の中心座標
        frame: アニメフレーム番号（脚の動きに使用）
        scale: 拡大率
        """
        tag = self.tag
        s   = scale
        # 胴体
        canvas.create_oval(
            x - 22*s, y - 10*s, x + 22*s, y + 10*s,
            fill=color, outline="", tags=tag)
        # 首
        canvas.create_polygon(
            x + 14*s, y - 8*s,
            x + 24*s, y - 22*s,
            x + 32*s, y - 18*s,
            x + 20*s, y - 4*s,
            fill=color, outline="", tags=tag)
        # 頭
        canvas.create_oval(
            x + 22*s, y - 30*s, x + 38*s, y - 14*s,
            fill=color, outline="", tags=tag)
        # 耳
        canvas.create_polygon(
            x + 28*s, y - 30*s,
            x + 26*s, y - 38*s,
            x + 31*s, y - 30*s,
            fill=color, outline="", tags=tag)
        # 脚（フレームで動く）
        leg_offset = [0, 4, 0, -4][frame % 4]
        legs = [
            (x - 14*s, y + 10*s, x - 14*s, y + 26*s + leg_offset),
            (x -  4*s, y + 10*s, x -  4*s, y + 26*s - leg_offset),
            (x +  6*s, y + 10*s, x +  6*s, y + 26*s + leg_offset),
            (x + 16*s, y + 10*s, x + 16*s, y + 26*s - leg_offset),
        ]
        for lx1, ly1, lx2, ly2 in legs:
            canvas.create_line(lx1, ly1, lx2, ly2,
                               fill=color, width=max(2, int(3*s)), tags=tag)
        # たてがみ
        canvas.create_line(
            x + 16*s, y - 10*s,
            x + 24*s, y - 24*s,
            fill="#FFFFFF", width=max(1, int(2*s)), tags=tag)
        # 目
        canvas.create_oval(
            x + 30*s, y - 26*s, x + 34*s, y - 22*s,
            fill="#000000", outline="", tags=tag)

    def clear(self, canvas):
        canvas.delete(self.tag)


class ImageHorseRenderer(HorseRenderer):
    """
    将来の実装: PNG画像フレームでアニメーション描画
    使用方法:
        frames = [tk.PhotoImage(file=f"horse_frames/run_{i}.png") for i in range(4)]
        renderer = ImageHorseRenderer(frames, goal_frame=tk.PhotoImage(file="horse_frames/goal.png"))
    """
    def __init__(self, frames, goal_frame=None):
        self.frames     = frames
        self.goal_frame = goal_frame
        self.tag        = "horse_img"
        self._ids       = []

    def draw(self, canvas, x, y, color, frame=0, scale=1.0, is_goal=False):
        img = self.goal_frame if (is_goal and self.goal_frame) else self.frames[frame % len(self.frames)]
        iid = canvas.create_image(x, y, image=img, anchor="center", tags=self.tag)
        self._ids.append(iid)

    def clear(self, canvas):
        canvas.delete(self.tag)
        self._ids.clear()
