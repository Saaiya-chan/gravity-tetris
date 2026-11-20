# テスト

`free.html` を実際のブラウザ（Chrome）で開いて、仕様書（`docs/SPEC.md`）の要件を確かめます。
各テストの説明の先頭にある `[EN-01]` のような番号が、仕様書の要件番号です。

## 準備（最初の1回）

```
pip install pytest playwright
```

Chrome が入っていればそのまま動きます。別の場所にある場合は、環境変数 `CHROME` に実行ファイルの場所を入れてください。

## 実行

```
pytest tests              # 全部（5分ほど）
pytest tests -k energy    # エネルギーだけ
pytest tests -k weakness  # テスト名の一部で指定
```

## ファイル

| ファイル | 内容 |
|---|---|
| `conftest.py` | ゲームを開く下ごしらえ（製品版・セーブデータなし） |
| `test_energy.py` | エネルギー（EN） |
| `test_items.py` | アイテム・強化・研究所（ITEM / UP / LAB） |
| `test_boss.py` | ボス・王冠・相性・宝石（BOSS / GEM） |
| `test_star.py` | スター（STAR） |
| `test_world.py` | ワールド・ぷに・ライフ・放置・ショップ（WORLD / PUNI / CHAIN / LIFE / IDLE / SHOP） |

## 仕様を変えるとき

1. `docs/SPEC.md` の要件を直す（新しいものには番号をつける）。
2. その番号を docstring に書いたテストを足す・直す。
3. `free.html` を直して、`pytest tests` が通ることを確かめる。
