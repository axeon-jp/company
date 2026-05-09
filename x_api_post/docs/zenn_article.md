# Zenn 記事

---

## タイトル
Claude APIとX APIで「毎日自動投稿bot」を10分で作った話【コード全公開】

## トピック
Python / X API / Claude API / 自動化 / SNS

## 公開設定
有料（¥2,980）※ 途中まで無料で読めるように設定

---

## 本文

---

Axeon という X 運用 AI サービスを作っています。

そのサービスの公式アカウント（@Axeon_JP）を、**自分たちで作ったスクリプトで毎日自動投稿しています。**

「AIが運営しているアカウント」を実証デモとして使う作戦です。

今回は、そのスクリプトの仕組みと実装を全部公開します。

---

## 完成形のイメージ

毎日 7:00 / 12:00 / 21:00 に、こんな感じで動きます。

```
[2026-04-24 07:00] 投稿タイプ: 教育系

生成されたツイート:
----------------------------------------
フォロワーが伸びない人の共通点

投稿が「自分の報告」になっている。
伸びている人は「読んだ人の役に立つか」だけを考えて書いている。

たったこれだけの差。

#X運用 #SNS
----------------------------------------

[2026-04-24 07:00] 投稿完了
```

cron に登録しておけば、完全放置で毎日3本投稿されます。

---

## 使った技術

| 役割 | ライブラリ / サービス |
|------|------------------|
| ツイート生成 | Claude API（Haiku）|
| X への投稿 | tweepy（X API v2）|
| 環境変数管理 | python-dotenv |
| 自動実行 | cron |

月のAPI費用は**約¥15**です。

---

## コード解説

### 全体の流れ

```python
def main():
    # 1. 現在時刻からコンテンツタイプを決定（教育系/共感系/深掘り系）
    content_type, description = get_content_type()

    # 2. Claude API でツイートを生成
    tweet = generate_tweet(content_type, description)

    # 3. X API で投稿
    post_tweet(tweet)
```

シンプルです。3ステップだけ。

---

### STEP1: 時間帯でコンテンツタイプを変える

```python
TIME_SLOTS = {
    "morning":  (5,  10, "教育系",  "読んで得した・知らなかったと感じるノウハウ"),
    "noon":     (10, 17, "共感系",  "読者が『わかる』と感じる悩みや気づき"),
    "evening":  (17, 24, "深掘り系", "一つのテーマを掘り下げた考察"),
}

def get_content_type():
    hour = datetime.now().hour
    for slot, (start, end, label, description) in TIME_SLOTS.items():
        if start <= hour < end:
            return label, description
```

朝は教育系、昼は共感系、夜は深掘り系。
時間帯によってエンゲージメントが高いコンテンツタイプが違うので、これで最適化します。

---

### STEP2: Claude でツイートを生成する

```python
def generate_tweet(content_type, description):
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    system = f"""あなたはXアカウントの投稿を生成するAIです。
テーマ: {ACCOUNT_THEME}
口調: {ACCOUNT_PERSONA}
ルール: 140文字以内、ツイート本文のみ出力"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        system=system,
        messages=[{"role": "user", "content": f"投稿タイプ: {content_type}\n方向性: {description}"}]
    )
    return message.content[0].text.strip()
```

ポイントは**システムプロンプトでアカウントのキャラクターを定義**することです。
`ACCOUNT_THEME` と `ACCOUNT_PERSONA` を書き換えるだけで、どんなニッチにも対応できます。

---

### STEP3: tweepy で投稿する

```python
def post_tweet(text):
    client = tweepy.Client(
        consumer_key=os.getenv("X_API_KEY"),
        consumer_secret=os.getenv("X_API_SECRET"),
        access_token=os.getenv("X_ACCESS_TOKEN"),
        access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET")
    )
    client.create_tweet(text=text)
```

tweepy v4 の `Client.create_tweet()` を使うだけです。

---

## cron の設定（自動実行）

```bash
# crontab -e で追加する
0 7  * * * /usr/bin/python3 /path/to/auto_post.py >> /path/to/post.log 2>&1
0 12 * * * /usr/bin/python3 /path/to/auto_post.py >> /path/to/post.log 2>&1
0 21 * * * /usr/bin/python3 /path/to/auto_post.py >> /path/to/post.log 2>&1
```

これで毎日3回、自動実行されます。

---

## 注意点

**dotenv は絶対パスで読む**

cron はカレントディレクトリが `/` になるため、`load_dotenv()` だと `.env` を見つけられません。

```python
# NG
load_dotenv()

# OK
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
```

これにハマりました。同じミスをしないように。

---

## まとめ

- Claude Haiku + tweepy で X 自動投稿は**月¥15で動く**
- 時間帯でコンテンツタイプを変えると投稿品質が上がる
- cron の dotenv 問題には注意

---

:::message
このスクリプトのパッケージ版（セットアップガイド・カスタマイズガイド付き）を Gumroad で販売しています。
コードは全部この記事で公開していますが、「設定が面倒」「ガイドが欲しい」という方はどうぞ。
→ [Gumroad リンク]
:::

---

*続きは有料部分で：実際の投稿パフォーマンスのデータと、フォロワー増加の推移を公開します。*

<!-- ここから有料 -->

## 実際の運用データ（Axeon公式Xアカウント）

（運用開始後のデータをここに追記予定）
