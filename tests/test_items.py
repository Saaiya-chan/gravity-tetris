"""アイテム・強化・ぷに研究所（ITEM / UP / LAB）"""
import pytest

GEM_ITEM = {"sticky": "hand", "space": "mag", "bouncy": "jump", "ice": "stop", "desert": "shuf",
            "meadow": "broom", "popcorn": "pop", "magma": "weight", "fire": "fire", "flower": "water"}
NAMES = {"boost": "ブースター", "stop": "ストップ", "mag": "マグネット", "shuf": "シャッフル", "jump": "ジャンプ", "hand": "魔法の手",
         "broom": "ほうき", "pop": "はじけ玉", "weight": "おもし", "fire": "ひのたま", "water": "じょうろ"}


def test_only_boost_at_first(game):
    """[ITEM-01] 最初から使えるのはブースターだけ。"""
    got = game.js("['stop','mag','shuf','jump','boost','hand','broom','pop','weight','fire','water'].filter(itemOpen)")
    assert got == ["boost"]


@pytest.mark.parametrize("fn,var,ms", [("useStop", "stopLeft", 6000), ("useMag", "magLeft", 6000),
                                        ("useBoost", "boostLeft", 15000), ("useHand", "handLeft", 5000),
                                        ("useWeight", "weightLeft", 8000)])
def test_durations(game, fn, var, ms):
    """[ITEM-02] 効果時間: ストップ6秒・マグネット6秒・ブースター15秒・魔法の手5秒・おもし8秒。"""
    game.js("devItems=['stop','mag','hand','weight']")
    game.start()
    game.js(f"energy=100; {fn}()")
    assert ms - 400 <= game.js(var) <= ms


def test_no_stack(game):
    """[ITEM-03] 効果が続いている間は、同じアイテムを重ねて使えない。"""
    game.js("devItems=['mag']")
    game.start()
    game.js("energy=100; useMag(); useMag()")
    assert game.js("energy") == 60


def test_stop_extends_others(game):
    """[ITEM-04] ほかのアイテムの効果中にストップを使うと、その効果が元の長さの2割のびる（1回の効果につき1度だけ）。"""
    game.js("devItems=['stop','mag']")
    game.start()
    game.js("energy=100; useMag(); useStop()")
    assert game.js("itemTot.mag") == pytest.approx(7200)
    game.js("stopLeft=0; energy=100; useStop()")
    assert game.js("itemTot.mag") == pytest.approx(7200)


def test_level_extends_duration(game):
    """[UP-03] 時間で効くアイテムは、レベルが1上がるごとに効果時間が2割のびる（Lv5で1.8倍）。"""
    game.js("devItems=['mag']; itemLv.mag=2")
    game.start()
    game.js("energy=100; useMag()")
    assert game.js("itemTot.mag") == pytest.approx(6000 * 1.4)
    game.js("magLeft=0; itemLv.mag=4; energy=100; useMag()")
    assert game.js("itemTot.mag") == pytest.approx(6000 * 1.8)


def test_jump_power(game):
    """[UP-04] ジャンプは、レベルが1上がるごとにジャンプ力が2割ふえる。"""
    assert game.js("UP_TEXT.jump") == "ジャンプ力 +20%"
    game.js("devItems=['jump']")
    game.start(); game.clear_board(); game.put(4, 0); game.put(4, 1, row=1); game.wait(600)
    def top():
        game.wait(1500)                                              # 落ちて止まるのを待つ
        return game.js("(()=>{ for(const o of balls){o.vx=0;o.vy=0;} energy=100; Math.random=()=>0.5; useJump(); return Math.max(...balls.map(o=>Math.hypot(o.vx,o.vy))); })()")
    v1 = top()
    game.js("itemLv.jump=2")
    v3 = top()
    assert v3 / v1 == pytest.approx((1.4) ** 0.5, rel=0.02)      # 高さ1.4倍 = 速さ√1.4倍


def test_develop(game):
    """[LAB-01] 宝石5個で開発できる。足りないぶんは虹の宝石で払える。"""
    game.js("gems={space:4}")
    assert game.js("canDevelop('mag')") is False
    game.js("gems={space:3, rainbow:3}")
    assert game.js("develop('mag')") is True
    assert game.js("[gems.space, gems.rainbow, itemOpen('mag')]") == [0, 1, True]


def test_gem_item_table(game):
    """[LAB-02] 宝石とアイテムの対応。"""
    assert game.js("GEM_ITEM") == GEM_ITEM
    assert sorted(GEM_ITEM) == sorted(game.js("THEMES.map(t=>t.k)"))      # 全10ワールドの宝石に、作れるアイテムがある
    assert game.js("[typeof GEM_SOON, typeof COUNTER_SOON]") == ["undefined", "undefined"]            # 準備中の表は、もう無い


def test_upgrade(game):
    """[UP-01][UP-02] 強化は宝石3個（虹で代用可）、ブースターは虹1個。Lv5まで。"""
    game.js("devItems=['mag']; gems={space:5, rainbow:2}")
    assert game.js("[upgrade('mag'), lvOf('mag'), gems.space]") == [True, 2, 2]
    assert game.js("[upgrade('mag'), lvOf('mag'), gems.space, gems.rainbow]") == [True, 3, 0, 1]
    assert game.js("canUpgrade('mag')") is False                  # 宝石がたりない（2個+虹1個が要る）
    assert game.js("[upgrade('boost'), lvOf('boost'), gems.rainbow]") == [True, 2, 0]
    assert game.js("canUpgrade('boost')") is False                # 虹の宝石がない
    game.js("gems={space:99, rainbow:99}")
    assert game.js("[upgrade('mag'), upgrade('mag'), lvOf('mag')]") == [True, True, 5]
    assert game.js("[UP_MAX, canUpgrade('mag'), upgrade('mag'), lvOf('mag'), gems.space]") == [5, False, False, 5, 93]   # Lv5 が上限


def test_lab_max(game):
    """[UP-02][LAB-03] 研究所: Lv5 まで強化ボタンで上げられ、Lv5 になると強化ボタンが消えて「MAX」と出る。"""
    game.js("devItems=['mag']; gems={space:99}; showMenu('skills')"); game.wait(300)
    card = game.page.locator(".lab.own", has_text="マグネット")
    for lv in range(1, 5):
        assert card.locator(".lab-lv").inner_text() == f"Lv{lv}"
        card.locator("button[data-up='mag']").click(); game.wait(200)
    assert card.locator(".lab-lv").inner_text() == "Lv5"
    assert card.locator("button[data-up]").count() == 0 and card.locator(".lab-max").inner_text() == "MAX"
    assert game.js("[lvOf('mag'), gems.space, enCost('mag')]") == [5, 87, 56]
    boost = game.page.locator(".lab.own", has_text="ブースター")       # 宝石がたりないアイテムは、ボタンが押せない
    assert boost.locator("button[data-up='boost']").is_disabled()


def test_lab_screen(game):
    """[LAB-03][LAB-04][LAB-05] 研究所: 開発ずみは消費エネルギーつきで並び、特効になる相手は見破るまで「？？？」。どのカードにも、道具の席（属性と手）が出る。"""
    game.js("devItems=['mag','stop','pop']; showMenu('skills')"); game.wait(300)
    text = game.page.locator("#overlay").inner_text()
    assert "消費エネルギー" in text and "？？？" in text
    card = lambda name: game.page.locator(".lab", has_text=name)
    assert card("マグネット").inner_text().count("？？？のボスにきく") == 1      # マグネットが特効になるのは、草原のボス
    assert card("ストップ").inner_text().count("？？？のボスにきく") == 2        # ストップは、マグマとポップコーンの2体
    assert "のボスにきく" not in card("はじけ玉").inner_text() and "のボスにきく" not in card("ブースター").inner_text()   # 特効の相手がまだいない道具には、出さない
    game.js("weakFound=['meadow','magma']; showMenu('skills')"); game.wait(300)
    assert "草原のボスにきく" in card("マグネット").inner_text() and "？？？" not in card("マグネット").inner_text()
    assert "マグマのボスにきく" in card("ストップ").inner_text() and card("ストップ").inner_text().count("？？？のボスにきく") == 1
    seat = lambda name: card(name).locator("h3 .seat")
    assert [seat(n).get_attribute("aria-label") for n in ["ブースター", "マグネット", "ストップ", "はじけ玉"]] == ["日のグー", "金のパー", "水のパー", "火のグー"]
    assert seat("ストップ").inner_text().replace("\n", "") == "水🖐️" and seat("ストップ").is_visible()
    assert game.page.locator(".lab.todo h3 .seat").count() == 7                 # これから開発する道具にも、席が出る（宝石で何を作るか、えらぶ手がかり）
    assert game.page.locator(".lab h3 .seat").count() == 11
    for name in ["たいよう", "じしゃく", "うみ", "ようがん"]:                   # タイプの名前は出さない
        assert name not in game.page.locator("#overlay").inner_text()


@pytest.mark.parametrize("lv,rate", [(1, 0.6), (2, 0.7), (3, 0.8), (4, 0.9), (5, 1.0)])
def test_shuffle_rate(game, lv, rate):
    """[ITEM-06][UP-06] シャッフルが巻きこむのは Lv1 で6割。レベルごとにふえて、最大レベルで全部。残りはその場に残る。"""
    game.js(f"devItems=['shuf']; itemLv.shuf={lv - 1}")
    assert game.js("shufRate()") == pytest.approx(rate)
    assert game.js("UP_TEXT.shuf") == "巻きこむ割合 +10%"
    game.start(); game.clear_board()
    for row, c in enumerate((0, 1, 2, 3, 0)):
        game.put(4, c, row=row)
    game.wait(700)
    game.js("energy=100; useShuffle()")
    assert game.js("[shuffle.from.length, balls.filter(o=>!o.live).length]") == [round(20 * rate), 20 - round(20 * rate)]
    game.wait(2500)
    assert game.js("shuffle") is None                                # 演出が終わって、ばらまかれた


# ===== 新しいアイテム5種（ほうき・はじけ玉・おもし・ひのたま・じょうろ） =====

def count(game, cond):
    return game.js(f"balls.filter(o=>{cond}).length")


@pytest.mark.parametrize("gem,item", [(g, i) for g, i in GEM_ITEM.items() if i in ("broom", "pop", "weight", "fire", "water")])
def test_develop_new(game, gem, item):
    """[LAB-01][LAB-02] 新しい5種も、対応する宝石5個で開発できる。"""
    game.js(f"gems={{{gem}:4}}")
    assert game.js(f"canDevelop('{item}')") is False
    game.js(f"gems={{{gem}:5}}")
    assert game.js(f"[develop('{item}'), itemOpen('{item}'), gems.{gem}]") == [True, True, 0]


def test_lab_all_items(game):
    """[LAB-03] 研究所: 11種すべてが「つかえるアイテム」か「これから開発」のどちらかに名前つきで並ぶ（じゅんび中は無い）。"""
    game.js("devItems=['mag','broom','fire']; showMenu('skills')"); game.wait(300)
    own = [t.split("\n")[0] for t in game.page.locator(".lab.own h3").all_inner_texts()]       # （名前のあとに、席の札がつく。LAB-05）
    todo = [t.split("\n")[0] for t in game.page.locator(".lab.todo h3").all_inner_texts()]
    assert own == ["ブースター", "マグネット", "ほうき", "ひのたま"]
    assert sorted(own + todo) == sorted(NAMES.values()) and len(todo) == 7
    text = game.page.locator("#overlay").inner_text()
    assert "じゅんび中" not in text and "ぷよ" not in text
    card = game.page.locator(".lab.own", has_text="ひのたま")
    assert "消費エネルギー 35" in card.inner_text().replace("\n", " ") and "燃やす数 +1個" in card.inner_text()


def test_broom(game):
    """[ITEM-09][EN-09] ほうき: 止まっているぷにの べたべた・感染・時限をはらい落とし、舞っている花びらを消す。Lv1 ではお邪魔ぷには減らない。消費25。"""
    game.js("devItems=['broom']")
    game.start(); game.clear_board()
    game.put(3, 0); game.put(3, 1, row=1); game.put(2, "GARBAGE", row=2)
    game.js("balls[0].sticky=true; balls[3].sticky=true; balls[1].virus=true; balls[1].vLeft=3; balls[4].timer=20000; makeBonds()")
    assert game.js("bonds.some(([a,b])=>a.c!==b.c)") is True              # べたべたで、違う色がくっついている
    game.js("petalFx={t:performance.now(), seed:1}; energy=100; useBroom()")
    assert game.js("petalFx") is None                                     # 舞っている花びらも、はき出す
    assert count(game, "o.sticky||o.virus||o.timer!=null") == 0
    assert game.js("bonds.some(([a,b])=>a.c!==b.c)") is False             # 違う色どうしは、はなれる
    assert game.js("[balls.length, popped, energy]") == [8, 0, 75]
    assert count(game, "o.c===GARBAGE") == 2


def test_broom_upgrade(game):
    """[UP-07] ほうきは、レベルが1上がるごとに、お邪魔ぷにを1個多くはき出す（Lv1は0個）。消した数には数えない。"""
    assert game.js("UP_TEXT.broom") == "はき出すお邪魔ぷに +1個"
    game.js("devItems=['broom']; itemLv.broom=2")
    game.start(); game.clear_board()
    game.put(4, "GARBAGE")
    game.js("energy=100; useBroom()")
    assert game.js("[balls.length, popped, score]") == [2, 0, 40]


def test_pop_item(game):
    """[ITEM-10][EN-09] はじけ玉: まわりのぷにを、お邪魔ぷにごと消す。消した数・スコア・エネルギー・ボスへのダメージに数える。消費35。"""
    game.js("devItems=['pop']")
    game.boss(5); game.clear_board()                                     # 宇宙のボス（月のグー。はじけ玉は「ふつう」）
    game.js("energy=100; usePop()")
    assert game.js("energy") == 100                                      # ぷにが無ければ使えない
    game.put(2, 0); game.put(2, 1, row=1); game.put(2, "GARBAGE", row=2)
    game.js("energy=100; usePop()")
    assert game.js("[popped, chain, energy, boss.maxHp-boss.hp]") == [6, 1, 100 - 35 + 6, 6]
    assert game.js("score") > 0
    game.wait(1200)
    assert game.js("balls.filter(o=>!o.live).length") == 0


def test_pop_upgrade(game):
    """[UP-08] はじけ玉は、レベルが1上がるごとに、爆発の広さが1割ふえる。"""
    assert game.js("UP_TEXT.pop") == "爆発の広さ +10%"
    r1 = game.js("popRad()")
    assert r1 == pytest.approx(game.js("2.6*2*R"))
    game.js("itemLv.pop=2")
    assert game.js("popRad()") == pytest.approx(r1 * 1.2)
    game.js("devItems=['pop']; itemLv.pop=4")                              # 広くなると、遠くのぷににも届く
    game.start(); game.clear_board()
    game.put(5, "GARBAGE"); game.js("for(let i=0;i<5;i++) balls[i].x=1.5+i*1.3")
    game.js("energy=100; usePop()")
    assert game.js("popped") == 5
    game.wait(1200); game.js("itemLv.pop=0")
    game.put(5, "GARBAGE"); game.js("for(let i=0;i<5;i++) balls[i].x=1.5+i*1.3")
    game.js("energy=100; usePop()")
    assert game.js("popped") == 5 + 3                                     # Lv1 では、真ん中から両どなりまで


def test_weight(game):
    """[ITEM-11][BOSS-16][EN-09][TALK-07] おもし: 効いている間は、ボスのおおゆれでもはね上げられない。壁でもはずまない。消費30。"""
    game.js("devItems=['weight']")
    game.boss(4); game.clear_board()                                     # トランポリン（ボヨンキング）
    game.put(4, 0); game.put(4, 1, row=1); game.wait(1200)
    fastest = "Math.max(...balls.map(o=>Math.hypot(o.vx,o.vy)))"
    game.js("bossAbility(performance.now())")
    assert game.js(fastest) > 5                                           # ふだんは、全部はね上げられる
    assert game.js(f"(()=>{{ energy=100; useWeight(); return [energy, weightLeft>7500, {fastest}]; }})()") == [70, True, 0]   # 飛ばされている途中でも、その場で止まって落ちる
    game.js("talkReset(); bossAbility(performance.now())")               # （相性のセリフが出ている間は、下の優先度のセリフは出ないので、いったん消しておく）
    assert game.js("[talk.text, talk.mood, abilFx.text]") == ["おもしで\nびくともしない！", "happy", "おおゆれ！"]   # ぷに妖精が知らせる（TALK-07）。盤面には妨害の名前だけ
    assert game.js(fastest) < 2                                           # はね上げられない（重力で落ちる速さだけ）
    hit = "(()=>{ balls.forEach((o,i)=>{ o.x=1.2+i; o.y=R; o.vx=0; o.vy=-20; }); physicsStep(16); return Math.max(...balls.map(o=>o.vy)); })()"
    assert game.js(hit) < 2                                               # 天井にぶつけても、はね返らない
    game.js("weightLeft=0")
    assert game.js(hit) > 5                                               # おもしが切れると、またはずむ


def test_weight_clock(game):
    """[ITEM-08] おもしが効いている間、ボタンに残り時間の扇形が出る。"""
    game.js("devItems=['weight']; slots.L0='weight'; layoutItems()")
    game.start()
    game.js("energy=100; useWeight()"); game.wait(300)
    assert game.js("document.getElementById('itemWeight').classList.contains('timing')") is True
    assert 0.8 < float(game.js("document.getElementById('itemWeight').style.getPropertyValue('--left')")) <= 1


def test_stop_extends_weight(game):
    """[ITEM-04][UP-03] おもしも、ストップの隠し効果で2割のびる。レベルでも2割ずつのびる。"""
    game.js("devItems=['stop','weight']")
    game.start()
    game.js("energy=100; useWeight(); useStop()")
    assert game.js("itemTot.weight") == pytest.approx(9600)
    game.js("weightLeft=0; itemLv.weight=2; energy=100; useWeight()")
    assert game.js("itemTot.weight") == pytest.approx(8000 * 1.4)
    assert game.js("UP_TEXT.weight") == "効果時間 +20%"


@pytest.mark.parametrize("lv,n", [(1, 6), (2, 7), (5, 10)])
def test_fire(game, lv, n):
    """[ITEM-12][UP-09][EN-09] ひのたま: 凍ったぷにを全部とかし、お邪魔ぷにを最大6個（レベルごとに+1）燃やす。消した数には数えない。"""
    assert game.js("UP_TEXT.fire") == "燃やす数 +1個"
    game.js(f"devItems=['fire']; itemLv.fire={lv - 1}")
    game.start(); game.clear_board()
    game.put(3, 0)
    for row in (1, 2, 3):
        game.put(4, "GARBAGE", row=row)
    game.js("for(const o of balls) if(o.c===0) o.frozen=true")
    cost = game.js("enCost('fire')")
    game.js("energy=100; useFire()")
    assert count(game, "o.frozen") == 0 and count(game, "o.c===0") == 3
    assert count(game, "o.c===GARBAGE") == 12 - n
    assert game.js("[popped, chain, score, energy]") == [0, 0, 20 * n, 100 - cost]
    assert cost == round(35 * (1 + 0.1 * (lv - 1)) + 1e-9)


@pytest.mark.parametrize("lv,n", [(1, 4), (2, 5), (5, 8)])
def test_water(game, lv, n):
    """[ITEM-13][UP-10][EN-09] じょうろ: 火の粉とマグマぷにを消し、お邪魔ぷにを最大4個（レベルごとに+1）ふつうのぷにに育てる。"""
    assert game.js("UP_TEXT.water") == "育てる数 +1個"
    game.js(f"devItems=['water']; itemLv.water={lv - 1}")
    game.start(3); game.clear_board()                                     # 炎ワールド
    game.put(2, "MAGMA")
    for row in (1, 2, 3):
        game.put(3, "GARBAGE", row=row)
    game.js("emberFx={t0:performance.now(), o:balls[2], x0:0, y0:0}")
    cost = game.js("enCost('water')")
    game.js("energy=100; useWater()")
    assert game.js("emberFx") is None
    assert count(game, "o.c===MAGMA") == 0
    assert [count(game, "o.c===GARBAGE"), count(game, "o.c>=0&&o.c<5")] == [9 - n, n]
    assert game.js("[balls.length, popped, score, energy]") == [9, 0, 0, 100 - cost]


def test_slots(game):
    """[ITEM-14] ボタンはスロット（8か所）に置いたものだけ出る。開発すると空きスロットへ自動で入り、空きがなければ「アイテム配置」で入れ替える。"""
    game.js("gems={meadow:5, fire:5, popcorn:5, flower:5, magma:5}")
    assert game.js("SLOT_DEF.length") == 8
    game.js("develop('broom'); develop('fire')")
    assert game.js("[slots.L0, slots.L2, slots.L1]") == ["can", "broom", "fire"]   # 空いている場所へ（左手1はエネルギー缶。左手2は、まだ使えない魔法の手の場所をゆずる）
    game.js("develop('pop')")
    used = game.js("Object.values(slots)")
    assert "pop" in used and "hand" not in used                           # まだ使えない魔法の手の場所をゆずる
    game.js("devItems=['stop','mag','shuf','jump','hand','broom','fire','pop','water','weight']")
    game.start()
    shown = game.js("[...document.querySelectorAll('.item')].filter(e=>getComputedStyle(e).display!=='none').map(e=>e.id)")
    assert len(shown) <= 8 and "itemBroom" in shown and "itemWater" not in shown
    game.js("slots.L0=''; layoutItems(); openSlotPick('L0', document.querySelector('.slotEmpty'))")
    picks = game.page.locator("#slotPick button[data-k]").all_inner_texts()
    assert len(picks) == 5 and any("じょうろ" in t for t in picks)        # 置いていない・開発ずみのもの（とエネルギー缶）から選べる
    game.page.locator("#slotPick button[data-k='water']").click(); game.wait(200)
    assert game.js("slots.L0") == "water" and game.page.locator("#itemWater").is_visible()
    game.js("layoutKey='tiles'; layoutItems()")                            # タイルのレイアウトでも、スロットのものだけ
    shown = game.js("[...document.querySelectorAll('.item')].filter(e=>getComputedStyle(e).display!=='none').map(e=>e.id)")
    assert len(shown) == 8


def test_can_slot(game):
    """[ITEM-15] エネルギー缶は開発なしでスロットに置ける。はじめは空きスロット（左手1）に自動で置かれ、外しても「アイテム配置」の候補に出る。レベル・強化・研究所の対象ではない。"""
    assert game.js("[slots.L0, itemOpen('can'), store.get('canSlotted',false)]") == ["can", True, True]
    game.js("carry.can=3")
    game.start()
    assert game.js("getComputedStyle(document.getElementById('itemCan')).display") != "none"
    assert game.js("document.getElementById('itemCan').dataset.slot") == "L0"
    for lay in ("tiles", "ring", "ringL"):                               # 3種類のレイアウトのどれでも、盤面の外に見えている
        game.js(f"layoutKey='{lay}'; layoutItems(); updateHud()")
        box = game.page.locator("#itemCan").bounding_box()
        assert box and box["width"] > 20 and box["height"] > 20, lay
        assert box["x"] >= 0 and box["y"] >= 0 and box["x"] + box["width"] <= 1133 and box["y"] + box["height"] <= 744, lay
    game.js("slots.L0=''; layoutItems(); openSlotPick('L0', document.querySelector('.slotEmpty'))")   # 外すと、候補に本数つきで出る
    pick = game.page.locator("#slotPick button[data-k='can']")
    assert "エネルギー缶" in pick.inner_text() and "×3" in pick.inner_text()
    pick.click(); game.wait(200)
    assert game.js("slots.L0") == "can" and game.page.locator("#itemCan").is_visible()
    game.js("paused=true; enterSlotEdit('pause')"); game.wait(200)         # スロット編集画面でも、置いたボタンとして出る
    assert game.page.locator("#itemCan[data-slot='L0'] .rm").is_visible()
    game.js("removeFromSlot('L0')"); game.wait(100)
    assert game.page.locator("#slotBar .tray-item[data-k='can']").count() == 1
    game.js("exitSlotEdit(); hideOverlay(); paused=false")
    game.js("showMenu('skills')"); game.wait(300)                          # 研究所には出ない・強化もできない
    assert "エネルギー缶" not in game.page.locator("#overlay").inner_text()
    assert game.js("[canUpgrade('can'), canDevelop('can'), 'can' in EN_COST, 'can' in ITEM_BTN]") == [False, False, False, False]


def test_can_slot_migration(game):
    """[ITEM-15] 前のセーブデータ: 空きスロットがあればエネルギー缶を一度だけ置き、空きがなければ置かない。外したあとは、勝手に置き直さない。"""
    def reopen(slots, dev):
        game.js(f"localStorage.clear(); store.set('slots',{slots}); store.set('devItems',{dev}); store.set('handSlotted',true)")
        game.reopen()
    full = "{R0:'stop',R1:'mag',R2:'shuf',R3:'boost',R4:'jump',L0:'broom',L1:'hand',L2:'fire'}"
    reopen(full, "['stop','mag','shuf','jump','hand','broom','fire']")
    assert "can" not in game.js("Object.values(slots)")                   # 8か所とも使えるアイテムで埋まっている
    reopen("{R0:'stop',R1:'mag',R2:'shuf',R3:'boost',R4:'jump',L0:'broom',L1:'hand',L2:''}", "['stop','mag','shuf','jump','hand','broom']")
    assert game.js("slots.L2") == "can"                                   # 空いている場所へ
    game.js("slots.L2=''; store.set('slots',slots)")
    game.reopen()
    assert "can" not in game.js("Object.values(slots)")                   # 自分で外したら、そのまま
