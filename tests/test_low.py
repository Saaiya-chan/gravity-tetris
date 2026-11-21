"""低い画面（iPhone の横向きなど。高さ 500px 以下）のプレイ画面のレイアウト（LOW）"""
import itertools
import pytest

ALL = "devItems=['stop','mag','shuf','jump','hand','broom','pop','weight','fire','water']; carry.can=2; "
FULL = "slots={R0:'stop',R1:'mag',R2:'shuf',R3:'boost',R4:'jump',L0:'can',L1:'hand',L2:'broom'}; "
PHONES = [(844, 390), (667, 375), (932, 430)]
LAYOUTS = ["ringL", "ring", "tiles"]
# 見えているもの（id → [左, 上, 右, 下]）。sel にあてはまる要素のうち、大きさがあって display:none でないもの
RECTS = """(sel=>{ const o={}; for(const e of document.querySelectorAll(sel)){ const r=e.getBoundingClientRect(), cs=getComputedStyle(e);
    if(r.width>0 && r.height>0 && cs.display!=='none' && cs.visibility!=='hidden') o[e.id||('plus'+e.dataset.slot)]=[r.left,r.top,r.right,r.bottom]; } return o; })"""
BUTTONS = ".item, .slotEmpty, #mvA, #dropBtn, #mvB, #rotBtn, #pauseBtn"


def apart(a, b, gap=0):
    return a[2] + gap <= b[0] or b[2] + gap <= a[0] or a[3] + gap <= b[1] or b[3] + gap <= a[1]


def play(g, lay="ringL", ad=0, slots=FULL):
    """道具を全部開発ずみにして、スロットをうめ、ボス戦にして、ぷに妖精にしゃべらせる。"""
    g.js(ALL + slots)
    if ad:
        g.js(f"window.__setAd({ad})")
    g.js(f"layoutKey='{lay}'; layoutItems()")
    g.boss(0)
    g.js("say('弱点を見破った！！\\n弱点はほうき！','happy',2); updateHud()"); g.wait(300)


@pytest.mark.parametrize("w,h", PHONES)
def test_low_card_hidden(game_at, w, h):
    """[LOW-01] 低い画面では、プレイ中にワールドの説明カードを出さない。スコア・最大連鎖・ステージは出す。"""
    g = game_at(w, h)
    play(g)
    assert g.page.locator("#stageCard").is_visible() is False
    for q in ["#score", "#lines", "#stageN"]:
        assert g.page.locator(q).is_visible(), q
    hud = g.js(f"{RECTS}('#hudL, #pauseBtn, #stage, #ctrlL')")
    assert apart(hud["hudL"], hud["pauseBtn"]) and apart(hud["hudL"], hud["stage"]) and apart(hud["hudL"], hud["ctrlL"])
    text = g.page.locator("#hudL").inner_text()
    assert "SCORE" in text and "最大連鎖" in text and "ステージ" in text and "ボス戦" not in text


def test_big_screen_keeps_card(game):
    """[LOW-01] 大きい画面（iPad など）では、ワールドの説明カードを今までどおり出し、ぷに妖精の右にポーズボタンがある。ポーズ画面にワールドの説明は足さない。"""
    game.js(ALL + FULL); game.js("layoutItems()"); game.boss(0)
    assert game.page.locator("#stageCard").is_visible() and "草原ワールド" in game.page.locator("#stageCard").inner_text()
    r = game.js(f"{RECTS}('#talker, #pauseBtn, #mvA, #dropBtn')")
    assert r["talker"][2] <= r["pauseBtn"][0] and r["pauseBtn"][2] > 1133 - 20
    assert r["dropBtn"][3] < r["mvA"][3]                                     # 「落とす」は、今までどおり ← → より上（山の形）
    game.js("togglePause()"); game.wait(250)
    assert game.page.locator("#pzWorld").is_visible() is False


@pytest.mark.parametrize("w,h", PHONES[:2])
def test_low_pause_shows_world(game_at, w, h):
    """[LOW-02] 低い画面では、ポーズ画面で、ワールドの説明（カードと同じ中身: 名前・特徴の箇条書き・次の目標・ボス戦）を読める。"""
    g = game_at(w, h)
    play(g, ad=50)
    card = g.js("[scName.textContent, [...scPts.children].map(li=>li.textContent), scNext.textContent, scFx.textContent]")
    assert "草原" in card[0] and len(card[1]) >= 2 and card[1][0].startswith("盤面: ") and card[2] == "ボスを倒すとワールドクリア" and "ボス戦: ぷにキング" in card[3]
    g.page.click("#pauseBtn"); g.wait(300)                                    # 左上へ移したポーズボタンを、実際に押せる
    assert g.js("paused") is True
    pz = g.page.locator("#pzWorld")
    assert pz.is_visible()
    assert g.js("[...document.querySelectorAll('#pzWorld .sc-pts li')].map(li=>li.textContent)") == card[1]
    text = pz.inner_text()
    for part in [card[0], card[2], card[3]] + card[1]:
        assert part in text, part
    box = pz.bounding_box()
    assert box["y"] >= 0 and box["y"] + box["height"] <= h - 50 and box["x"] >= 0 and box["x"] + box["width"] <= w     # 開いたとき、スクロールしなくても、広告の帯の上に全部見えている
    g.page.click("#resumeBtn"); g.wait(200)
    assert g.js("paused") is False
    g.start(2); g.js("togglePause()"); g.wait(250)                            # 別のワールド・ボス戦でないときも、そのときの中身
    text = g.page.locator("#pzWorld").inner_text()
    assert "氷" in text and "次のステージまで あと" in text and "ボス戦" not in text


@pytest.mark.parametrize("w,h", PHONES)
def test_low_fairy_right_edge(game_at, w, h):
    """[LOW-03] 低い画面では、ポーズボタンは画面の右上の隅、ぷに妖精はそのすぐ下（右端）。左上はスコア・最大連鎖・ステージだけ。吹き出しは顔の左に出て、盤面には右はしだけかかり、道具のボタンには重ならない。"""
    g = game_at(w, h)
    for lay in LAYOUTS:
        play(g, lay)
        r = g.js(f"{RECTS}('#talker, #talkBub, #pauseBtn, #stage, #hudL, #ctrlR, #ctrlL, #rotBtn, .item')")
        t, p, st = r["talker"], r["pauseBtn"], r["stage"]
        assert w - 12 <= p[2] <= w and 0 <= p[1] <= 12, f"{lay}: ポーズボタンが右上の隅にない {p}"
        assert p[2] - p[0] >= 44 and p[3] - p[1] >= 44
        assert w - 12 <= t[2] <= w and p[3] <= t[1] <= p[3] + 12, f"{lay}: 妖精がポーズボタンのすぐ下にいない {t} {p}"
        assert t[2] - t[0] >= 60
        for name, o in r.items():
            if name not in ("talker", "talkBub"):
                assert apart(t, o), f"{lay}: 妖精が {name} と重なっている"
            if name not in ("pauseBtn",):
                assert apart(p, o), f"{lay}: ポーズボタンが {name} と重なっている"
        assert r["hudL"][2] <= st[0] and r["hudL"][0] < 60 and r["hudL"][1] < 20          # 左上は、スコアなどだけ
        b = r["talkBub"]
        assert g.js("document.getElementById('talkBub').classList.contains('on')") and b[2] <= t[0] and b[0] >= 0 and b[1] >= 0
        assert b[0] >= st[0] + (st[2] - st[0]) * 0.55, f"{lay}: 吹き出しが盤面に大きくかかっている {b} {st}"     # 盤面の右はしだけ
        for name, o in r.items():
            if name.startswith("item") or name == "rotBtn":
                assert apart(b, o), f"{lay}: 吹き出しが {name} と重なっている"
        g.js("goHome()")


def check_buttons(g, w, h, ad, label, n_items=8):
    r = g.js(f"{RECTS}('{BUTTONS}')")
    st = g.js(f"{RECTS}('#stage, #talker')")
    assert len([k for k in r if k.startswith("item")]) == n_items, f"{label}: {sorted(r)}"
    for k in ["mvA", "dropBtn", "mvB", "rotBtn", "pauseBtn"]:
        assert k in r, f"{label}: {k} が見えない"
    for (ka, a), (kb, b) in itertools.combinations(r.items(), 2):
        assert apart(a, b), f"{label}: {ka} と {kb} が重なっている {a} {b}"
    for k, a in r.items():
        assert a[0] >= 0 and a[1] >= 0 and a[2] <= w and a[3] <= h - ad, f"{label}: {k} が画面の外か、広告の帯にはみ出している {a}"
        assert apart(a, st["stage"]) and apart(a, st["talker"]), f"{label}: {k} が盤面か妖精に重なっている"
    return r


@pytest.mark.parametrize("w,h", PHONES)
@pytest.mark.parametrize("ad", [0, 50])
def test_low_buttons_apart(game_at, w, h, ad):
    """[LOW-06] 低い画面では、見えている道具ボタン・操作ボタン・ポーズボタンが、どの配置でも重ならず、画面の外・広告の帯・盤面・妖精にはみ出さない。押せる大きさ（44px 以上）がある。"""
    g = game_at(w, h)
    for lay in LAYOUTS:
        play(g, lay, ad)
        r = check_buttons(g, w, h, ad, f"{w}x{h} ad={ad} {lay}")
        for k, a in r.items():
            wide, tall = a[2] - a[0], a[3] - a[1]
            if lay == "tiles" and k.startswith("item"):
                assert wide >= 44 and tall >= 32, f"{lay}: {k} が小さい"       # タイルは横長（名前つき）
            else:
                assert wide >= 44 and tall >= 44, f"{lay}: {k} が小さい {wide}x{tall}"
        g.js("goHome()")


def test_slot_size_data(game):
    """[LOW-04] スロットの大きさは、位置ごとのデータ（SLOT_SIZE）で持つ: 右手1〜3が「大」、右手4・5と左手が「中」。スロットは8か所のまま。"""
    assert game.js("SLOT_SIZE") == {"R0": "L", "R1": "L", "R2": "L", "R3": "M", "R4": "M", "L0": "M", "L1": "M", "L2": "M"}
    assert game.js("SLOT_DEF.map(d=>d[0]).sort()") == sorted(game.js("Object.keys(SLOT_SIZE)"))


@pytest.mark.parametrize("w,h,ad", [(844, 390, 0), (844, 390, 50), (667, 375, 0), (667, 375, 50), (932, 430, 0)])
def test_low_slot_sizes(game_at, w, h, ad):
    """[LOW-04] 低い画面では、右手の道具を、大3つ（右手1〜3。回転ボタンと 2×2 のかたまり）と中2つ（その外側）に並べる。大は中より大きい。大きさは位置で決まり、道具を入れかえると、大の位置に入った道具が大きく出る。"""
    g = game_at(w, h)
    size = lambda a: (a[2] - a[0], a[3] - a[1])
    for lay in ["ringL", "ring"]:
        play(g, lay, ad)
        assert g.js("lowScreen()") is True
        assert g.js("slots") == {"R0": "stop", "R1": "mag", "R2": "shuf", "R3": "boost", "R4": "jump", "L0": "can", "L1": "hand", "L2": "broom"}
        assert g.js("Object.fromEntries([...document.querySelectorAll('.item[data-slot]')].map(e=>[e.dataset.slot,[e.id,e.dataset.size]]))") == {
            "R0": ["itemStop", "L"], "R1": ["itemMag", "L"], "R2": ["itemShuf", "L"], "R3": ["itemBoost", "M"], "R4": ["itemJump", "M"],
            "L0": ["itemCan", "M"], "L1": ["itemHand", "M"], "L2": ["itemBroom", "M"]}
        r = g.js(f"{RECTS}('{BUTTONS}')")
        big, mid, rot = [r[k] for k in ["itemStop", "itemMag", "itemShuf"]], [r[k] for k in ["itemBoost", "itemJump"]], r["rotBtn"]
        for a in big + mid:
            assert abs(size(a)[0] - size(a)[1]) < 1                                                          # 四角
        assert len({round(size(a)[0]) for a in big}) == 1 and len({round(size(a)[0]) for a in mid}) == 1
        L, M = size(big[0])[0], size(mid[0])[0]
        assert M >= 44 and L >= M + 4, f"{lay}: 大 {L} が 中 {M} より大きくない"
        if ad == 0:
            assert L >= M * 1.4, f"{lay}: 大 {L} と 中 {M} の差が小さい"                                    # 広告の帯がなければ、はっきり差がつく
        stop, mag, shuf = big
        assert abs(mag[0] - stop[0]) < 1 and mag[3] <= stop[1] and abs(shuf[1] - mag[1]) < 1 and mag[2] <= shuf[0]     # 上の段: 右手2・右手3 ／ 下の段: 右手1・回転
        cx, cy = lambda a: (a[0] + a[2]) / 2, lambda a: (a[1] + a[3]) / 2
        assert stop[2] <= rot[0] and shuf[3] <= rot[1] and abs(cy(rot) - cy(stop)) <= 4 and abs(cx(rot) - cx(shuf)) <= 4     # 回転ボタンは、右手1の右・右手3の真下
        near = lambda a: ((cx(a) - cx(rot)) ** 2 + (cy(a) - cy(rot)) ** 2) ** 0.5
        assert max(near(a) for a in big) < min(near(a) for a in mid)                                         # 大は回転ボタンの近く、中はその外側
        fs = g.js("Object.fromEntries(['itemStop','itemBoost'].map(id=>[id, parseFloat(getComputedStyle(document.querySelector('#'+id+' .badge')).fontSize)]))")
        assert fs["itemStop"] >= fs["itemBoost"]
        g.js("slots.R0='jump'; slots.R4='stop'; layoutItems(); updateHud()"); g.wait(100)                   # 入れかえると、大きさは位置についていく
        r2 = g.js(f"{RECTS}('.item')")
        assert abs(size(r2["itemJump"])[0] - L) < 1 and abs(size(r2["itemStop"])[0] - M) < 1
        assert g.js("[itemJump.dataset.size, itemStop.dataset.size]") == ["L", "M"]
        g.js("goHome()")


@pytest.mark.parametrize("w,h", PHONES[:2])
def test_low_left_hand(game_at, w, h):
    """[LOW-05] 低い画面では、「落とす」は ← と → のあいだで、← → より下（谷の形）。左手の道具3つは、その上に、たがいに重ならずに並び、名前がボタンからはみ出さない。"""
    g = game_at(w, h)
    for lay in ["ringL", "ring"]:
        play(g, lay, ad=50)
        r = g.js(f"{RECTS}('{BUTTONS}')")
        a, d, b = r["mvA"], r["dropBtn"], r["mvB"]
        assert a[2] <= d[0] and d[2] <= b[0] and abs(a[1] - b[1]) < 1
        assert d[1] > a[1] + 8 and d[3] > a[3] + 8 and d[3] <= h - 50, f"{lay}: 落とすが ← → より下にない"
        can, hand, broom = r["itemCan"], r["itemHand"], r["itemBroom"]
        assert can[2] < hand[0] and hand[2] < broom[0] and max(can[3], hand[3], broom[3]) <= min(a[1], b[1])
        over = g.js("""[...document.querySelectorAll('.item')].filter(e=>e.offsetWidth>0).map(e=>{ const l=e.querySelector('.lbl'); if(!l || !l.offsetWidth) return null;
            const rg=document.createRange(); rg.selectNodeContents(l); const t=rg.getBoundingClientRect(), b=e.getBoundingClientRect(); return (t.left<b.left-0.5 || t.right>b.right+0.5) ? e.id : null; }).filter(Boolean)""")
        assert over == [], f"{lay}: 名前がボタンからはみ出している {over}"
        g.js("goHome()")


def test_low_badges_not_hidden(game_at):
    """[LOW-06][EN-13][ITEM-08] 低い画面でも、消費エネルギーのバッジ・缶の本数・残り時間の白い扇形が、となりのボタンにかくれない。"""
    for w, h in PHONES[:2]:
        g = game_at(w, h)
        for lay in LAYOUTS:
            play(g, lay)
            shown = g.js("""[...document.querySelectorAll('.item')].filter(e=>getComputedStyle(e).display!=='none').map(e=>{
                const r=e.querySelector('.badge').getBoundingClientRect(), pts=[[.5,.5],[.15,.5],[.85,.5],[.5,.15],[.5,.85]];
                return [e.id, r.width>0 && pts.every(([u,v])=>e.contains(document.elementFromPoint(r.left+r.width*u, r.top+r.height*v)))]; })""")
            assert len(shown) == 8 and [i for i, ok in shown if not ok] == [], f"{w}x{h} {lay}"
            badges = g.js(f"{RECTS}('.item .badge')")
            assert g.page.locator("#itemCan .badge").inner_text().strip() == "×2" and g.page.locator("#itemBoost .badge").inner_text().strip() == "30"
            g.js("energy=100; stopLeft=0; useStop(); updateHud()"); g.wait(150)
            assert g.js("document.getElementById('itemStop').classList.contains('timing')") is True
            fan = g.js("(()=>{ const e=document.getElementById('itemStop'), r=e.getBoundingClientRect(); return [[.5,.5],[.25,.5],[.75,.5],[.5,.25],[.5,.75]].every(([u,v])=>e.contains(document.elementFromPoint(r.left+r.width*u, r.top+r.height*v))); })()")
            assert fan, f"{w}x{h} {lay}: 残り時間の扇形がかくれている"
            g.js("goHome()")


def test_low_slot_edit(game_at):
    """[LOW-04][ITEM-14] 低い画面でも、空きスロットの「＋」は、そのスロットの場所に出て、ほかのボタンと重ならない。スロットは8か所のままで、「＋」から道具を置ける。"""
    g = game_at(844, 390)
    play(g, slots="slots={R0:'stop',R1:'',R2:'shuf',R3:'',R4:'jump',L0:'can',L1:'',L2:''}; ")
    assert g.js("SLOT_DEF.length") == 8
    r = check_buttons(g, 844, 390, 0, "空きあり", n_items=4)
    assert sorted(k for k in r if k.startswith("plus")) == ["plusL1", "plusL2", "plusR1", "plusR3"]
    cx = lambda a: (a[0] + a[2]) / 2
    wide = lambda a: a[2] - a[0]
    assert abs(cx(r["plusR1"]) - cx(r["itemStop"])) < 1 and r["plusR1"][3] <= r["itemStop"][1]     # 右手2は、右手1（ストップ）の真上
    assert wide(r["plusR1"]) > wide(r["plusR3"]) + 4 and abs(cx(r["plusR3"]) - cx(r["itemJump"])) < 1   # 「＋」の大きさも、位置（大・中）で決まる
    g.page.click(".slotEmpty[data-slot='R1']"); g.wait(200)
    g.page.locator("#slotPick button[data-k='mag']").click(); g.wait(200)
    assert g.js("slots.R1") == "mag" and g.page.locator("#itemMag").is_visible()
    r = check_buttons(g, 844, 390, 0, "マグネットを置いたあと", n_items=5)
    assert abs(r["itemMag"][0] - r["itemStop"][0]) < 1 and r["itemMag"][3] < r["itemStop"][1]
    g.js("paused=true; enterSlotEdit('pause')"); g.wait(200)                  # 配置の編集画面でも、同じ場所
    assert g.js("document.body.classList.contains('slot-edit')") and g.js("[...document.querySelectorAll('.slotEmpty')].length") == 3
    g.js("exitSlotEdit(); hideOverlay(); paused=false")
