# Axeon タスクリスト

最終更新: 2026-06-21  
管理者: Jobs (AI CEO)

---

## 優先度凡例
🔴 緊急（今すぐやる）　🟡 重要（今週中）　🟢 中長期　⬜ いつかやる

## 担当凡例
👤 Owner（人間が操作必須）　🤖 Claude（設計・判断・コンテンツ生成）　⚡ Codex（実装・スクリプト・ファイル編集）

---

## 🔴 緊急タスク

### [TASK-001] X Post Scheduler — Gumroad出品 & X告知
- [ ] Gumroadに商品登録（¥1,980、Windows zip & AppImage） **👤 Owner**
- [ ] announce_tweet.md の案B or Cで告知投稿 **🤖 Claude** (`/axeon-tweet`)
- [ ] electron-app/ を git commit & push **🤖 Claude**
- **背景**: ビルド・note記事・Gumroad原稿がすべて揃っており、出品待ちの状態

---

## 🟡 重要タスク（今週中）

### [TASK-002] note記事 #08 X告知テキスト作成
- [ ] `08_au_hikari_ai_internet.md` のX告知テキストを作成・保存 **🤖 Claude** (`/axeon-note`)

### [TASK-003] 自社X（Axeon公式）投稿の継続監視
- [ ] VPS上のcronが正常稼働しているか定期確認 **🤖 Claude** (`/axeon-post-check`)
- [ ] アフィリエイト自動投稿のエラー状況確認・ログ読み取り **⚡ Codex**
- **背景**: 5月にネットワークエラーで停止した履歴あり

---

## 🟢 中長期タスク

### [TASK-004] note記事 #14以降の継続制作
- [ ] 次回テーマの選定・記事作成・サムネイル・X告知テキストのセット制作 **🤖 Claude** (`/axeon-note`)
- **目安**: 週1〜2本ペース

### [TASK-005] パイロット顧客の獲得（1〜3社）
- [ ] アプローチ方法・オファー設計の戦略立案 **🤖 Claude**（Jobs と Owner で決定）
- [ ] マネタイズができていない原因の究明 **🤖 Claude**（分析・判断）
- [ ] コンテンツ・ターゲットの最適化案の言語化 **🤖 Claude**
- [ ] ケーススタディ用レポートテンプレート作成 **⚡ Codex**（ファイル生成）
- **背景**: ロードマップ フェーズ1の必須項目。現在0社

### [TASK-006] 競合調査・差別化ポイントの定義
- [ ] 他ユーザー（競合アカウント）の分析・差別化言語化 **🤖 Claude**（調査・判断）
- [ ] `strategy/competitive.md` への記録 **⚡ Codex**（ファイル作成）

### [TASK-007] Claude Runtime の安定稼働
- [ ] Claude runtime を正常実行できる環境の整備・スクリプト修正 **⚡ Codex**（実装）

---

## ⬜ バックログ

### [TASK-008] エンゲージメント分析レポートの自動化
- [ ] X APIでいいね・リプライ・インプレッション数を取得するスクリプト作成 **⚡ Codex**
- [ ] 週次レポート自動集計の仕組み構築 **⚡ Codex**
- [ ] レポート設計・出力フォーマット定義 **🤖 Claude**

### [TASK-009] SaaS版（セルフサービス型）の設計
- [ ] フリーミアムプランの機能範囲・課金フローの設計 **🤖 Claude**（設計・判断）
- [ ] 実装（Stripe連携等） **⚡ Codex**
- **前提**: フェーズ2以降（パイロット顧客10社達成後）

---

## ✅ 完了済み

- [x] 会社名・事業・ターゲット・収益モデルの確定（2026-04-14）
- [x] AI CEO/CTO/CMO/COO 体制の構築（2026-04-14）
- [x] Axeon公式X 透明性戦略の確定（2026-04-14）
- [x] note記事 #01〜#13 作成（〜2026-06）
- [x] X投稿自動化スクリプト（auto_post.py / affiliate_post.py）
- [x] VPSへの自動投稿デプロイ
- [x] X Post Scheduler Electron app 開発・ビルド完了
- [x] Gumroad / note記事原稿の作成完了

---

## 次のアクション（Jobs推薦）

1. **今すぐ**: TASK-001 — Gumroad出品（Ownerのみ操作可）+ Claude がX告知投稿
2. **今週**: TASK-002（Claude）、TASK-003のログ確認（Codex）
3. **来週以降**: TASK-005 — 戦略をClaudeと決定 → Codexがテンプレ実装
