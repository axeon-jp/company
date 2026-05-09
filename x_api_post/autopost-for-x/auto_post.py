"""
AutoPost for X — AIによるX自動投稿スクリプト
=============================================
Claude API でツイートを自動生成し、X API で投稿します。
cron に登録することで毎日指定時刻に自動実行できます。

セットアップ: setup_guide.pdf を参照してください。
"""

import os
import sys
import tweepy
import anthropic
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# ============================================================
# ここだけ編集すれば自分のアカウントに合わせられます
# ============================================================

# アカウントのテーマ・ニッチ（何の情報を発信するアカウントか）
ACCOUNT_THEME = "X運用・SNS成長・AI活用"

# アカウントの口調・キャラクター
ACCOUNT_PERSONA = """
- 親しみやすく、実用的な情報を発信する
- 難しい専門用語は使わない
- 改行を効果的に使い、読みやすくする
- ハッシュタグは最大2つまで
"""

# 時間帯ごとの投稿テーマ（cron の設定時刻に合わせて変更してください）
TIME_SLOTS = {
    "morning":  (5,  10, "教育系",  "読んで得した・知らなかったと感じるノウハウや豆知識。箇条書き推奨。"),
    "noon":     (10, 17, "共感系",  "ターゲット読者が『わかる』と感じる悩みや気づき。感情に寄り添う文体で。"),
    "evening":  (17, 24, "深掘り系", "一つのテーマを掘り下げた考察や体験談。スレッドの1本目にもなる内容。"),
}

# ============================================================
# 以下は変更不要です
# ============================================================

def get_content_type() -> tuple[str, str]:
    hour = datetime.now().hour
    for slot, (start, end, label, description) in TIME_SLOTS.items():
        if start <= hour < end:
            return label, description
    # デフォルト（深夜帯）
    return "共感系", "ターゲット読者が共感できる内容。"

def generate_tweet(content_type: str, description: str) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("[エラー] ANTHROPIC_API_KEY が .env に設定されていません。setup_guide.pdf を確認してください。")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    system = f"""あなたはXアカウントの投稿を生成するAIアシスタントです。

このアカウントのテーマ: {ACCOUNT_THEME}

口調・スタイル: {ACCOUNT_PERSONA}

ルール:
- 140文字以内で書く
- ツイート本文のみ出力する（前置き・説明・かっこは不要）
- 読んだ人が「いいね」か「保存」したくなる内容にする
"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        system=system,
        messages=[
            {
                "role": "user",
                "content": f"投稿タイプ: {content_type}\n方向性: {description}\n\nツイートを1本生成してください。"
            }
        ]
    )
    return message.content[0].text.strip()

def post_tweet(text: str):
    required_keys = ["X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET"]
    missing = [k for k in required_keys if not os.getenv(k)]
    if missing:
        print(f"[エラー] .env に以下のキーが設定されていません: {', '.join(missing)}")
        print("setup_guide.pdf の「X APIキーの設定」を確認してください。")
        sys.exit(1)

    client = tweepy.Client(
        consumer_key=os.getenv("X_API_KEY"),
        consumer_secret=os.getenv("X_API_SECRET"),
        access_token=os.getenv("X_ACCESS_TOKEN"),
        access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET")
    )
    client.create_tweet(text=text)

def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    content_type, description = get_content_type()

    print(f"[{now}] 投稿タイプ: {content_type}")

    tweet = generate_tweet(content_type, description)
    print(f"\n生成されたツイート:\n{'-'*40}\n{tweet}\n{'-'*40}\n")

    post_tweet(tweet)
    print(f"[{now}] 投稿完了")

if __name__ == "__main__":
    main()
