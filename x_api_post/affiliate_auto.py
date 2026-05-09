"""
affiliate_auto.py — 商材を自動選択してアフィリエイト投稿するスクリプト
====================================================================
Claude が商材カタログから最適な商材を選び、投稿文を生成・投稿します。
全投稿に #PR を自動付与します（ステマ規制対応）。
PCがスリープ中にスキップされたスロットは、次回起動時にまとめて投稿します。

使い方:
  python affiliate_auto.py              # 通常投稿
  python affiliate_auto.py --dry-run   # 投稿せず内容だけ確認
"""

import os
import sys
import time
import json
import argparse
import tempfile
import urllib.request
import anthropic
import tweepy
import openai
from datetime import datetime, date
from dotenv import load_dotenv

sys.path.append(os.path.dirname(__file__))
from products_catalog import PRODUCTS

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

ACCOUNT_THEME = "X運用・SNS成長・AI活用・副業"
ACCOUNT_PERSONA = "親しみやすく実用的。難しい言葉は使わない。改行を効果的に使う。"

# スロット名: 予定時刻
AFFILIATE_SLOTS = {
    "morning": 8,
    "noon":    13,
    "evening": 20,
}

LAST_POST_FILE = os.path.join(os.path.dirname(__file__), "affiliate_last_post.json")

def load_last_post() -> dict:
    if os.path.exists(LAST_POST_FILE):
        with open(LAST_POST_FILE) as f:
            return json.load(f)
    return {}

def save_last_post(data: dict):
    with open(LAST_POST_FILE, "w") as f:
        json.dump(data, f)

def get_missed_slots() -> list[tuple[str, str]]:
    """今日分で未投稿のスロットを時刻順に返す"""
    last = load_last_post()
    today = date.today().isoformat()
    now_hour = datetime.now().hour
    missed = []

    for slot, hour in AFFILIATE_SLOTS.items():
        key = f"{today}_{slot}"
        if now_hour >= hour and key not in last:
            missed.append((key, slot))

    missed.sort(key=lambda x: list(AFFILIATE_SLOTS.keys()).index(x[1]))
    return missed

def mark_posted(key: str):
    last = load_last_post()
    last[key] = datetime.now().isoformat()
    cutoff = date.today().toordinal() - 3
    last = {k: v for k, v in last.items()
            if date.fromisoformat(k[:10]).toordinal() >= cutoff}
    save_last_post(last)

def wait_for_network(max_wait: int = 300) -> bool:
    import socket
    for i in range(max_wait // 5):
        try:
            socket.setdefaulttimeout(5)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("1.1.1.1", 80))
            return True
        except Exception:
            if i == 0:
                print(f"[ネットワーク待機中] 最大{max_wait}秒リトライします...")
            time.sleep(5)
    return False

def select_product(time_slot: str) -> dict:
    # note_urlが設定済みの商材を優先、なければaffiliate_link持ちにフォールバック
    with_note = [p for p in PRODUCTS if p.get("note_url") and time_slot in p["best_time"]]
    available = with_note or [p for p in PRODUCTS if p.get("note_url")]
    if not available:
        available = [p for p in PRODUCTS if p["affiliate_link"] and time_slot in p["best_time"]]
    if not available:
        available = [p for p in PRODUCTS if p["affiliate_link"]]
    if not available:
        print("[エラー] 投稿可能な商材がありません。")
        sys.exit(1)

    log_path = os.path.join(os.path.dirname(__file__), "affiliate_log.json")
    recent_ids = []
    if os.path.exists(log_path):
        with open(log_path) as f:
            logs = json.load(f)
            recent_ids = [l["product_id"] for l in logs[-5:]]

    fresh = [p for p in available if p["id"] not in recent_ids]
    candidates = fresh if fresh else available
    candidates.sort(key=lambda x: x["reward"], reverse=True)

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    catalog_text = "\n".join([
        f"- {p['id']}: {p['name']}（{p['category']}）ターゲット: {p['target']}"
        for p in candidates
    ])

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=50,
        messages=[{
            "role": "user",
            "content": f"""アカウントテーマ「{ACCOUNT_THEME}」のフォロワーに今最も刺さる商材を1つ選んでください。
時間帯: {time_slot}（morning=朝/noon=昼/evening=夜）

候補:
{catalog_text}

商材IDのみを1行で回答してください。"""
        }]
    )

    selected_id = message.content[0].text.strip()
    return next((p for p in candidates if p["id"] == selected_id), candidates[0])

def shorten_url(url: str) -> str:
    api = "https://tinyurl.com/api-create.php?url=" + urllib.parse.quote(url)
    try:
        with urllib.request.urlopen(api, timeout=10) as r:
            return r.read().decode().strip()
    except Exception:
        return url

def generate_affiliate_tweet(product: dict) -> str:
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        system=f"""あなたはXアカウントのアフィリエイト投稿を生成するAIです。
アカウントテーマ: {ACCOUNT_THEME}
口調: {ACCOUNT_PERSONA}

絶対ルール:
- 投稿末尾に必ず「#PR」を入れる
- 押しつけではなく「こんな人におすすめ」の紹介トーン
- 140文字以内（リンクは23文字換算）
- ツイート本文のみ出力（前置き不要）
- 「A8.net」は絶対に書かない（XがURLと誤検知してブロックされる）""",
        messages=[{
            "role": "user",
            "content": f"""以下の商材を自然に紹介するツイートを1本生成してください。

商材名: {product['name']}
特徴: {product['description']}
ターゲット: {product['target']}
推奨タグ: {' '.join(product['tags'])}

URLは含めないこと。#PRを末尾に必ず入れること。"""
        }]
    )
    tweet = message.content[0].text.strip()
    if "#PR" not in tweet and "#pr" not in tweet.lower():
        tweet = tweet.rstrip() + "\n\n#PR"
    return tweet

def save_log(product: dict, tweet: str):
    log_path = os.path.join(os.path.dirname(__file__), "affiliate_log.json")
    logs = []
    if os.path.exists(log_path):
        with open(log_path) as f:
            logs = json.load(f)
    logs.append({
        "timestamp": datetime.now().isoformat(),
        "product_id": product["id"],
        "product_name": product["name"],
        "tweet": tweet,
    })
    with open(log_path, "w") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

def generate_image(product: dict, tweet: str) -> str:
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = f"""Clean, eye-catching social media image for Japanese X (Twitter) post.
Product: {product['name']} ({product['category']})
Style: Bright, modern, minimal. No text overlay. Photorealistic or flat illustration.
Theme: {product['description']}"""
    response = client.images.generate(model="dall-e-3", prompt=prompt, size="1024x1024", quality="standard", n=1)
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    urllib.request.urlretrieve(response.data[0].url, tmp.name)
    return tmp.name

def post_tweet(text: str, image_path: str = None):
    api_v1 = tweepy.API(tweepy.OAuth1UserHandler(
        consumer_key=os.getenv("X_API_KEY"),
        consumer_secret=os.getenv("X_API_SECRET"),
        access_token=os.getenv("X_ACCESS_TOKEN"),
        access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET")
    ))
    client = tweepy.Client(
        consumer_key=os.getenv("X_API_KEY"),
        consumer_secret=os.getenv("X_API_SECRET"),
        access_token=os.getenv("X_ACCESS_TOKEN"),
        access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET")
    )
    media_ids = None
    if image_path:
        media = api_v1.media_upload(filename=image_path)
        media_ids = [media.media_id]
        os.unlink(image_path)
    response = client.create_tweet(text=text, media_ids=media_ids)
    return response.data["id"]

def post_reply(tweet_id: str, url: str):
    import urllib.parse
    encoded_url = url.replace("+", "%2B")
    client = tweepy.Client(
        consumer_key=os.getenv("X_API_KEY"),
        consumer_secret=os.getenv("X_API_SECRET"),
        access_token=os.getenv("X_ACCESS_TOKEN"),
        access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET")
    )
    try:
        client.create_tweet(text=encoded_url, in_reply_to_tweet_id=tweet_id)
    except Exception as e:
        print(f"  [警告] リプライ投稿失敗: {e}")

def run_post(time_slot: str, dry_run: bool):
    print(f"  商材を選択中... ({time_slot})")
    product = select_product(time_slot)
    print(f"  選択: {product['name']}（{product['category']}）")

    tweet = generate_affiliate_tweet(product)
    print(f"  生成: {tweet[:50]}...")

    if "#PR" not in tweet:
        print("  [中止] #PRが含まれていません。スキップします。")
        return False

    # note_urlがあればツイート本文に含める（XはA8.net URLを直接ブロックするため）
    note_url = product.get("note_url", "")
    if note_url:
        tweet = f"{tweet}\n\n詳細はこちら→ {note_url}"

    if dry_run:
        print(f"  [DRY RUN]\n{tweet}")
        return True

    tweet_id = post_tweet(tweet, None)
    save_log(product, tweet)
    print(f"  投稿完了（ID: {tweet_id}）")
    if note_url:
        print(f"  note URL: {note_url}")
    return True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="投稿せずに内容だけ確認")
    args = parser.parse_args()

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"[{now_str}] 起動")

    if not wait_for_network(max_wait=10):
        print("[エラー] ネットワークに繋がりませんでした。スキップします。")
        sys.exit(1)

    missed = get_missed_slots()
    if not missed:
        print(f"[{now_str}] 投稿対象なし（すべて投稿済み）")
        return

    print(f"[{now_str}] 投稿対象: {len(missed)}件")

    for i, (key, slot) in enumerate(missed):
        print(f"\n[{i+1}/{len(missed)}] {slot}")
        success = run_post(slot, args.dry_run)
        if success and not args.dry_run:
            mark_posted(key)
        if i < len(missed) - 1:
            time.sleep(3)

    print(f"\n[{now_str}] 全投稿完了")

if __name__ == "__main__":
    main()
