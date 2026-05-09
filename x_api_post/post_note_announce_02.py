"""note記事「PythonとClaude APIでX自動投稿システムを作る」の告知スレッド"""

import os
import tweepy
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

NOTE_URL = "https://note.com/axeon_jp/n/ned8da3ce3256"

TWEETS = [
    """PythonとClaude APIでX自動投稿システムを作る方法——コード全公開🧵

毎日投稿したいけど時間がない。そう思って作ったシステムを、そのままの形で公開します。""",

    """このシステムでできること：

・毎日決まった時間に自動投稿
・Claude APIがツイート文を自動生成
・PCが落ちていた場合も起動後に補完
・スレッド投稿にも対応

必要なのはPythonの基礎知識だけ。""",

    """一番こだわったのは「missed slot recovery」

PCがスリープ中や電源オフの間にスキップした投稿時刻を記録しておいて、起動後にまとめて補完する仕組みです。

これがないと「昨日の夜の投稿が飛んでた」が頻発します。""",

    f"""X API申請からcron設定、WSL対応、スレッド投稿まで全部書きました。

コードはそのままコピペで動きます。¥1,980

👇
{NOTE_URL}

ノーコードで使いたい方は @axeon_post まで""",
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
        print(f"ツイート{i}/{len(TWEETS)} 投稿完了 (ID: {reply_to_id})")

    print("\n告知スレッド投稿完了")

if __name__ == "__main__":
    post_thread()
