"""ボス・王冠・相性・宝石（BOSS / GEM）"""
import pytest

WORLDS = ["meadow", "desert", "ice", "fire", "bouncy", "space", "sticky", "popcorn", "flower", "magma"]
# 相性の階段（docs/SPEC.md の相性表）。段の中の順は、ワールドをえらぶ画面の順
TIERS = [["meadow", "desert", "ice"], ["flower", "sticky", "magma"], ["fire", "popcorn", "bouncy", "space"]]
COUNTER = {"meadow": "pop", "desert": "mag", "ice": "fire",
           "flower": "broom", "sticky": "shuf", "magma": "stop",
           "fire": "water", "popcorn": "hand", "bouncy": "weight", "space": "jump"}
USE = {"pop": "usePop", "broom": "useBroom", "weight": "useWeight", "fire": "useFire", "water": "useWater"}
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
    """[BOSS-05][LAB-04] 弱点アイテム: 妨害を10秒封じ、王冠を15%けずり、弱点が記録される。"""
    game.js(ALL); game.boss(1)                                       # 砂漠 ← マグネット
    game.js("energy=100; useMag()")
    assert game.js("[boss.crown, abilFx.text, weakFound]") == [1700, "弱点を見破った！！", ["desert"]]
    left = game.js("boss.sealUntil-performance.now()")
    assert 9000 < left <= 10000
    game.js("magLeft=0; energy=100; useMag()")
    assert game.js("[boss.crown, abilFx.text]") == [1400, "効果ばつぐん！！"]


def test_neutral_and_resisted(game):
    """[BOSS-06][BOSS-07] ふつうのアイテムは4%「効いてる！」、ボス自身の宝石から作るアイテムは1%「あまり効いてない…」。"""
    game.js(ALL); game.boss(1)                                       # 砂漠の宝石 → シャッフル
    game.js("energy=100; useBoost()")
    assert game.js("[boss.crown, abilFx.text]") == [1920, "効いてる！"]
    game.clear_board(); game.put(3, 0); game.wait(500)
    game.js("energy=100; useShuffle()")
    assert game.js("[boss.crown, abilFx.text]") == [1900, "あまり効いてない…"]


def test_level_adds_crown_damage(game):
    """[UP-05] アイテムのレベルが1上がるごとに、王冠へのダメージが1%ふえる。"""
    game.js(ALL + "itemLv={mag:2, boost:1}"); game.boss(1)
    game.js("energy=100; useMag()")
    assert game.js("boss.crown") == 2000 - 2000 * 0.17
    game.js("energy=100; useBoost()")
    assert game.js("boss.crown") == 2000 - 2000 * 0.17 - 2000 * 0.05


@pytest.mark.parametrize("boss_k,item", COUNTER.items())
def test_counter_table(game, boss_k, item):
    """[BOSS-08] 相性表のとおりに弱点が決まっている（全10ボス）。"""
    assert game.js(f"COUNTER['{boss_k}']") == item
    assert len(COUNTER) == 10 and sorted(game.js("Object.keys(COUNTER)")) == sorted(WORLDS)
    assert game.js(f"GEM_ITEM['{boss_k}']") != item                    # 自分の宝石から作るアイテムは、弱点にならない


def test_counter_stairs(game):
    """[BOSS-08] 相性の階段: 2段目・3段目のボスの弱点は、ひとつ前の段の宝石で作れるアイテム。1段目のボスの弱点は、3段目の宝石で作れるアイテム。"""
    assert game.js("TIER") == {k: n + 1 for n, ks in enumerate(TIERS) for k in ks}
    made = [sorted(game.js(f"GEM_ITEM['{k}']") for k in ks) for ks in TIERS]         # その段の宝石で作れるアイテム
    weak = [[COUNTER[k] for k in ks] for ks in TIERS]
    assert sorted(weak[1]) == made[0]                                 # 2段目の弱点 = 1段目の道具（3つとも）
    assert sorted(weak[2][:3]) == made[1]                             # 3段目（炎・ポップコーン・トランポリン）の弱点 = 2段目の道具
    assert weak[2][3] == game.js("GEM_ITEM.bouncy")                   # 宇宙の弱点は、同じ3段目のトランポリンの道具（ジャンプ）
    assert set(weak[0]) <= set(made[2])                               # 1段目の弱点は、3段目の道具


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


@pytest.mark.parametrize("item", ["pop", "broom", "weight", "fire", "water"])
def test_new_weakness(game, item):
    """[BOSS-05][BOSS-08][LAB-04] 新しい5種も弱点として効く: 妨害を10秒封じ、王冠を15%けずり、弱点が記録されて表示される。"""
    k = next(b for b, i in COUNTER.items() if i == item)
    game.js(ALL); game.boss(WORLDS.index(k)); game.clear_board()
    game.put(2, 0); game.put(2, 1, row=1)
    assert game.js(f"weakKnown('{k}')") is False
    game.js(f"energy=100; {USE[item]}()")
    assert game.js("[boss.crown, abilFx.text, weakFound]") == [1700, "弱点を見破った！！", [k]]
    assert 9000 < game.js("boss.sealUntil-performance.now()") <= 10000
    game.wait(1200); game.clear_board(); game.put(2, 0); game.put(2, 1, row=1)
    game.js(f"weightLeft=0; energy=100; {USE[item]}()")
    sealed = 4 * 3 if item == "pop" else 0                             # はじけ玉で消した4個は、封印中なので王冠も個数×3けずる（BOSS-09）
    assert game.js("[boss.crown, abilFx.text]") == [1400 - sealed, "効果ばつぐん！！"]
    game.js("paused=true; showMenu('skills')"); game.wait(300)        # 研究所にも相手の名前が出る
    name = game.js(f"THEMES.find(t=>t.k==='{k}').name")
    assert f"{name}のボスにきく" in game.page.locator("#overlay").inner_text()


@pytest.mark.parametrize("item", ["pop", "broom", "weight", "fire", "water"])
def test_new_resisted(game, item):
    """[BOSS-07] 新しい5種も、自分の宝石のボスには1%「あまり効いてない…」。"""
    k = game.js(f"gemOf('{item}')")
    game.js(ALL); game.boss(WORLDS.index(k)); game.clear_board()
    game.put(2, 0)
    game.js(f"energy=100; {USE[item]}()")
    assert game.js("[boss.crown, abilFx.text]") == [1980, "あまり効いてない…"]


def test_counter_cleanup(game):
    """[BOSS-16] 弱点アイテムは、ふだんの効果で、そのボスの妨害の後始末もする（氷・花びら・火の粉）。"""
    game.js(ALL)
    game.boss(2); game.clear_board()                                     # アイスキング: 氷がとける
    game.put(4, 0); game.put(4, 1, row=1)
    game.js("bossAbility(performance.now())")
    assert game.js("balls.filter(o=>o.frozen).length") >= 3
    game.js("energy=100; useFire()")
    assert game.js("balls.filter(o=>o.frozen).length") == 0
    game.js("goHome()")
    game.boss(8); game.clear_board()                                     # フラワークイーン: 舞っている花びらが消える
    game.put(2, 0)
    game.js("bossAbility(performance.now())")
    assert game.js("!!petalFx") is True
    game.js("energy=100; useBroom()")
    assert game.js("[petalFx, abilFx.text]") == [None, "弱点を見破った！！"]
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
    """[BOSS-15] マグマキングにストップが効くと、盤面のマグマぷにがお邪魔ぷにに変わる。"""
    game.js(ALL); game.boss(9); game.clear_board()
    game.js("for(let i=0;i<3;i++) balls.push(newBall(1.5+i*4*R, N-R-0.01, MAGMA)); dirty=true")
    game.js("energy=100; stopLeft=0; useStop()")
    assert game.js("[balls.filter(o=>o.c===MAGMA).length, balls.filter(o=>o.c===GARBAGE).length, abilFx.text]") == [0, 3, "弱点を見破った！！"]


def test_shuffle_shakes_off_honey(game):
    """[BOSS-15][ITEM-06] ハニーキングにシャッフルが効くと、巻きこんだぷにのべたべたが取れ、かたまりがばらける。残ったぷにと、ほかの相手のときは、べたべたのまま。"""
    game.js(ALL); game.boss(6); game.clear_board()
    game.put(4, 0); game.put(4, 1, row=1); game.wait(500)
    game.js("for(const o of balls) o.sticky=true; makeBonds()")
    assert game.js("bonds.some(([a,b])=>a.c!==b.c)") is True              # べたべたで、違う色がかたまりになっている
    game.js("energy=100; useShuffle()")
    assert game.js("abilFx.text") == "弱点を見破った！！"
    assert game.js("[shuffle.to.length, shuffle.to.filter(b=>b.sticky).length, bonds.length]") == [5, 0, 0]   # Lv1 は8個の6割 = 5個を巻きこむ
    assert game.js("balls.filter(o=>!o.live).map(o=>!!o.sticky)") == [True] * 3                               # 巻きこまれなかった3個は、そのまま
    game.wait(2600)
    assert game.js("[shuffle, balls.length, balls.filter(o=>o.sticky).length]") == [None, 8, 3]
    game.js("goHome()")
    game.boss(1); game.clear_board()                                     # サンドキングには弱点ではない: べたべたは取れない
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
