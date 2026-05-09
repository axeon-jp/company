# AutoPost for X — セットアップガイド

**所要時間: 約15〜20分**

---

## 必要なもの

| 項目 | 費用 | 取得先 |
|------|------|--------|
| X (Twitter) アカウント | 無料 | — |
| X Developer アカウント | 無料 | developer.twitter.com |
| Anthropic APIキー | 従量課金（月数円〜数百円） | console.anthropic.com |
| Python 3.9以上 | 無料 | python.org |

---

## STEP 1 — ファイルを準備する

1. ZIPファイルを解凍する
2. フォルダの中身を確認する

```
autopost-for-x/
├── auto_post.py       ← メインスクリプト
├── .env.example       ← APIキー設定のテンプレート
├── requirements.txt   ← 必要なライブラリ一覧
└── docs/              ← このガイドが入っています
```

3. `.env.example` を複製して `.env` にリネームする

---

## STEP 2 — Pythonライブラリをインストールする

ターミナル（Mac: Terminal / Windows: コマンドプロンプト）を開いて以下を実行:

```bash
pip install -r requirements.txt
```

---

## STEP 3 — X APIキーを取得する

### 3-1. Developer Portalにアクセス
`https://developer.twitter.com/` にアクセスしてXアカウントでログイン

### 3-2. アプリを作成する
1. 「+ Create Project」をクリック
2. プロジェクト名を入力（例: `AutoPost`）
3. ユースケースは「Making a bot」を選択
4. アプリ名を入力

### 3-3. APIキーをコピーする
作成完了後に表示される以下の4つをコピーして `.env` に貼り付ける:

```
X_API_KEY=（API Key）
X_API_SECRET=（API Key Secret）
X_ACCESS_TOKEN=（Access Token）
X_ACCESS_TOKEN_SECRET=（Access Token Secret）
```

> ⚠️ キーは一度しか表示されません。必ずすぐにメモしてください。

### 3-4. アプリの権限を変更する
1. アプリの「Settings」→「User authentication settings」
2. 「App permissions」を **Read and Write** に変更
3. 保存する

---

## STEP 4 — Anthropic APIキーを取得する

1. `https://console.anthropic.com/` にアクセスしてアカウント作成
2. 「API Keys」→「Create Key」
3. 作成したキーをコピーして `.env` に貼り付ける

```
ANTHROPIC_API_KEY=（sk-ant-xxxxx）
```

> 💡 料金について: Claude Haiku は非常に安価です。1ツイート生成あたり約0.01円。1日3投稿 × 30日 = 月約1円です。

---

## STEP 5 — 動作確認する

ターミナルでスクリプトのフォルダに移動して実行:

```bash
cd autopost-for-x
python auto_post.py
```

以下のように表示されれば成功です:

```
[2026-04-24 12:00] 投稿タイプ: 共感系

生成されたツイート:
----------------------------------------
（ツイート内容）
----------------------------------------

[2026-04-24 12:00] 投稿完了
```

実際のXアカウントを確認して投稿されていればセットアップ完了です。

---

## STEP 6 — 自動実行を設定する（cron）

毎日自動で投稿するには cron の設定が必要です。
詳しくは **cron_setup.pdf** を参照してください。

---

## よくある質問

**Q. 「API Keyが見つかりません」と表示される**
→ `.env.example` を `.env` にリネームしているか確認してください。`.env.example` のままでは読み込まれません。

**Q. 「Read and Write権限がありません」エラーが出る**
→ STEP 3-4 の権限変更を行い、その後アクセストークンを再生成してください。

**Q. 投稿内容を自分のアカウントに合わせたい**
→ **prompt_customize.pdf** を参照してください。

---

*AutoPost for X — ご購入ありがとうございました*
