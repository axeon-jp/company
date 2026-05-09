"""note記事「会社員がAIで副業を始めて3ヶ月でできたこと」の告知スレッド"""

import os
import tweepy
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

NOTE_URL = "https://note.com/axeon_jp/n/nbc0f65d500cf"

TWEETS = [
    f"""会社員がAIで副業を始めて3ヶ月でできたこと——収益・ツール・失敗も全部公開しました🧵

プログラミング少しできる。ChatGPT使ったことある。でも「副業になるの？」と思っていた側の話です。""",

    """最初の1ヶ月は何も起きませんでした。

Claude API + X API で自動投稿の仕組みを1週間で作った。
でもフォロワーは増えない。インプレッションも伸びない。

「AIがあれば勝手に稼げる」は完全に幻想だった。""",

    """転機は「売るものを作る」に切り替えたこと。

・AIプロンプト集 → note
・自動投稿スクリプト → Gumroad
・Notionテンプレ → note

3ヶ月の実収益と、失敗した3つのことを記事に全部書きました。""",

    f"""無料で読めます（後半は有料）

3ヶ月の実収益、ツールの費用、やらなければよかったこと——
キラキラ成功談ではなく、手を動かした記録です。

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

    print("\n告知スレッド投稿完了")

if __name__ == "__main__":
    post_thread()
