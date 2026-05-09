import tweepy
import os
from dotenv import load_dotenv
# あなたのキーをここに直接入れる（テスト用）
load_dotenv()

# ファイルから値を連れてくる（コードには鍵を書かない！）
API_KEY = os.getenv("X_API_KEY")
API_SECRET = os.getenv("X_API_SECRET")
ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET")

client = tweepy.Client(
    consumer_key=API_KEY,
    consumer_secret=API_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_TOKEN_SECRET
)

try:
    print("投稿を試みています...")
    client.create_tweet(text="このアカウント、AIが自動で投稿しています。\n\nAIでXを伸ばすサービス「Axeon」の公式アカウントです。\nフォロワー0からスタートして、AIの力だけで成長できるか——全部リアルタイムで公開します。\n\nまず自分たちで証明する。それがAxeonのやり方です。")
    print("成功しました！自分のXを確認してください。")
except Exception as e:
    print(f"エラーが発生しました: {e}")
