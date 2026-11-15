# グラビティ・ポップ iOS アプリ

ゲーム本体（`../free.html`）を全画面の WebView で表示するだけの、小さなアプリです。

- 起動すると GitHub Pages の最新版を読み込みます。`free.html` を push すれば、アプリを入れ直さなくても次の起動で反映されます。
- ネットにつながらないときは、ビルド時にアプリへ同梱した `free.html` で動きます。
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
