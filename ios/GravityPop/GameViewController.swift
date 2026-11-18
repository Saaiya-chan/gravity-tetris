import UIKit
import WebKit
import LinkPresentation

/// ゲーム本体（free.html）を全画面の WebView で表示する。
///
/// - App Store 用（Release ビルド・Archive）: アプリに同梱した free.html だけを読み込む。
///   審査を通った中身のまま動き、ネットがなくても遊べる。開発用のボタンはページ側で隠す。
/// - 開発用（Debug ビルド・Xcode から実行）: GitHub Pages の最新版を読み込む（push するとすぐ反映）。
///   ネットにつながらないときは同梱の free.html にする。
final class GameViewController: UIViewController, WKNavigationDelegate, WKUIDelegate {
    private static let remoteURL = URL(string: "https://saaiya-chan.github.io/gravity-tetris/free.html")!

    private var webView: WKWebView!
    private let money = Monetization()   // バナー広告と「広告を消す」買い切り
    private var usingBundled = false
    private var moneyStarted = false

    override func loadView() {
        let config = WKWebViewConfiguration()
        config.allowsInlineMediaPlayback = true
        config.mediaTypesRequiringUserActionForPlayback = []   // 効果音をすぐ鳴らせるように
        // ページから「この URL を外のアプリで開いて」と頼めるようにする（X への投稿など）
        let opener = ExternalOpener()
        config.userContentController.add(opener, name: "openExternal")
        config.userContentController.add(opener, name: "shareImage")
        config.userContentController.add(opener, name: "postX")
        config.userContentController.add(money, name: "iap")
        #if !DEBUG
        // App Store 版であることをページに教える（開発用の機能を隠してもらう）
        config.userContentController.addUserScript(WKUserScript(
            source: "window.__appRelease = true;", injectionTime: .atDocumentStart, forMainFrameOnly: true))
        #endif

        webView = WKWebView(frame: .zero, configuration: config)
        opener.webView = webView
        opener.controller = self
        money.webView = webView
        money.controller = self
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
        #if DEBUG
        loadRemote()
        #else
        loadBundled()
        #endif
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
    // 傾けて遊ぶので、大きく傾けたときに iOS が画面をくるっと逆さまにしないよう、
    // 起動したときの横向きに固定する（反対向きで遊びたいときは、アプリを開き直す）
    private var lockedMask: UIInterfaceOrientationMask = .landscape
    override var supportedInterfaceOrientations: UIInterfaceOrientationMask { lockedMask }

    private func lockOrientation() {
        guard lockedMask == .landscape, let o = view.window?.windowScene?.interfaceOrientation else { return }
        lockedMask = (o == .landscapeLeft) ? .landscapeLeft : .landscapeRight
        if #available(iOS 16.0, *) { setNeedsUpdateOfSupportedInterfaceOrientations() }
    }

    // MARK: - 画面の向きをページに教える
    // 縦持ちのまま起動すると、画面は横なのに window.orientation が 0（縦）のままになり、
    // 傾きの向きが90度ずれる。本当の画面の向きをページに渡して、それを使ってもらう。

    override func viewDidAppear(_ animated: Bool) {
        super.viewDidAppear(animated)
        pushOrientation()
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { [weak self] in self?.lockOrientation(); self?.pushOrientation() }
        if !moneyStarted { moneyStarted = true; money.start() }   // 画面が出てから（同意画面などを出せるように）
    }

    override func viewWillTransition(to size: CGSize, with coordinator: UIViewControllerTransitionCoordinator) {
        super.viewWillTransition(to: size, with: coordinator)
        coordinator.animate(alongsideTransition: nil) { [weak self] _ in self?.pushOrientation() }
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        pushOrientation()
        money.pageDidLoad()
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
        if message.name == "postX" { postX(message.body); return }
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

    /// X で投稿: 結果カードの画像をクリップボードにコピーしてから、X の投稿画面を開く
    private func postX(_ body: Any) {
        guard let d = body as? [String: Any], let s = d["intent"] as? String, let url = URL(string: s) else { return }
        if let dataURL = d["image"] as? String, let comma = dataURL.firstIndex(of: ","),
           let data = Data(base64Encoded: String(dataURL[dataURL.index(after: comma)...]), options: .ignoreUnknownCharacters),
           let img = UIImage(data: data) {
            UIPasteboard.general.image = img
        }
        DispatchQueue.main.async {
            UIApplication.shared.open(url, options: [:]) { [weak self] ok in
                if !ok { self?.report("X を開けませんでした") }
            }
        }
    }

    /// 結果カードの画像と文を、iOS の共有メニューで共有する（X を選べば画像つきで投稿できる）
    private func shareImage(_ body: Any) {
        guard let d = body as? [String: Any] else { report("共有データが正しくありません"); return }
        var items: [Any] = []
        let text = (d["text"] as? String ?? "") + "\n" + (d["url"] as? String ?? "")
        // 結果カードの画像を PNG ファイルにして渡す（X などのアプリに画像として確実に渡すため）
        if let dataURL = d["image"] as? String, let comma = dataURL.firstIndex(of: ","),
           let data = Data(base64Encoded: String(dataURL[dataURL.index(after: comma)...]), options: .ignoreUnknownCharacters),
           let img = UIImage(data: data) {
            let url = FileManager.default.temporaryDirectory.appendingPathComponent("gravity-pop.png")
            try? data.write(to: url)
            items.append(ShareImageSource(image: img, fileURL: url, title: "グラビティ・ポップの記録"))
        } else {
            report("画像を作れませんでした（文だけ共有します）")
        }
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
                DispatchQueue.main.async { self?.webView?.evaluateJavaScript("window.__shareDone && __shareDone()") }
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

/// 共有メニューに渡す画像。メニューの一番上に画像のサムネイルとタイトルを出す。
private final class ShareImageSource: NSObject, UIActivityItemSource {
    let image: UIImage, fileURL: URL, title: String
    init(image: UIImage, fileURL: URL, title: String) { self.image = image; self.fileURL = fileURL; self.title = title }

    func activityViewControllerPlaceholderItem(_ activityViewController: UIActivityViewController) -> Any { image }

    func activityViewController(_ activityViewController: UIActivityViewController,
                                itemForActivityType activityType: UIActivity.ActivityType?) -> Any? {
        activityType == .saveToCameraRoll ? image : fileURL      // 「画像を保存」は写真に、ほかはファイルとして渡す
    }

    func activityViewControllerLinkMetadata(_ activityViewController: UIActivityViewController) -> LPLinkMetadata? {
        let m = LPLinkMetadata()
        m.title = title
        m.imageProvider = NSItemProvider(object: image)
        m.iconProvider = NSItemProvider(object: image)
        return m
    }
}
