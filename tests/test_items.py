"""アイテム・強化・ぷに研究所（ITEM / UP / LAB）"""
import pytest


def test_only_boost_at_first(game):
    """[ITEM-01] 最初から使えるのはブースターだけ。"""
    got = game.js("['stop','mag','shuf','jump','boost','hand'].filter(itemOpen)")
    assert got == ["boost"]


@pytest.mark.parametrize("fn,var,ms", [("useStop", "stopLeft", 6000), ("useMag", "magLeft", 6000),
                                        ("useBoost", "boostLeft", 15000), ("useHand", "handLeft", 5000)])
def test_durations(game, fn, var, ms):
    """[ITEM-02] 効果時間: ストップ6秒・マグネット6秒・ブースター15秒・魔法の手5秒。"""
    game.js("devItems=['stop','mag','hand']")
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
    """[UP-03] 時間で効くアイテムは、レベルが1上がるごとに効果時間が2割のびる。"""
    game.js("devItems=['mag']; itemLv.mag=2")
    game.start()
    game.js("energy=100; useMag()")
    assert game.js("itemTot.mag") == pytest.approx(6000 * 1.4)


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
    assert game.js("GEM_ITEM") == {"sticky": "hand", "space": "mag", "bouncy": "jump", "ice": "stop", "desert": "shuf"}


def test_upgrade(game):
    """[UP-01][UP-02] 強化は宝石3個（虹で代用可）、ブースターは虹1個。Lv3まで。"""
    game.js("devItems=['mag']; gems={space:5, rainbow:2}")
    assert game.js("[upgrade('mag'), lvOf('mag'), gems.space]") == [True, 2, 2]
    assert game.js("[upgrade('mag'), lvOf('mag'), gems.space, gems.rainbow]") == [True, 3, 0, 1]
    assert game.js("canUpgrade('mag')") is False                  # Lv3 が上限
    assert game.js("[upgrade('boost'), lvOf('boost'), gems.rainbow]") == [True, 2, 0]
    assert game.js("canUpgrade('boost')") is False                # 虹の宝石がない


def test_lab_screen(game):
    """[LAB-03][LAB-04] 研究所: 開発ずみは消費エネルギーつきで並び、弱点の相手は見破るまで「？？？」。"""
    game.js("devItems=['mag']; showMenu('skills')"); game.wait(300)
    text = game.page.locator("#overlay").inner_text()
    assert "消費エネルギー" in text and "？？？" in text
    game.js("weakFound=['desert']; showMenu('skills')"); game.wait(300)
    assert "砂漠のボスにきく" in game.page.locator("#overlay").inner_text()


@pytest.mark.parametrize("lv,rate", [(1, 0.6), (2, 0.8), (3, 1.0)])
def test_shuffle_rate(game, lv, rate):
    """[ITEM-06][UP-06] シャッフルが巻きこむのは Lv1 で6割。レベルごとにふえて、最大レベルで全部。残りはその場に残る。"""
    game.js(f"devItems=['shuf']; itemLv.shuf={lv - 1}")
    assert game.js("shufRate()") == pytest.approx(rate)
    game.start(); game.clear_board()
    for row, c in enumerate((0, 1, 2, 3, 0)):
        game.put(4, c, row=row)
    game.wait(700)
    game.js("energy=100; useShuffle()")
    assert game.js("[shuffle.from.length, balls.filter(o=>!o.live).length]") == [round(20 * rate), 20 - round(20 * rate)]
    game.wait(2500)
    assert game.js("shuffle") is None                                # 演出が終わって、ばらまかれた
