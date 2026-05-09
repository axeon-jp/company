# AutoPost for X — 自動実行（cron）設定ガイド

毎日指定した時刻に自動でツイートを投稿する設定方法です。

---

## Mac / Linux の場合

### STEP 1 — Pythonのフルパスを確認する

ターミナルで以下を実行:

```bash
which python3
```

表示されたパスをメモしてください。
例: `/usr/local/bin/python3` または `/usr/bin/python3`

### STEP 2 — crontab を開く

```bash
crontab -e
```

### STEP 3 — 以下の3行を追加する

```
0 7  * * * /usr/local/bin/python3 /フルパス/auto_post.py >> /フルパス/post.log 2>&1
0 12 * * * /usr/local/bin/python3 /フルパス/auto_post.py >> /フルパス/post.log 2>&1
0 21 * * * /usr/local/bin/python3 /フルパス/auto_post.py >> /フルパス/post.log 2>&1
```

**フルパスの確認方法**:
```bash
# auto_post.py があるフォルダで実行
pwd
```

**設定例（ファイルが /home/user/autopost/ にある場合）**:
```
0 7  * * * /usr/local/bin/python3 /home/user/autopost/auto_post.py >> /home/user/autopost/post.log 2>&1
0 12 * * * /usr/local/bin/python3 /home/user/autopost/auto_post.py >> /home/user/autopost/post.log 2>&1
0 21 * * * /usr/local/bin/python3 /home/user/autopost/auto_post.py >> /home/user/autopost/post.log 2>&1
```

### STEP 4 — 保存して閉じる

- **vim の場合**: `Esc` → `:wq` → Enter
- **nano の場合**: `Ctrl+X` → `Y` → Enter

### STEP 5 — 設定を確認する

```bash
crontab -l
```

3行が表示されれば設定完了です。

---

## Windows の場合

Windowsでは「タスクスケジューラ」を使います。

### STEP 1 — タスクスケジューラを開く

スタートメニューで「タスクスケジューラ」と検索して開く

### STEP 2 — 基本タスクの作成

1. 右側の「基本タスクの作成」をクリック
2. 名前: `AutoPost 7時` と入力 → 次へ
3. トリガー: 「毎日」を選択 → 次へ
4. 開始時刻: `07:00:00` → 次へ
5. 操作: 「プログラムの開始」→ 次へ

### STEP 3 — プログラムの設定

- プログラム: `python` のフルパス（例: `C:\Python312\python.exe`）
- 引数の追加: `C:\Users\ユーザー名\autopost\auto_post.py`

### STEP 4 — 同じ手順で12時・21時分も作成

---

## 投稿ログの確認

ログファイル（`post.log`）を確認することで、投稿の成否を確認できます。

```bash
# 最新の投稿ログを表示
tail -20 post.log
```

**成功時のログ例**:
```
[2026-04-24 07:00] 投稿タイプ: 教育系
生成されたツイート:
----------------------------------------
（ツイート内容）
----------------------------------------
[2026-04-24 07:00] 投稿完了
```

**エラーが出た場合**: ログのエラー内容をそのままGumroadのサポートメッセージに送ってください。

---

## 投稿時刻を変えたい場合

cron の時刻部分を変更します。

```
# 書式: 分 時 * * * コマンド
0 7  * * * ...  ← 毎日 7:00
0 12 * * * ...  ← 毎日 12:00
0 21 * * * ...  ← 毎日 21:00

# 変更例: 8時・13時・22時にしたい場合
0 8  * * * ...
0 13 * * * ...
0 22 * * * ...
```

---

*AutoPost for X — ご購入ありがとうございました*
