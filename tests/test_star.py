"""スター（STAR）"""
import pytest

WORLDS = ["meadow", "desert", "ice", "fire", "bouncy", "space", "sticky", "popcorn", "flower", "magma"]


def clear(game, world=2, crown=False, can=0):
    """ワールド world のボスを倒して、クリア画面が出るまで待つ。crown なら王冠をこわしてから倒す。can は持っている缶の数。"""
    game.js(f"carry.can={can}")
    game.boss(world)
    if crown:
        game.js("crownHit(99999, performance.now())")
    game.js("chain=1; hitBoss(99999, performance.now())")
    game.page.wait_for_function("menuKind==='clear'", timeout=20000)
    game.wait(300)


def test_star_clear_only(game):
    """[STAR-01][STAR-02][STAR-03] 缶なし・王冠をこわさずにクリア: 1つ目と3つ目のスターがもらえ、2つ目はもらえない。"""
    assert game.js("[starsOf('ice'), starTotal()]") == [[0, 0, 0], 0]
    clear(game, 2)
    assert game.js("[canUsed, starsOf('ice'), lastStars.fresh, starTotal()]") == [False, [1, 0, 1], [1, 0, 1], 2]
    assert game.js("starsOf('desert')") == [0, 0, 0]              # ほかのワールドにはつかない


def test_star_crown(game):
    """[STAR-02] 王冠をこわしてから倒すと、2つ目のスターがもらえる。"""
    clear(game, 2, crown=True)
    assert game.js("[lastCrownBroken, starsOf('ice')]") == [True, [1, 1, 1]]


def test_star_not_with_can(game):
    """[STAR-03] エネルギー缶を使って始めたプレイでは、3つ目のスターはもらえない。"""
    clear(game, 2, crown=True, can=1)
    assert game.js("[canUsed, carry.can, starsOf('ice'), starTotal()]") == [True, 0, [1, 1, 0], 2]
    game.js("goHome(); start('world',2)"); game.wait(600)        # 次のプレイは缶がないので、缶なしにもどる
    assert game.js("canUsed") is False


def test_star_kept(game):
    """[STAR-04] 一度取ったスターは消えない: 条件をみたさないクリアのあとも、開き直したあとも残る。"""
    game.js("awardStars('ice', true, false)")
    assert game.js("starsOf('ice')") == [1, 1, 1]
    got = game.js("awardStars('ice', false, true)")               # 王冠をこわさず・缶ありでもう一度クリア
    assert got["now"] == [1, 0, 0] and got["fresh"] == [0, 0, 0]
    assert game.js("starsOf('ice')") == [1, 1, 1]
    game.js("awardStars('desert', false, true); awardStars('desert', false, false)")   # あとから足りないぶんだけ取れる
    assert game.js("[starsOf('desert'), lastStars.fresh]") == [[1, 0, 1], [0, 0, 1]]
    game.page.reload(); game.wait(600)
    assert game.js("[starsOf('ice'), starsOf('desert'), starTotal()]") == [[1, 1, 1], [1, 0, 1], 5]


def test_star_total(game):
    """[STAR-05] スターはワールドごとに最大3つ、全10ワールドで最大30。"""
    assert game.js("[THEMES.map(t=>t.k), starMax(), starTotal()]") == [WORLDS, 30, 0]
    for i, w in enumerate(WORLDS):
        game.js(f"awardStars('{w}', true, false); awardStars('{w}', true, false)")   # 同じワールドを何度クリアしても3つまで
        assert game.js("starTotal()") == 3 * (i + 1)
    assert game.js("starTotal()") == 30


@pytest.mark.parametrize("n,cap,first", [(0, 100, 40), (5, 110, 45), (30, 160, 70)])
def test_star_energy(game, n, cap, first):
    """[STAR-06][STAR-07][EN-01][EN-02][EN-04] 上限は 100+2×スター数、スタート時は 40+スター数。缶ありなら上限まで満タン。上限はこえない。"""
    stars = {w: [1 if i * 3 + j < n else 0 for j in range(3)] for i, w in enumerate(WORLDS)}
    game.js(f"wstars={stars}")
    assert game.js("[starTotal(), enCap(), enStart()]") == [n, cap, first]
    game.start()
    assert game.js("energy") == first
    game.js("addEnergy(999)")
    assert game.js("energy") == cap
    game.js("goHome(); carry.can=1; start('world',0)"); game.wait(600)
    assert game.js("[energy, carry.can]") == [cap, 0]


def test_star_clear_screen(game):
    """[STAR-08] クリア画面: 3つのスターが説明つきで並び、取れたものは点灯、今回新しく取れたものに NEW、合計と効果も出る。"""
    game.js("wstars={ice:[1,0,0]}")
    clear(game, 2, crown=True, can=1)                                # 1つ目は前から・2つ目は今回・3つ目は缶ありで取れない
    cells = game.page.locator(".cl-stars .cl-star")
    assert [c.inner_text().split("\n")[0].strip() for c in cells.all()] == ["ボスをたおした", "王冠をこわした", "缶なしでクリア"]
    assert game.js("[...document.querySelectorAll('.cl-stars .cl-star')].map(e=>[e.classList.contains('on'), e.classList.contains('new')])") \
        == [[True, False], [True, True], [False, False]]
    assert game.page.locator(".cl-stars .cl-new").count() == 1
    cap = game.page.locator(".cl-starcap").inner_text()
    assert "2/30" in cap and "104" in cap and "42" in cap


def test_star_world_select(game):
    """[STAR-09] ワールドをえらぶ画面: ワールドごとに、スター3つぶんの取得状況が出る。"""
    game.js("wstars={meadow:[1,1,1], desert:[1,0,1]}; showMenu('worlds')"); game.wait(300)
    got = game.js("[...document.querySelectorAll('.wl[data-w]:not([data-w=\"-1\"]) .wl-stars')].map(e=>[...e.children].map(s=>s.classList.contains('on')?1:0))")
    assert got == [[1, 1, 1], [1, 0, 1]] + [[0, 0, 0]] * 8


def test_star_profile(game):
    """[STAR-10] プロフィール: スターの合計（n/30）と、今のエネルギー上限・スタート時エネルギーが出る。"""
    game.js("wstars={meadow:[1,1,1], desert:[1,0,1]}; showMenu('records')"); game.wait(300)
    text = game.page.locator(".pf-star").inner_text().replace("\n", " ")
    assert "5/30" in text and "エネルギー上限 110" in text and "スタート時 45" in text
