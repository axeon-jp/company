"""
AutoPost for X — AIによるX自動投稿スクリプト
=============================================
Claude API でツイートを自動生成し、X API で投稿します。
cron に登録することで毎日指定時刻に自動実行できます。
PCがスリープ中にスキップされたスロットは、次回起動時にまとめて投稿します。

セットアップ: setup_guide.pdf を参照してください。
"""

import os
import sys
import time
import json
import argparse
import tempfile
import urllib.request
import tweepy
import anthropic
import openai
from datetime import datetime, date
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# ============================================================
# ここだけ編集すれば自分のアカウントに合わせられます
# ============================================================

ACCOUNT_THEME = "AI×副業・X自動化の実録"

ACCOUNT_PERSONA = """
【人物設定】
- 20代後半〜30代前半の会社員。副業でAI×自動化に挑戦中
- プログラミングは独学中級（Python・API連携ができる）
- 「まずやってみる」行動優先型。完璧より速度を重視
- 失敗も包み隠さず書く。成功談よりも試行錯誤の記録を大切にする
- キラキラした煽りは絶対に使わない。地に足がついた等身大の発信

【文体ルール】
- 一人称は「自分」または「私」
- 数字を具体的に出す（「少し増えた」より「+47フォロワー」）
- 改行を多用して読みやすくする
- 難しい技術用語は使ってよいが一言で補足する
- 上から目線・説教口調は禁止
- ハッシュタグは最大2つ
- 絵文字は使わない（または1個まで）
- URLは絶対に含めない
- 3〜4投稿に1回は末尾に質問を入れる
"""

# 実際の実績・数値（投稿のリアリティを出すために使う）
REAL_ACHIEVEMENTS = """
【実際にやってきたこと・数値】
- Claude API + Python + cronでX自動投稿システムを構築し、24時間稼働中（ConoHa VPS上）
- AxeonPost（AI X自動投稿SaaS）を開発・Vercelにデプロイ済み（axeon-project.vercel.app）
- note記事を3本公開：無料記事・¥1,980の技術解説・¥500のClaude API入門
- アフィリエイト自動投稿も並行稼働（転職・クレカ系の高単価商材）
- X API・Claude API・Supabase・Next.jsを組み合わせた開発経験あり
- 失敗例：最初の1ヶ月はフォロワーが全く増えなかった、Supabaseのトリガーが何度もエラーを出した
"""

# スロット名: (開始時刻, 投稿タイプ, 方向性)
TIME_SLOTS = {
    "morning": (7,  "教育系",  "AIや自動化について『知らなかった・得した』と感じるノウハウ。実際に自分が試したこと・数値を盛り込む。箇条書き推奨。"),
    "noon":    (12, "共感系",  "副業・AI活用で感じるリアルな悩みや気づき。『あるある』『自分だけじゃなかった』と思える内容。感情に寄り添う文体で。"),
    "evening": (21, "実録系",  "今日やったこと・わかったこと・失敗したこと。日記感覚で正直に。数字や具体的なエピソードを入れる。"),
}

# スレッドを投稿する曜日（0=月, 1=火, 2=水, 3=木, 4=金, 5=土, 6=日）
THREAD_DAYS = [1, 4]  # 火曜・金曜

# スレッドのトピック候補（順番に使い回す）
THREAD_TOPICS = [
    "Claude APIとPythonでX自動投稿を作った全手順",
    "会社員がAI副業を始めて最初の1ヶ月でやったこと・失敗したこと",
    "X APIを無料で使い倒す方法【Free Tierの限界と対策】",
    "VPS上でcronを動かしてPCなしで自動投稿する仕組みを解説",
    "noteで稼ぐために最初にやるべきこと【記事3本書いてわかった現実】",
    "Supabase + Next.jsでSaaSを作ってVercelにデプロイした話",
    "アフィリエイト自動投稿システムを作った話【設計から実装まで】",
    "AIで副業収益化するまでのリアルなロードマップ",
    "Xのフォロワーが増えない人がやりがちな3つの間違い",
    "毎日投稿が続かない本当の理由と、AIで解決した話",
    "Xのフォロワーをメールリストにつなぐとどうなるか【実録】",
    "「保存される投稿」と「流れる投稿」の違いを分析してみた",
]

# ============================================================
# 以下は変更不要です
# ============================================================

LAST_POST_FILE = os.path.join(os.path.dirname(__file__), "last_post.json")

def load_last_post() -> dict:
    if os.path.exists(LAST_POST_FILE):
        with open(LAST_POST_FILE) as f:
            return json.load(f)
    return {}

def save_last_post(data: dict):
    with open(LAST_POST_FILE, "w") as f:
        json.dump(data, f)

def get_missed_slots() -> list[tuple[str, str, str]]:
    """今日分で未投稿のスロットを時刻順に返す"""
    last = load_last_post()
    today = date.today().isoformat()
    now_hour = datetime.now().hour
    missed = []

    for slot, (hour, label, description) in TIME_SLOTS.items():
        key = f"{today}_{slot}"
        # 今日の予定時刻を過ぎていて、まだ投稿していない
        if now_hour >= hour and key not in last:
            missed.append((key, label, description))

    # 時刻順（morning → noon → evening）
    slot_order = list(TIME_SLOTS.keys())
    missed.sort(key=lambda x: slot_order.index(x[0].split("_")[1]))
    return missed

def mark_posted(key: str):
    last = load_last_post()
    last[key] = datetime.now().isoformat()
    # 直近3日分だけ保持
    cutoff = (date.today().toordinal() - 3)
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

def generate_tweet(content_type: str, description: str) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("[エラー] ANTHROPIC_API_KEY が設定されていません。")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    system = f"""あなたはXアカウントの投稿を生成するAIアシスタントです。
このアカウントのテーマ: {ACCOUNT_THEME}
口調・スタイル: {ACCOUNT_PERSONA}

発信者の実績・背景（これを使ってリアリティを出す）:
{REAL_ACHIEVEMENTS}

絶対ルール:
- 140文字以内で書く
- ツイート本文のみ出力する（前置き・説明・かっこは不要）
- URLやリンクは絶対に含めない
- 読んだ人が「いいね」「保存」「リプライ」したくなる内容にする
- 毎回違う角度・切り口で書く
"""
    for attempt in range(3):
        try:
            message = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=300,
                system=system,
                messages=[{"role": "user", "content": f"投稿タイプ: {content_type}\n方向性: {description}\n\nツイートを1本生成してください。"}]
            )
            return message.content[0].text.strip()
        except Exception as e:
            print(f"[リトライ {attempt+1}/3] Claude API エラー: {e}")
            if attempt < 2:
                time.sleep(10)
    print("[エラー] Claude API に3回失敗しました。")
    sys.exit(1)

def generate_thread(topic: str) -> list[str]:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=api_key)
    for attempt in range(3):
        try:
            message = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1500,
                system=f"""あなたはXのスレッド投稿を生成するAIアシスタントです。
発信者の実績・背景:
{REAL_ACHIEVEMENTS}

口調・スタイル: {ACCOUNT_PERSONA}

絶対ルール:
- 7ツイートのスレッドを作る（6〜8の範囲で内容に合わせて調整）
- 1本目（フック）: 80〜100文字。数字・意外性・問いかけで即座に興味を引く。短くシャープに
- 2〜6本目（ボディ）: 100〜140文字。1ツイート1メッセージ。具体的・実体験ベース
- 7本目（CTA）: 60〜80文字。「フォローすると続報が見れます」など簡潔な行動促進のみ
- URLは絶対に含めない
- 各ツイートを「---」だけの行で区切って出力する
- ツイート本文のみ出力（番号・説明は不要）""",
                messages=[{"role": "user", "content": f"以下のトピックでスレッドを生成してください：\n{topic}"}]
            )
            raw = message.content[0].text.strip()
            tweets = [t.strip() for t in raw.split("---") if t.strip()]
            return tweets[:8]
        except Exception as e:
            print(f"[リトライ {attempt+1}/3] スレッド生成エラー: {e}")
            if attempt < 2:
                time.sleep(10)
    print("[エラー] スレッド生成に3回失敗しました。")
    sys.exit(1)

def post_thread_tweets(tweets: list[str]):
    client = tweepy.Client(
        consumer_key=os.getenv("X_API_KEY"),
        consumer_secret=os.getenv("X_API_SECRET"),
        access_token=os.getenv("X_ACCESS_TOKEN"),
        access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET")
    )
    reply_to_id = None
    for i, text in enumerate(tweets):
        if reply_to_id:
            resp = client.create_tweet(text=text, in_reply_to_tweet_id=reply_to_id)
        else:
            resp = client.create_tweet(text=text)
        reply_to_id = resp.data["id"]
        print(f"  スレッド {i+1}/{len(tweets)} 投稿完了")
        time.sleep(3)

def get_thread_topic() -> str:
    last = load_last_post()
    used_count = sum(1 for k in last if k.endswith("_thread"))
    return THREAD_TOPICS[used_count % len(THREAD_TOPICS)]

def is_thread_day() -> bool:
    return datetime.now().weekday() in THREAD_DAYS

def generate_image(tweet: str, content_type: str) -> str:
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = f"Clean, modern social media image for Japanese X post. Theme: {ACCOUNT_THEME}. Content type: {content_type}. Style: minimal, bright, no text overlay."
    response = client.images.generate(model="dall-e-3", prompt=prompt, size="1024x1024", quality="standard", n=1)
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    urllib.request.urlretrieve(response.data[0].url, tmp.name)
    return tmp.name

def post_tweet(text: str, image_path: str = None):
    required_keys = ["X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET"]
    missing = [k for k in required_keys if not os.getenv(k)]
    if missing:
        print(f"[エラー] .env に以下のキーが設定されていません: {', '.join(missing)}")
        sys.exit(1)

    media_ids = None
    if image_path:
        api_v1 = tweepy.API(tweepy.OAuth1UserHandler(
            consumer_key=os.getenv("X_API_KEY"),
            consumer_secret=os.getenv("X_API_SECRET"),
            access_token=os.getenv("X_ACCESS_TOKEN"),
            access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET")
        ))
        media = api_v1.media_upload(filename=image_path)
        media_ids = [media.media_id]
        os.unlink(image_path)

    client = tweepy.Client(
        consumer_key=os.getenv("X_API_KEY"),
        consumer_secret=os.getenv("X_API_SECRET"),
        access_token=os.getenv("X_ACCESS_TOKEN"),
        access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET")
    )
    client.create_tweet(text=text, media_ids=media_ids)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--with-image", action="store_true", help="画像を生成して添付する")
    args = parser.parse_args()

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"[{now_str}] 起動")

    if not wait_for_network(max_wait=10):
        print("[エラー] ネットワークに繋がりませんでした。スキップします。")
        sys.exit(1)

    # スレッド投稿（火・金の朝スロット）
    thread_key = f"{date.today().isoformat()}_thread"
    last = load_last_post()
    if is_thread_day() and datetime.now().hour >= 7 and thread_key not in last:
        topic = get_thread_topic()
        print(f"\n[スレッド投稿] {topic}")
        tweets = generate_thread(topic)
        post_thread_tweets(tweets)
        mark_posted(thread_key)
        print("[スレッド] 投稿完了")
        time.sleep(5)

    missed = get_missed_slots()
    if not missed:
        print(f"[{now_str}] 投稿対象なし（すべて投稿済み）")
        return

    print(f"[{now_str}] 投稿対象: {len(missed)}件")

    for i, (key, content_type, description) in enumerate(missed):
        slot_name = key.split("_")[1]
        print(f"\n[{i+1}/{len(missed)}] {slot_name} — {content_type}")

        tweet = generate_tweet(content_type, description)
        print(f"生成: {tweet[:50]}...")

        image_path = None
        if args.with_image and slot_name == "evening":
            print("画像を生成中...")
            image_path = generate_image(tweet, content_type)

        post_tweet(tweet, image_path)
        mark_posted(key)
        print(f"[{slot_name}] 投稿完了")

        if i < len(missed) - 1:
            time.sleep(3)

    print(f"\n[{now_str}] 全投稿完了")

if __name__ == "__main__":
    main()
