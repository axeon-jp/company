"""note記事「Claude APIを今日から使う【入門ハンズオン】」+ 全記事まとめの告知"""

import os
import time
import tweepy
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

NOTE_URL_03 = "https://note.com/axeon_jp/n/n341e056e88e6"
NOTE_URL_02 = "https://note.com/axeon_jp/n/ned8da3ce3256"
NOTE_URL_01 = "https://note.com/axeon_jp/n/nbc0f65d500cf"

TWEETS_03 = [
    """Claude APIを今日から使う入門ハンズオンを書きました🧵

「APIって聞いたことあるけど何から始めればいい？」という人向けです。30分で動くコードが書けます。""",

    """この記事でわかること：

・APIキーの取得と設定
・最初のコードを動かす
・モデルの選び方（Haiku推奨）
・プロンプトの書き方
・エラーハンドリング
・コスト管理のコツ

コピペで動くサンプルコード付き。""",

    f"""¥500です。コーヒー1杯分でClaudeと話せるようになります。

👇
{NOTE_URL_03}""",
]

TWEET_ALL_ARTICLES = f"""Axeonのnote記事まとめ📚

①【無料】会社員がAIで副業を始めて3ヶ月でできたこと
{NOTE_URL_01}

②【¥1,980】PythonとClaude APIでX自動投稿システムを作る
{NOTE_URL_02}

③【¥500】Claude APIを今日から使う入門ハンズオン
{NOTE_URL_03}"""


def post_thread(tweets: list[str]):
    client = tweepy.Client(
        consumer_key=os.getenv("X_API_KEY"),
        consumer_secret=os.getenv("X_API_SECRET"),
        access_token=os.getenv("X_ACCESS_TOKEN"),
        access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET")
    )

    reply_to_id = None
    for i, text in enumerate(tweets, 1):
        if reply_to_id:
            response = client.create_tweet(text=text, in_reply_to_tweet_id=reply_to_id)
        else:
            response = client.create_tweet(text=text)
        reply_to_id = response.data["id"]
        print(f"ツイート{i}/{len(tweets)} 投稿完了 (ID: {reply_to_id})")
        time.sleep(3)


if __name__ == "__main__":
    print("=== 記事03 告知スレッド ===")
    post_thread(TWEETS_03)

    print("\n5秒待機...")
    time.sleep(5)

    print("=== 全記事まとめポスト ===")
    client = tweepy.Client(
        consumer_key=os.getenv("X_API_KEY"),
        consumer_secret=os.getenv("X_API_SECRET"),
        access_token=os.getenv("X_ACCESS_TOKEN"),
        access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET")
    )
    response = client.create_tweet(text=TWEET_ALL_ARTICLES)
    print(f"投稿完了 (ID: {response.data['id']})")

    print("\n全投稿完了")
