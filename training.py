"""
馬育成ロジック (training.py) v2
"""
import random
import struct
import datetime
import hashlib

TRAINING_MONTHS   = 12
STAT_MAX          = 100
STAT_INITIAL_MIN  = 20
STAT_INITIAL_MAX  = 60
CODE_VERSION      = 1
BASE62_CHARS      = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
MAX_NAME_BYTES    = 24

# ── ステータス日本語名 ────────────────────────────────
STAT_LABELS = {
    "speed":        "速度",
    "stamina":      "スタミナ",
    "corner":       "コーナー",
    "mental":       "精神力",
    "adaptability": "適応力",
    "fatigue":      "疲労",
}

# ── 育成メニュー ──────────────────────────────────────
TRAINING_MENUS = [
    {
        "id": 0, "label": "スピード特訓",
        "desc": "瞬発力を鍛える。疲労が増す。",
        "effects": {"speed": 8, "fatigue": 10},
    },
    {
        "id": 1, "label": "スタミナ調教",
        "desc": "持続力を鍛える。コーナーも少し向上。",
        "effects": {"stamina": 8, "corner": 2, "fatigue": 8},
    },
    {
        "id": 2, "label": "コーナー練習",
        "desc": "コーナリング技術を磨く。精神も鍛えられる。",
        "effects": {"corner": 8, "mental": 2, "fatigue": 6},
    },
    {
        "id": 3, "label": "メンタルケア",
        "desc": "精神力を高め疲労を回復する。",
        "effects": {"mental": 8, "adaptability": 2, "fatigue": -8},
    },
    {
        "id": 4, "label": "放牧",
        "desc": "疲労を大きく回復。成長は少ない。",
        "effects": {"fatigue": -20, "mental": 3},
    },
    {
        "id": 5, "label": "適応力強化",
        "desc": "馬場や距離への対応力を高める。",
        "effects": {"adaptability": 8, "stamina": 2, "fatigue": 6},
    },
    {
        "id": 6, "label": "総合調教",
        "desc": "全能力をバランスよく鍛える。",
        "effects": {"speed": 3, "stamina": 3, "corner": 3, "mental": 3, "fatigue": 12},
    },
    {
        "id": 7, "label": "特別特訓",
        "desc": "大きな成長が期待できるが消耗も激しい。",
        "effects": {"speed": 5, "stamina": 5, "corner": 5, "mental": 5, "fatigue": 20},
    },
]

# ── 調教師メッセージ（メニュー別・通常時） ──────────────
COACH_MESSAGES = {
    0: [  # スピード特訓
        "今日のダッシュは切れがあったぞ。このまま続けよう。",
        "瞬発力が少しずつ上がっている。いい感触だ。",
        "スタートダッシュが鋭くなってきた。本物になるぞ。",
    ],
    1: [  # スタミナ調教
        "長距離を粘り強く走れるようになってきた。",
        "最後の直線で粘れるようになれば怖い存在になる。",
        "スタミナは地道な積み重ねだ。焦らずいこう。",
    ],
    2: [  # コーナー練習
        "コーナリングのキレが増してきた。いい傾向だ。",
        "内回りコースでの動きが格段に良くなった。",
        "コーナーで膨らまなくなってきたな。成長してる。",
    ],
    3: [  # メンタルケア
        "今日は馬がリラックスしていた。精神面は大事だぞ。",
        "落ち着いて走れる馬は本番で力を出せる。",
        "気持ちが安定してきた。この状態をキープしよう。",
    ],
    4: [  # 放牧
        "今日はゆっくり休ませた。英気を養ってくれ。",
        "放牧で気分転換。次の調教に備えるぞ。",
        "無理をさせても伸びない。休養も調教のうちだ。",
    ],
    5: [  # 適応力強化
        "芝でもダートでも対応できる馬を目指そう。",
        "距離が変わっても動じないようになってきた。",
        "どんな条件でも力を発揮できる馬になれ。",
    ],
    6: [  # 総合調教
        "バランスよく鍛えるのが理想の調教だ。",
        "どこかに特化するより、まず全体を底上げしよう。",
        "総合力が上がれば、レースの幅が広がる。",
    ],
    7: [  # 特別特訓
        "今日は限界まで追い込んだ。頑張ったぞ！",
        "ハードな調教だったが、この馬には潜在能力がある。",
        "特別特訓は両刃の剣だ。結果が出ることを祈ろう。",
    ],
}

# ── ランダムイベント定義 ─────────────────────────────
EVENTS = [
    {
        "id": "injury",
        "prob": 0.08,   # 疲労60以上で発動率×2
        "fatigue_threshold": 40,
        "message_prefix": "【アクシデント】",
        "messages": [
            "調教中に軽い打撲を負ってしまった。無理はできない……。",
            "足元に違和感が出た。様子を見ながら進めよう。",
            "ちょっとした怪我だが、油断は禁物だ。",
        ],
        "effect": lambda stats, rng: _apply_injury(stats, rng),
    },
    {
        "id": "breakthrough",
        "prob": 0.04,
        "fatigue_threshold": 0,
        "message_prefix": "【覚醒！】",
        "messages": [
            "突然、走りに変化が現れた！何かを掴んだようだ！",
            "今日の調教で大きな壁を突き破った！",
            "信じられない！この馬、本当の力が目覚めたぞ！",
        ],
        "effect": lambda stats, rng: _apply_breakthrough(stats, rng),
    },
    {
        "id": "recovery",
        "prob": 0.12,
        "fatigue_threshold": 0,
        "message_prefix": "【好調】",
        "messages": [
            "今日は馬の調子が抜群だ。疲れも感じないようだ。",
            "天気も良く、馬がいきいきしている。",
            "なぜか今日は特別元気だ。いいことがありそうだ。",
        ],
        "effect": lambda stats, rng: _apply_recovery(stats, rng),
    },
]

def _apply_injury(stats, rng):
    keys = ["speed", "stamina", "corner", "mental", "adaptability"]
    k = rng.choice(keys)
    delta = rng.randint(3, 8)
    stats[k] = max(0, stats[k] - delta)
    return stats, f"{STAT_LABELS[k]}が{delta}下がってしまった……。"

def _apply_breakthrough(stats, rng):
    keys = ["speed", "stamina", "corner", "mental", "adaptability"]
    k = rng.choice(keys)
    delta = rng.randint(8, 15)
    stats[k] = min(STAT_MAX, stats[k] + delta)
    return stats, f"{STAT_LABELS[k]}が{delta}も急上昇した！"

def _apply_recovery(stats, rng):
    return stats, "疲労がすっきり回復した！"

# ── 特性定義（能力値系・コース系・育成ルート系） ────────
# condition引数: stats dict（history・fatigue含む）
TRAITS = [
    # ── 能力値系（単体） ──────────────────────────
    {"id":  0, "name": "快速型",      "condition": lambda s: s["speed"] >= 80},
    {"id":  1, "name": "鉄人",        "condition": lambda s: s["stamina"] >= 80},
    {"id":  2, "name": "コーナー巧者","condition": lambda s: s["corner"] >= 80},
    {"id":  3, "name": "精神力",      "condition": lambda s: s["mental"] >= 80},
    {"id":  4, "name": "万能型",      "condition": lambda s: all(s[k] >= 60 for k in ["speed","stamina","corner","mental","adaptability"])},
    {"id":  5, "name": "鬼神",        "condition": lambda s: s["speed"] >= 90 and s["stamina"] >= 90},
    {"id":  6, "name": "瞬足",        "condition": lambda s: s["speed"] >= 92},
    {"id":  7, "name": "不屈",        "condition": lambda s: s["stamina"] >= 92},
    {"id":  8, "name": "堅実派",      "condition": lambda s: all(40 <= s[k] <= 72 for k in ["speed","stamina","corner","mental","adaptability"])},
    {"id":  9, "name": "晩成型",      "condition": lambda s: s.get("peak_month", 6) >= 10},
    {"id": 10, "name": "早熟型",      "condition": lambda s: s.get("peak_month", 6) <= 4},

    # ── コース系 ─────────────────────────────────
    {"id": 11, "name": "芝巧者",      "condition": lambda s: s.get("apt_turf") == "◎"},
    {"id": 12, "name": "ダート巧者",  "condition": lambda s: s.get("apt_dirt") == "◎"},
    {"id": 13, "name": "長距離適性",  "condition": lambda s: s["stamina"] >= 70 and s["adaptability"] >= 60},
    {"id": 14, "name": "短距離砲",    "condition": lambda s: s["speed"] >= 75 and s["stamina"] <= 50},
    {"id": 15, "name": "万場巧者",    "condition": lambda s: s.get("apt_turf") == "◎" and s.get("apt_dirt") == "◎"},

    # ── 育成ルート系 ─────────────────────────────
    {"id": 16, "name": "鍛錬の申し子","condition": lambda s: s.get("_history_count", {}).get(0, 0) >= 4},
    {"id": 17, "name": "メンタルの強さ","condition": lambda s: s.get("_history_count", {}).get(3, 0) >= 4},
    {"id": 18, "name": "放牧好き",    "condition": lambda s: s.get("_history_count", {}).get(4, 0) >= 3},
    {"id": 19, "name": "無敗の気質",  "condition": lambda s: s.get("_injury_count", 0) == 0},
    {"id": 20, "name": "苦労人",      "condition": lambda s: s.get("_injury_count", 0) >= 2 and s["speed"]+s["stamina"] >= 120},
    {"id": 21, "name": "特訓の鬼",    "condition": lambda s: s.get("_history_count", {}).get(7, 0) >= 3},
    {"id": 22, "name": "バランス調教","condition": lambda s: len(set(s.get("_history_list", []))) >= 6},
]

# ── コンボ特性（複数特性の組み合わせで付与） ───────────
COMBO_TRAITS = [
    {
        "name": "先行逃げ切り",
        "requires": {"快速型", "コーナー巧者"},
        "bonus": {"speed_race": 1.06},
        "desc": "短〜中距離で先行有利",
    },
    {
        "name": "末脚怪物",
        "requires": {"鉄人", "精神力"},
        "bonus": {"stamina_race": 1.06},
        "desc": "長距離で末脚が炸裂",
    },
    {
        "name": "芝の帝王",
        "requires": {"芝巧者", "万能型"},
        "bonus": {"turf_bonus": 1.08},
        "desc": "芝レースで圧倒的な適性",
    },
    {
        "name": "復活の申し子",
        "requires": {"苦労人", "不屈"},
        "bonus": {"cond_protect": True},
        "desc": "不調時でも能力低下しにくい",
    },
    {
        "name": "天才肌",
        "requires": {"無敗の気質", "快速型"},
        "bonus": {"luck_bias": 0.08},
        "desc": "レース結果がプラス方向に偏る",
    },
    {
        "name": "孤高の怪物",
        "requires": {"特訓の鬼", "鬼神"},
        "bonus": {"all_bonus": 1.07},
        "desc": "全距離でトップクラスの補正",
    },
    {
        "name": "芝ダート二刀流",
        "requires": {"芝巧者", "ダート巧者"},
        "bonus": {"turf_bonus": 1.04, "dirt_bonus": 1.04},
        "desc": "どちらのコースでも力を発揮",
    },
    {
        "name": "長距離の鬼",
        "requires": {"長距離適性", "鉄人"},
        "bonus": {"stamina_race": 1.08},
        "desc": "長距離レースで無類の強さ",
    },
]

# ── 調教師の完成評価メッセージ ────────────────────────
def get_completion_message(stats):
    total = sum(stats[k] for k in ["speed","stamina","corner","mental","adaptability"])
    avg   = total / 5

    if avg >= 85:
        return (
            "……これは、とんでもない馬が完成したぞ。\n"
            "正直、こんなに仕上がるとは思っていなかった。\n"
            "レースで暴れ回ってくれ。期待しているぞ！"
        )
    elif avg >= 70:
        return (
            "よく育ってくれた。文句のない仕上がりだ。\n"
            "どんな相手にも引けを取らない馬になったぞ。\n"
            "自信を持ってレースに挑め！"
        )
    elif avg >= 55:
        return (
            "まずまずの出来だな。平均よりは上だ。\n"
            "うまくはまれば上位も狙えるぞ。\n"
            "あとはレースで本物の経験を積んでくれ。"
        )
    elif avg >= 40:
        return (
            "……正直、もう少し伸びてほしかったが。\n"
            "育成の流れが噛み合わなかったかもしれない。\n"
            "それでもお前の馬だ。精一杯走らせてやれ。"
        )
    else:
        return (
            "厳しいことを言うぞ。\n"
            "育成がうまくいかなかったな……。\n"
            "だが、レースに出ることに意味がある。次に活かそう。"
        )


# ── seed・初期値生成 ──────────────────────────────────
def generate_birth_seed():
    now = datetime.datetime.now()
    seed_str = now.strftime("%Y%m%d%H%M")
    h = hashlib.md5(seed_str.encode()).hexdigest()[:8]
    return int(h, 16)

def generate_initial_stats(seed):
    rng = random.Random(seed)
    stats = {
        "speed":        rng.randint(STAT_INITIAL_MIN, STAT_INITIAL_MAX),
        "stamina":      rng.randint(STAT_INITIAL_MIN, STAT_INITIAL_MAX),
        "corner":       rng.randint(STAT_INITIAL_MIN, STAT_INITIAL_MAX),
        "mental":       rng.randint(STAT_INITIAL_MIN, STAT_INITIAL_MAX),
        "adaptability": rng.randint(STAT_INITIAL_MIN, STAT_INITIAL_MAX),
    }
    apt_choices = ["◎", "○", "△"]
    stats["apt_turf"]    = rng.choices(apt_choices, weights=[30,50,20])[0]
    stats["apt_dirt"]    = rng.choices(apt_choices, weights=[30,50,20])[0]
    stats["growth_rate"] = round(rng.uniform(0.8, 1.5), 2)
    stats["peak_month"]  = rng.randint(3, 10)
    return stats


# ── 月次メニュー選択肢生成 ────────────────────────────
def get_monthly_choices(month, current_fatigue, seed, history_so_far):
    rng = random.Random(seed + month * 1000 + sum(history_so_far))
    available = list(range(len(TRAINING_MENUS)))
    forced = []
    if current_fatigue >= 60 and 4 not in forced:
        forced.append(4)
        available = [x for x in available if x not in forced]
    rest = rng.sample(available, min(3 - len(forced), len(available)))
    choices = forced + rest
    return [TRAINING_MENUS[i] for i in choices[:3]]


# ── 育成効果適用 ──────────────────────────────────────
def apply_training(stats, fatigue, menu_id, month, growth_rate, peak_month):
    """
    returns: (new_stats, new_fatigue, event_result)
    event_result: None or {"message_prefix":str, "message":str, "sub":str}
    """
    menu       = TRAINING_MENUS[menu_id]
    s          = dict(stats)
    f          = fatigue
    peak_bonus = 1.5 if month == peak_month else 1.0
    rng        = random.Random(month * 7919 + menu_id * 31 + int(growth_rate * 100))

    for key, delta in menu["effects"].items():
        if key == "fatigue":
            f = max(0, min(100, f + delta))
        else:
            effective        = delta * growth_rate * peak_bonus
            fatigue_penalty  = 1.0 - (f / 200)
            effective       *= fatigue_penalty
            s[key]           = int(min(STAT_MAX, s.get(key, 0) + effective))

    # ── ランダムイベント判定 ──
    event_result = None
    for ev in EVENTS:
        if f < ev["fatigue_threshold"] and ev["id"] == "injury":
            continue
        prob = ev["prob"]
        if ev["id"] == "injury" and f >= 60:
            prob *= 2.0
        if rng.random() < prob:
            new_s, sub_msg = ev["effect"](s, rng)
            s = new_s
            if ev["id"] == "recovery":
                f = max(0, f - rng.randint(10, 20))
            if ev["id"] == "injury":
                s["_injury_count"] = s.get("_injury_count", 0) + 1
            msg = rng.choice(ev["messages"])
            event_result = {
                "message_prefix": ev["message_prefix"],
                "message":        msg,
                "sub":            sub_msg,
            }
            break

    # 育成ルート記録
    hc = s.get("_history_count", {})
    hc[menu_id] = hc.get(menu_id, 0) + 1
    s["_history_count"] = hc
    hl = s.get("_history_list", [])
    hl.append(menu_id)
    s["_history_list"] = hl

    return s, f, event_result


# ── 通常コーチメッセージ取得 ──────────────────────────
def get_coach_message(menu_id, rng=None):
    if rng is None:
        import random as _r
        rng = _r
    msgs = COACH_MESSAGES.get(menu_id, ["よく頑張った。この調子で続けよう。"])
    return rng.choice(msgs)


# ── 育成を全月分再適用 ────────────────────────────────
def replay_training(seed, history):
    stats       = generate_initial_stats(seed)
    fatigue     = 0
    growth_rate = stats["growth_rate"]
    peak_month  = stats["peak_month"]
    for month, menu_id in enumerate(history):
        stats, fatigue, _ = apply_training(
            stats, fatigue, menu_id, month + 1, growth_rate, peak_month)
    traits          = [t["name"] for t in TRAITS if t["condition"](stats)]
    stats["traits"] = traits
    stats["fatigue"]= fatigue
    return stats


# ── 特性決定（単体＋コンボ） ─────────────────────────
def determine_traits(stats):
    """単体特性 + コンボ特性を判定して名前リストを返す"""
    single = [t["name"] for t in TRAITS if t["condition"](stats)]
    single_set = set(single)
    combo  = [c["name"] for c in COMBO_TRAITS if c["requires"].issubset(single_set)]
    return single + combo


def get_trait_bonus(traits):
    """
    特性リストからレース計算用ボーナス辞書を返す
    returns: {bonus_key: value}
    """
    bonus = {}
    trait_set = set(traits)
    for c in COMBO_TRAITS:
        if c["name"] in trait_set:
            for k, v in c["bonus"].items():
                if k in bonus:
                    bonus[k] = bonus[k] * v if isinstance(v, float) else v
                else:
                    bonus[k] = v
    return bonus


# ── コンディションボーナス計算（B: 育成終盤→調子影響） ─
def calc_condition_bonus(stats, history, final_fatigue):
    """
    育成終盤の状態から調子確率のシフト量を返す
    returns: int -2〜+2
      +2 = 絶好調になりやすい
      -2 = 不調になりやすい
    """
    score = 0

    # 疲労による判定
    if final_fatigue <= 20:
        score += 2
    elif final_fatigue <= 40:
        score += 1
    elif final_fatigue >= 70:
        score -= 2
    elif final_fatigue >= 55:
        score -= 1

    # 終盤3ヶ月のメニュー
    last3 = history[-3:] if len(history) >= 3 else history
    recovery_menus = {3, 4}   # メンタルケア・放牧
    heavy_menus    = {7}       # 特別特訓
    recovery_count = sum(1 for m in last3 if m in recovery_menus)
    heavy_count    = sum(1 for m in last3 if m in heavy_menus)
    score += recovery_count
    score -= heavy_count

    # 怪我の直近履歴
    injury = stats.get("_injury_count", 0)
    if injury >= 2:
        score -= 1

    # 全盛期が後期なら調子が乗りやすい
    if stats.get("peak_month", 6) >= 10:
        score += 1

    return max(-2, min(2, score))


def shift_condition_weights(base_weights, bonus):
    """
    base_weights: [◎, ○, △, ×] の確率ウェイト
    bonus: -2〜+2
    """
    w = list(base_weights)
    # +1ごとに◎+5, ×-5; -1ごとに◎-5, ×+5
    w[0] = max(1, w[0] + bonus * 5)   # ◎
    w[3] = max(1, w[3] - bonus * 5)   # ×
    return w


# ── 表示ヘルパー ──────────────────────────────────────
def to_stars(value, stars=5):
    if value <= 0:
        return "☆" * stars
    rank = min(stars, int(value / STAT_MAX * stars) + 1)
    return "★" * rank + "☆" * (stars - rank)


# ── コードエンコード/デコード ─────────────────────────
def encode_horse_code(name, seed, history):
    name_bytes = name.encode("utf-8")
    if len(name_bytes) > MAX_NAME_BYTES:
        raise ValueError("馬名が長すぎます（最大8文字）")
    buf = bytearray()
    buf.append(CODE_VERSION)
    buf.append(len(name_bytes))
    buf.extend(name_bytes)
    buf.extend(struct.pack(">I", seed & 0xFFFFFFFF))
    hist_val = 0
    for i, v in enumerate(history):
        hist_val |= (int(v) & 0xF) << (i * 4)
    buf.extend(hist_val.to_bytes(6, "big"))
    buf.append(sum(buf) & 0xFF)
    num = int.from_bytes(buf, "big")
    if num == 0:
        return "0"
    result = []
    while num > 0:
        result.append(BASE62_CHARS[num % 62])
        num //= 62
    raw = "".join(reversed(result))
    return "-".join(raw[i:i+4] for i in range(0, len(raw), 4))


def decode_horse_code(code):
    raw = code.replace("-", "").strip()
    if not raw:
        raise ValueError("コードが空です")
    num = 0
    for ch in raw:
        if ch not in BASE62_CHARS:
            raise ValueError(f"無効な文字: {ch}")
        num = num * 62 + BASE62_CHARS.index(ch)
    byte_len = (num.bit_length() + 7) // 8
    buf = list(num.to_bytes(max(byte_len, 10), "big"))
    checksum = buf[-1]
    if sum(buf[:-1]) & 0xFF != checksum:
        raise ValueError("コードが破損しています（チェックサム不一致）")
    idx     = 0
    version = buf[idx]; idx += 1
    if version != CODE_VERSION:
        raise ValueError(f"未対応のバージョン: {version}")
    name_len = buf[idx]; idx += 1
    name     = bytes(buf[idx:idx+name_len]).decode("utf-8"); idx += name_len
    seed     = struct.unpack(">I", bytes(buf[idx:idx+4]))[0]; idx += 4
    hist_val = int.from_bytes(bytes(buf[idx:idx+6]), "big"); idx += 6
    history  = [(hist_val >> (i*4)) & 0xF for i in range(TRAINING_MONTHS)]
    return name, seed, history


# ── 育成馬→レース用馬データ変換 ──────────────────────
def trained_to_race_horse(name, seed, history, number, surface):
    from horserace import make_jockey, CONDITIONS, CONDITION_WEIGHTS, AFFINITY_LABELS
    import random as _r
    stats   = replay_training(seed, history)
    jockey  = make_jockey()
    def normalize(v):
        return max(1, min(10, round(v / 10)))
    aff_val                    = _r.choices([-1,0,1,2], weights=[10,40,35,15])[0]
    aff_sym, aff_mult, _       = AFFINITY_LABELS[aff_val]
    # 育成結果を調子確率に反映（B: コンディションボーナス）
    cond_bonus  = calc_condition_bonus(stats, stats.get("_history_list",[]), stats.get("fatigue",0))
    cond_weights = shift_condition_weights(list(CONDITION_WEIGHTS), cond_bonus)
    cond_sym, cond_mult, _ = _r.choices(CONDITIONS, weights=cond_weights)[0]
    from horserace import make_comment
    horse = {
        "number":       number,
        "name":         name,
        "speed":        normalize(stats["speed"]),
        "stamina":      normalize(stats["stamina"]),
        "corner":       normalize(stats["corner"]),
        "mental":       normalize(stats["mental"]),
        "adaptability": normalize(stats["adaptability"]),
        "apt_turf":     stats["apt_turf"],
        "apt_dirt":     stats["apt_dirt"],
        "condition":    cond_sym,
        "cond_mult":    cond_mult,
        "cond_label":   "",
        "jockey":       jockey,
        "affinity":     aff_sym,
        "aff_mult":     aff_mult,
        "aff_label":    "",
        "coat":         _r.choice(["brown","white"]),
        "is_trained":   True,
        "traits":       stats.get("traits", []),
        "trait_bonus":  get_trait_bonus(stats.get("traits", [])),  # コンボ効果
        "cond_bonus":   cond_bonus,   # 調子ボーナス値（表示用）
        "raw_stats":    stats,
    }
    horse["comment"] = make_comment(horse, surface, 2000)
    return horse
