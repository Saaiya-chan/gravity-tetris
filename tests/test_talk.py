"""ぷに妖精の実況・吹き出し・NEXT の非表示（TALK）"""
import pathlib
import pytest

ALL = "devItems=['stop','mag','shuf','jump','hand','broom','pop','weight','fire','water']; "
BUB = "document.getElementById('talkBub')"
# 盤面を空にして、組も出ないようにする（放置の注意・出口の注意・連鎖のセリフが、調べたいセリフに割りこまないように）。ボスの動きは止めない
QUIET = "spawn=function(){}; piece=null; balls=[]; bonds=[]; idleT=-1e9; dangerT=0; "


def test_next_hidden(game):
    """[TALK-01] NEXT の箱は、いったん表示しない。次の組そのものは、今までどおり作られて出てくる。"""
    game.start()
    assert game.js("SHOW_NEXT") is False
    assert game.page.locator(".nextbox").is_visible() is False
    assert "NEXT" not in game.page.locator("#hudR").inner_text()
    first = game.js("JSON.stringify(nextPairs[0].c)")
    assert game.js("nextPairs.length") == 2
    game.js("balls=[]; bonds=[]; piece=null; spawnT=-1e9; spawn()")      # 次の組が、予告していたとおりに出る
    assert game.js("JSON.stringify(piece.balls.map(o=>o.c))") == first


def test_talker_visible(game):
    """[TALK-02] ぷに妖精の顔が、NEXT の箱があった場所（右上）に見える。ポーズボタン・盤面・アイテムのボタンと重ならない。"""
    game.js(ALL)
    for lay in ["ringL", "tiles", "ring"]:
        game.js(f"layoutKey='{lay}'; layoutItems()")
        game.start(); game.wait(200)
        assert game.page.locator("#talkCv").is_visible()
        box = "(id=>{ const r=document.querySelector(id).getBoundingClientRect(); return [r.left,r.top,r.right,r.bottom]; })"
        t = game.js(f"{box}('#talker')")
        for other in ["#pauseBtn", "#stage", "#ctrlR"] + [f"#{i}" for i in game.js("ITEM_IDS.filter(id=>document.getElementById(id).offsetWidth>0)")]:
            o = game.js(f"{box}('{other}')")
            assert t[2] <= o[0] or o[2] <= t[0] or t[3] <= o[1] or o[3] <= t[1], f"{lay}: ぷに妖精が {other} と重なっている"
        assert t[0] >= 0 and t[1] >= 0 and t[2] <= 1133 and t[1] < 150 and t[0] > 1133 / 2     # 画面の右上にいる
        painted = game.js("(()=>{ const c=document.getElementById('talkCv'), d=c.getContext('2d').getImageData(c.width/2|0, c.height*0.8|0, 1, 1).data; return d[3]; })()")
        assert painted == 255                                             # 顔が描かれている
        game.js("goHome()")


# ぷに妖精の顔（#talkCv）の絵を、決まった時刻で描いて読む。pick は canvas の中の場所（0〜1）。時刻をそろえるので、まばたき・息づかいのちがいは出ない
SNAP = "(()=>{ talkReset(); const c=document.getElementById('talkCv'); drawTalker(1000); return c.toDataURL(); })()"
PIX = "((fx,fy)=>{ talkReset(); const c=document.getElementById('talkCv'); drawTalker(1000); return [...c.getContext('2d').getImageData(c.width*fx|0, c.height*fy|0, 1, 1).data]; })"


def test_fairy_look(game):
    """[TALK-13] 右上の顔は、プレイヤーが今つけているぷに妖精（体の色とデコ）。色やデコを変えると、絵が変わる。ショップで着せかえると、次のプレイに出る。"""
    game.start(); game.clear_board()
    assert game.js("fairyLook()") == {"b": "red", "head": "", "face": "", "fx": ""}        # はじめは、あか・デコなし
    red, red_px = game.js(SNAP), game.js(f"{PIX}(0.5, 0.8)")
    assert red_px[3] == 255 and red_px[0] > red_px[2] + 60                                 # 赤いからだ
    game.js("profile.avatar='blue'")
    blue, blue_px = game.js(SNAP), game.js(f"{PIX}(0.5, 0.8)")
    assert blue != red and blue_px[2] > blue_px[0] + 60                                    # 青に変えると、青いからだ
    seen = {red, blue}
    for deco in [{"head": "crown"}, {"face": "glasses"}, {"fx": "sticky"}, {"head": "ribbon", "face": "hige", "fx": "virus"}]:
        game.js(f"profile.deco=Object.assign({{head:'',face:'',fx:''}}, {deco})")
        seen.add(game.js(SNAP))                                                            # デコをつけると、絵が変わる
    assert len(seen) == 6
    game.js("profile.deco={head:'crown',face:'',fx:''}")
    gold = game.js(f"{PIX}(0.5, 0.3)")
    assert gold[1] > 150 and gold[2] < 100 and game.js("fairyLook().head") == "crown"      # 王冠は、頭の上に金色で描かれる
    game.js("profile.deco={head:'',face:'',fx:''}")
    plain = game.js(f"{PIX}(0.5, 0.3)")
    assert plain[2] > plain[0] + 60                                                        # はずすと、そこは青いからだ
    game.js("goHome(); coins=500; shopTab='avatar'; showShop('title')"); game.wait(300)     # ショップで着せかえる → 次のプレイから、その姿
    game.page.click("[data-use='a:green']"); game.wait(200)
    game.page.click("[data-buy='d:ribbon']"); game.wait(200)
    assert game.js("fairyLook()") == {"b": "green", "head": "ribbon", "face": "", "fx": ""}
    game.js("showMenu('title')"); game.start(); game.clear_board()
    green_px = game.js(f"{PIX}(0.5, 0.85)")
    assert green_px[1] > green_px[0] + 40 and green_px[1] > green_px[2] + 40


def test_fairy_faces_with_deco(game):
    """[TALK-13][TALK-04] デコをつけていても、表情3つ（ふつう・よろこび・あせり）は、絵として区別がつく。どのデコでも、エラーなく描ける。"""
    game.start(); game.clear_board()
    looks = [("red", "", "", "")] + [("purple", h, f, x) for h, f, x in [("witch", "shades", "frozen"), ("cap", "glasses", "bomb"), ("santa", "hige", "magnet"),
             ("straw", "fang", "heavy"), ("flower", "", "balloon"), ("crown", "shades", "sticky"), ("ribbon", "glasses", "virus")]] + [("rainbow", "", "", ""), ("garbage", "", "hige", "")]
    for b, h, f, x in looks:
        game.js(f"profile.avatar='{b}'; profile.deco={{head:'{h}',face:'{f}',fx:'{x}'}}")
        faces = set()
        for mood in ["normal", "happy", "worry"]:
            game.js(f"talkReset(); talk={{text:'x', mood:'{mood}', prio:0, kind:'t', t:-600}}")     # しゃべりはじめのはずみが終わったあと（口は、とじている）
            faces.add(game.js("(()=>{ const c=document.getElementById('talkCv'); drawTalker(1000); return c.toDataURL(); })()"))
        assert len(faces) == 3, (b, h, f, x)
    game.js("talkReset()"); game.wait(200)


def test_no_avatar_word(game):
    """[TALK-14] 画面の言葉は「ぷに妖精」。「アバター」「実況ぷに」「相棒」「ぷよ」の文字は、どの画面にも（ゲームのファイルのどこにも）残っていない。"""
    src = (pathlib.Path(__file__).resolve().parent.parent / "free.html").read_text(encoding="utf-8")
    for word in ["アバター", "実況ぷに", "相棒"]:
        assert word not in src, word
    seen = ""
    for open_ in ["showMenu('title')", "showMenu('worlds')", "showMenu('skills')", "showMenu('help')", "showMenu('records')", "showMenu('settings')",
                  "shopTab='item'; showShop('title')", "shopTab='avatar'; showShop('title')", "shopTab='frame'; showShop('title')", "showZukan('title')"]:
        game.js(open_); game.wait(250)
        seen += game.page.locator("body").inner_text() + "\n"
    game.js("showMenu('title')"); game.start(); game.js("paused=true; showMenu('pause')"); game.wait(250)
    seen += game.page.locator("body").inner_text()
    for word in ["アバター", "実況", "相棒", "ぷよ"]:
        assert word not in seen, word
    game.js("shopTab='avatar'; showShop('title')"); game.wait(250)
    assert game.page.locator(".tabs button.on").inner_text() == "ぷに妖精"
    game.js("showMenu('records')"); game.wait(250)
    assert game.page.locator("#pfDress").inner_text() == "ぷに妖精・フレームをかえる"
    game.js("showMenu('help')"); game.wait(250)
    help_ = game.page.locator("ul.help").inner_text()
    assert "じゃんけんで勝つと、妨害をしばらく封じる" in help_ and "王冠を大きくけずる" in help_ and "いじわる光線" not in help_     # [BOSS-23] あそびかたに、じゃんけんと属性の説明がある


def test_bubble(game):
    """[TALK-03] セリフは吹き出しに出て、2.3秒ほどで消える。新しいセリフが来たら置きかえる。セリフは2行まで。"""
    game.start(); game.clear_board(); game.js("talkReset()")             # （盤面を空にして、放置の注意なども出ないようにしておく）
    assert game.js(f"[talking(), {BUB}.classList.contains('on')]") == [False, False]
    assert game.js("say('テスト！')") is True
    assert game.js(f"[talking(), talk.text, {BUB}.textContent, {BUB}.classList.contains('on')]") == [True, "テスト！", "テストぷに！", True]
    game.wait(300)
    assert game.page.locator("#talkBub").is_visible()
    game.js("say('つぎのセリフ', 'happy', 0, 'b')")                       # 置きかえ
    assert game.js(f"[talk.text, {BUB}.textContent]") == ["つぎのセリフ", "つぎのセリフぷに"]
    assert 2000 <= game.js("TALK_MS") <= 2500
    game.wait(game.js("TALK_MS") + 500)
    assert game.js(f"[talking(), {BUB}.classList.contains('on')]") == [False, False]
    assert game.page.locator("#talkBub").is_visible() is False
    game.js("level=worldNo*5+5; startBoss(performance.now()); energy=0; useBoost(); carry.can=1; useCan()")
    game.js("boss.crown=1; crownHit(5, performance.now()); chain=1; hitBoss(99999, performance.now())")
    assert all(len(t.split("\n")) <= 2 for t in game.js("talkLog"))
    assert not any("ぷよ" in t for t in game.js("talkLog"))


def test_moods(game):
    """[TALK-04] 表情は ふつう・よろこび・あせり の3つ。セリフが消えると ふつう にもどる。だまっていても、出口があぶない間は あせり。"""
    game.start(); game.clear_board(); game.js("talkReset()")
    assert game.js("talkMood()") == "normal"
    for mood in ["happy", "worry", "normal"]:
        game.js(f"talkReset(); say('x', '{mood}', 2)")
        assert game.js(f"[talkMood(), {BUB}.dataset.mood]") == [mood, mood]
        game.wait(150)                                                    # 3つの顔を描いてもエラーにならない
    game.js("talk.t=-1e9; talk.mood='happy'")
    assert game.js("talkMood()") == "normal"
    game.js("dangerT=500")
    assert game.js("talkMood()") == "worry"


def test_aisho_lines(game):
    """[TALK-05][BOSS-05][BOSS-06][BOSS-07][BOSS-18][BOSS-19] 相性の5通りと見破りは、ぷに妖精のセリフと表情で知らせる。盤面（abilFx）には同じ文言を出さない。"""
    game.js(ALL); game.boss(1)                                           # 砂漠（土のパー）: 特効はほうき、封印だけはじょうろ、同じ席はシャッフル
    said = lambda: game.js("[talk.text, talk.mood, talk.prio, abilFx && abilFx.text]")
    game.js("energy=100; useBroom()")
    assert said() == ["弱点を見破った！！", "happy", 2, None]
    game.js("energy=100; useBroom()")
    assert said() == ["効果ばつぐん！！", "happy", 2, None]
    game.js("energy=100; useWater()")
    assert said() == ["王冠を封じた！\nいまのうちに攻撃する！", "happy", 2, None]
    game.js("energy=100; useBoost()")
    assert said() == ["効いてる！", "normal", 2, None]
    game.clear_board(); game.put(3, 0); game.wait(500)
    game.js("energy=100; useShuffle()")
    assert said() == ["あまり効いてない…", "worry", 2, None]
    assert game.page.locator("#talkBub").inner_text() == "あまり効いてないぷに…"
    game.js("goHome()")
    game.boss(0)                                                         # 草原（木のグー）: 魔法の手（金のチョキ）は、属性で勝つ
    game.js("energy=100; useHand()")
    assert said() == ["王冠に効いてる！", "normal", 2, None]


def test_crown_lines(game):
    """[TALK-06] 王冠が半分をきると「王冠にひびが！」、こわれると「王冠撃破！」（よろこび）。"""
    game.boss(2); game.js(QUIET + "talkReset()")
    game.js("crownHit(900, performance.now())")
    assert game.js("talking()") is False                                  # まだ半分より上
    game.js("crownHit(200, performance.now())")
    assert game.js("[talk.text, talk.mood, talk.prio]") == ["王冠にひびが！", "normal", 2]
    game.js("crownHit(100, performance.now())")
    assert game.js("talkLog") == ["王冠にひびが！"]                       # ひびは1回だけ
    game.js("crownHit(99999, performance.now())")
    assert game.js("[boss.crown, talk.text, talk.mood, talk.prio]") == [0, "王冠撃破！", "happy", 2]


def test_boss_lines(game):
    """[TALK-07] ボスが出たとき（名前入り）・妨害の予告・封印中・体力が残り2割・倒したときに、ぷに妖精がしゃべる。"""
    game.boss(1)
    assert game.js("[talk.text.includes(boss.name), talk.prio]") == [True, 1]      # 「サンドキングだ！…」
    game.js(QUIET + "talkReset(); boss.nextAtk=performance.now()+1000"); game.wait(250)    # 妨害の1.1秒前: 出口が赤く光る
    assert game.js("[!!boss.warn, talk.text, talk.mood, talk.prio]") == [True, "妨害がくるぞ！", "worry", 1]
    game.wait(1200)
    game.js("talkReset(); boss.nextAtk=performance.now()+1e9; boss.sealUntil=performance.now()+60000"); game.wait(250)
    assert game.js("[talk.text, talk.prio]") == ["いまのうちだ！", 1]
    game.js("talkReset()"); game.wait(250)
    assert game.js("talking()") is False                                  # 封印1回につき1度だけ
    game.js("chain=1; hitBoss(boss.maxHp*0.5, performance.now())")
    assert game.js("talking()") is False                                  # 残り5割では言わない
    game.js("hitBoss(boss.maxHp*0.35, performance.now())")
    assert game.js("[talk.text, talk.prio]") == ["あと少し！", 1]
    game.js("hitBoss(99999, performance.now())"); game.wait(4500)
    assert "ボス撃破！" in game.js("talkLog")
    assert game.js("talkLog.filter(t=>t==='あと少し！').length") == 1


def test_seal_line_after_aisho(game):
    """[TALK-07][TALK-10] 封じる道具（特効・封印だけ）のあとの「いまのうちだ！」は、相性のセリフをじゃませず、それが消えてから出る。"""
    game.js(ALL); game.boss(1)
    game.js(QUIET + "energy=100; useBroom()"); game.wait(600)
    assert game.js("talk.text") == "弱点を見破った！！"
    game.wait(game.js("TALK_MS"))
    assert game.js("talk.text") == "いまのうちだ！"
    game.js("goHome()")
    game.boss(1)
    game.js(QUIET + "energy=100; useWater()"); game.wait(600)             # 封印だけ（6秒）でも同じ
    assert game.js("talk.text") == "王冠を封じた！\nいまのうちに攻撃する！"
    game.wait(game.js("TALK_MS"))
    assert game.js("talk.text") == "いまのうちだ！"


def test_energy_short(game):
    """[TALK-09][EN-08] エネルギーが足りなくてアイテムが使えなかったとき、「エネルギーがたりない…」（あせり）。持っていないアイテムでは言わない。"""
    game.start(); game.js(QUIET + "talkReset(); energy=0; useMag()")
    assert game.js("talking()") is False                                  # マグネットは、まだ開発していない
    game.js("useBoost()")
    assert game.js("[talk.text, talk.mood, talk.prio, energy, boostLeft]") == ["エネルギーが\nたりない…", "worry", 0, 0, 0]
    game.js("talkReset(); energy=100; useBoost()")
    assert game.js("[talking(), energy]") == [False, 70]                  # 足りていれば言わない


def test_everyday_lines(game):
    """[TALK-08] ふだんのセリフ: 3連鎖以上「○連鎖！」、エネルギー缶「エネルギー満タン！」、放置「うごかして！」、出口があぶない、ステージアップ。"""
    game.start()
    assert game.js("talkLog[0]") == "がんばろう！"
    game.clear_board()
    game.js("talkReset(); chain=2; cascade=true; chainUntil=performance.now()+60000")
    game.put(5, 0); game.wait(1200)
    assert game.js("[chain, talk.text, talk.mood]") == [3, "3連鎖！", "happy"]
    game.js("talkReset(); carry.can=1; energy=10; useCan()")
    assert game.js("[talk.text, talk.mood]") == ["エネルギー満タン！", "happy"]
    game.wait(900)                                                        # （消える演出の間は、放置を数えない）
    game.js("talkReset(); idleWarned=false; stopLeft=0; idleT=4900"); game.wait(400)
    assert game.js("[idleWarned, talk.text, talk.mood]") == [True, "うごかして！", "worry"]
    game.js("talkReset(); balls=[newBall(N/2+0.6, N/2, 0)]; dangerT=320; checkDanger()")
    assert game.js("[talk.text, talk.mood]") == ["出口があぶない！", "worry"]
    game.js("balls=[]; dangerT=0; talkReset(); stagePop=stageNeed(level)-5; popped=0; chain=0; cascade=false")
    game.put(5, 1); game.wait(1200)
    assert game.js("[level, talk.text]") == [2, "ステージ 1-2！\nそのちょうし！"]


def test_priority(game):
    """[TALK-10] 大事なセリフ（相性・王冠・撃破）は、予告・封印やふだんのセリフで上書きされない。大事なセリフは、下のセリフを置きかえる。"""
    game.js(ALL); game.boss(1); game.js(QUIET + "talkReset()")
    game.js("energy=100; useBroom()")                                    # 優先度2
    assert game.js("say('出口があぶない！', 'worry', 0, 'danger')") is False
    assert game.js("say('妨害がくるぞ！', 'worry', 1, 'warn')") is False
    game.js("energy=0; useBoost(); chain=3")                             # エネルギー不足（ふだん）でも上書きしない
    assert game.js("[talk.text, talk.mood]") == ["弱点を見破った！！", "happy"]
    game.js("boss.sealUntil=0; talkReset(); say('出口があぶない！', 'worry', 0, 'danger')")     # （封印をといて、「いまのうちだ！」が割りこまないようにしておく）
    assert game.js("say('うごかして！', 'worry', 0, 'idle')") is True      # 同じ優先度は、新しいほうに置きかえる
    assert game.js("say('妨害がくるぞ！', 'worry', 1, 'warn')") is True    # 上の優先度は、下を置きかえる
    assert game.js("say('ステージ 1-2！', 'normal', 0, 'stage')") is False
    game.js("energy=100; useBroom(); boss.sealSaid=boss.sealUntil")
    assert game.js("[talk.text, talk.prio]") == ["効果ばつぐん！！", 2]
    game.js("talk.t=performance.now()-TALK_MS-1")                         # 消えたあとは、ふだんのセリフも出る
    assert game.js("say('ステージ 1-2！', 'normal', 0, 'stage')") is True


def test_important_lines_take_turns(game):
    """[TALK-11] 大事なセリフが同時に重なったら、先のセリフを1秒見せてから次を出す（「効果ばつぐん！！」→「王冠にひびが！」）。"""
    game.js(ALL + "weakFound=['desert']"); game.boss(1)
    game.js(QUIET + "boss.crown=1100; energy=100; useBroom()")                   # 15% けずれて、半分をきる
    assert game.js("[boss.crown, talk.text, talkLog.slice(-2)]") == [800, "効果ばつぐん！！", ["効果ばつぐん！！", "王冠にひびが！"]]
    game.wait(game.js("TALK_HOLD") + 300)
    assert game.js("[talk.text, talking()]") == ["王冠にひびが！", True]


def test_gap(game):
    """[TALK-12] 同じ種類のふだんのセリフは、6秒あくまでくり返さない。"""
    game.start(); game.js(QUIET + "talkReset()")
    assert game.js("say('出口があぶない！', 'worry', 0, 'danger')") is True
    game.js("talk.t=performance.now()-TALK_MS-1")                         # 吹き出しが消えたあとでも
    assert game.js("say('出口があぶない！', 'worry', 0, 'danger')") is False
    assert game.js("TALK_GAP") == 6000
    game.js("talkLast.danger=performance.now()-TALK_GAP-1")
    assert game.js("say('出口があぶない！', 'worry', 0, 'danger')") is True


def test_fairy_tic(game):
    """[TALK-15] 吹き出しでは、セリフのおわりの記号の前に語尾「ぷに」がつく。"""
    assert game.js("fairyTalk('効果ばつぐん！！')") == "効果ばつぐんぷに！！"
    assert game.js("fairyTalk('エネルギーが\\nたりない…')") == "エネルギーが\nたりないぷに…"
    assert game.js("fairyTalk('がんばろう')") == "がんばろうぷに"
    game.start()
    game.js("talkReset(); say('封じた！','happy',3,'t',0)"); game.wait(200)
    assert game.page.locator("#talkBub").inner_text() == "封じたぷに！"
    assert game.js("fairyTalk('王冠を封じた！\\nいまのうちに攻撃する！')") == "王冠を封じたぷに！\nいまのうちに攻撃するぷに！"
    assert game.js("talk.text") == "封じた！"
