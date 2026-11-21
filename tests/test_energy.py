"""エネルギー（EN）"""
import pytest

COST = {"stop": 30, "jump": 20, "shuf": 35, "mag": 40, "boost": 30, "hand": 40,
        "broom": 25, "pop": 35, "weight": 30, "fire": 35, "water": 30}


def test_start_energy(game):
    """[EN-01] スターが0なら、プレイ開始時のエネルギーは40。上限は100。"""
    game.start()
    assert game.js("[energy, enCap()]") == [40, 100]


def test_can_not_used_at_start(game):
    """[EN-02] エネルギー缶を持って始めても、缶はへらず、エネルギーはいつものスタート時の量。"""
    game.js("carry.can=2")
    game.start()
    assert game.js("[energy, carry.can, canUsed]") == [40, 2, False]


def test_can_fills_energy(game):
    """[EN-14] プレイ中にエネルギー缶のボタンを押すと、1本へって（保存され）、エネルギーが上限まで満タンになり、canUsed が立つ。"""
    game.js("carry.can=2; saveShop()")
    game.start()
    assert game.page.locator("#itemCan").is_visible()
    game.page.click("#itemCan"); game.wait(200)
    assert game.js("[energy, enCap(), carry.can, canUsed]") == [100, 100, 1, True]
    assert game.js("store.get('carry',{}).can") == 1                 # 保存されている
    assert game.js("performance.now()-enFlash") < 2000               # ゲージが光る演出
    game.js("wstars={meadow:[1,1,1]}; energy=10; useCan()")          # 上限がふえていれば、その上限まで
    assert game.js("[energy, carry.can]") == [106, 0]


def test_can_not_usable(game):
    """[EN-15] エネルギーが満タンのとき・缶が0本のときは使えず、何もへらない。"""
    game.js("carry.can=2")
    game.start()
    game.js("energy=enCap(); useCan()")
    assert game.js("[energy, carry.can, canUsed]") == [100, 2, False]   # 満タン
    game.page.click("#itemCan", force=True); game.wait(200)
    assert game.js("[energy, carry.can, canUsed]") == [100, 2, False]
    game.js("carry.can=0; energy=30; useCan()")
    assert game.js("[energy, carry.can, canUsed]") == [30, 0, False]    # 0本
    game.js("delete carry.can; useCan()")
    assert game.js("[energy, carry.can||0, canUsed]") == [30, 0, False]


def test_can_badge(game):
    """[EN-16] エネルギー缶のボタンのバッジは持っている本数（×2）。使えない間（0本・満タン）は「使えない見た目」になる。"""
    game.js("carry.can=2")
    game.start()
    badge = game.page.locator("#itemCan .badge")
    empty = lambda: game.js("document.getElementById('itemCan').classList.contains('empty')")
    assert badge.inner_text().strip() == "×2" and empty() is False
    assert game.js("getComputedStyle(document.querySelector('#itemCan .badge'),'::before').content") == "none"   # ⚡ はつかない
    game.page.click("#itemCan"); game.wait(200)
    assert badge.inner_text().strip() == "×1" and empty() is True     # 満タンなので使えない
    game.js("energy=50; carry.can=0; updateHud()")
    assert badge.inner_text().strip() == "×0" and empty() is True     # 0本
    game.js("carry.can=1; updateHud()")
    assert empty() is False


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


@pytest.mark.parametrize("lv,k", [(2, 1.1), (3, 1.2), (4, 1.3), (5, 1.4)])
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
    """[EN-10] アイテムのボタンには、消費エネルギーを出さない（缶の本数だけ出す）。足りないときは、使えない見た目になる。"""
    game.start()
    assert game.page.locator("#itemBoost .badge").is_hidden()
    assert game.page.locator("#itemCan .badge").is_visible()
    game.js("energy=10; updateHud()")
    assert game.js("document.getElementById('itemBoost').classList.contains('empty')") is True


def test_badge_not_hidden(game):
    """[EN-13] 消費エネルギーのバッジは、となりのアイテムのボタンに隠れない（ブースターのバッジがジャンプに隠れていた）。"""
    game.js("devItems=['stop','mag','shuf','jump','hand','broom','water']")
    game.js("slots.L0='broom'; slots.L2='water'; layoutItems()")
    game.start()
    shown = game.js("""[...document.querySelectorAll('#itemCan')].filter(e=>getComputedStyle(e).display!=='none').map(e=>{
        const r=e.querySelector('.badge').getBoundingClientRect(), pts=[[.5,.5],[.15,.5],[.85,.5],[.5,.15],[.5,.85]];
        return [e.id, pts.every(([u,v])=>e.contains(document.elementFromPoint(r.left+r.width*u, r.top+r.height*v)))]; })""")
    assert len(shown) <= 1                                                # 出るバッジは、缶の本数だけ
    assert game.js("[...document.querySelectorAll('.item:not(#itemCan) .badge')].every(b=>getComputedStyle(b).display==='none')") is True
    assert [i for i, ok in shown if not ok] == []
