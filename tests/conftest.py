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
        self.js("spawn=function(){}; stopLeft=600000; piece=null; balls=[]; bonds=[]; chain=0; cascade=false; idleT=-1e9;")

    def put(self, n, color, row=0):
        """床の上に、同じ色のぷにを n 個ならべて置く。"""
        self.js(f"(()=>{{ for(let i=0;i<{n};i++) balls.push(newBall(1.5+i*2*R, N-R-0.01-{row}*2*R, {color})); dirty=true; }})()")

    def boss(self, world=0, quiet=True):
        """ワールド world のボス戦にする。quiet なら妨害をしばらく止めておく。"""
        self.start(world)
        self.js("level=worldNo*5+5; startBoss(performance.now());")
        if quiet:
            self.js("boss.nextAtk=performance.now()+1e9; boss.nextBeam=performance.now()+1e9;")
        self.wait(200)


@pytest.fixture
def game(browser):
    """製品版（開発用の機能なし）・セーブデータなしの状態で開いたゲーム。"""
    ctx = browser.new_context(viewport={"width": 1133, "height": 744})
    page = ctx.new_page()
    page.add_init_script("if(!sessionStorage.__t){ localStorage.clear(); sessionStorage.__t=1; } window.__appRelease=true;")
    page.goto(URL)
    page.wait_for_timeout(600)
    g = Game(page)
    g.js("introSeen={has:()=>true,add(){},size:0}")          # ワールドの紹介画面は出さない
    if page.locator(".x-close").count():                       # デイリーのお知らせを閉じる
        page.locator(".x-close").first.click()
        page.wait_for_timeout(200)
    yield g
    assert g.errors == [], f"JavaScript のエラー: {g.errors}"
    ctx.close()
