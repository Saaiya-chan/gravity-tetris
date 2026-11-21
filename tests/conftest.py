"""グラビティ・ポップの自動テスト（Playwright + pytest）。

free.html を実際のブラウザで開き、ゲームの中の変数や関数を直接さわって確かめる。
各テストの docstring の先頭にある [XXX-00] は docs/SPEC.md の要件番号。

実行:  pytest tests            （Chrome の場所は環境変数 CHROME で指定できる）
"""
import os, pathlib, pytest
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = (ROOT / "free.html").as_uri()
CHROME = os.environ.get("CHROME") or next((p for p in (
    "/usr/bin/google-chrome",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome") if os.path.exists(p)), None)


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=CHROME) if CHROME else p.chromium.launch()
        yield b
        b.close()


class Game:
    """1ページ分のゲーム。js() で中の式を評価する。"""

    def __init__(self, page):
        self.page, self.errors = page, []
        page.on("pageerror", lambda e: self.errors.append(str(e)))

    def js(self, expr):
        return self.page.evaluate(expr)

    def wait(self, ms):
        self.page.wait_for_timeout(ms)

    def start(self, world=0, wait=2600):
        """ワールド world（0〜9）を始めて、最初の演出が終わるまで待つ。"""
        self.js(f"start('world',{world})")
        self.wait(wait)

    def clear_board(self):
        """盤面を空にして、新しい組が出ないようにする（消え方を調べる下ごしらえ）。"""
        # はじめの数秒のあいだに自然に消えたぶん（フラワーでは、はなぷに3個の組が落ちただけで消える）は、数えなかったことにする
        self.js("spawn=function(){}; stopLeft=600000; piece=null; balls=[]; bonds=[]; chain=0; cascade=false; idleT=-1e9;"
                " popping=null; petalFx=null; popped=0; stagePop=0; score=0;")

    def put(self, n, color, row=0):
        """床の上に、同じ色のぷにを n 個ならべて置く。"""
        self.js(f"(()=>{{ for(let i=0;i<{n};i++) balls.push(newBall(1.5+i*2*R, N-R-0.01-{row}*2*R, {color})); dirty=true; }})()")

    def reopen(self, wait=600):
        """ゲームを開き直す（セーブデータは残す）。
        テスト用のブラウザは、負荷が高いと、読みこみ直しのときに localStorage をまるごと落とすことがある
        （ゲームのコードがない空のページでも起きる）。保存された中身をひかえておき、開き直したページへ入れ直す。"""
        saved = self.js("JSON.stringify(Object.fromEntries(Object.entries(localStorage)))")
        self.page.add_init_script(f"(()=>{{ const s={saved}; localStorage.clear(); for(const k in s) localStorage.setItem(k,s[k]); }})()")
        self.page.reload()
        self.wait(wait)

    def boss(self, world=0, quiet=True):
        """ワールド world のボス戦にする。quiet なら妨害をしばらく止めておく。"""
        self.start(world)
        self.js("level=worldNo*5+5; startBoss(performance.now());")
        if quiet:
            self.js("boss.nextAtk=performance.now()+1e9; boss.nextBeam=performance.now()+1e9;")
        self.wait(200)


def open_game(browser, width=1133, height=744):
    """製品版・セーブデータなしでゲームを開く。(Game, context) を返す。"""
    ctx = browser.new_context(viewport={"width": width, "height": height})
    page = ctx.new_page()
    page.add_init_script("if(window.name!==\"gp-test\"){ localStorage.clear(); window.name=\"gp-test\"; } window.__appRelease=true;")
    page.goto(URL)
    page.wait_for_timeout(600)
    g = Game(page)
    g.js("introSeen={has:()=>true,add(){},size:0}")          # ワールドの紹介画面は出さない
    if page.locator(".x-close").count():                       # デイリーのお知らせを閉じる
        close = page.locator(".x-close").first
        close.click() if width >= height else close.dispatch_event("click")   # 縦向きでは「横向きにしてね」の案内が上にかぶさるので、直接押す
        page.wait_for_timeout(200)
    return g, ctx


@pytest.fixture
def game(browser):
    """製品版（開発用の機能なし）・セーブデータなしの状態で開いたゲーム（iPad くらいの大きさ 1133x744）。"""
    g, ctx = open_game(browser)
    yield g
    assert g.errors == [], f"JavaScript のエラー: {g.errors}"
    ctx.close()


@pytest.fixture
def game_at(browser):
    """画面の大きさをえらんで開く: game_at(844, 390) → Game。いろいろな画面（iPhone の横向き・iPad）のテスト用。"""
    opened = []

    def make(width, height):
        g, ctx = open_game(browser, width, height)
        opened.append((g, ctx))
        return g
    yield make
    for g, ctx in opened:
        assert g.errors == [], f"JavaScript のエラー: {g.errors}"
        ctx.close()
