"""プロンプト集の告知スレッドを投稿する（1回限り使用）"""

import os
import tweepy
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

TWEETS = [
    """Axeon公式Xで毎日使っているプロンプトを、全部公開することにしました。

投稿生成・プロフィール最適化・ネタ出し・バズ分析まで50本。
AIに「なんか書いて」と頼んでも薄い内容しか出ない。プロンプトの質が全てです🧵""",

    """収録内容はこの7カテゴリ

・投稿生成（教育系/共感系/AI裏側）: 25本
・プロフィール文最適化: 5本
・リプライ・返信: 10本
・バズ分析・改善: 5本
・ネタ切れ解消: 5本

【】を自分の情報に書き換えるだけで使えます""",

    """¥1,480でnoteで販売中です。

Axeon公式Xはこのプロンプトで毎日3本投稿しています。
実際に使っているものなので、即戦力として使えます。

→ https://note.com/axeon_jp/n/n9836f0c793e5""",
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
