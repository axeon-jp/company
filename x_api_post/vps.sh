#!/bin/bash
# VPS管理スクリプト — デプロイ・ログ・cron操作をワンコマンドで実行

VPS_IP="160.251.206.26"
VPS_USER="root"
SSH_KEY="/home/y75a3/.ssh/id_ed25519"
VPS_DIR="/root/x_api_post"
LOCAL_DIR="$(cd "$(dirname "$0")" && pwd)"

SSH="ssh -i $SSH_KEY $VPS_USER@$VPS_IP"
SCP="scp -i $SSH_KEY"

case "$1" in
  deploy)
    echo "[デプロイ] affiliate_auto.py / products_catalog.py → VPS"
    $SCP "$LOCAL_DIR/affiliate_auto.py" "$VPS_USER@$VPS_IP:$VPS_DIR/"
    $SCP "$LOCAL_DIR/products_catalog.py" "$VPS_USER@$VPS_IP:$VPS_DIR/"
    echo "[完了] デプロイ成功"
    ;;

  deploy-all)
    echo "[デプロイ] 全ファイル → VPS"
    $SCP "$LOCAL_DIR/affiliate_auto.py" \
         "$LOCAL_DIR/products_catalog.py" \
         "$LOCAL_DIR/auto_post.py" \
         "$VPS_USER@$VPS_IP:$VPS_DIR/"
    echo "[完了] 全ファイルデプロイ成功"
    ;;

  log)
    echo "[ログ] affiliate.log（最新50行）"
    $SSH "tail -50 /var/log/affiliate.log"
    ;;

  log-auto)
    echo "[ログ] auto_post.log（最新50行）"
    $SSH "tail -50 /var/log/auto_post.log"
    ;;

  log-error)
    echo "[エラーログ] affiliate + auto_post"
    $SSH "grep -i 'error\|エラー\|fail\|traceback' /var/log/affiliate.log /var/log/auto_post.log | tail -30"
    ;;

  cron)
    echo "[cron確認]"
    $SSH "crontab -l"
    ;;

  cron-start)
    echo "[cron開始] affiliate_auto.py を有効化"
    $SSH "crontab -l | grep -q 'affiliate_auto' && echo '既に有効です' || (crontab -l; echo '0 * * * * cd $VPS_DIR && $VPS_DIR/venv/bin/python3 affiliate_auto.py >> /var/log/affiliate.log 2>&1') | crontab -"
    ;;

  cron-stop)
    echo "[cron停止] affiliate_auto.py を無効化"
    $SSH "crontab -l | grep -v 'affiliate_auto.py' | crontab -"
    echo "[完了] affiliate cronを停止しました"
    ;;

  dry-run)
    echo "[DRY RUN] 投稿内容を確認（実際には投稿しない）"
    $SSH "cd $VPS_DIR && source venv/bin/activate && python3 affiliate_auto.py --dry-run"
    ;;

  ssh)
    $SSH
    ;;

  *)
    echo "使い方: $0 <コマンド>"
    echo ""
    echo "  deploy       affiliate_auto.py / products_catalog.py をVPSに転送"
    echo "  deploy-all   全スクリプトをVPSに転送"
    echo "  log          アフィリエイト投稿ログを表示"
    echo "  log-auto     通常投稿ログを表示"
    echo "  log-error    エラーログを抽出"
    echo "  cron         cronジョブを確認"
    echo "  cron-start   アフィリエイトcronを有効化"
    echo "  cron-stop    アフィリエイトcronを停止"
    echo "  dry-run      投稿内容を確認（投稿なし）"
    echo "  ssh          VPSにSSH接続"
    ;;
esac
