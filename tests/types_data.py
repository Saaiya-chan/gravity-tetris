"""裏設定のタイプ（docs/TYPES.md と同じ内容）。ゲーム本体には入れない、開発用のデータ。"""

LAYERS = ["天", "地", "人"]          # 天 → 地 → 人 → 天 の順に勝つ
GOGYO = ["木", "土", "水", "火", "金"]  # 次の属性に勝つ（次の次にも少し強い）
NICHIGETSU = ["日", "月"]            # おたがいに勝ち合う

# 属性 → [天, 地, 人]
TYPES = {
    "木": [
        "かぜ",
        "くさ",
        "かみ"
    ],
    "土": [
        "すな",
        "いわ",
        "けっかい"
    ],
    "水": [
        "あめ",
        "ぬま",
        "いど"
    ],
    "火": [
        "ほし",
        "ほのお",
        "はなび"
    ],
    "金": [
        "こおり",
        "ほうせき",
        "はがね"
    ],
    "日": [
        "たいよう",
        "ひなた",
        "かがみ"
    ],
    "月": [
        "うちゅう",
        "やみ",
        "ゆめ"
    ]
}


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
