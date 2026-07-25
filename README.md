# 進行垢・引退垢・BOX公開アカウント 販売サイト

公開用の静的サイト + **Windows 11 ローカルサーバーAPI** による商品管理機能付き。

デザインは元のまま完全維持しています。

## ファイル構成

```
.
├── index.html          # 公開ページ（デザインそのまま）
├── admin.html          # 管理画面（ローカル専用）
├── main.py             # FastAPI ローカルサーバー
├── requirements.txt
├── data/
│   ├── games.json      # タイトル（カテゴリ）データ
│   └── products.json   # 商品データ
├── images/             # アップロードした画像（自動生成）
└── README.md
```

## セットアップ（Windows 11）

1. **Python 3.10+** が入っていることを確認  
   （Microsoft Store または python.org からインストール可）

2. このフォルダを開いて、コマンドプロンプト or PowerShell で：

```bash
pip install -r requirements.txt
```

3. サーバー起動：

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

4. ブラウザでアクセス：
   - 公開ページ: http://127.0.0.1:8000/
   - 管理画面:   http://127.0.0.1:8000/admin
   - APIドキュメント: http://127.0.0.1:8000/docs

## 管理画面の使い方

### タイトル（ゲーム）追加
- 「タイトル（ゲーム）管理」セクションで ID・表示名・正式名称・アイコンを入力して追加
- 例: ID=`monst`, 表示名=`モンスト`, 正式名称=`モンスターストライク`, アイコン=`M`

### 商品の追加・編集・削除
1. 「＋ 新規商品」ボタンでモーダルを開く
2. ゲームを選択、タイトル・説明・価格・連絡先URLを入力
3. **画像エリアにドラッグ＆ドロップ**（またはクリックして選択）で複数画像を追加
4. プレビューで不要な画像は × で削除可能
5. 「保存」でアップロード＋登録完了
6. 一覧の「編集」「削除」で既存商品を変更可能

画像は自動的に `images/` フォルダに保存され、`products.json` に相対パスが記録されます。

## GitHub 公開時の注意

- **公開するのは静的ファイルのみ推奨**:
  - `index.html`
  - `data/games.json`
  - `data/products.json`
  - `images/` フォルダ全体
- `main.py` / `admin.html` / `requirements.txt` はローカル編集用なので、リポジトリに含めても良いですが、GitHub Pages では編集機能は動きません（静的ホスティングのため）。
- GitHub Pages で公開する場合は、`data/` と `images/` を同じ階層に置けば、`index.html` が自動で JSON を読み込みます。
- 編集したいときはローカルで `uvicorn` を起動して管理画面を使ってください。変更後、`data/` と `images/` をコミットすれば公開側に反映されます。

## 初期データの注意

初回起動時に `data/products.json` が存在しない場合、画像なしのサンプル商品が生成されます。  
管理画面で画像をドラッグ＆ドロップして追加してください。

元のプレースホルダー（SVG）は `index.html` 内の FALLBACK に残っているため、JSON が読めない環境ではそちらが表示されます。

## API 概要（参考）

| Method | Path                  | 説明                     |
|--------|-----------------------|--------------------------|
| GET    | /api/games            | タイトル一覧             |
| POST   | /api/games            | タイトル追加             |
| PUT    | /api/games/{id}       | タイトル更新             |
| DELETE | /api/games/{id}       | タイトル削除             |
| GET    | /api/products         | 商品一覧                 |
| POST   | /api/products         | 商品追加                 |
| PUT    | /api/products/{id}    | 商品更新                 |
| DELETE | /api/products/{id}    | 商品削除（画像も削除）   |
| POST   | /api/upload           | 画像アップロード（複数） |

## トラブルシューティング

- **画像が表示されない**: `images/` フォルダのパスが正しいか、サーバーを再起動して確認。
- **CORS / 読み込みエラー**: 必ず `uvicorn` 経由で開いてください（`file://` では fetch が失敗します）。
- **ポートが使われている**: `--port 8001` などに変更。
- **Python が見つからない**: `py -m pip install -r requirements.txt` や `py -m uvicorn ...` を試す。

---

© tools_A  
デザインはそのまま、ローカル管理機能を追加しました。

## 管理画面から GitHub に公開する（新機能）

管理画面の右上に **「🚀 GitHubへ公開」** ボタンがあります。

1. 商品の追加・編集・画像アップロードを行う（通常の保存）
2. 「GitHubへ公開」ボタンをクリック
3. コミットメッセージを入力して確定
4. 自動で `data/` と `images/` が `git add` → `commit` → `push` されます

### 初回準備（必須）

このフォルダを Git リポジトリにしておく必要があります。

```bash
git init
git remote add origin https://github.com/あなたのユーザー名/リポジトリ名.git
git add .
git commit -m "initial"
git branch -M main
git push -u origin main
```

その後は管理画面のボタンだけで公開できます。

認証は Git Credential Manager（Windows 標準）や SSH 鍵、Personal Access Token などで行ってください。
push に失敗した場合でもコミットまでは自動で行われるので、手動で `git push` すればOKです。

## 簡単起動（Windows）

ダブルクリックするだけで起動できるバッチファイルを用意しています。

- `起動.bat` （日本語）
- `start.bat` （英語）

どちらをダブルクリックしても同じです。

起動すると：
1. 自動で依存パッケージを確認（初回のみインストール）
2. 管理画面をブラウザで自動オープン
3. サーバーが起動

終了するときはウィンドウで **Ctrl + C** を押してください。
