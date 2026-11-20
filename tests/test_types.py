"""裏設定のタイプと、ゲームの相性表が食いちがっていないか（docs/TYPES.md の決まり）"""
from types_data import WORLD_TYPE, STRONG


def test_every_world_has_own_type(game):
    """[TYPE-01][TYPE-04] どのワールドにもタイプがあり、同じタイプは2つない。"""
    worlds = game.js("THEMES.map(t=>t.k)")
    assert sorted(worlds) == sorted(WORLD_TYPE)
    assert len(set(WORLD_TYPE.values())) == len(WORLD_TYPE)


def test_weakness_is_super_effective(game):
    """[TYPE-02][TYPE-03] ボスの弱点の道具は、そのボスのタイプに「ばつぐん」なタイプ（道具のタイプ＝作る宝石のボスのタイプ）。"""
    counter, gem_item = game.js("COUNTER"), game.js("GEM_ITEM")
    item_type = {item: WORLD_TYPE[w] for w, item in gem_item.items()}
    assert sorted(counter) == sorted(WORLD_TYPE), "弱点のないボスがいる"
    for boss, item in counter.items():
        assert item in item_type, f"{item} を作る宝石がない"
        assert WORLD_TYPE[boss] in STRONG[item_type[item]], f"{boss}（{WORLD_TYPE[boss]}）に {item}（{item_type[item]}）は ばつぐん ではない"
