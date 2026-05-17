# 📡 ニュースリリース監視ダッシュボード

企業のニュースリリースページを自動監視し、新着をまとめて表示するシステムです。  
**完全無料・GitHub アカウントだけで動作します。**

---

## セットアップ手順

### 1. このリポジトリを Fork / テンプレートとして使う

GitHub 上で「Use this template」または「Fork」ボタンをクリックします。

---

### 2. 監視したい企業を設定する

`sites.json` を編集して、監視したい企業を追加・変更します。

```json
[
  {
    "name":          "企業名（表示用）",
    "url":           "https://example.com/news/",
    "selector":      "article, .news-item, li.release",
    "link_selector": "a"
  }
]
```

#### `selector` の決め方（重要）

1. 監視したいページをブラウザで開く
2. F12 → 要素を調べる
3. ニュース一覧の各行に使われている CSS セレクタを確認する

よくあるパターン：
- `article` — 汎用ニュース記事
- `.news-list__item` — クラス名付きリスト
- `li.press-release` — リスト形式

---

### 3. GitHub Pages を有効にする

1. リポジトリの **Settings** → **Pages**
2. Source: **Deploy from a branch**
3. Branch: `main` / Folder: `/docs`
4. Save

数分後、`https://YOUR_USERNAME.github.io/YOUR_REPO/` でアクセスできます。

---

### 4. 初回スクレイピングを手動実行

1. **Actions** タブ → **News Monitor**
2. 「Run workflow」ボタンをクリック
3. 完了後、ダッシュボードにアクセス

---

### 5. 自動実行のスケジュール確認

`.github/workflows/monitor.yml` で実行時刻を変更できます。

```yaml
schedule:
  - cron: "0 23 * * *"   # 毎日 8:00 JST
  - cron: "0 3 * * *"    # 毎日 12:00 JST
  - cron: "0 9 * * *"    # 毎日 18:00 JST
```

---

## ディレクトリ構成

```
.
├── sites.json                    # 監視する企業リスト（ここを編集）
├── data/
│   └── news.json                 # 前回取得データ（差分検出用・自動更新）
├── docs/
│   ├── index.html                # ダッシュボード（GitHub Pages で公開）
│   └── news.json                 # ダッシュボード用データ（自動更新）
├── scripts/
│   └── scrape.py                 # スクレイピングスクリプト
└── .github/workflows/
    └── monitor.yml               # GitHub Actions 定義
```

---

## よくある問題

| 症状 | 対処法 |
|------|--------|
| データが空 | `selector` が合っていない。DevTools で確認 |
| 全部 NEW になる | 初回は必ずそうなる（2回目以降は差分のみ） |
| Actions が失敗する | ログを確認。サイトが Bot 対策しているかも |
| ページが表示されない | GitHub Pages の設定を再確認 |

---

## ライセンス

MIT
