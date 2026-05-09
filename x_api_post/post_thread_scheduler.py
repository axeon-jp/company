"""X投稿スケジューラの告知スレッドを投稿する（1回限り使用）"""

import os
import tweepy
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

TWEETS = [
    """Xの投稿、毎日続けられていますか？

「ネタが尽きる」「時間がない」「続かない」——
それ全部、AIに任せられます。

X投稿スケジューラをGumroadで販売開始しました🧵""",

    """このスクリプトでできること

・Claude AIがあなたのニッチに合わせてツイートを自動生成
・毎日7時・12時・21時に自動投稿
・時間帯ごとに教育系/共感系/深掘り系を自動で切り替え
・月のAPI費用は約¥15

設定10分。あとは完全放置。""",

    """Axeon公式X（このアカウント）も
このスクリプトで毎日動いています。

実際に使っているものをそのまま販売しています。
セットアップガイド・カスタマイズガイド付き。

¥3,980 → https://axeon.gumroad.com/l/X-post-scheduler""",
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
