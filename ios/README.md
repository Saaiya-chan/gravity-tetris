# グラビティ・ポップ iOS アプリ

ゲーム本体（`../free.html`）を全画面の WebView で表示するだけの、小さなアプリです。

- **Xcode から ▶︎ で入れた開発版（Debug）**: GitHub Pages の最新版を読み込みます。`free.html` を push すれば、次の起動で反映されます。ネットにつながらないときは同梱の `free.html` で動きます。
- **App Store に出す版（Release・Archive）**: アプリに同梱した `free.html` だけで動きます。開発用のボタン（全ぷに解禁・ボス戦・コイン+100・「フリー」表記）は出ません。中身を変えたら、もう一度 Archive して審査に出します。
- 横向き専用・ステータスバーなし・ホームインジケーターは自動で隠れる・遊んでいる間は画面が暗くならない。
- 傾きセンサーの許可は、アプリ側で自動的に「許可」と答えます。

## iPad に入れる

1. `GravityPop.xcodeproj` を Xcode で開く
2. 左のファイル一覧で一番上の **GravityPop** → TARGETS の **GravityPop** → **Signing & Capabilities**
   - **Team** で自分の Apple ID を選ぶ（無料の Apple ID でも可）
   - 「Bundle Identifier が使えない」と言われたら `com.saaiya.gravitypop` の末尾を変える
3. iPad を Mac にケーブルでつなぎ、上の実行先で iPad を選んで ▶︎（⌘R）
4. 初回は iPad の **設定 → 一般 → VPN とデバイス管理** で自分の開発元を「信頼」
   - iPad 側で **デベロッパモード** をオンにするよう求められたら、設定 → プライバシーとセキュリティ → デベロッパモード

無料の Apple ID で入れたアプリは 7 日で起動できなくなります。そのときはもう一度 ▶︎ で入れ直してください。


## App Store に出す

準備済みのもの: アイコン（`GravityPop/Assets.xcassets`）、プライバシーマニフェスト（`PrivacyInfo.xcprivacy`）、暗号化の申告（Info.plist）、バージョン 1.0、スクリーンショット（`../appstore/screenshots/`）、
プライバシーポリシー https://saaiya-chan.github.io/gravity-tetris/privacy.html 、サポート https://saaiya-chan.github.io/gravity-tetris/support.html

1. https://appstoreconnect.apple.com → アプリ → ＋ → 新規 App（iOS、Bundle ID は `com.saaiya.gravitypop`、SKU は `gravitypop` など自由）
2. Xcode で実行先を **Any iOS Device (arm64)** にする → メニュー **Product → Archive**
3. できあがった Organizer で **Distribute App → App Store Connect → Upload**
4. App Store Connect で、ビルドを選び、スクショ・説明文・年齢制限・価格・App のプライバシー（「データを収集しない」）を入れて **審査に提出**

## 広告と「広告を消す」買い切り

- バナー広告（Google AdMob）を盤面の下に出します。ゲームは広告の高さだけ盤面を小さくします（`window.__setAd`）。
- 「広告を消す」は非消耗型の App 内課金（製品 ID `com.saaiya.gravitypop.removeads`）。タイトルとポーズに「広告を消す」「購入を復元」ボタンが出ます。
- ヨーロッパなどでは Google の同意画面（UMP）、そのあと iOS の「トラッキングの許可」を聞きます。
- 初めて開くと、Xcode が Google の広告ライブラリ（Swift Package）を自動でダウンロードします。

AdMob の ID は設定済みです（アプリ ID は `Info.plist`、バナーのユニット ID は `Monetization.swift`。Debug ビルドでは Google のテスト広告が出ます）。
残り: App Store Connect で App 内課金「非消耗型」を作る（製品 ID は上と同じ）。

## リワード広告（動画を見るとコイン）

- ワールドクリアのコイン2倍と、デイリーボーナスの「動画を見てコイン」で使います。ユニット ID は `Monetization.swift` の `AdConfig.rewardedUnitID`（本番は AdMob「コイン報酬リワード」、Debug は Google のテスト用）。
- ページ → アプリ `{action:"reward"}`、アプリ → ページ `window.__rewardDone(true/false)`。準備できているかは `__iapState` の `rewardReady`。
- 「広告を消す」を買った人は、動画なしで2倍・おまけを受け取れます。
