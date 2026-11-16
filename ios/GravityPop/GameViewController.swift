import UIKit
import WebKit

/// ゲーム本体（free.html）を全画面の WebView で表示する。
///
/// - 通常は GitHub Pages の最新版を読み込む（push するとアプリにもすぐ反映される）。
/// - ネットにつながらないときは、アプリに同梱した free.html を読み込む。
final class GameViewController: UIViewController, WKNavigationDelegate, WKUIDelegate {
    private static let remoteURL = URL(string: "https://saaiya-chan.github.io/gravity-tetris/free.html")!

    private var webView: WKWebView!
    private var usingBundled = false

    override func loadView() {
        let config = WKWebViewConfiguration()
        config.allowsInlineMediaPlayback = true
        config.mediaTypesRequiringUserActionForPlayback = []   // 効果音をすぐ鳴らせるように
        // ページから「この URL を外のアプリで開いて」と頼めるようにする（X への投稿など）
        let opener = ExternalOpener()
        config.userContentController.add(opener, name: "openExternal")
        config.userContentController.add(opener, name: "shareImage")

        webView = WKWebView(frame: .zero, configuration: config)
        opener.webView = webView
        opener.controller = self
        webView.navigationDelegate = self
        webView.uiDelegate = self
        webView.isOpaque = false
        webView.backgroundColor = UIColor(red: 0.04, green: 0.05, blue: 0.07, alpha: 1)
        webView.scrollView.isScrollEnabled = false
        webView.scrollView.bounces = false
        webView.scrollView.contentInsetAdjustmentBehavior = .never   // ノッチ・角丸まで使う（余白は CSS の safe-area で取る）
        webView.allowsLinkPreview = false
        #if DEBUG
        if #available(iOS 16.4, *) { webView.isInspectable = true }  // Mac の Safari から中身を調べられる
        #endif
        view = webView
    }

    override func viewDidLoad() {
        super.viewDidLoad()
        loadRemote()
    }

    private func loadRemote() {
        usingBundled = false
        let req = URLRequest(url: Self.remoteURL, cachePolicy: .reloadRevalidatingCacheData, timeoutInterval: 8)
        webView.load(req)
    }

    private func loadBundled() {
        guard !usingBundled, let url = Bundle.main.url(forResource: "free", withExtension: "html") else { return }
        usingBundled = true
        webView.loadFileURL(url, allowingReadAccessTo: url.deletingLastPathComponent())
    }

    // MARK: - 全画面

    override var prefersStatusBarHidden: Bool { true }
    override var prefersHomeIndicatorAutoHidden: Bool { true }
    override var preferredScreenEdgesDeferringSystemGestures: UIRectEdge { .all }   // 画面端のスワイプで誤って閉じにくくする
    override var supportedInterfaceOrientations: UIInterfaceOrientationMask { .landscape }

    // MARK: - 画面の向きをページに教える
    // 縦持ちのまま起動すると、画面は横なのに window.orientation が 0（縦）のままになり、
    // 傾きの向きが90度ずれる。本当の画面の向きをページに渡して、それを使ってもらう。

    override func viewDidAppear(_ animated: Bool) {
        super.viewDidAppear(animated)
        pushOrientation()
    }

    override func viewWillTransition(to size: CGSize, with coordinator: UIViewControllerTransitionCoordinator) {
        super.viewWillTransition(to: size, with: coordinator)
        coordinator.animate(alongsideTransition: nil) { [weak self] _ in self?.pushOrientation() }
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        pushOrientation()
    }

    private func pushOrientation() {
        guard let o = view.window?.windowScene?.interfaceOrientation else { return }
        // window.orientation と同じ決まり: 端末を反時計回りに回すと正
        let angle: Int
        switch o {
        case .landscapeRight: angle = 90      // ホームボタン（または USB-C 端子）が右
        case .landscapeLeft: angle = -90
        case .portraitUpsideDown: angle = 180
        default: angle = 0
        }
        webView.evaluateJavaScript("window.__nativeAngle=\(angle); if(window.applyOrientation) applyOrientation();")
    }

    // MARK: - 読み込み失敗したら同梱版へ

    func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
        loadBundled()
    }

    func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
        loadBundled()
    }

    // MARK: - ゲーム以外のリンク（X への投稿など）は外のアプリで開く

    private func isGameURL(_ url: URL) -> Bool {
        url.isFileURL || url.host == Self.remoteURL.host || url.scheme == "about"
    }

    func webView(_ webView: WKWebView,
                 decidePolicyFor navigationAction: WKNavigationAction,
                 decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        if let url = navigationAction.request.url, !isGameURL(url) {
            UIApplication.shared.open(url)          // X アプリが入っていれば X、なければ Safari で開く
            decisionHandler(.cancel)
            return
        }
        decisionHandler(.allow)
    }

    // window.open(..., "_blank") で開こうとしたとき
    func webView(_ webView: WKWebView,
                 createWebViewWith configuration: WKWebViewConfiguration,
                 for navigationAction: WKNavigationAction,
                 windowFeatures: WKWindowFeatures) -> WKWebView? {
        if let url = navigationAction.request.url { UIApplication.shared.open(url) }
        return nil
    }

    // MARK: - 傾きセンサーの許可（ページの DeviceMotionEvent.requestPermission() に答える）

    @available(iOS 15.0, *)
    func webView(_ webView: WKWebView,
                 requestDeviceOrientationAndMotionPermissionFor origin: WKSecurityOrigin,
                 initiatedByFrame frame: WKFrameInfo,
                 decisionHandler: @escaping (WKPermissionDecision) -> Void) {
        decisionHandler(.grant)
    }
}

/// ページの window.webkit.messageHandlers.openExternal.postMessage(url) を受けて、
/// その URL を外のアプリ（X アプリが入っていれば X、なければ Safari）で開く。
private final class ExternalOpener: NSObject, WKScriptMessageHandler {
    weak var webView: WKWebView?
    weak var controller: UIViewController?

    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        if message.name == "shareImage" { shareImage(message.body); return }
        guard let s = message.body as? String, let url = URL(string: s),
              url.scheme == "https" || url.scheme == "http" else {
            report("URL が正しくありません")
            return
        }
        DispatchQueue.main.async {
            UIApplication.shared.open(url, options: [:]) { [weak self] ok in
                self?.report(ok ? "X を開きました" : "X を開けませんでした（iOS が拒否）")
            }
        }
    }

    /// 結果カードの画像と文を、iOS の共有メニューで共有する（X を選べば画像つきで投稿できる）
    private func shareImage(_ body: Any) {
        guard let d = body as? [String: Any] else { report("共有データが正しくありません"); return }
        var items: [Any] = []
        if let dataURL = d["image"] as? String, let comma = dataURL.firstIndex(of: ","),
           let data = Data(base64Encoded: String(dataURL[dataURL.index(after: comma)...])),
           let img = UIImage(data: data) { items.append(img) }
        let text = (d["text"] as? String ?? "") + "\n" + (d["url"] as? String ?? "")
        items.append(text)
        DispatchQueue.main.async {
            guard let vc = self.controller, let wv = self.webView else { return }
            let av = UIActivityViewController(activityItems: items, applicationActivities: nil)
            if let pop = av.popoverPresentationController {           // iPad は吹き出しで出す
                pop.sourceView = wv
                pop.sourceRect = CGRect(x: wv.bounds.midX, y: wv.bounds.midY, width: 1, height: 1)
                pop.permittedArrowDirections = []
            }
            av.completionWithItemsHandler = { [weak self] _, done, _, _ in
                self?.report(done ? "シェアしました" : "")
            }
            vc.present(av, animated: true)
        }
    }

    /// 結果をページの「𝕏 でシェア」の下に表示する
    private func report(_ text: String) {
        let js = "var m=document.getElementById('xMsg'); if(m) m.textContent=\(String(reflecting: text));"
        DispatchQueue.main.async { self.webView?.evaluateJavaScript(js) }
    }
}
