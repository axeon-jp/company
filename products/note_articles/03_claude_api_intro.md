# Claude APIを今日から使う【入門ハンズオン】APIキー取得からコード実行まで

---

## ここから無料で読めます

「Claude APIって聞いたことあるけど、どこから始めればいいかわからない」

この記事はそういう人向けです。

ChatGPTは使ったことある。でもAPIを叩いたことはない——そのくらいの前提知識で読めるように書きました。

**この記事を読み終わると、PythonからClaudeに質問を送って答えを受け取るコードが動きます。**

所要時間は30分程度です。

---

## Claude APIでできること

Claude APIはAnthropicが提供するAI APIです。ChatGPTのAPI版みたいなものですが、長文処理・コード生成・日本語の精度で優れています。

できることの例：
- ツイート・ブログ記事・メールの自動生成
- 長い文章の要約
- データの分類・タグ付け
- コードのレビューや生成
- 質問応答システムの構築

---

## 必要なもの

- Python 3.10以上
- Anthropicのアカウント（無料で作れる）
- クレジットカード（APIの従量課金用）

---

## ステップ1：APIキーを取得する

1. [console.anthropic.com](https://console.anthropic.com) にアクセス
2. アカウント作成（Googleログイン可）
3. **API Keys** → **Create Key**
4. 表示されたキーをコピーして保存（一度しか表示されません）

初回は$5のクレジットが付与されます。Claude Haikuなら数万回のAPI呼び出しができる量です。

---

## ステップ2：ライブラリをインストールする

```bash
pip install anthropic python-dotenv
```

---

## ステップ3：最初のコードを動かす

ここから有料コンテンツになります。

↓ 以下の内容を¥500で購入できます

---

## 【有料】ステップ3：最初のコードを動かす

`.env` ファイルを作成：

```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxx
```

`hello_claude.py` を作成：

```python
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

message = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "こんにちは！自己紹介してください。"}
    ]
)

print(message.content[0].text)
```

実行：

```bash
python3 hello_claude.py
```

Claudeからの返答がターミナルに表示されれば成功です。

---

## 【有料】モデルの選び方

Anthropicには3種類のモデルがあります：

| モデル | 特徴 | 用途 | コスト |
|--------|------|------|--------|
| claude-opus-4-7 | 最高性能 | 複雑な分析・コード | 高め |
| claude-sonnet-4-6 | バランス型 | 汎用・ブログ生成 | 中 |
| claude-haiku-4-5-20251001 | 高速・安価 | 大量処理・自動投稿 | 安い |

**自動投稿や大量生成にはHaikuが最適です。** Sonnetの10分の1以下のコストで、品質は十分実用的です。

コスト感の目安（Haiku使用時）：
- ツイート1件生成：約0.01円
- 月1,000件生成：約10円

---

## 【有料】プロンプトの書き方

Claude APIの品質はプロンプト次第です。基本構造：

```python
message = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=500,
    messages=[
        {
            "role": "user",
            "content": """
あなたはプロのライターです。

以下の条件でブログ記事の導入文を書いてください：
- テーマ：AI副業
- 文字数：200文字程度
- 読者：副業に興味がある会社員
- トーン：親しみやすく、具体的

導入文のみ出力してください。
"""
        }
    ]
)
```

**良いプロンプトの3要素：**
1. **役割を与える**（「あなたはプロのライターです」）
2. **条件を箇条書きにする**（文字数・トーン・形式）
3. **出力形式を指定する**（「〜のみ出力」）

---

## 【有料】システムプロンプトを使う

毎回同じ前提を書くのは非効率です。`system` パラメータを使うと、会話全体に適用される指示を設定できます：

```python
message = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=500,
    system="あなたはXの自動投稿ツールです。日本語で140文字以内のツイートのみを出力します。余計な説明は不要です。",
    messages=[
        {"role": "user", "content": "AIと副業について投稿して"}
    ]
)
```

自動投稿システムでは、システムプロンプトにペルソナや制約を書いておくと安定した品質が得られます。

---

## 【有料】会話履歴を持たせる

ChatGPTのように前の発言を踏まえた返答をさせるには、`messages` リストに会話履歴を渡します：

```python
history = []

def chat(user_message: str) -> str:
    history.append({"role": "user", "content": user_message})
    
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=history
    )
    
    assistant_message = response.content[0].text
    history.append({"role": "assistant", "content": assistant_message})
    
    return assistant_message

# 使い方
print(chat("私の名前はAxeonです"))
print(chat("私の名前を覚えていますか？"))
```

注意：`history` はメモリ上にあるため、スクリプトを再起動すると消えます。永続化が必要な場合はJSONやDBに保存してください。

---

## 【有料】実用サンプル：ツイート自動生成

```python
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def generate_tweet(theme: str) -> str:
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        system="Xに投稿するツイートを生成します。140文字以内、ハッシュタグ1〜2個。ツイート本文のみ出力。",
        messages=[{"role": "user", "content": f"テーマ：{theme}"}]
    )
    return response.content[0].text.strip()

# 5件生成
themes = ["AI副業", "時間管理", "Python入門", "Claude API", "自動化の楽しさ"]
for theme in themes:
    tweet = generate_tweet(theme)
    print(f"【{theme}】\n{tweet}\n")
```

---

## 【有料】エラーハンドリングとリトライ

本番環境では必ずエラー処理を入れます：

```python
import time

def generate_with_retry(prompt: str, max_retries: int = 3) -> str:
    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text.strip()
        except anthropic.RateLimitError:
            wait = 60 * (attempt + 1)
            print(f"レート制限。{wait}秒待機...")
            time.sleep(wait)
        except anthropic.APIError as e:
            print(f"APIエラー (試行{attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(10)
    
    raise Exception("最大リトライ回数に達しました")
```

主なエラー：
- `RateLimitError`：短時間に大量リクエスト → 待機してリトライ
- `APIError`：一時的なサーバーエラー → リトライ
- `AuthenticationError`：APIキー間違い → キーを確認

---

## 【有料】コスト管理のコツ

APIの使いすぎを防ぐために：

**1. max_tokensを適切に設定する**
ツイート生成なら200、長文なら2000。不必要に大きくしない。

**2. Haikuを使い分ける**
品質よりスピード・コストが重要な処理はHaikuで。品質が求められるときだけSonnetを使う。

**3. コンソールで使用量を確認する**
[console.anthropic.com/usage](https://console.anthropic.com/usage) で日別・モデル別の使用量が確認できます。

**4. 使用量に上限を設ける**
コンソールの **Billing** → **Usage limits** で月次の上限金額を設定できます。設定しておくと安心です。

---

## まとめ

> 💡 ちなみにClaude APIを使った自動投稿スクリプトを24時間動かすには、VPSが便利です。[ConoHa WING](https://px.a8.net/svt/ejp?a8mat=4B1V22+6C11GY+50+5SS2PD) のVPSは月660円〜で常時稼働、Pythonスクリプトをそのままデプロイしてcronで定期実行できます。#PR

Claude APIの基本を押さえました：

- ✅ APIキーの取得と設定
- ✅ 基本的なメッセージ送受信
- ✅ モデルの選び方（Haiku推奨）
- ✅ 効果的なプロンプトの書き方
- ✅ 会話履歴の扱い
- ✅ エラーハンドリング
- ✅ コスト管理

ここまでできれば、あとは組み合わせるだけです。次のステップとしてX自動投稿システムの構築に挑戦してみてください。

---

*Claude APIを使ったX自動投稿をノーコードで試したい方は [AxeonPost](https://axeon-project.vercel.app) をご利用ください。*
