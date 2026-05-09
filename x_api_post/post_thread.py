"""告知スレッドを1本目→2本目→3本目の順で投稿する（1回限り使用）"""

import os
import tweepy
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

TWEETS = [
    """Axeon公式Xは毎日このスクリプトで動いています。

Claude API + X API で自動生成・自動投稿。
仕組みを全部公開します🧵""",

    """使っているのはこの3つ

・Claude API（Haiku）→ ツイート生成
・X API（tweepy）→ 自動投稿
・cron → 毎日7時・12時・21時に実行

月のAPI費用：約¥15
それで毎日3本、完全自動で投稿できます。""",

    """このスクリプト、販売することにしました。

セットアップガイド・カスタマイズガイド・cron設定ガイド付き。
自分のニッチに合わせて10分で動かせます。

¥3,980 → https://axeon.gumroad.com/l/pqzgc""",
]

def post_thread():
    client = tweepy.Client(
        consumer_key=os.getenv("X_API_KEY"),
        consumer_secret=os.getenv("X_API_SECRET"),
        access_token=os.getenv("X_ACCESS_TOKEN"),
        access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET")
    )

    reply_to_id = None
    for i, text in enumerate(TWEETS, 1):
        if reply_to_id:
            response = client.create_tweet(text=text, in_reply_to_tweet_id=reply_to_id)
        else:
            response = client.create_tweet(text=text)
        reply_to_id = response.data["id"]
        print(f"ツイート{i}/3 投稿完了 (ID: {reply_to_id})")

    print("\nスレッド投稿完了")

if __name__ == "__main__":
    post_thread()
