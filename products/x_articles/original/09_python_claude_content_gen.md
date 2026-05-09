# PythonとClaude APIを使ったコンテンツ自動生成の作り方

<!-- 約1,500語 / オリジナル / 無料公開 -->

---

## 「月100本の記事を20時間で作る」の仕組みを解説する

大げさに聞こえるかもしれないが、仕組みを理解すれば現実的だとわかる。

人間が100本の記事を書くのではない。**AIが100本の初稿を生成して、人間が確認・修正する**のだ。

この記事では、PythonとClaude APIを使ったコンテンツ自動生成の実装を、動くコードと一緒に解説する。

---

## システムの構成

```
[テーマリスト / 商材カタログ]
        ↓ Pythonで読み込む
[Claude API] ← プロンプトを送る
        ↓ 生成されたテキストを受け取る
[Markdownファイル] ← 保存する
        ↓
[note / Xアーティクルに転記して公開]
```

完全自動化ではない。最後の「公開」は人間が行う。生成→確認→公開の流れだ。

---

## 環境構築

```bash
pip install anthropic python-dotenv
```

`.env`ファイルを作成：

```
ANTHROPIC_API_KEY=sk-ant-...
```

---

## 基本的な記事生成コード

```python
import anthropic
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def generate_article(theme: str, format_type: str, affiliate_url: str = "") -> str:
    """
    theme: 記事のテーマ
    format_type: "note" or "x_article"
    affiliate_url: アフィリエイトリンク（任意）
    """
    
    word_count = "1,000〜1,500字" if format_type == "x_article" else "1,500〜2,000字"
    
    affiliate_instruction = ""
    if affiliate_url:
        affiliate_instruction = f"""
- 記事末尾にアフィリエイトリンクを1つ入れる: {affiliate_url}
- リンクのラベルは「詳細・申し込みはこちら →」
- リンクの後に #PR をつける
"""
    
    prompt = f"""
以下の条件でブログ記事の初稿を作成してください。

テーマ: {theme}
文字数: {word_count}
形式: Markdown
対象読者: AI副業・自動化・副業収益化に興味がある20〜40代
トーン: 体験談・実用的・押し付けがましくない
構成:
- 書き出し: 共感を呼ぶ問題提起
- 本文: 具体的な手順・数字・比較
- まとめ: 行動を促すCTA
{affiliate_instruction}

記事本文のみ出力してください。
"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=[
            {
                "type": "text",
                "text": "あなたはAxeon（AI副業・自動化の発信アカウント）のコンテンツライターです。実体験ベースで実用的な記事を書きます。",
                "cache_control": {"type": "ephemeral"}
            }
        ],
        messages=[{"role": "user", "content": prompt}]
    )
    
    return message.content[0].text
```

---

## 複数商材を一括生成するスクリプト

```python
from products_catalog import PRODUCTS

def batch_generate_articles(format_type: str = "x_article"):
    results = []
    
    for product in PRODUCTS:
        theme = f"{product['name']}の体験談・選び方"
        article = generate_article(
            theme=theme,
            format_type=format_type,
            affiliate_url=product.get("affiliate_link", "")
        )
        
        # ファイルに保存
        filename = f"generated_{product['id']}_{format_type}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# {theme}\n\n")
            f.write(article)
        
        results.append({
            "product": product["name"],
            "file": filename,
            "status": "generated"
        })
        
        print(f"✓ {product['name']} の記事を生成しました")
    
    return results

if __name__ == "__main__":
    batch_generate_articles("x_article")
```

`products_catalog.py`に商材が7つあれば、実行すると7つの記事初稿が数分で生成される。

---

## プロンプトキャッシュで生成コストを下げる

上記のコードにはすでに`cache_control`が入っているが、その効果を確認する方法：

```python
# レスポンスからキャッシュ使用状況を確認
message = client.messages.create(...)

usage = message.usage
print(f"入力トークン: {usage.input_tokens}")
print(f"キャッシュ作成: {usage.cache_creation_input_tokens}")
print(f"キャッシュ読み出し: {usage.cache_read_input_tokens}")
```

`cache_read_input_tokens`が0より大きければキャッシュが効いている。2回目以降の実行でコストが下がる。

---

## 生成品質を上げるポイント

**1. システムプロンプトにペルソナを詳しく書く**

「あなたはコンテンツライターです」より「あなたはAxeon（AI副業・自動化の発信アカウント）のコンテンツライターで、VPS自動化・Claude API活用・アフィリエイト運用の実体験を持ちます」の方が精度が上がる。

**2. 出力形式を明示する**

「Markdownで書いて」「見出しはH2を使って」「箇条書きは3つ以内に絞って」など、フォーマットを指定すると後処理が楽になる。

**3. 生成後に必ず確認する**

事実誤認・古い情報・リンク切れが含まれることがある。公開前に必ず確認する。特にアフィリエイトリンクが正しく入っているかを確認する。

---

## 実際の生成コスト

7商材 × Xアーティクル形式（約1,500字）を一括生成した場合：

- モデル: claude-sonnet-4-6
- 入力トークン（プロンプト）: 約400トークン × 7 = 2,800
- 出力トークン（記事本文）: 約1,200トークン × 7 = 8,400
- プロンプトキャッシュ適用後の費用: 約$0.10〜$0.15

1本あたり2〜3円。これで1,500字の初稿が出来上がる。

---

## 次のステップ: 生成から公開の自動化

現状は「生成→人間が確認→手動で公開」だが、さらに自動化できる余地がある：

- note APIが使えれば下書き保存まで自動化できる
- Xアーティクルの公開は現時点では手動（APIなし）
- Slack/LINE通知で「新しい記事の初稿ができました」を知らせる

完全自動化は難しいが「確認するだけで公開できる状態を自動で作る」は実現できる。

---

## まとめ

> 💡 ちなみに生成スクリプトをcronで定期実行するには、常時稼働のVPSが必要です。[ConoHa WING](https://px.a8.net/svt/ejp?a8mat=4B1V22+6C11GY+50+5SS2PD) のVPSは月660円〜でSSH設定も簡単、Pythonスクリプトをそのままデプロイして使っています。#PR

PythonとClaude APIでコンテンツを自動生成する仕組みのポイント：

1. `cache_control`でシステムプロンプトをキャッシュしてコストを下げる
2. 商材カタログから自動的にテーマを取り出す
3. format_typeで媒体ごとの書き方を切り替える
4. 生成後は必ず人間が確認してから公開する

コードの完全版は [AxeonPost](https://axeon-project.vercel.app) で公開している。

---

*[@axeon_jp](https://x.com/axeon_jp) でAI副業・自動化の知見を発信中。*
