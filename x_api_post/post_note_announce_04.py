"""note記事「Xフォロワーを増やすための投稿戦略まとめ」の告知スレッド"""

import os
import time
import tweepy
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

NOTE_URL = "https://note.com/axeon_jp/n/n30eac3780f00"

TWEETS = [
    """毎日投稿しているのにフォロワーが増えない理由、3ヶ月かけてやっとわかった🧵

自分のデータと伸びているアカウントを見比べて気づいたことを全部書きました。""",

    """伸びない原因はシンプルだった。

・投稿が「報告」になっていた
・テーマが混在していた
・読者への問いかけがゼロ

これを直してから数字が変わった。""",

    """アルゴリズムが重視するシグナルの順位を知ってますか？

リポスト×20 > リプライ×13.5 > いいね×1

「いいねを集める投稿」より「コメントしたくなる投稿」の方が伸びる理由はここにある。""",

    f"""フックの型・投稿の型・スレッドの構成・やめたこと——全部書きました。¥500です。

👇
{NOTE_URL}""",
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
        time.sleep(3)

    print("\n告知スレッド投稿完了")


if __name__ == "__main__":
    post_thread()
