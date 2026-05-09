# X自動投稿システムを0から作った全手順

<!-- 約1,500語 / オリジナル / 無料公開 -->

---

## なぜ自動投稿システムを作ったのか

Xを毎日手動で更新していた時期がある。

朝起きて投稿して、昼に投稿して、夜に投稿する。それだけで1日に30分以上消えていた。しかも「今日は何を投稿しようか」と毎回考えるコストが積み重なる。

副業や開発と並行してXを運用するには、手動は無理だと判断した。

結論として、**Python + Claude API + X API + VPS(cron)** の構成で完全自動化できた。今は投稿内容の方向性だけ管理すれば、毎日決まった時間に自動で投稿される。

この記事では、その仕組みを0から作った手順を全部書く。

---

## システムの全体像

```
[商材カタログ / テーマリスト]
        ↓
[Claude API] → 投稿文を生成
        ↓
[X API] → Xに投稿
        ↓
[VPS + cron] → 毎日定時に自動実行
```

コードの行数は本体200行以下。Pythonが少し読めれば理解できる構成にした。

---

## ステップ1: 必要なものを揃える

### X API（Basic以上）

X APIの無料枠（Free tier）は月500ツイートまで投稿できる。1日16〜17本の計算なので、通常の運用には十分だ。

[X Developer Portal](https://developer.twitter.com)でアプリを作成し、以下の4つのキーを取得する：
- API Key / API Secret
- Access Token / Access Token Secret

### Claude API

[Anthropic Console](https://console.anthropic.com)でAPIキーを取得する。

モデルはHaiku（claude-haiku-4-5）が最も安い。投稿文生成程度の用途なら品質も十分だ。

### VPS

月額数百円から使えるVPSであればどこでも動く。ConoHaのVPSはSSH接続の設定が簡単でおすすめだ。

Pythonが動くLinux環境であればOK。

---

## ステップ2: 投稿文生成スクリプトを作る

Claude APIに送るプロンプトの設計が、投稿品質を決める。

```python
import anthropic

client = anthropic.Anthropic(api_key="YOUR_API_KEY")

def generate_post(theme: str, tone: str = "実用的") -> str:
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[
            {
                "role": "user",
                "content": f"""
以下の条件でX（Twitter）の投稿文を1つ作成してください。

テーマ: {theme}
トーン: {tone}
文字数: 100〜140字
条件:
- 体験談・具体的な数字を含める
- ハッシュタグを2〜3個末尾につける
- 宣伝臭くしない

投稿文のみ出力してください。
"""
            }
        ]
    )
    return message.content[0].text
```

テーマに「AI副業」「通信費削減」「自動化」などを渡すと、それに応じた投稿文が生成される。

---

## ステップ3: X APIで投稿するスクリプトを作る

```python
import tweepy

def post_to_x(text: str) -> dict:
    client = tweepy.Client(
        consumer_key="API_KEY",
        consumer_secret="API_SECRET",
        access_token="ACCESS_TOKEN",
        access_token_secret="ACCESS_TOKEN_SECRET"
    )
    response = client.create_tweet(text=text)
    return response
```

generate_post()で生成したテキストをpost_to_x()に渡すだけで投稿される。

---

## ステップ4: 商材カタログと組み合わせる

複数の商材やテーマを管理するためのカタログを用意する。

```python
THEMES = [
    {"theme": "ahamo光の乗り換えメリット", "tag": "#光回線"},
    {"theme": "Claude APIを使った自動化の始め方", "tag": "#AI副業"},
    {"theme": "VPSでcron自動化する方法", "tag": "#Python"},
]
```

毎日1テーマずつローテーションすることで、同じ内容が繰り返されない仕組みにした。

---

## ステップ5: VPSにデプロイしてcronで定時実行

VPSにSSHでアクセスし、スクリプトをアップロードする。

```bash
scp auto_post.py user@YOUR_VPS_IP:~/
```

crontabを設定して毎朝8時に自動実行：

```bash
crontab -e
# 毎朝8時に実行
0 8 * * * /usr/bin/python3 /home/user/auto_post.py >> /home/user/post.log 2>&1
```

ログファイル（post.log）に実行結果が残るため、エラーが起きた時に確認できる。

---

## 実際に運用してわかったこと

**1. 生成品質は「プロンプト」で9割決まる**

モデルを高いものに変えるより、プロンプトを改善する方が品質向上の費用対効果が高い。

**2. 投稿時間の分散が重要**

毎日同じ時間に投稿するとスパム判定リスクが上がる可能性がある。cronで複数の時間帯にランダム幅を持たせた。

```bash
# 8時〜9時の間でランダムに実行（分単位でばらつき）
30 8 * * * sleep $((RANDOM % 60))m && python3 auto_post.py
```

**3. コストはほぼゼロに近い**

1投稿あたりのClaude API費用はHaikuで約0.01〜0.03円。月30本投稿しても1円以下だ。

X APIは月500投稿まで無料枠があるため、通常運用なら追加費用はかからない。

---

## システムを作って変わったこと

手動で毎日投稿していた頃と比べて、**Xに使う時間がゼロになった。**

その分の時間をコンテンツの質の改善やシステムの拡張に使えるようになった。

「毎日継続するのが大変」というXの課題は、仕組みで解決できる。

---

## まとめ

構成をまとめると：

| コンポーネント | 役割 | コスト目安 |
|-------------|------|-----------|
| Claude API（Haiku） | 投稿文生成 | 月1円以下 |
| X API（Free） | 投稿実行 | 無料 |
| VPS（ConoHa等） | 定時自動実行 | 月数百円〜 |

Pythonの基礎が理解できれば2〜3時間で動くものができる。

自動化の詳細な実装と商材カタログ運用の仕組みは [AxeonPost](https://axeon-project.vercel.app) で公開している。

> 💡 VPSは [ConoHa WING](https://px.a8.net/svt/ejp?a8mat=4B1V22+6C11GY+50+5SS2PD) を使っています。月660円〜で24時間稼働、SSH設定も簡単です。#PR

---

*[@axeon_jp](https://x.com/axeon_jp) でAI副業・自動化の知見を発信中。*
