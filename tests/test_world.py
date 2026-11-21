"""ワールド・ぷに・ライフ・放置・ショップ（WORLD / PUNI / LIFE / IDLE / SHOP）"""
import pytest


@pytest.mark.parametrize("w", range(10))
def test_all_worlds_open(game, w):
    """[WORLD-01] セーブデータがなくても、10のワールドを全部えらんで始められる。"""
    game.start(w, wait=1200)
    assert game.js("[running, mode, theme().k]") == [True, "world", game.js(f"THEMES[{w}].k")]


def test_world_select_shows_ten(game):
    """[WORLD-01] ワールドをえらぶ画面に10個ならぶ。どれも、えらべる。"""
    assert game.js("THEMES.length") == 10
    game.js("showMenu('worlds')"); game.wait(300)
    cards = game.page.locator(".wl[data-w]:not([data-w='-1'])")
    assert cards.count() == 10 and all(c.is_enabled() for c in cards.all())


def world_select(game):
    """ワールドをえらぶ画面の中身を、上から順に: 見出しは ["段", 名前, ひとこと]、カードは ワールドのキー（ランダムは "random"）。"""
    game.js("showMenu('worlds')"); game.wait(300)
    return game.js("""[...document.querySelectorAll('#sheet .tier-h, #sheet .wl')].map(e=>e.classList.contains('wl')
        ? (+e.dataset.w<0 ? 'random' : THEMES[+e.dataset.w].k)
        : ['段', e.querySelector('b').textContent, e.querySelector('small').textContent])""")


def test_world_select_tiers(game):
    """[WORLD-07][WORLD-08][LAB-04] ワールドをえらぶ画面: 見出しは「1段目」「2段目」の2つだけ。1段目に草原・砂漠・氷、2段目にそれ以外の7つがならぶ。ランダムは最後。"""
    assert world_select(game) == [
        ["段", "1段目", "まずはここから"], "meadow", "desert", "ice",
        ["段", "2段目", "道具をあつめて いどもう"], "flower", "sticky", "magma", "fire", "popcorn", "bouncy", "space",
        "random"]
    assert game.page.locator("#sheet .tier-h").count() == 2 and "3段目" not in game.page.locator("#sheet").inner_text()
    assert game.js("[TIER_NOTE.length, Object.values(TIER).filter(n=>n===1).length, Object.values(TIER).filter(n=>n===2).length]") == [2, 3, 7]
    tops = game.js("[...document.querySelectorAll('#sheet .tier-h, #sheet .wl')].map(e=>Math.round(e.getBoundingClientRect().top))")
    assert tops == sorted(tops)                                       # 画面の上でも、この順に上から下へならんでいる
    assert game.js("[...document.querySelectorAll('#sheet .tier-h')].every(h=>{ const r=h.getBoundingClientRect(), s=sheet.getBoundingClientRect(); return r.left>=s.left && r.right<=s.right && r.height>0; })")
    game.js("THEMES.forEach(t=>worldClears[t.k]=1); weakFound=['flower']")   # 全部クリアしても、弱点を見破っても、順番は同じ
    got = world_select(game)
    assert [x for x in got if isinstance(x, str)] == ["meadow", "desert", "ice", "flower", "sticky", "magma", "fire", "popcorn", "bouncy", "space", "random"]
    assert game.page.locator(".wl[data-w='-1']").is_enabled()
    assert game.page.locator(".wl[data-w='8'] .wl-vs").inner_text() == "弱点: 魔法の手"       # 見破ったフラワー（木のパー）: 特効は魔法の手（金のチョキ）
    assert game.page.locator(".wl[data-w='6'] .wl-vs").inner_text() == "弱点: ？？？"
    assert game.page.locator(".wl[data-w='5'] .wl-vs").count() == 0                            # 宇宙には、まだ特効の道具がないので、何も出さない
    game.js("goHome(); worldClears={}")
    game.start(0); game.js("level=5; startBoss(performance.now())")                            # 段がちがっても、ボスの体力は同じ（差をつけない）
    hp1 = game.js("boss.maxHp")
    game.js("goHome()"); game.start(5); game.js("level=worldNo*5+5; startBoss(performance.now())")
    assert game.js("boss.maxHp") == hp1 == 1600


def test_world_numbers_unchanged(game):
    """[WORLD-09] ならび順を変えても、ワールドの番号は変わらない: カードを押すと、そのワールドが始まり、ステージの表示も元の番号のまま。"""
    assert game.js("THEMES.map(t=>t.k)") == ["meadow", "desert", "ice", "fire", "bouncy", "space", "sticky", "popcorn", "flower", "magma"]
    assert world_select(game)[5] == "flower"                          # 画面では4番目のカード
    game.page.locator("#sheet .wl").nth(3).click(); game.wait(1200)
    assert game.js("[running, mode, theme().k, worldNo, level, stageLabel()]") == [True, "world", "flower", 8, 41, "9-1"]


def test_stage_need(game):
    """[WORLD-03] 次のステージまでの個数は 45+6×クリア回数（8回ぶんまで、最大90）。"""
    game.start(0)
    assert game.js("stageNeed(1)") == 45
    game.js("worldClears.meadow=2"); assert game.js("stageNeed(1)") == 57
    game.js("worldClears.meadow=30"); assert game.js("stageNeed(1)") == 90


def test_stage_up_and_boss(game):
    """[WORLD-02][WORLD-04] 5ステージ目でボスが出る。5ステージ目は個数では進まない。"""
    game.start(0); game.clear_board()
    game.js("level=4; stagePop=stageNeed(4)-5")
    game.put(5, 0); game.wait(5500)
    assert game.js("[level, !!boss]") == [5, True]
    game.js("boss.nextAtk=boss.nextBeam=performance.now()+1e9; stagePop=9999")
    game.put(5, 1); game.wait(2500)
    assert game.js("[level, !!boss]") == [5, True]


def test_pop_needs_five(game):
    """[PUNI-01][PUNI-02] 同じ色が5個つながると消える。4個では消えない。"""
    game.start(); game.clear_board()
    game.put(4, 0); game.wait(2000)
    assert game.js("[popped, balls.length]") == [0, 4]
    game.js("balls=[]; bonds=[]"); game.put(5, 0); game.wait(2500)
    assert game.js("[popped, balls.length]") == [5, 0]


def test_flower(game):
    """[PUNI-03][PUNI-04] はなぷには3個で消え、花びらが舞う。ふつうのぷにとはつながらない。"""
    game.start(8); game.clear_board()
    game.put(2, 7); game.put(3, 0, row=1); game.wait(2000)
    assert game.js("popped") == 0
    game.js("balls=[]; bonds=[]"); game.put(3, 7); game.wait(2500)
    assert game.js("[popped, !!petalFx]") == [3, True]


def test_magma_burn_not_counted(game):
    """[PUNI-05] マグマぷにに燃やされたぷには、消した数・スコア・エネルギーに数えない。"""
    game.start(9); game.clear_board()
    game.put(1, 0); game.wait(400)
    game.js("balls.push(newBall(1.5+2*R, N-R-0.01, MAGMA)); dirty=true"); game.wait(3000)
    assert game.js("[balls.length, popped, score, energy]") == [0, 0, 0, 40]


def test_chain_window(game):
    """[CHAIN-01] 連鎖の受付時間は 2秒+0.5秒×(連鎖数-1)、最大4.5秒。ブースター中は2倍。"""
    game.start()
    assert game.js("[chainWin(1), chainWin(3), chainWin(9)]") == [2000, 3000, 4500]
    game.js("boostLeft=1000")
    assert game.js("chainWin(1)") == 4000


def test_life(game):
    """[LIFE-01][LIFE-02] 始めるとライフが1へる。0のときは始められない。"""
    assert game.js("lives.n") == 5
    game.start()
    assert game.js("lives.n") == 4
    game.js("goHome(); lives.n=0; running=false; start('world',0)"); game.wait(500)
    assert game.js("[running, menuKind]") == [False, "nolife"]


def test_game_over_when_exit_blocked(game):
    """[WORLD-06] 出口がふさがったまま3秒たつとゲームオーバー。"""
    game.start()
    game.js("idleT=-1e9; piece=null; balls=[]; bonds=[]; for(let y=3;y<10;y+=0.97) for(let x=1.5;x<11.6;x+=0.97) balls.push(newBall(x,y,(Math.round(x)+2*Math.round(y))%5)); dirty=true")
    game.wait(9000)
    assert game.js("over") is True


def test_idle_garbage(game):
    """[IDLE-01][IDLE-02] 5秒さわらないと注意が出て、8秒でお邪魔ぷにが降ってくる。"""
    game.start(); game.js("stopLeft=0; piece=null; balls=[]; bonds=[]; idleT=4900; idleWarned=false"); game.wait(400)
    assert game.js("idleWarned") is True
    game.js("idleT=7900"); game.wait(500)
    assert game.js("balls.filter(o=>o.c===GARBAGE).length") >= 2


def test_buy_can(game):
    """[SHOP-01] エネルギー缶は80コイン。9本まで。"""
    game.js("coins=100; shopTab='item'; showShop('title')"); game.wait(300)
    game.page.click("button.buy[data-k=can]"); game.wait(300)
    assert game.js("[coins, carry.can]") == [20, 1]
    game.js("coins=1000; carry.can=9; showShop('title')"); game.wait(300)
    assert game.page.locator("button.buy[data-k=can]").is_disabled()


def test_daily(game):
    """[SHOP-02] デイリーは7日でひとめぐり: コイン30・缶1・50・缶1・80・缶1・150と缶2。"""
    assert game.js("DAILY") == [{"c": 30}, {"e": 1}, {"c": 50}, {"e": 1}, {"c": 80}, {"e": 1}, {"c": 150, "e": 2}]
    game.js("coins=0; carry={}; giveReward(DAILY[6])")
    assert game.js("[coins, carry.can]") == [150, 2]
