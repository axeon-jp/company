# PythonとClaude APIでX自動投稿システムを作る【完全ガイド】コード全公開

---

## ここから無料で読めます

「毎日Xに投稿したいけど、時間がない」

この悩みを持っている人は多いと思います。

Xは継続投稿が命です。でも毎日ネタを考えて、文章を書いて、投稿する——これを続けるのは意外とキツい。

この記事では、**PythonとClaude APIを使ってX自動投稿システムを構築する方法**を、実際に動いているコードを全公開しながら解説します。

私が実際に使っているシステムで、毎日自動で投稿しています。

---

## このシステムで何ができるか

- **毎日決まった時間に自動投稿**（cronで定期実行）
- **Claude APIがツイート文を自動生成**（毎回違う内容）
- **PCが落ちていた場合のリカバリ**（起動後に未投稿分を補完）
- **スレッド投稿にも対応**

必要なのはPythonの基礎知識だけ。プログラミング未経験の方には少し難しいですが、コピペで動かせるよう丁寧に説明します。

---

## 必要なもの

| ツール | 用途 | 費用 |
|--------|------|------|
| Python 3.10以上 | スクリプト実行環境 | 無料 |
| X Developer Account | X API利用 | 無料（申請必要） |
| Anthropic API Key | Claude APIでツイート生成 | 従量課金（月数百円〜） |
| WSL / Mac / Linux | cronでの定期実行 | 無料 |

Windowsの方はWSL（Windows Subsystem for Linux）の導入が必要です。

---

## ステップ1：X Developer Accountを取得する

まず X API の利用申請が必要です。

1. [developer.twitter.com](https://developer.twitter.com) にアクセス
2. **Sign up** → 利用目的を英語で記入（「Personal use, learning automation」など）
3. アプリを作成 → **Keys and Tokens** でAPIキーを取得

取得するキーは4つ：
- API Key
- API Secret
- Access Token
- Access Token Secret

これらを `.env` ファイルに保存します：

```
X_API_KEY=xxxxxxxxxxxx
X_API_SECRET=xxxxxxxxxxxx
X_ACCESS_TOKEN=xxxxxxxxxxxx
X_ACCESS_TOKEN_SECRET=xxxxxxxxxxxx
ANTHROPIC_API_KEY=xxxxxxxxxxxx
```

---

## ステップ2：Pythonの環境を整える

必要なライブラリをインストールします：

```bash
pip install tweepy anthropic python-dotenv
```

- **tweepy**：X API操作
- **anthropic**：Claude API操作
- **python-dotenv**：.envファイルの読み込み

---

## ステップ3：Claude APIでツイートを生成する

ここから有料コンテンツになります。

↓ 以下の内容を¥1,980で購入できます

---

## 【有料】ステップ3：Claude APIでツイートを生成する

```python
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

def generate_tweet(theme: str, persona: str) -> str:
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    prompt = f"""
あなたはXに投稿するツイートを生成するアシスタントです。

テーマ: {theme}
ペルソナ: {persona}

以下の条件でツイートを1件生成してください：
- 140文字以内
- 改行は最大2回まで
- ハッシュタグは1〜2個
- 読者が「いいね」したくなるような内容
- ツイート本文のみ出力（説明文は不要）
"""
    
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return message.content[0].text.strip()
```

Claude APIはモデルによって料金が大きく変わります。自動投稿用途なら **claude-haiku** が最もコスパが良く、月1,000投稿でも数百円程度で済みます。

---

## 【有料】ステップ4：X APIで実際に投稿する

```python
import tweepy
import os
from dotenv import load_dotenv

load_dotenv()

def post_tweet(text: str) -> str:
    client = tweepy.Client(
        consumer_key=os.getenv("X_API_KEY"),
        consumer_secret=os.getenv("X_API_SECRET"),
        access_token=os.getenv("X_ACCESS_TOKEN"),
        access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET"),
    )
    
    response = client.create_tweet(text=text)
    return response.data["id"]
```

tweepyのv4以降はTwitter API v2を使います。古い記事にある `tweepy.OAuthHandler` はv1の書き方なので注意してください。

---

## 【有料】ステップ5：メインスクリプトを組み立てる

生成と投稿を組み合わせて、実際に動くスクリプトを作ります。

```python
import json
import os
import time
import socket
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

LAST_POST_FILE = "last_post.json"
THEME = "AI・テクノロジー・副業"
PERSONA = "親しみやすく、具体的な情報を届ける"

def wait_for_network(max_wait: int = 300) -> bool:
    """ネットワーク接続を待つ（起動直後対策）"""
    start = time.time()
    while time.time() - start < max_wait:
        try:
            socket.setdefaulttimeout(3)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(
                ("8.8.8.8", 53)
            )
            return True
        except OSError:
            time.sleep(10)
    return False

def load_last_post() -> dict:
    if os.path.exists(LAST_POST_FILE):
        with open(LAST_POST_FILE) as f:
            return json.load(f)
    return {"last_post_time": None}

def save_last_post(dt: datetime):
    with open(LAST_POST_FILE, "w") as f:
        json.dump({"last_post_time": dt.isoformat()}, f)

def get_missed_slots(last_time: datetime, now: datetime, 
                     post_hours: list[int]) -> list[datetime]:
    """前回投稿から今まで、スキップされた投稿時刻を返す"""
    missed = []
    check = last_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    while check <= now:
        if check.hour in post_hours:
            missed.append(check)
        check += timedelta(hours=1)
    return missed

def main():
    if not wait_for_network():
        print("ネットワーク接続できませんでした")
        return

    POST_HOURS = [7, 12, 19, 22]  # 投稿する時間帯
    now = datetime.now()
    
    data = load_last_post()
    last_post_time = (
        datetime.fromisoformat(data["last_post_time"]) 
        if data["last_post_time"] else None
    )

    # 未投稿スロットを確認
    slots_to_post = []
    if last_post_time:
        missed = get_missed_slots(last_post_time, now, POST_HOURS)
        slots_to_post.extend(missed)
    
    # 現在時刻が投稿時間帯で、まだ投稿していない場合
    if now.hour in POST_HOURS:
        current_slot = now.replace(minute=0, second=0, microsecond=0)
        if not last_post_time or last_post_time < current_slot:
            if current_slot not in slots_to_post:
                slots_to_post.append(current_slot)

    if not slots_to_post:
        print("投稿するスロットなし")
        return

    print(f"{len(slots_to_post)}件の投稿を処理します")

    for slot in sorted(slots_to_post):
        for attempt in range(3):  # 最大3回リトライ
            try:
                tweet_text = generate_tweet(THEME, PERSONA)
                tweet_id = post_tweet(tweet_text)
                save_last_post(slot)
                print(f"投稿完了: {slot} → {tweet_id}")
                break
            except Exception as e:
                print(f"失敗 (試行{attempt+1}/3): {e}")
                if attempt < 2:
                    time.sleep(30)
        else:
            print(f"スキップ: {slot}")
        
        time.sleep(5)  # 連続投稿を避ける

if __name__ == "__main__":
    main()
```

このコードのポイントは **「missed slot recovery」** です。

PCが落ちていた時間帯の投稿時刻を計算し、起動後にまとめて投稿します。これにより、PCが再起動された直後に過去の未投稿分を補完できます。

---

## 【有料】ステップ6：cronで定期実行する

Linuxのcronを使って、毎時実行するように設定します。

```bash
crontab -e
```

以下を追加：

```
# 毎時0分に実行（内部で投稿時間帯を判定）
0 * * * * cd /path/to/your/script && /usr/bin/python3 auto_post.py >> /tmp/auto_post.log 2>&1

# 起動時にも実行（ネットワーク接続待ち込み）
@reboot sleep 300 && cd /path/to/your/script && /usr/bin/python3 auto_post.py >> /tmp/auto_post.log 2>&1
```

`@reboot` でPC起動時にも実行することで、前回の未投稿分を自動補完します。

---

## 【有料】ステップ7：Windowsで使う場合（WSL対応）

WindowsでWSLを使っている場合、デフォルトではPCを再起動するとWSLのcronが止まります。

対策として、WindowsのタスクスケジューラからWSL cronを自動起動します。

**start_wsl_cron.vbs** を作成：

```vbscript
Set objShell = CreateObject("WScript.Shell")
objShell.Run "wsl -d Ubuntu -u root service cron start", 0, False
```

タスクスケジューラ設定：
1. **タスクスケジューラ** を開く
2. **タスクの作成** → トリガー：**ログオン時**
3. 操作：**プログラムの開始** → `wscript.exe`
4. 引数：`"C:\path\to\start_wsl_cron.vbs"`

これでWindowsにログインするたびにWSLのcronが自動起動します。

---

## 【有料】スレッド投稿に対応する

単発ツイートだけでなく、スレッド投稿にも対応できます。

```python
def generate_thread(theme: str, persona: str, topic: str) -> list[str]:
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    prompt = f"""
以下のテーマでXのスレッド投稿を生成してください。

テーマ: {theme}
ペルソナ: {persona}
今回のトピック: {topic}

条件：
- 5〜7ツイートのスレッド
- 各ツイートは140文字以内
- 1ツイート目は続きを読みたくなるフック
- 最後のツイートはまとめ＋行動促進
- 各ツイートを---で区切って出力
"""
    
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )
    
    tweets = message.content[0].text.strip().split("---")
    return [t.strip() for t in tweets if t.strip()]

def post_thread(tweets: list[str]) -> list[str]:
    client = tweepy.Client(
        consumer_key=os.getenv("X_API_KEY"),
        consumer_secret=os.getenv("X_API_SECRET"),
        access_token=os.getenv("X_ACCESS_TOKEN"),
        access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET"),
    )
    
    ids = []
    for i, tweet in enumerate(tweets):
        kwargs = {"text": tweet}
        if ids:
            kwargs["in_reply_to_tweet_id"] = ids[-1]
        response = client.create_tweet(**kwargs)
        ids.append(response.data["id"])
        time.sleep(2)  # レート制限対策
    
    return ids
```

---

## 【有料】実運用でハマったポイント

**1. X APIのレート制限**

Free Tierでは月1,500ツイートまで。毎日4投稿 × 30日 = 120ツイートなので余裕があります。ただし連続投稿はスパム判定されることがあるので、投稿間隔は最低5秒空けましょう。

**2. Claude APIのタイムアウト**

稀にAPIがタイムアウトします。3回リトライする実装を入れておくことを強く推奨します（サンプルコードには組み込み済み）。

**3. ツイート内容の重複**

同じプロンプトを使い続けると似た内容のツイートが増えます。日付や曜日、ランダムなシードをプロンプトに含めると多様性が増します：

```python
from datetime import datetime
import random

day_context = datetime.now().strftime("%A, %B %d")
seed = random.choice(["実体験", "データ", "比較", "初心者向け", "上級者向け"])

prompt = f"今日は{day_context}です。{seed}の視点から..."
```

**4. `.env` ファイルのセキュリティ**

`.env` は絶対にGitにコミットしないこと。`.gitignore` に追加してください：

```
.env
last_post.json
*.log
```

---

## まとめ

このシステムを導入することで：

> 💡 なお、このシステムを24時間放置で動かすには常時稼働サーバーが必要です。[ConoHa WING](https://px.a8.net/svt/ejp?a8mat=4B1V22+6C11GY+50+5SS2PD) のVPSは月660円〜、SSHの設定も簡単でcronとの相性も抜群です。#PR

- ✅ 毎日の投稿作業がゼロになる
- ✅ 一貫したテーマで継続投稿できる
- ✅ PCが落ちていても自動リカバリ
- ✅ 月数百円のAPIコストで運用可能

最初のセットアップに2〜3時間かかりますが、一度動かしてしまえば放置でOKです。

コードはすべてコピペで動くように書きました。疑問点はコメントやXのDMで聞いてください。

---

*この記事で紹介したシステムをノーコードで使いたい方は、[AxeonPost](https://axeon-project.vercel.app) をご利用ください。X APIの申請不要で、AIが自動投稿してくれます。*
