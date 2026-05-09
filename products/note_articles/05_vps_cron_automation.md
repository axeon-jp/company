# VPS + cronで24時間自動化システムを作る【PCなしで動き続ける仕組み】

---

## ここから無料で読めます

「自動投稿を設定したのにPCを閉じたら止まってた」

これ、最初にWSLでcronを動かしていた時の自分です。

ローカルPCでcronを動かす限り、PCがスリープするたびに投稿がスキップされる。起動したタイミングで過去分をまとめて投稿しようにも、ネットワーク接続の問題でそれも失敗する。

VPSに移してからこの問題が完全に解決しました。

この記事では、**ConoHa VPS上でPythonスクリプトをcronで24時間動かすまでの全手順**を解説します。

---

## VPSとは何か

VPS（Virtual Private Server）は、クラウド上に自分専用のサーバーを持てるサービスです。

PCと違って：
- 24時間365日起動したまま
- ネットワークは常時接続
- スリープしない・電源が落ちない

月額数百円〜で借りられます。今回はConoHa VPSを使います。

---

## 必要なもの

- ConoHa VPSアカウント（月額660円〜）
- SSH接続できる環境（Windowsならコマンドプロンプト、MacはTerminal）
- 動かしたいPythonスクリプト（今回はX自動投稿スクリプトを例に）

---

## ここから有料コンテンツです（¥500）

---

## 【有料】VPSのセットアップ

### ConoHaでVPSを作成

1. ConoHa管理画面 → **VPS** → **追加**
2. OS：**Ubuntu 22.04**を選択
3. プラン：最安の512MBプランで十分（月660円）
4. rootパスワードを設定（必ず記録しておく）
5. セキュリティグループ：**IPv4v6-SSH**を追加

### SSH接続

```bash
ssh root@VPSのIPアドレス
```

初回接続時にフィンガープリントの確認が出たら`yes`を入力。

---

## 【有料】サーバーの初期設定

```bash
# パッケージ更新
apt update && apt install -y python3 python3-pip cron

# Python仮想環境の作成
apt install -y python3.12-venv
mkdir /root/myapp && cd /root/myapp
python3 -m venv venv
source venv/bin/activate

# 必要なライブラリをインストール
pip install tweepy anthropic python-dotenv openai
```

---

## 【有料】スクリプトをVPSに転送

ローカルPCから転送する（WSLまたはTerminalで実行）：

```bash
# ディレクトリを作成
ssh root@VPSのIP "mkdir -p /root/myapp"

# スクリプトをまとめて転送
scp -r /path/to/your/scripts/ root@VPSのIP:/root/myapp/

# .envファイルも転送（APIキーが入っている）
scp /path/to/.env root@VPSのIP:/root/myapp/
```

---

## 【有料】cronの設定

VPS上でcronを設定する：

```bash
crontab -e
```

エディタが開いたら以下を追加（nanoの場合はCtrl+Xで保存）：

```cron
# 毎時0分に実行
0 * * * * cd /root/myapp && /root/myapp/venv/bin/python3 auto_post.py >> /var/log/auto_post.log 2>&1
```

cronサービスを起動して自動起動設定：

```bash
service cron start
systemctl enable cron
```

---

## 【有料】ネットワーク確認の実装

VPSは常時ネット接続されているが、稀に一時的な接続断が起きることがある。スクリプトにネットワーク確認を入れておくと安全：

```python
import socket
import time

def wait_for_network(max_wait: int = 60) -> bool:
    for _ in range(max_wait // 5):
        try:
            socket.setdefaulttimeout(5)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("1.1.1.1", 80))
            return True
        except Exception:
            time.sleep(5)
    return False

if not wait_for_network():
    print("ネットワーク接続できませんでした")
    exit(1)
```

VPS用なのでmax_waitは10〜60秒で十分。WSLのように300秒待つ必要はない。

---

## 【有料】ログの確認方法

```bash
# リアルタイムでログを確認
tail -f /var/log/auto_post.log

# エラーだけ抽出
grep -i "エラー\|error" /var/log/auto_post.log

# 今日の投稿ログ
grep $(date +%Y-%m-%d) /var/log/auto_post.log
```

---

## 【有料】ローカルとVPSの使い分け

| 用途 | ローカル（WSL） | VPS |
|------|----------------|-----|
| 開発・テスト | ○ | △ |
| 本番の自動実行 | × | ○ |
| 費用 | 無料 | 月660円〜 |
| 24時間稼働 | × | ○ |

**開発はローカル、本番はVPS**が正解。スクリプトを修正したらscpでVPSに転送するだけ。

---

## 【有料】よくあるトラブルと解決策

**「ModuleNotFoundError」が出る**
→ 仮想環境を有効化してからpipインストール：
```bash
source /root/myapp/venv/bin/activate
pip install [モジュール名]
```

**cronが実行されない**
→ cronサービスが動いているか確認：
```bash
service cron status
```

**外部リソースエラー**
→ cronの実行環境はPATHが限られる。スクリプト内で絶対パスを使う：
```python
# NG
load_dotenv(".env")
# OK
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
```

---

## まとめ

VPS + cronで自動化システムを作ると：

> 💡 VPSは [ConoHa WING](https://px.a8.net/svt/ejp?a8mat=4B1V22+6C11GY+50+5SS2PD) を使っています。月660円〜で24時間稼働、SSH設定も簡単です。#PR

- ✅ PCの電源を切っても動き続ける
- ✅ ネットワーク断の心配がない
- ✅ 月660円でインフラが完成
- ✅ スクリプトをscpで転送するだけで更新できる

一度セットアップしてしまえば、あとは完全放置です。

*X自動投稿をコードなしで始めたい方は [AxeonPost](https://axeon-project.vercel.app) をどうぞ。VPSもcronも不要です。*
