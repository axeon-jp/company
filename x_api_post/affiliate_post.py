"""
affiliate_post.py — クライアント向けアフィリエイト投稿スクリプト
=============================================================
クライアントのXアカウントに、アフィリエイト投稿を自動生成・投稿します。
全投稿に #PR を自動付与します（ステマ規制対応）。

使い方:
  python affiliate_post.py --client client_a

設定ファイル: clients/[client_id]/config.py を作成してください。
"""

import os
import sys
import argparse
import anthropic
import tweepy
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# ============================================================
# クライアント設定（clients/[client_id]/config.py に記述）
# ============================================================

def load_client_config(client_id: str) -> dict:
    config_path = os.path.join(os.path.dirname(__file__), "clients", client_id, "config.py")
    if not os.path.exists(config_path):
        print(f"[エラー] クライアント設定が見つかりません: {config_path}")
        print("clients/[client_id]/config.py を作成してください。")
        sys.exit(1)

    config = {}
    with open(config_path) as f:
        exec(f.read(), config)
    return config

# ============================================================
# アフィリエイト投稿生成（#PR 必須）
# ============================================================

def generate_affiliate_tweet(config: dict) -> str:
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    product = config["AFFILIATE_PRODUCT"]
    account_theme = config["ACCOUNT_THEME"]
    account_persona = config["ACCOUNT_PERSONA"]
    affiliate_link = config["AFFILIATE_LINK"]

    system = f"""あなたはXアカウントのアフィリエイト投稿を生成するAIです。

アカウントのテーマ: {account_theme}
口調・スタイル: {account_persona}

ルール（必ず守ること）:
- 投稿の末尾に必ず「#PR」を付ける（ステマ規制対応・省略不可）
- アフィリエイトリンクを自然に組み込む
- 商品を「押しつける」のではなく「紹介する」トーンで書く
- 140文字以内（リンクは23文字換算）
- ツイート本文のみ出力する（前置き不要）
"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        system=system,
        messages=[
            {
                "role": "user",
                "content": f"""以下の商品を紹介するツイートを1本生成してください。

商品名: {product['name']}
特徴: {product['description']}
ターゲット: {product['target']}
アフィリエイトリンク: {affiliate_link}

#PRを末尾に必ず入れること。"""
            }
        ]
    )

    tweet = message.content[0].text.strip()

    # #PR が含まれていない場合は強制付与
    if "#PR" not in tweet and "#pr" not in tweet.lower():
        tweet = tweet.rstrip() + "\n\n#PR"

    return tweet

# ============================================================
# X への投稿
# ============================================================

def post_tweet(config: dict, text: str):
    client = tweepy.Client(
        consumer_key=config["X_API_KEY"],
        consumer_secret=config["X_API_SECRET"],
        access_token=config["X_ACCESS_TOKEN"],
        access_token_secret=config["X_ACCESS_TOKEN_SECRET"]
    )
    client.create_tweet(text=text)

# ============================================================
# メイン
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="クライアント向けアフィリエイト投稿")
    parser.add_argument("--client", required=True, help="クライアントID（例: client_a）")
    parser.add_argument("--dry-run", action="store_true", help="投稿せずにツイート内容だけ表示する")
    args = parser.parse_args()

    config = load_client_config(args.client)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    print(f"[{now}] クライアント: {args.client}")
    print(f"商材: {config['AFFILIATE_PRODUCT']['name']}")

    tweet = generate_affiliate_tweet(config)
    print(f"\n生成されたツイート:\n{'-'*40}\n{tweet}\n{'-'*40}\n")

    if "#PR" not in tweet:
        print("[警告] #PRが含まれていません。投稿を中止します。")
        sys.exit(1)

    if args.dry_run:
        print("[DRY RUN] 投稿はしません。")
        return

    post_tweet(config, tweet)
    print(f"[{now}] 投稿完了")

if __name__ == "__main__":
    main()
