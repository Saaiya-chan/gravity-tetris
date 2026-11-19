import UIKit
import WebKit
import StoreKit
import AppTrackingTransparency
import GoogleMobileAds
import UserMessagingPlatform

/// 広告と「広告を消す」買い切りの設定。
enum AdConfig {
    /// バナー広告のユニット ID。
    /// 開発中（Debug）は Google のテスト用 ID を使う（本物の広告を自分でタップするとアカウント停止になるため）。
    /// App Store 版（Release）は AdMob で作った本番の ID。アプリ ID は Info.plist の GADApplicationIdentifier。
    #if DEBUG
    static let bannerUnitID = "ca-app-pub-3940256099942544/2435281174"
    #else
    static let bannerUnitID = "ca-app-pub-1305362296318691/2739880720"   // 本番: AdMob「プレイ画面バナー」
    #endif

    /// リワード広告（動画を最後まで見るとコインがもらえる）のユニット ID。開発中は Google のテスト用 ID
    #if DEBUG
    static let rewardedUnitID = "ca-app-pub-3940256099942544/1712485313"
    #else
    static let rewardedUnitID = "ca-app-pub-1305362296318691/3438487363"   // 本番: AdMob「コイン報酬リワード」
    #endif

    /// App Store Connect で作る「非消耗型」App 内課金の製品 ID
    static let removeAdsProductID = "com.saaiya.gravitypop.removeads"
}

/// バナー広告の表示と、広告を消す買い切り（StoreKit 2）を受け持つ。
///
/// ページとのやりとり:
/// - ページ → アプリ: `window.webkit.messageHandlers.iap.postMessage({action: "buy" | "restore" | "privacy" | "state"})`
/// - アプリ → ページ: `window.__iapState({adFree, price, privacyOptions, busy, message})`、`window.__setAd(高さpx)`
final class Monetization: NSObject, WKScriptMessageHandler, BannerViewDelegate, FullScreenContentDelegate {
    weak var controller: UIViewController?
    weak var webView: WKWebView?

    private var banner: BannerView?
    private var adBar: UIView?
    private var bannerHeight: CGFloat = 0
    private var adFree = UserDefaults.standard.bool(forKey: "adFree")
    private var product: Product?
    private var updatesTask: Task<Void, Never>?
    private var adsStarted = false
    private var busy = false
    private var rewarded: RewardedAd?
    private var rewardLoading = false
    private var rewardEarned = false

    deinit { updatesTask?.cancel() }

    // MARK: - はじめる

    func start() {
        // 別の端末で買ったとき・返金されたときなどの知らせを受け取る
        updatesTask = Task { [weak self] in
            for await result in Transaction.updates { await self?.handle(result) }
        }
        Task { [weak self] in
            guard let self else { return }
            await self.refreshEntitlements()
            await self.loadProduct()
            await MainActor.run {
                self.pushState()
                if !self.adFree { self.gatherConsentAndStartAds() }
            }
        }
    }

    // MARK: - 同意（ヨーロッパなどの同意画面 → iOS の「トラッキングの許可」）→ 広告を始める

    private func gatherConsentAndStartAds() {
        guard let vc = controller else { return }
        let params = UMPRequestParameters()
        UMPConsentInformation.sharedInstance.requestConsentInfoUpdate(with: params) { [weak self] _ in
            UMPConsentForm.loadAndPresentIfRequired(from: vc) { [weak self] _ in
                guard let self else { return }
                self.pushState()                                     // 「プライバシー設定」ボタンを出すかどうか
                self.requestTrackingThenStart()
            }
        }
    }

    private func requestTrackingThenStart() {
        let go = { [weak self] in
            guard let self, UMPConsentInformation.sharedInstance.canRequestAds else { return }
            self.startAds()
        }
        if #available(iOS 14.5, *), ATTrackingManager.trackingAuthorizationStatus == .notDetermined {
            // 同意画面を閉じた直後だと表示されないことがあるので、少し待ってから聞く
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.6) {
                ATTrackingManager.requestTrackingAuthorization { _ in DispatchQueue.main.async { go() } }
            }
        } else {
            go()
        }
    }

    private func startAds() {
        guard !adsStarted, !adFree else { return }
        adsStarted = true
        MobileAds.shared.start(completionHandler: nil)
        showBanner()
        loadRewarded()
    }

    // MARK: - バナー（画面のいちばん下・全幅の帯）

    /// 画面の下端に全幅の帯を敷き、その中に広告を置く。帯はホームバーの下まで伸ばし、広告そのものは安全な範囲の中に収める。
    private func showBanner() {
        guard banner == nil, !adFree, let wv = webView, let vc = controller else { return }
        let safeWidth = wv.bounds.inset(by: wv.safeAreaInsets).width
        let size = currentOrientationAnchoredAdaptiveBanner(width: max(320, floor(safeWidth)))
        let bar = UIView()
        bar.backgroundColor = UIColor(red: 0.09, green: 0.19, blue: 0.43, alpha: 1)   // ゲームの紺色 #17306e
        bar.translatesAutoresizingMaskIntoConstraints = false
        bar.isHidden = true                                    // 広告が届くまでは場所を空けない
        let b = BannerView(adSize: size)
        b.adUnitID = AdConfig.bannerUnitID
        b.rootViewController = vc
        b.delegate = self
        b.translatesAutoresizingMaskIntoConstraints = false
        wv.addSubview(bar)
        bar.addSubview(b)
        NSLayoutConstraint.activate([
            bar.leadingAnchor.constraint(equalTo: wv.leadingAnchor),
            bar.trailingAnchor.constraint(equalTo: wv.trailingAnchor),
            bar.bottomAnchor.constraint(equalTo: wv.bottomAnchor),
            bar.topAnchor.constraint(equalTo: b.topAnchor),
            b.centerXAnchor.constraint(equalTo: wv.safeAreaLayoutGuide.centerXAnchor),
            b.bottomAnchor.constraint(equalTo: wv.safeAreaLayoutGuide.bottomAnchor),
        ])
        banner = b
        adBar = bar
        b.load(Request())
    }


    // MARK: - リワード広告（動画を見るとコイン）
    // ページ → アプリ: {action: "reward"}。見終わったら window.__rewardDone(true)、見られなかったら false。
    // 準備ができているかは __iapState の rewardReady で知らせる

    private func loadRewarded() {
        guard rewarded == nil, !rewardLoading, !adFree, adsStarted else { return }
        rewardLoading = true
        RewardedAd.load(with: AdConfig.rewardedUnitID, request: Request()) { [weak self] ad, _ in
            DispatchQueue.main.async {
                guard let self else { return }
                self.rewardLoading = false
                self.rewarded = ad
                ad?.fullScreenContentDelegate = self
                self.pushState()
                if ad == nil {                                 // 読み込めなかったら、少し待ってもう一度
                    DispatchQueue.main.asyncAfter(deadline: .now() + 30) { [weak self] in self?.loadRewarded() }
                }
            }
        }
    }

    private func showRewarded() {
        guard let ad = rewarded, let vc = controller else { rewardDone(false); loadRewarded(); return }
        rewardEarned = false
        ad.present(from: vc) { [weak self] in self?.rewardEarned = true }
    }

    private func rewardDone(_ ok: Bool) {
        DispatchQueue.main.async { [weak self] in
            self?.webView?.evaluateJavaScript("window.__rewardDone && window.__rewardDone(\(ok ? "true" : "false"))")
        }
    }

    func adDidDismissFullScreenContent(_ ad: FullScreenPresentingAd) {
        rewarded = nil
        rewardDone(rewardEarned)
        pushState()
        loadRewarded()                                         // 次の分を用意しておく
    }

    func ad(_ ad: FullScreenPresentingAd, didFailToPresentFullScreenContentWithError error: Error) {
        rewarded = nil
        rewardDone(false)
        pushState()
        loadRewarded()
    }

    private func hideBanner() {
        adBar?.removeFromSuperview()
        adBar = nil
        banner = nil
        setAdHeight(0)
    }

    private func setAdHeight(_ h: CGFloat) {
        bannerHeight = h
        webView?.evaluateJavaScript("window.__setAd && window.__setAd(\(Int(ceil(h))))")
    }

    func bannerViewDidReceiveAd(_ bannerView: BannerView) {
        adBar?.isHidden = false
        setAdHeight(bannerView.adSize.size.height)       // ページ側はこの高さ＋ホームバーの分だけ下を空ける
    }

    func bannerView(_ bannerView: BannerView, didFailToReceiveAdWithError error: Error) {
        adBar?.isHidden = true
        setAdHeight(0)                                         // 広告が来ないときは盤面を大きく戻す
    }

    /// ページを読み込み直したときに、今の状態をもう一度教える
    func pageDidLoad() {
        setAdHeight(adBar?.isHidden == false ? bannerHeight : 0)
        pushState()
    }

    // MARK: - ページからの頼みごと

    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        guard let d = message.body as? [String: Any], let action = d["action"] as? String else { return }
        switch action {
        case "buy": Task { await buy() }
        case "restore": Task { await restore() }
        case "reward": showRewarded()
        case "privacy":
            guard let vc = controller else { return }
            UMPConsentForm.presentPrivacyOptionsForm(from: vc) { [weak self] _ in self?.pushState() }
        default: pushState()
        }
    }

    // MARK: - 買い切り（StoreKit 2）

    private func loadProduct() async {
        product = try? await Product.products(for: [AdConfig.removeAdsProductID]).first
    }

    private func refreshEntitlements() async {
        var owned = false
        for await result in Transaction.currentEntitlements {
            if case .verified(let t) = result, t.productID == AdConfig.removeAdsProductID, t.revocationDate == nil { owned = true }
        }
        await setAdFree(owned)
    }

    private func handle(_ result: VerificationResult<Transaction>) async {
        guard case .verified(let t) = result else { return }
        if t.productID == AdConfig.removeAdsProductID { await setAdFree(t.revocationDate == nil) }
        await t.finish()
    }

    private func buy() async {
        if product == nil { await loadProduct() }
        guard let product else { await report("いまは購入できません。通信を確認してください"); return }
        await setBusy(true)
        do {
            switch try await product.purchase() {
            case .success(let v):
                await handle(v)
                await report("ありがとうございます！ 広告を消しました")
            case .pending: await report("購入の承認待ちです")
            case .userCancelled: break
            @unknown default: break
            }
        } catch {
            await report("購入できませんでした")
        }
        await setBusy(false)
    }

    private func restore() async {
        await setBusy(true)
        try? await AppStore.sync()
        await refreshEntitlements()
        await report(adFree ? "購入を復元しました" : "復元できる購入が見つかりませんでした")
        await setBusy(false)
    }

    @MainActor private func setAdFree(_ v: Bool) {
        let was = adFree
        adFree = v
        UserDefaults.standard.set(v, forKey: "adFree")
        if v { hideBanner(); rewarded = nil } else if was && !v { gatherConsentAndStartAds() }
        pushState()
    }

    @MainActor private func setBusy(_ v: Bool) { busy = v; pushState() }

    @MainActor private func report(_ text: String) { pushState(message: text) }

    // MARK: - ページへ知らせる

    private func pushState(message: String? = nil) {
        let privacy = UMPConsentInformation.sharedInstance.privacyOptionsRequirementStatus == .required
        var d: [String: Any] = ["adFree": adFree, "privacyOptions": privacy, "busy": busy, "canBuy": product != nil, "rewardReady": rewarded != nil]
        if let p = product { d["price"] = p.displayPrice }
        if let m = message { d["message"] = m }
        guard let data = try? JSONSerialization.data(withJSONObject: d), let json = String(data: data, encoding: .utf8) else { return }
        DispatchQueue.main.async { [weak self] in
            self?.webView?.evaluateJavaScript("window.__iapState && window.__iapState(\(json))")
        }
    }
}
