"""ボス・王冠・相性・宝石（BOSS / GEM）"""
import pytest
from types_data import BOSS_SEAT, ITEM_SEAT, effect

WORLDS = ["meadow", "desert", "ice", "fire", "bouncy", "space", "sticky", "popcorn", "flower", "magma"]
# 相性は「属性 × じゃんけん」（docs/TYPES.md）。裏設定の表（tests/types_data.py）は日本語の名前、ゲームは内部キーなので、対応表でつなぐ
BOSS_KEY = {"草原": "meadow", "砂漠": "desert", "氷": "ice", "フラワー": "flower", "べたべた": "sticky", "マグマ": "magma",
            "炎": "fire", "ポップコーン": "popcorn", "トランポリン": "bouncy", "宇宙": "space"}
ITEM_KEY = {"ブースター": "boost", "ほうき": "broom", "シャッフル": "shuf", "ストップ": "stop", "じょうろ": "water", "魔法の手": "hand",
            "おもし": "weight", "ひのたま": "fire", "はじけ玉": "pop", "ジャンプ": "jump", "マグネット": "mag"}
KIND = {"特効": "sp", "封印": "seal", "王冠": "crown", "ふつう": "normal", "同じ": "same"}      # effect() の答え → ゲームの aisho() の答え
PAIRS = {kind: [(ITEM_KEY[i], BOSS_KEY[b]) for b in BOSS_SEAT for i in ITEM_SEAT if effect(i, b) == kind] for kind in KIND}   # 判定 → [(道具, ボス)…]
HAND_IC = {"グー": "✊", "チョキ": "✌️", "パー": "🖐️"}
USE = {"boost": "useBoost", "stop": "useStop", "mag": "useMag", "shuf": "useShuffle", "jump": "useJump", "hand": "useHand",
       "pop": "usePop", "broom": "useBroom", "weight": "useWeight", "fire": "useFire", "water": "useWater"}
# 道具を使える状態にして（盤面にぷにを少し置き、効果中のものを切って）、1回使う
READY = "stopLeft=0; magLeft=0; boostLeft=0; handLeft=0; weightLeft=0; shuffle=null; energy=100; "


def use(game, item, settle=True):
    game.clear_board(); game.put(2, 0); game.put(2, 1, row=1)
    if settle:
        game.wait(500)                                                # （シャッフル・ジャンプは、止まっているぷにが要る）
    game.js(READY + USE[item] + "()")
AISHO_WAIT = 2000
ALL = "devItems=['stop','mag','shuf','jump','hand','broom','pop','weight','fire','water']; "


@pytest.mark.parametrize("w", range(10))
def test_every_boss_appears(game, w):
    """[BOSS-01] どのワールドにも、そのワールドのボスがいる。"""
    game.boss(w, quiet=False)
    assert game.js("[boss.k, boss.name]") == [WORLDS[w], game.js(f"BOSS_NAME['{WORLDS[w]}']")]
    game.js("bossAbility(performance.now())"); game.wait(600)       # 妨害を1回出してもエラーにならない


def test_boss_hp_and_crown(game):
    """[BOSS-02][BOSS-03] 体力は 80×(1+0.12×クリア回数)×20、王冠は2000。クリア回数は8回ぶんまで。"""
    game.boss(0)
    assert game.js("[boss.maxHp, boss.crown]") == [1600, 2000]
    game.js("worldClears.meadow=3; startBoss(performance.now())")
    assert game.js("boss.maxHp") == round(80 * 1.36 * 20)
    game.js("worldClears.meadow=50; startBoss(performance.now())")
    assert game.js("[boss.lv, boss.maxHp]") == [8, round(80 * 1.96 * 20)]


def test_pop_damage(game):
    """[BOSS-04] ぷにを消すと、個数×(1+(連鎖数-1)×0.6) のダメージ。"""
    game.boss(0)
    game.js("chain=1; hitBoss(10, performance.now())")
    assert game.js("boss.maxHp-boss.hp") == 10
    game.js("chain=3; hitBoss(10, performance.now())")
    assert game.js("boss.maxHp-boss.hp") == 10 + 22


def test_weakness(game):
    """[BOSS-05][LAB-04][TALK-05] 特効の道具: 妨害を10秒封じ、王冠を15%けずり、弱点が記録される。セリフはぷに妖精の吹き出しに出る。"""
    game.js(ALL); game.boss(1)                                       # 砂漠（土のパー）← ほうき（木のチョキ）
    assert game.js("aisho('broom','desert')") == "sp"
    game.js("energy=100; useBroom()")
    assert game.js("[boss.crown, talk.text, weakFound]") == [1700, "弱点を見破った！！\n弱点はほうきだ！", ["desert"]]
    left = game.js("boss.sealUntil-performance.now()")
    assert 9000 < left <= 10000
    game.js("energy=100; useBroom()")
    assert game.js("[boss.crown, talk.text]") == [1400, "効果ばつぐん！！"]


def test_neutral_and_resisted(game):
    """[BOSS-06][BOSS-07][TALK-05] ふつうの道具は4%「効いてる！」、ボスと同じ席の道具は1%「あまり効いてない…」（ぷに妖精の吹き出し）。どちらも封印しない。"""
    game.js(ALL); game.boss(1)                                       # 砂漠（土のパー）と同じ席 → シャッフル
    game.js("energy=100; useBoost()")
    assert game.js("[boss.crown, talk.text]") == [1920, "効いてる！"]
    game.clear_board(); game.put(3, 0); game.wait(500)
    game.js("energy=100; useShuffle()")
    assert game.js("[boss.crown, talk.text, boss.sealUntil, weakFound]") == [1900, "あまり効いてない…", 0, []]
    game.js("goHome()")
    game.boss(0)                                                     # ボス自身の宝石から作る道具（草原の宝石 → ほうき）でも、席がちがえば ふつうに効く
    game.js("energy=100; useBroom()")
    assert game.js("[aisho('broom','meadow'), boss.crown, talk.text]") == ["normal", 1920, "効いてる！"]


def test_level_adds_crown_damage(game):
    """[UP-05][BOSS-07] 道具のレベルが1上がるごとに、王冠へのダメージが1%ふえる。同じ席の道具は、レベルが上がっても1%のまま。"""
    game.js(ALL + "itemLv={broom:2, boost:1, shuf:3}"); game.boss(1)
    game.js("energy=100; useBroom()")                                # 特効 15% + 2%
    assert game.js("boss.crown") == 2000 - 2000 * 0.17
    game.js("energy=100; useBoost()")                                # ふつう 4% + 1%
    assert game.js("boss.crown") == 2000 - 2000 * 0.17 - 2000 * 0.05
    game.clear_board(); game.put(3, 0); game.wait(500)
    game.js("boss.sealUntil=0; energy=100; useShuffle()")            # 同じ席 1%（Lv4 でも）
    assert game.js("boss.crown") == 2000 - 2000 * 0.17 - 2000 * 0.05 - 2000 * 0.01


def test_seat_tables(game):
    """[BOSS-08] ボスと道具の席（属性と手）が、裏設定の表（docs/TYPES.md・tests/types_data.py）と同じ。エネルギー缶に席はない。"""
    assert game.js("BOSS_SEAT") == {BOSS_KEY[b]: seat for b, seat in BOSS_SEAT.items()}
    assert game.js("ITEM_SEAT") == {ITEM_KEY[i]: seat for i, seat in ITEM_SEAT.items()}
    assert sorted(BOSS_KEY.values()) == sorted(WORLDS) == sorted(game.js("THEMES.map(t=>t.k)"))
    assert sorted(ITEM_KEY.values()) == sorted(game.js("Object.keys(ITEM_NAME).filter(k=>k!=='can')"))
    assert game.js("[ITEM_SEAT.can===undefined, aisho('can','meadow')]") == [True, None]
    assert game.js("[typeof COUNTER, typeof COUNTER_SOON, typeof GEM_SOON]") == ["undefined"] * 3     # 「弱点は1つ」の表は、もう無い


def test_aisho_matrix(game):
    """[BOSS-08] 全10ボス × 全11道具の判定が、裏設定の effect() と一致する（ゲームの表と裏設定の表の食いちがいを見はる）。"""
    got = game.js("Object.fromEntries(Object.keys(BOSS_SEAT).map(b=>[b, Object.fromEntries(Object.keys(ITEM_SEAT).map(i=>[i, aisho(i,b)]))]))")
    want = {BOSS_KEY[b]: {ITEM_KEY[i]: KIND[effect(i, b)] for i in ITEM_SEAT} for b in BOSS_SEAT}
    assert got == want
    assert sum(len(v) for v in want.values()) == 110
    assert game.js("spItems('space')") == [] and game.js("spItems('magma')") == ["stop"]     # 宇宙には、まだ特効の道具がない
    assert game.js("spBosses('stop')") == ["popcorn", "magma"]                                # 1つの道具が、2体のボスに特効のこともある
    rules = "[handWins('グー','チョキ'), handWins('チョキ','パー'), handWins('パー','グー'), handWins('グー','パー'), handWins('グー','グー')," \
            " elemWins('木','土'), elemWins('金','木'), elemWins('土','木'), elemWins('日','月'), elemWins('月','日'), elemWins('日','木'), elemWins('火','月')]"
    assert game.js(rules) == [True, True, True, False, False, True, True, False, True, True, False, False]


# 判定ごとに1組: (判定, 道具, ボスのワールド番号, 王冠%, 封印の秒, セリフ, 表情)
FIVE = [("sp", "broom", 1, 15, 10, "弱点を見破った！！", "happy"),      # ほうき（木のチョキ）→ 砂漠（土のパー）
        ("seal", "water", 1, 4, 6, "王冠を封じた！", "happy"),               # じょうろ（水のチョキ）→ 砂漠（土のパー）
        ("crown", "hand", 0, 10, 0, "王冠に効いてる！", "normal"),      # 魔法の手（金のチョキ）→ 草原（木のグー）
        ("normal", "boost", 1, 4, 0, "効いてる！", "normal"),           # ブースター（日のグー）→ 砂漠（土のパー）
        ("same", "weight", 4, 1, 0, "あまり効いてない…", "worry")]      # おもし（金のグー）→ トランポリン（金のグー）


@pytest.mark.parametrize("kind,item,w,pct,seal,line,mood", FIVE)
def test_five_results(game, kind, item, w, pct, seal, line, mood):
    """[BOSS-05][BOSS-06][BOSS-07][BOSS-18][BOSS-19][TALK-05] 5通りの判定: 王冠ダメージ（15・4・10・4・1%。レベルで+1%、同じ席はふえない）、封印（10秒・6秒・なし）、セリフと表情。"""
    game.js(ALL); game.boss(w)
    assert game.js(f"aisho('{item}', boss.k)") == kind and (item, WORLDS[w]) in PAIRS[next(k for k, v in KIND.items() if v == kind)]
    game.js(READY + USE[item] + "()")
    assert game.js("[boss.crown, talk.text.split('\\n')[0], talk.mood, talk.prio, abilFx && abilFx.text]") == [2000 - 20 * pct, line, mood, 2, None]
    left = game.js("boss.sealUntil-performance.now()")
    assert (seal * 1000 - 1000 < left <= seal * 1000) if seal else left < 0
    assert game.js("weakFound") == ([WORLDS[w]] if kind == "sp" else [])            # 見破った記録がつくのは、特効だけ
    game.js(f"itemLv.{item}=2; " + READY + USE[item] + "()")                         # Lv3: +2%（同じ席は 1% のまま）
    assert game.js("boss.crown") == 2000 - 20 * pct - 20 * (pct + (0 if kind == "same" else 2))
    if kind == "sp":
        assert game.js("talk.text") == "効果ばつぐん！！"


def test_seal_not_shortened(game):
    """[BOSS-20] 封印の残りが長いほうを、短く上書きしない（特効の10秒のあとに、封印だけの6秒を使っても、10秒のまま）。長いほうへは、のびる。"""
    game.js(ALL); game.boss(1)
    game.js("energy=100; useWater()")                                # 封印だけ: 6秒
    six = game.js("boss.sealUntil")
    game.js("energy=100; useBroom()")                                # 特効: 10秒にのびる
    ten = game.js("boss.sealUntil")
    assert 3900 < ten - six <= 4100
    game.js("energy=100; useWater()")                                # もう一度 6秒: 短くならない
    assert game.js("[boss.sealUntil, talk.text]") == [ten, "王冠を封じた！\nいまのうちに攻撃する！"]


def test_crown_from_pops(game):
    """[BOSS-09] 封印中に消すと個数×3、ふだんは2連鎖以上で個数×1.2、王冠がけずれる。1連鎖ではけずれない。"""
    game.boss(0); game.clear_board()
    game.put(5, 0); game.wait(2500)
    assert game.js("boss.crown") == 2000                              # 1連鎖
    game.js("boss.sealUntil=performance.now()+60000")
    game.put(5, 1); game.wait(2500)
    assert game.js("boss.crown") == 2000 - 15


def test_sealed_boss_cannot_attack(game):
    """[BOSS-10] 封印中と、王冠がこわれたあとは、ボスは妨害できない。"""
    game.boss(0); game.clear_board()
    game.js("boss.sealUntil=performance.now()+60000; boss.nextAtk=performance.now()+300")
    game.wait(1500)
    assert game.js("balls.filter(o=>o.c===GARBAGE).length") == 0
    game.js("boss.sealUntil=0; boss.crown=0; boss.nextAtk=performance.now()+300")
    game.wait(1500)
    assert game.js("balls.filter(o=>o.c===GARBAGE).length") == 0


def test_crown_break_gem(game):
    """[BOSS-11] 王冠が0になるとこわれ、5割の確率でそのワールドの宝石が1個もらえる。"""
    game.boss(2)
    game.js("Math.random=()=>0.1; crownHit(99999, performance.now())")
    assert game.js("[boss.crown, gems.ice, !!crownFx]") == [0, 1, True]


def test_defeat_and_rewards(game):
    """[BOSS-12][GEM-01][GEM-02][WORLD-05] 撃破でワールドクリア: 宝石1〜3個、王冠をこわしていれば虹の宝石1個、クリア回数+1、ライフ+1。"""
    game.boss(2)
    lives = game.js("lives.n")
    game.js("boss.crown=0; chain=1; hitBoss(99999, performance.now())")
    game.wait(9000)
    assert game.js("menuKind") == "clear"
    assert 1 <= game.js("gems.ice") <= 3
    assert game.js("[gems.rainbow, worldClears.ice, lives.n]") == [1, 1, lives + 1]


def test_no_rainbow_without_crown_break(game):
    """[GEM-02] 王冠をこわさずに倒すと、虹の宝石はもらえない。"""
    game.boss(2)
    game.js("chain=1; hitBoss(99999, performance.now())")
    game.wait(9000)
    assert game.js("[menuKind, gems.rainbow||0]") == ["clear", 0]


def test_storm_blocks_bonds(game):
    """[BOSS-13] 砂嵐の間は、ぷにがくっつかず、消えない。"""
    game.boss(1); game.clear_board()
    game.js("bossAbility(performance.now())"); game.wait(300)
    assert game.js("!!boss.storm") is True
    game.put(5, 0); game.wait(1200)
    assert game.js("[popped, bonds.length]") == [0, 0]


@pytest.mark.parametrize("item,k", PAIRS["特効"])
def test_every_weakness(game, item, k):
    """[BOSS-05][BOSS-08][LAB-04] 特効になる組は、どれも: 妨害を10秒封じ、王冠を15%けずり、弱点が記録されて、研究所と画面に相手の名前が出る。"""
    game.js(ALL); game.boss(WORLDS.index(k))
    assert game.js(f"weakKnown('{k}')") is False
    use(game, item)
    assert game.js("[boss.crown, talk.text.split('\\n')[0], weakFound]") == [1700, "弱点を見破った！！", [k]]
    assert 9000 < game.js("boss.sealUntil-performance.now()") <= 10000
    name = game.js(f"THEMES.find(t=>t.k==='{k}').name")
    assert game.js(f"weakText('{k}')") == "弱点: " + game.js(f"ITEM_NAME['{item}']")
    game.js("paused=true; showMenu('skills')"); game.wait(300)        # 研究所にも相手の名前が出る
    card = game.page.locator(".lab.own", has_text=game.js(f"ITEM_NAME['{item}']"))
    assert f"{name}のボスにきく" in card.inner_text()
    others = [b for i, b in PAIRS["特効"] if i == item and b != k]      # 同じ道具が特効になる、まだ見破っていないボスは、伏せたまま
    assert card.inner_text().count("？？？のボスにきく") == len(others)


def test_weakness_pairs():
    """[BOSS-08] 宇宙のほかのボスには、特効の道具が1つずつある（マグマとポップコーンは同じ席なので、どちらもストップ）。"""
    assert sorted(PAIRS["特効"]) == sorted([("mag", "meadow"), ("broom", "desert"), ("shuf", "ice"), ("hand", "flower"), ("jump", "sticky"),
                                           ("stop", "magma"), ("water", "fire"), ("stop", "popcorn"), ("fire", "bouncy")])
    assert sorted(PAIRS["同じ"]) == sorted([("shuf", "desert"), ("stop", "sticky"), ("pop", "magma"), ("pop", "popcorn"), ("fire", "fire"), ("weight", "bouncy")])


@pytest.mark.parametrize("item,k", PAIRS["同じ"])
def test_same_seat(game, item, k):
    """[BOSS-07] ボスと同じ席の道具は、どれも1%「あまり効いてない…」。封印しない。"""
    game.js(ALL); game.boss(WORLDS.index(k))
    use(game, item)
    assert game.js("[boss.crown, talk.text, talk.mood, boss.sealUntil]") == [1980, "あまり効いてない…", "worry", 0]


def test_puni_king_no_beam(game):
    """[BOSS-21] ぷにキング（草原）の妨害は「お邪魔ふらし」だけ。いじわる光線は、ふだんのプレイでは出ない（開発用の切りかえ beamDev を入れたときだけ出る）。"""
    game.boss(0, quiet=False); game.clear_board(); game.js("stopLeft=0")       # （ストップ中は、ボスも止まるので、切っておく）
    assert game.js("[beamDev, BOSS_ABIL.meadow, ABIL_DESC.meadow]") == [False, "お邪魔ふらし", "お邪魔ぷにを降らせる"]
    game.js("boss.nextBeam=performance.now()-1; window.__beams=0; const bs=beamStep; beamStep=function(n){ bs(n); if(beam) window.__beams++; }")
    game.js("bossAbility(performance.now())")
    assert game.js("[balls.filter(o=>o.c===GARBAGE).length>=2, abilFx.text]") == [True, "お邪魔ふらし！"]     # 妨害は、お邪魔ふらし
    game.wait(2500)
    assert game.js("[beam, window.__beams]") == [None, 0]                    # 光線の番が来ても、出ない
    game.js("beamDev=true; boss.nextAtk=performance.now()+1e9; boss.nextBeam=performance.now()-1"); game.wait(400)
    assert game.js("!!beam") is True                                         # 光線のコードと、開発用の切りかえは残っている
    game.js("beamDev=false")


def test_seat_shown_on_boss(game):
    """[BOSS-22] ボス戦の画面: ボスの体力バーのそばに、ボスの席（属性と手）を出す。タイプの名前（たいぼく など）は出さない。"""
    game.js("window.__seats=[]; const ds=drawSeat; drawSeat=function(g,seat,x,y,r){ window.__seats.push([seat,x,y,r]); return ds(g,seat,x,y,r); }")
    game.boss(6); game.wait(300)                                             # ハニーキング: 水のパー
    seat, x, y, r = game.js("window.__seats.at(-1)")
    assert seat == ["水", "パー"] == BOSS_SEAT["べたべた"]
    w = game.js("document.getElementById('board').width")
    assert r >= 6 and 0 <= x - r * 4.5 and x < w * 0.25 and 0 < y - r * 1.25 and y < w * 0.15    # 盤面の左上、体力バーの左に、おさまっている
    px = game.js(f"[...document.getElementById('board').getContext('2d').getImageData({x}-{r}*4.5+{r}*1.25-{r}*0.75|0, {y}|0, 1, 1).data].slice(0,3)")
    assert px == [0x2f, 0x7f, 0xe8]                                          # 属性の丸は、水の色
    src = game.js("document.documentElement.outerHTML")
    for name in ["たいぼく", "いばら", "けっしょう", "てっきゅう", "ようがん", "じしゃく", "ながれぼし"]:
        assert name not in src                                               # タイプの名前は、裏設定のまま


def test_seat_shown_on_items(game):
    """[ITEM-16] プレイ中の道具ボタンに、席（属性と手）の小さな札を出す。エネルギー缶には出さない。札は、消費エネルギーのバッジと重ならない。"""
    game.js(ALL)
    box = "(q=>{ const r=document.querySelector(q).getBoundingClientRect(); return [r.left,r.top,r.right,r.bottom]; })"
    for lay in ["ringL", "tiles", "ring"]:
        game.js(f"layoutKey='{lay}'; layoutItems()")
        game.start(); game.wait(200)
        shown = game.js("Object.keys(ITEM_EL).filter(k=>document.getElementById(ITEM_EL[k]).offsetWidth>0)")
        assert len(shown) >= 6
        for k in shown:
            el = game.page.locator(f"#{game.js(f'ITEM_EL.{k}')} .seat")
            if k == "can":
                assert el.count() == 0
                continue
            e, h = next(s for n, s in ITEM_SEAT.items() if ITEM_KEY[n] == k)
            assert el.is_visible() and el.inner_text().replace("\n", "") == e + HAND_IC[h] and el.get_attribute("aria-label") == f"{e}の{h}"
            s, b = game.js(f"{box}('#'+ITEM_EL.{k}+' .seat')"), game.js(f"{box}('#'+ITEM_EL.{k}+' .badge')")
            assert s[2] <= b[0] or b[2] <= s[0] or s[3] <= b[1] or b[3] <= s[1], f"{lay}: {k} の席の札が、バッジと重なっている"
            assert s[3] - s[1] <= 34 and s[2] - s[0] <= 40                   # じゃまにならない小ささ
        game.js("goHome()")


def test_counter_cleanup(game):
    """[BOSS-16] 道具は、ふだんの効果で、ボスの妨害の後始末もする（氷・花びら・火の粉）。相性とは別に、いつでも起きる。"""
    game.js(ALL)
    game.boss(2); game.clear_board()                                     # アイスキング: 氷がとける
    game.put(4, 0); game.put(4, 1, row=1)
    game.js("bossAbility(performance.now())")
    assert game.js("balls.filter(o=>o.frozen).length") >= 3
    game.js("energy=100; useFire()")
    assert game.js("[balls.filter(o=>o.frozen).length, talk.text]") == [0, "王冠を封じた！\nいまのうちに攻撃する！"]    # ひのたま（火のパー）は、アイスキング（水のグー）を封じる。王冠は大きくけずれない
    game.js("goHome()")
    game.boss(8); game.clear_board()                                     # フラワークイーン: 舞っている花びらが消える
    game.put(2, 0)
    game.js("bossAbility(performance.now())")
    assert game.js("!!petalFx") is True
    game.js("energy=100; useBroom()")
    assert game.js("[petalFx, talk.text]") == [None, "王冠を封じた！\nいまのうちに攻撃する！"]                # ほうき（木のチョキ）は、フラワークイーン（木のパー）を封じる
    game.js("goHome()")
    game.boss(3); game.clear_board()                                     # ファイアキング: 飛んでいる火の粉が消える
    game.put(4, 0)
    game.js("boss.lv=3; bossAbility(performance.now())")
    assert game.js("[!!emberFx, boss.emberLeft]") == [True, 2]              # 1つ飛んでいて、あと2つ出る
    game.js("energy=100; useWater()")
    assert game.js("[emberFx, boss.emberLeft, balls.length]") == [None, 0, 4]
    game.wait(1500)
    assert game.js("balls.filter(o=>!o.live).length") == 4               # ぷには、とかされない


def test_stop_cools_magma(game):
    """[BOSS-15] ストップでボスを封じたとき（マグマキングには特効）、盤面のマグマぷにがお邪魔ぷにに変わる。封じられない相手（同じ席のハニーキング）では、変わらない。"""
    game.js(ALL); game.boss(9); game.clear_board()
    game.js("for(let i=0;i<3;i++) balls.push(newBall(1.5+i*4*R, N-R-0.01, MAGMA)); dirty=true")
    game.js("energy=100; stopLeft=0; useStop()")
    assert game.js("[balls.filter(o=>o.c===MAGMA).length, balls.filter(o=>o.c===GARBAGE).length, talk.text]") == [0, 3, "弱点を見破った！！\n弱点はストップだ！"]
    game.js("goHome()")
    game.boss(6); game.clear_board()
    game.js("for(let i=0;i<3;i++) balls.push(newBall(1.5+i*4*R, N-R-0.01, MAGMA)); dirty=true")
    game.js("energy=100; stopLeft=0; useStop()")
    assert game.js("[balls.filter(o=>o.c===MAGMA).length, talk.text]") == [3, "あまり効いてない…"]


def test_shuffle_shakes_off_honey(game):
    """[BOSS-15][ITEM-06] ハニーキング（水）にシャッフル（土）を使うと、巻きこんだぷにのべたべたが取れ、かたまりがばらける（属性で勝つ「王冠だけ」。封印はしない）。残ったぷにと、ほかの相手のときは、べたべたのまま。"""
    game.js(ALL); game.boss(6); game.clear_board()
    game.put(4, 0); game.put(4, 1, row=1); game.wait(500)
    game.js("for(const o of balls) o.sticky=true; makeBonds()")
    assert game.js("bonds.some(([a,b])=>a.c!==b.c)") is True              # べたべたで、違う色がかたまりになっている
    game.js("energy=100; useShuffle()")
    assert game.js("[talk.text, boss.crown, boss.sealUntil]") == ["王冠に効いてる！", 1800, 0]
    assert game.js("[shuffle.to.length, shuffle.to.filter(b=>b.sticky).length, bonds.length]") == [5, 0, 0]   # Lv1 は8個の6割 = 5個を巻きこむ
    assert game.js("balls.filter(o=>!o.live).map(o=>!!o.sticky)") == [True] * 3                               # 巻きこまれなかった3個は、そのまま
    game.wait(2600)
    assert game.js("[shuffle, balls.length, balls.filter(o=>o.sticky).length]") == [None, 8, 3]
    game.js("goHome()")
    game.boss(1); game.clear_board()                                     # サンドキング（同じ席）のときは、べたべたは取れない
    game.put(4, 0); game.put(4, 1, row=1); game.wait(500)
    game.js("for(const o of balls) o.sticky=true")
    game.js("energy=100; useShuffle()")
    assert game.js("shuffle.to.filter(b=>b.sticky).length") == 5


def test_can_no_crown_damage(game):
    """[ITEM-15][EN-14] ボス戦でエネルギー缶を使っても、王冠にダメージを与えず、妨害も封じない（エネルギーは満タンになる）。"""
    game.js("carry.can=1"); game.boss(1)
    crown, hp = game.js("[boss.crown, boss.hp]")
    game.js("energy=10; useCan()")
    assert game.js("[energy, carry.can, canUsed]") == [100, 0, True]
    assert game.js("[boss.crown, boss.hp, weakFound]") == [crown, hp, []]
    assert not (game.js("boss.sealUntil") or 0) > game.js("performance.now()")


def test_no_magma_in_pieces_during_boss(game):
    """[BOSS-17] マグマワールドのボス戦の間は、落ちてくる組にマグマぷにがまざらない（ふだんのステージではまざる）。"""
    game.start(9)
    count = "(()=>{ let n=0; for(let i=0;i<300;i++) if(newPair().c.includes(MAGMA)) n++; return n; })()"
    assert game.js(count) > 50
    game.js("level=worldNo*5+5; startBoss(performance.now()); boss.nextAtk=performance.now()+1e9")
    assert game.js(count) == 0


def test_black_hole(game):
    """[BOSS-24] ブラックホール: ランダムに5個を出口へ吸いこむ。つながりが外れ、しばらくくっつかない。"""
    game.boss(5); game.clear_board()
    for row in range(3):
        game.put(4, row, row=row)                                          # 4個ずつ（消えない数）
    game.wait(900)
    assert game.js("bonds.length") >= 6
    y0 = game.js("Math.min(...balls.map(o=>o.y))")
    game.js("stopLeft=0; bossAbility(performance.now())"); game.wait(700)
    assert game.js("[!!boss.hole, boss.hole.set.size, balls.filter(o=>o.noBond>performance.now()).length]") == [True, 5, 5]
    assert game.js("Math.min(...balls.map(o=>o.y))") < y0 - 1.5            # 山から引きはがされて、上がっている
    assert game.js("[...boss.hole.set].every(o=>!bonds.some(b=>b.a===o||b.b===o))") is True
    game.wait(1300)
    assert game.js("boss.hole") is None


def test_black_hole_sealed(game):
    """[BOSS-24][BOSS-10] 封印すると、吸いこみはその場で止まる。"""
    game.js("devItems=['stop']"); game.boss(5); game.clear_board(); game.put(9, 0); game.wait(600)
    game.js("stopLeft=0; bossAbility(performance.now())"); game.wait(200)
    assert game.js("!!boss.hole") is True
    game.js("energy=100; useStop()"); game.wait(200)
    assert game.js("boss.hole") is None


def test_aisho_banner(game):
    """[BOSS-25] 道具を使うと、相性の結果が盤面に大きく出る。"""
    game.js("devItems=['stop','broom','shuf']"); game.boss(1)                # 砂漠（土のパー）
    for fn, kind in (("useBroom", "sp"), ("useBoost", "normal")):
        game.js(f"aishoFx=null; energy=100; boostLeft=0; {fn}()".format(fn=fn)); game.wait(300)
        assert game.js("aishoFx && aishoFx.kind") == kind
    game.wait(AISHO_WAIT)
    assert game.js("aishoFx") is None
