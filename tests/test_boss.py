"""ボス・王冠・相性・宝石（BOSS / GEM）"""
import pytest

WORLDS = ["meadow", "desert", "ice", "fire", "bouncy", "space", "sticky", "popcorn", "flower", "magma"]
COUNTER = {"popcorn": "hand", "desert": "mag", "space": "jump", "magma": "stop", "flower": "shuf"}
ALL = "devItems=['stop','mag','shuf','jump','hand']; "


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
    """[BOSS-08] 相性表のとおりに弱点が決まっている。"""
    assert game.js(f"COUNTER['{boss_k}']") == item


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
