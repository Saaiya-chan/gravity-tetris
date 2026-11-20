"""エネルギー（EN）"""
import pytest

COST = {"stop": 30, "jump": 20, "shuf": 35, "mag": 40, "boost": 30, "hand": 40}


def test_start_energy(game):
    """[EN-01] プレイ開始時のエネルギーは40。最大は100。"""
    game.start()
    assert game.js("[energy, EN_MAX]") == [40, 100]


def test_can_starts_full(game):
    """[EN-02] エネルギー缶を持って始めると、1本使って満タンで始まる。"""
    game.js("carry.can=2")
    game.start()
    assert game.js("[energy, carry.can]") == [100, 1]


def test_pop_gives_energy(game):
    """[EN-03] ぷにを1個消すごとにエネルギーが1ふえる。"""
    game.start(); game.clear_board()
    game.put(5, 0); game.wait(2500)
    assert game.js("[popped, energy]") == [5, 45]


def test_energy_cap(game):
    """[EN-04] エネルギーは100をこえない。"""
    game.start()
    game.js("addEnergy(999)")
    assert game.js("energy") == 100


def test_bonus_energy(game):
    """[EN-05] ごほうび（3連鎖・50個消すごと）でエネルギーが20ふえる。"""
    game.start()
    game.js("grantItem(performance.now())")
    assert game.js("energy") == 60
    assert game.js("EN_BONUS") == 20


@pytest.mark.parametrize("item,cost", COST.items())
def test_cost_lv1(game, item, cost):
    """[EN-06] Lv1 の消費エネルギーは表のとおり。"""
    assert game.js(f"enCost('{item}')") == cost


@pytest.mark.parametrize("lv,k", [(2, 1.1), (3, 1.2)])
def test_cost_grows_with_level(game, lv, k):
    """[EN-07] 消費エネルギーは、レベルが1上がるごとに元の1割ふえる（四捨五入）。"""
    for item, cost in COST.items():
        game.js(f"itemLv['{item}']={lv - 1}")
        assert game.js(f"enCost('{item}')") == round(cost * k + 1e-9), item


def test_not_enough_energy(game):
    """[EN-08] エネルギーが足りないアイテムは使えず、エネルギーも減らない。"""
    game.js("devItems=['mag']")
    game.start()
    game.js("energy=39; useMag()")
    assert game.js("[energy, magLeft]") == [39, 0]


def test_use_spends_energy(game):
    """[EN-09] アイテムを使うと、その消費エネルギーぶん減る。"""
    game.start()
    game.page.click("#itemBoost"); game.wait(200)
    assert game.js("[energy, boostLeft>0]") == [10, True]


def test_badge_shows_cost(game):
    """[EN-10] アイテムのボタンには消費エネルギーが出る。"""
    game.start()
    assert game.page.locator("#itemBoost .badge").inner_text().strip() == "30"
