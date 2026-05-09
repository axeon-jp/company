# アフィリエイト自動投稿システムの作り方【コード全公開】X×note×A8.net×Claude API

---

## ここから無料で読めます

「アフィリエイトをやりたいけど毎日投稿する時間がない」

この問題をAIと自動化で解決しました。

仕組みはシンプルです。Claude APIが商材に合ったアフィリエイトツイートを生成して、X APIが自動投稿する。**アフィリエイトリンクはnote記事に貼り、XにはそのnoteのURLを載せる。**

> ⚠️ XはA8.netなどのアフィリエイトURLを直接ブロックします。リプライに貼ってもエラーになるため、noteを中継するのが現在の正しい設計です。

この記事では、**実際に動いているアフィリエイト自動投稿システムのコードを全公開**します。

---

## このシステムでできること

- 商材カタログから時間帯に合わせて自動で商材を選択
- Claude APIが商材に合ったPRツイートを生成（#PR明記）
- 1日3回（朝・昼・夜）自動投稿
- アフィリエイトリンクはリプライに自動投稿
- 投稿済みスロットを記録して重複投稿を防止

---

## 必要なもの

| ツール | 用途 | 費用 |
|--------|------|------|
| Python 3.10以上 | スクリプト実行 | 無料 |
| X Developer Account | X API利用 | 無料 |
| Anthropic API Key | ツイート生成 | 従量課金 |
| [A8.netアカウント](https://px.a8.net/svt/ejp?a8mat=XXXXXX) | アフィリエイトASP（登録無料） | 無料 |
| [ConoHa VPS（任意）](https://px.a8.net/svt/ejp?a8mat=4B1V22+6C11GY+50+5SS2PD) | 24時間稼働 | 月660円〜 |

> ※ 上記リンクはアフィリエイトリンクです（#PR）。実際のURLはA8.netの管理画面から取得したものに差し替えてください。

---

## ステップ1：A8.netでアフィリエイトリンクを取得

1. [A8.netに登録（無料）](https://px.a8.net/svt/ejp?a8mat=XXXXXX) #PR
2. 提携したい広告主に申請
3. 承認されたら「広告リンク取得」からURLをコピー
4. **取得したURLはnote記事に貼る**（X投稿には直接貼らない）

高単価の商材カテゴリ：クレカ・証券口座・転職・光回線（1件¥3,000〜¥30,000）

---

## ここから有料コンテンツです（¥500）

---

## 【有料】商材カタログの設計

商材情報を辞書形式で管理する。Claude APIに渡す情報として重要なのは`description`と`target`：

```python
PRODUCTS = [
    {
        "id": "example_product",
        "name": "商材名",
        "category": "カテゴリ（転職・クレカ・光回線など）",
        "description": "商材の特徴・メリット（Claude APIへのインプット）",
        "target": "ターゲット読者（Claude APIへのインプット）",
        "reward": 5000,  # 成果報酬額（円）
        "affiliate_link": "https://px.a8.net/...",  # note記事内に掲載するURL
        "note_url": "https://note.com/yourname/n/xxxxx",  # XにはこのnoteのURLを貼る
        "best_time": ["morning", "noon"],  # 投稿に適した時間帯
        "tags": ["#ハッシュタグ1", "#ハッシュタグ2"],
    },
]
```

`note_url`にnote記事のURLを入れる。**XにはこのnoteのURLを投稿し、note記事の中にアフィリエイトリンクを掲載する**のが正しい構成。`best_time`で時間帯ごとに商材を使い分けられる。

---

## 【有料】Claude APIでアフィリエイトツイートを生成

ステマ規制対応のため`#PR`は必須。Claudeに明示的に指示する：

```python
import anthropic

def generate_affiliate_tweet(product: dict) -> str:
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        system="""アフィリエイト投稿を生成するAIです。

絶対ルール:
- 投稿末尾に必ず「#PR」を入れる
- 押しつけではなく「こんな人におすすめ」の紹介トーン
- 140文字以内（URLは含めない）
- ツイート本文のみ出力""",
        messages=[{
            "role": "user",
            "content": f"""以下の商材を紹介するツイートを1本生成してください。

商材名: {product['name']}
特徴: {product['description']}
ターゲット: {product['target']}
タグ: {' '.join(product['tags'])}

URLは含めないこと。#PRを末尾に必ず入れること。"""
        }]
    )
    
    tweet = message.content[0].text.strip()
    if "#PR" not in tweet:
        tweet = tweet.rstrip() + "\n\n#PR"
    return tweet
```

モデルはHaikuで十分。月1,000投稿でも数十円のコスト。

---

## 【有料】X APIで投稿とリプライを送る

**重要：アフィリエイトURLは本文にもリプライにも入れない。noteのURLを本文に入れる。**

A8.netなどのアフィリエイトURLはXにブロックされて投稿できない。代わりに、アフィリエイトリンクを埋め込んだnote記事のURLをX本文に載せる。これがXのリーチを保ちながらアフィリエイト成果を得る唯一の構成。

```python
import tweepy

def get_client():
    return tweepy.Client(
        consumer_key=os.getenv("X_API_KEY"),
        consumer_secret=os.getenv("X_API_SECRET"),
        access_token=os.getenv("X_ACCESS_TOKEN"),
        access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET")
    )

def post_tweet(text: str) -> str:
    client = get_client()
    response = client.create_tweet(text=text)
    return response.data["id"]

def post_tweet_with_note_url(text: str, note_url: str) -> str:
    client = get_client()
    # note URLはX本文に含めてOK（アフィリエイトURLではないため）
    full_text = f"{text}\n\n詳細はこちら→ {note_url}"
    response = client.create_tweet(text=full_text)
    return response.data["id"]
```

---

## 【有料】投稿済みスロット管理（重複防止）

同じ時間帯に二重投稿しないよう、投稿済みキーをJSONで管理する：

```python
import json
from datetime import datetime, date

LAST_POST_FILE = "affiliate_last_post.json"
SLOTS = {"morning": 8, "noon": 13, "evening": 20}

def load_last_post() -> dict:
    if os.path.exists(LAST_POST_FILE):
        with open(LAST_POST_FILE) as f:
            return json.load(f)
    return {}

def mark_posted(key: str):
    last = load_last_post()
    last[key] = datetime.now().isoformat()
    # 3日より古いデータを削除
    cutoff = date.today().toordinal() - 3
    last = {k: v for k, v in last.items()
            if date.fromisoformat(k[:10]).toordinal() >= cutoff}
    with open(LAST_POST_FILE, "w") as f:
        json.dump(last, f)

def get_pending_slots() -> list:
    last = load_last_post()
    today = date.today().isoformat()
    now_hour = datetime.now().hour
    pending = []
    for slot, hour in SLOTS.items():
        key = f"{today}_{slot}"
        if now_hour >= hour and key not in last:
            pending.append((key, slot))
    return pending
```

---

## 【有料】メインスクリプトを組み立てる

```python
def select_product(time_slot: str) -> dict:
    candidates = [p for p in PRODUCTS if time_slot in p["best_time"]]
    if not candidates:
        candidates = PRODUCTS
    # Claude APIで最適な商材を選択（または単純にランダム）
    import random
    return random.choice(candidates)

def main():
    pending = get_pending_slots()
    if not pending:
        print("投稿対象なし")
        return

    for key, slot in pending:
        product = select_product(slot)
        tweet = generate_affiliate_tweet(product)
        
        if "#PR" not in tweet:
            print("安全チェック失敗: スキップ")
            continue
        
        tweet_id = post_tweet_with_note_url(tweet, product["note_url"])
        mark_posted(key)
        print(f"投稿完了: {product['name']}")
        
        time.sleep(5)

if __name__ == "__main__":
    main()
```

**重要：`mark_posted`はメイン投稿の直後に呼ぶ。**リプライが失敗しても再投稿されないようにするため。

---

## 【有料】cronで自動実行

```bash
# 毎時0分に実行（内部でスロット判定）
0 * * * * cd /root/myapp && /root/myapp/venv/bin/python3 affiliate_auto.py >> /var/log/affiliate.log 2>&1
```

---

## 【有料】法的注意事項

**ステマ規制（2023年10月〜）**
アフィリエイト投稿には`#PR`または`#広告`の明記が必須。Claudeのプロンプトに強制的に入れる実装が必要。

**金融商品取引法**
クレカ・証券口座・ローン系の投稿は「〜%の利率」などの具体的な数字を使うと法規制の対象になる可能性がある。「詳しくは公式サイトで」にとどめること。

---

## まとめ

アフィリエイト自動投稿システムの核心：

1. **商材カタログ**で情報を整理
2. **Claude API**でPR明記のツイートを生成
3. **X API**で本文投稿→リプライにURL
4. **JSON管理**で重複投稿を防止
5. **VPS + cron**で24時間稼働

このシステムを動かしながら、別の仕事や開発に集中できています。

*X投稿の自動化をノーコードでやりたい方は [AxeonPost](https://axeon-project.vercel.app) へ。*

---

## この記事で紹介したリンク #PR

| サービス | 説明 | リンク |
|---|---|---|
| A8.net | 国内最大級のアフィリエイトASP。登録無料 | [登録はこちら](https://px.a8.net/svt/ejp?a8mat=XXXXXX) |
| ConoHa VPS | 月660円〜のVPS。cronで24時間稼働 | [申し込みはこちら](https://px.a8.net/svt/ejp?a8mat=4B1V22+6C11GY+50+5SS2PD) |

> ※上記リンクはアフィリエイトリンクです。リンク先で申し込みが完了すると報酬が発生します。
