"""裏設定のタイプ（docs/TYPES.md と同じ内容）。ゲーム本体には入れない、開発用のデータ。"""

HANDS = ["グー", "チョキ", "パー"]     # グー → チョキ → パー → グー の順に勝つ
GOGYO = ["木", "土", "水", "火", "金"]  # 次の属性に勝つ
NICHIGETSU = ["日", "月"]            # おたがいに勝ち合う

# 属性 → [グー, チョキ, パー]
TYPES = {
    "木": [
        "まるた",
        "とげ",
        "はっぱ"
    ],
    "土": [
        "いわ",
        "ほうせき",
        "すな"
    ],
    "水": [
        "こおり",
        "あめ",
        "うみ"
    ],
    "火": [
        "ようがん",
        "いなずま",
        "ほのお"
    ],
    "金": [
        "てっきゅう",
        "かたな",
        "じしゃく"
    ],
    "日": [
        "たいよう",
        "ひかり",
        "にじ"
    ],
    "月": [
        "つき",
        "ながれぼし",
        "やみ"
    ]
}

# いまのボスと道具の割りふり（案・ゲームには未反映）: 名前 → (属性, 手)
BOSS_SEAT = {
    "草原": [
        "木",
        "チョキ"
    ],
    "砂漠": [
        "土",
        "パー"
    ],
    "氷": [
        "水",
        "グー"
    ],
    "フラワー": [
        "木",
        "パー"
    ],
    "べたべた": [
        "水",
        "パー"
    ],
    "マグマ": [
        "火",
        "グー"
    ],
    "炎": [
        "火",
        "パー"
    ],
    "ポップコーン": [
        "火",
        "グー"
    ],
    "トランポリン": [
        "金",
        "グー"
    ],
    "宇宙": [
        "月",
        "グー"
    ]
}
ITEM_SEAT = {
    "ブースター": [
        "日",
        "グー"
    ],
    "ほうき": [
        "木",
        "チョキ"
    ],
    "シャッフル": [
        "土",
        "パー"
    ],
    "ストップ": [
        "水",
        "パー"
    ],
    "じょうろ": [
        "水",
        "チョキ"
    ],
    "魔法の手": [
        "金",
        "チョキ"
    ],
    "おもし": [
        "金",
        "グー"
    ],
    "ひのたま": [
        "火",
        "パー"
    ],
    "はじけ玉": [
        "火",
        "グー"
    ],
    "ジャンプ": [
        "土",
        "チョキ"
    ],
    "マグネット": [
        "金",
        "パー"
    ]
}


def hand_wins(a, b):
    return (HANDS.index(a) + 1) % 3 == HANDS.index(b)


def elem_wins(a, b):
    if a in GOGYO and b in GOGYO:
        return GOGYO[(GOGYO.index(a) + 1) % 5] == b
    return {a, b} == set(NICHIGETSU)


def beats(t):
    """タイプ t の (特効, [強い…]) を、決まりから出す。"""
    e = next(k for k, v in TYPES.items() if t in v)
    k = TYPES[e].index(t)
    win = (k + 1) % 3
    if e in GOGYO:
        i = GOGYO.index(e)
        n1, n2 = GOGYO[(i + 1) % 5], GOGYO[(i + 2) % 5]
        return TYPES[n1][win], [TYPES[n1][k], TYPES[n2][k]]
    other = NICHIGETSU[1 - NICHIGETSU.index(e)]
    return TYPES[other][win], [TYPES[e][win]]


def effect(item, boss):
    """道具がボスに起こすこと: "特効" / "封印" / "王冠" / "同じ" / "ふつう"。"""
    (ie, ih), (be, bh) = ITEM_SEAT[item], BOSS_SEAT[boss]
    if (ie, ih) == (be, bh):
        return "同じ"
    h, e = hand_wins(ih, bh), elem_wins(ie, be)
    return "特効" if h and e else "封印" if h else "王冠" if e else "ふつう"
