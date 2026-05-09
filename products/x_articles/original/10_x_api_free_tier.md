# X API無料枠の制限内で自動投稿を続ける方法

<!-- 約1,200語 / オリジナル / 無料公開 -->

---

## 2026年のX API、料金と制限の現状

X APIは2024〜2025年にかけて何度か料金体系が変わった。

現時点（2026年）の無料枠（Free tier）で自動投稿に関係する制限：

| 制限 | Free tier |
|-----|-----------|
| 月間投稿数 | 500ツイート |
| 読み取り | 制限あり（月1,500件） |
| アプリ数 | 1アプリ |

月500ツイートは1日あたり約16本の計算だ。1日3本投稿する運用なら月90本。無料枠で十分に足りる。

---

## 「制限に引っかかった」が起きるパターン

無料枠で自動投稿していて実際に問題になったケース：

**ケース1: バグで大量投稿**

ループのバグで同じ投稿が短時間に連続して送信された。レート制限（短時間での大量リクエスト）でアカウントが一時的に制限された。

**ケース2: テスト投稿のし過ぎ**

開発中にテストを繰り返して月の投稿数を消費した。本番運用に入る前に枠を使い切ってしまった。

**ケース3: 複数アカウントに同じアプリを使おうとした**

Free tierは1アプリにつき1アカウント。複数アカウントに使いたい場合はBasic以上が必要。

---

## 無料枠で安定運用するための設計

### ルール1: 1日の投稿数の上限をコードに組み込む

```python
import json
from datetime import date

DAILY_LIMIT = 5  # 1日の最大投稿数

def get_today_count() -> int:
    """今日の投稿数をログファイルから取得"""
    today = str(date.today())
    try:
        with open("post_count.json", "r") as f:
            data = json.load(f)
            return data.get(today, 0)
    except FileNotFoundError:
        return 0

def increment_count():
    today = str(date.today())
    try:
        with open("post_count.json", "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    
    data[today] = data.get(today, 0) + 1
    with open("post_count.json", "w") as f:
        json.dump(data, f)

def safe_post(text: str) -> bool:
    if get_today_count() >= DAILY_LIMIT:
        print(f"本日の投稿上限({DAILY_LIMIT}件)に達しました")
        return False
    
    # 実際の投稿処理
    post_to_x(text)
    increment_count()
    return True
```

上限に達したら投稿しない設計にしておくことで、バグや意図しない大量送信を防ぐ。

### ルール2: テスト環境と本番環境を分ける

```python
import os

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

def post_to_x(text: str):
    if ENVIRONMENT == "development":
        # テスト環境では実際には投稿しない
        print(f"[テスト] 投稿: {text[:50]}...")
        return
    
    # 本番環境のみ実際に投稿
    client = tweepy.Client(...)
    client.create_tweet(text=text)
```

`.env`で`ENVIRONMENT=production`と設定した場合のみ実際に投稿する。開発中のテストで枠を消費しなくなる。

### ルール3: 重複投稿を防ぐ

同じ内容を複数回投稿するとスパム判定リスクが上がる。

```python
import hashlib

def is_duplicate(text: str) -> bool:
    """過去7日間の投稿と重複チェック"""
    content_hash = hashlib.md5(text.encode()).hexdigest()
    
    try:
        with open("post_history.json", "r") as f:
            history = json.load(f)
        return content_hash in history.values()
    except FileNotFoundError:
        return False
```

---

## 月500件の枠を最大限に活かすスケジューリング

```
月曜: 通信費削減系（ahamo光・auひかり）
火曜: AI副業・自動化系
水曜: 副業マインド・気づき系
木曜: Python・技術系
金曜: アフィリエイト・収益化系
土曜: 週まとめ・振り返り
日曜: 告知・AxeonPost紹介
```

テーマを曜日でローテーションすることで：
- 投稿内容のバリエーションが生まれる
- 各テーマの読者に週1回必ず届く
- 何を投稿するか迷う時間がなくなる

1日3本 × 7日 = 21本/週 × 4週 = 84本/月。余裕で無料枠内に収まる。

---

## Basic以上にアップグレードすべきタイミング

無料枠で始めて、以下の状況になったらBasic（月$100）を検討する：

- 複数アカウントを運用したい
- 1日5本以上の投稿が必要になった
- APIの読み取り回数が制限に引っかかる

ただし副業初期段階で月$100のコストをかける必要はない。無料枠で収益化の仕組みが動いてから考えるので十分だ。

---

## レート制限エラーの対処法

X APIのレート制限エラーが出た時の対処：

```python
import time
import tweepy

def post_with_retry(text: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            client.create_tweet(text=text)
            return True
        except tweepy.TooManyRequests:
            wait_time = 60 * (attempt + 1)  # 1分, 2分, 3分と待機
            print(f"レート制限。{wait_time}秒待機します...")
            time.sleep(wait_time)
    
    print("投稿失敗: リトライ上限に達しました")
    return False
```

エラーが出たら一定時間待ってからリトライする。無限ループを防ぐためにリトライ上限を設ける。

---

## まとめ

> 💡 なお、X API自動投稿を完全放置で動かすには常時稼働サーバーが必要です。[ConoHa WING](https://px.a8.net/svt/ejp?a8mat=4B1V22+6C11GY+50+5SS2PD) のVPSは月660円〜でSSH設定も簡単、cronとセットで使うと無料枠の管理も楽になります。#PR

X API無料枠で自動投稿を安定して続けるポイント：

1. **1日の上限をコードに組み込む** — バグによる大量送信を防ぐ
2. **テスト環境と本番環境を分ける** — テストで枠を消費しない
3. **テーマのローテーションで重複を防ぐ** — 月84本でも内容のバリエーションを保つ
4. **レート制限エラーを正しく処理する** — エラーで止まらないシステムにする

これらを最初から設計に組み込んでおくと、後からトラブルで止まる回数が大幅に減る。

実装の詳細は [AxeonPost](https://axeon-project.vercel.app) で公開している。

---

*[@axeon_jp](https://x.com/axeon_jp) でAI副業・自動化の知見を発信中。*
