"""裏設定のタイプの決まり（docs/TYPES.md）。表そのものの形を確かめる（ゲーム側との一致は test_boss.py が見る）。"""
from types_data import TYPES, GOGYO, NICHIGETSU, BOSS_SEAT, ITEM_SEAT, beats, effect

ALL = [t for e in TYPES for t in TYPES[e]]
RING = {"五行": [t for e in GOGYO for t in TYPES[e]], "日月": [t for e in NICHIGETSU for t in TYPES[e]]}


def test_type_count():
    """[TYPE-01] 七曜 × じゃんけん で21タイプ。名前はかぶらない。"""
    assert len(ALL) == 21 == len(set(ALL))
    assert len(RING["五行"]) == 15 and len(RING["日月"]) == 6


def test_strong_and_weak_counts():
    """[TYPE-02] 五行の輪は3つに強く3つに弱い。日と月の輪は2つに強く2つに弱い。"""
    lose = {t: 0 for t in ALL}
    for t in ALL:
        sp, strong = beats(t)
        targets = [sp] + strong
        assert len(set(targets)) == len(targets) == (3 if t in RING["五行"] else 2)
        for x in targets:
            lose[x] += 1
    for t in ALL:
        assert lose[t] == (3 if t in RING["五行"] else 2), t


def test_rings_do_not_cross():
    """[TYPE-03] ふたつの輪のあいだに勝ち負けはない。"""
    for name, members in RING.items():
        for t in members:
            sp, strong = beats(t)
            assert all(x in members for x in [sp] + strong), t


def test_super_effective_makes_one_loop():
    """[TYPE-04] 特効をたどると、それぞれの輪がひとめぐりする（15 と 6）。"""
    for members in RING.values():
        seen, t = [], members[0]
        while t not in seen:
            seen.append(t)
            t = beats(t)[0]
        assert t == members[0] and sorted(seen) == sorted(members)


def test_no_mutual_wins():
    """[TYPE-05] おたがいに勝ち合う組はない。"""
    for t in ALL:
        sp, strong = beats(t)
        for x in [sp] + strong:
            xs, xstrong = beats(x)
            assert t not in [xs] + xstrong, (t, x)


def test_plan_every_boss_can_be_sealed_and_cracked():
    """[TYPE-06] 割りふり: どのボスにも「封じられる道具」があり、宇宙のほかは「特効の道具」が1つ以上ある。"""
    for boss in BOSS_SEAT:
        got = {item: effect(item, boss) for item in ITEM_SEAT}
        assert any(v in ("封印", "特効") for v in got.values()), boss
        if boss != "宇宙":
            assert "特効" in got.values(), boss
