# VPS+cronで「完全放置」の自動投稿を作るまで

<!-- 約1,400語 / オリジナル / 無料公開 -->

---

## 「自動投稿」と「完全放置」は別物

Pythonで投稿スクリプトを作って動かすのは難しくない。

問題はその「動かし続ける」部分だ。

ローカルのPCでスクリプトを実行する場合、PCがオフになれば止まる。スリープしても止まる。インターネットが切れても止まる。

**完全放置で動き続ける自動投稿には、常時稼働するサーバーが必要だ。** それがVPSだ。

この記事では、VPSを借りてcronで定時実行するまでの手順を、実際の経験をもとに書く。

---

## VPSとは何か

VPS（Virtual Private Server）は、クラウド上に借りる仮想のLinuxサーバーだ。

月数百円から借りられ、24時間365日動き続ける。自分のPCとは独立して動くため、PCを閉じていても投稿が続く。

自動投稿システムの「心臓部」として使う。

---

## VPSのセットアップ手順

### ステップ1: VPSを契約する

ConoHa VPSはGMOが運営しており、設定画面が日本語で管理しやすい。月額は最小プランで880円〜。

> 💡 VPSは [ConoHa WING](https://px.a8.net/svt/ejp?a8mat=4B1V22+6C11GY+50+5SS2PD) を使っています。月660円〜で24時間稼働、SSH設定も簡単です。#PR

申し込み時に：
- OSは「Ubuntu 22.04」を選ぶ
- rootパスワードを設定する
- SSHキーを登録する（セキュリティのため推奨）

### ステップ2: SSHで接続する

```bash
ssh root@YOUR_VPS_IP
```

初回接続時にfingerprintの確認が出るのでyesと入力する。

### ステップ3: Pythonと必要ライブラリを入れる

```bash
apt update && apt upgrade -y
apt install python3 python3-pip -y
pip3 install anthropic tweepy
```

### ステップ4: スクリプトをVPSにアップロードする

ローカルPCからVPSへファイルを転送する：

```bash
scp auto_post.py root@YOUR_VPS_IP:/root/
scp products_catalog.py root@YOUR_VPS_IP:/root/
```

または git clone でリポジトリごと持ってくる方がバージョン管理しやすい：

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
```

---

## cronの設定

cronはLinuxの定時実行スケジューラーだ。「毎日この時間にこのコマンドを実行する」を登録しておける。

### 基本の書き方

```
分 時 日 月 曜日 コマンド
```

例：毎朝8時30分に実行

```bash
30 8 * * * /usr/bin/python3 /root/auto_post.py
```

### crontabを編集する

```bash
crontab -e
```

初回は編集エディタを選ぶ画面が出る。nanoが扱いやすい（番号を入力して選択）。

### 実際に設定した内容

```bash
# 朝の投稿（8:30）
30 8 * * * /usr/bin/python3 /root/auto_post.py morning >> /root/post.log 2>&1

# 昼の投稿（12:15）
15 12 * * * /usr/bin/python3 /root/auto_post.py noon >> /root/post.log 2>&1

# 夜の投稿（21:00）
0 21 * * * /usr/bin/python3 /root/auto_post.py evening >> /root/post.log 2>&1
```

`>> /root/post.log 2>&1` の部分でログを記録している。実行結果とエラーが全部このファイルに残る。

---

## ログ管理の重要性

VPSで動かすと「なぜ投稿されなかったのか」を調査するのが難しくなる。ログが命綱だ。

### ログの確認方法

```bash
# 最新50行を確認
tail -50 /root/post.log

# エラーだけ抽出
grep "ERROR" /root/post.log

# 今日の分だけ確認
grep "$(date +%Y-%m-%d)" /root/post.log
```

### ログが肥大化しないようにする

放置するとログファイルが数GBになることがある。logrotateで自動的にローテーションする：

```bash
# /etc/logrotate.d/autopost に作成
/root/post.log {
    daily
    rotate 7
    compress
    missingok
}
```

7日分のログを保持して古いものは自動削除される。

---

## セキュリティの最低限の設定

VPSをそのまま放置すると攻撃対象になる。最低限やること：

### ルートログインを禁止する

```bash
# /etc/ssh/sshd_config を編集
PermitRootLogin no
```

別のユーザーを作ってそのユーザーでSSH接続する。

### UFW（ファイアウォール）を設定する

```bash
ufw allow 22    # SSH
ufw enable
```

不要なポートを閉じておくだけでほとんどの攻撃は防げる。

### APIキーは.envファイルで管理する

スクリプトにAPIキーを直接書かない：

```python
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("CLAUDE_API_KEY")
```

`.env`ファイルをgitの管理対象から外す（`.gitignore`に追加）。

---

## 運用中に起きたトラブルと対処法

**トラブル1: X APIの認証エラー**

Access TokenとAccess Token Secretの期限が切れていた。X Developer Portalで再生成して`.env`を更新した。

**トラブル2: Python環境のパスが違う**

cronはパスの設定がシェルと異なる。`which python3`で実際のパスを確認してcrontabに絶対パスで書く。

```bash
which python3
# /usr/bin/python3
```

**トラブル3: 連続して同じ内容が投稿される**

テーマのローテーションロジックにバグがあった。曜日や日付ベースでテーマを切り替える処理に変更した。

---

## 完全放置になるまでの実際の時間

- VPS契約〜SSH接続: 30分
- スクリプトのデプロイ〜動作確認: 1〜2時間
- ログ設定・セキュリティ設定: 1時間
- 最初の1週間で出たエラーの修正: 2〜3時間

合計で1日もあれば「完全放置で動き続けるシステム」ができる。

---

## まとめ

VPS + cronの構成でやることは：

1. VPSを借りてSSH接続できるようにする
2. Pythonとライブラリをインストールする
3. スクリプトをアップロードする
4. crontabに実行スケジュールを登録する
5. ログが残るようにする

これだけで、毎朝起きたら自動で投稿が済んでいる状態になる。

実装の詳細と設定ファイルのサンプルは [AxeonPost](https://axeon-project.vercel.app) で公開している。

---

*[@axeon_jp](https://x.com/axeon_jp) でAI副業・自動化の知見を発信中。*
