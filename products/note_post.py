#!/usr/bin/env python3
"""
note.com 自動投稿スクリプト

使い方:
  python note_post.py --login              # 初回: ブラウザでログイン & セッション保存
  python note_post.py <記事番号>           # 記事を公開
  python note_post.py <記事番号> --draft   # 下書き保存（公開しない）
  python note_post.py <記事番号> --preview # 投稿前に内容を確認して手動で公開

例:
  python note_post.py 13
  python note_post.py 13 --draft
"""

import sys
import re
import json
import time
import argparse
from pathlib import Path

ARTICLES_DIR = Path(__file__).parent / "note_articles"
SESSION_FILE = Path(__file__).parent / ".note_session.json"

# アフィリエイトリンクの判定パターン
AFFILIATE_PATTERNS = [
    r"px\.a8\.net",
    r"af\.moshimo\.com",
    r"ck\.jp\.ap\.valuecommerce\.com",
    r"#PR",
]


def find_article_files(number: int):
    prefix = f"{number:02d}_"
    md_files = list(ARTICLES_DIR.glob(f"{prefix}*.md"))
    img_files = list(ARTICLES_DIR.glob(f"{prefix}thumbnail.*"))
    return (md_files[0] if md_files else None, img_files[0] if img_files else None)


def parse_markdown(md_path: Path):
    """タイトル（# 行）と本文を分離"""
    content = md_path.read_text(encoding="utf-8")
    lines = content.split("\n")
    title = ""
    body_lines = []
    for line in lines:
        if not title and line.startswith("# "):
            title = line[2:].strip()
        else:
            body_lines.append(line)
    return title, "\n".join(body_lines).strip()


def is_affiliate(content: str) -> bool:
    return any(re.search(p, content) for p in AFFILIATE_PATTERNS)


def md_to_html(md_text: str) -> str:
    """マークダウンをnote.comエディタ用HTMLに変換"""
    import markdown
    return markdown.markdown(
        md_text,
        extensions=["extra", "nl2br"],
    )


def login_and_save_session():
    """ブラウザを開いてログインし、セッションを保存する"""
    from playwright.sync_api import sync_playwright

    print("ブラウザを開きます。note.comにログインしてください。")
    print("ログイン完了後、Enterキーを押してセッションを保存します。")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://note.com/login")
        input("\n>>> ログインが完了したらEnterを押してください...")

        cookies = context.cookies()
        SESSION_FILE.write_text(json.dumps(cookies, ensure_ascii=False, indent=2))
        print(f"セッションを保存しました: {SESSION_FILE}")
        browser.close()


def load_session(context):
    """保存済みセッションをロード"""
    if not SESSION_FILE.exists():
        print("セッションファイルが見つかりません。先に --login を実行してください。")
        sys.exit(1)
    cookies = json.loads(SESSION_FILE.read_text())
    context.add_cookies(cookies)


def post_article(number: int, draft: bool = False, preview: bool = False):
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

    md_file, img_file = find_article_files(number)
    if not md_file:
        print(f"エラー: 記事 {number:02d} のMarkdownファイルが見つかりません")
        sys.exit(1)

    content = md_file.read_text(encoding="utf-8")
    title, body = parse_markdown(md_file)
    free = is_affiliate(content)
    price = 0 if free else 300

    print(f"\n{'='*50}")
    print(f"記事    : {md_file.name}")
    print(f"タイトル: {title}")
    print(f"サムネイル: {img_file.name if img_file else 'なし'}")
    print(f"価格    : {'無料' if free else f'¥{price}'}")
    print(f"モード  : {'下書き' if draft else ('プレビュー停止' if preview else '公開')}")
    print(f"{'='*50}\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=80)
        context = browser.new_context()
        load_session(context)

        page = context.new_page()

        # ---- 新規記事ページを開く ----
        print("新規記事ページを開いています...")
        page.goto("https://note.com/notes/new", wait_until="networkidle")
        time.sleep(2)

        # ---- タイトル入力 ----
        print("タイトルを入力しています...")
        try:
            title_area = page.locator('[placeholder="タイトル"], [data-placeholder="タイトル"]').first
            title_area.click()
            title_area.fill(title)
        except PWTimeout:
            print("警告: タイトル欄が見つかりませんでした。手動で入力してください。")
        time.sleep(1)

        # ---- 本文入力（クリップボード経由でHTMLペースト）----
        print("本文をペーストしています...")
        html_body = md_to_html(body)
        try:
            editor = page.locator(".ProseMirror, [contenteditable='true']").last
            editor.click()
            time.sleep(0.5)

            # JavaScriptでクリップボードにHTMLをセットしてCtrl+Vでペースト
            page.evaluate(
                """async (html) => {
                    const item = new ClipboardItem({
                        'text/html': new Blob([html], { type: 'text/html' }),
                    });
                    await navigator.clipboard.write([item]);
                }""",
                html_body,
            )
            editor.press("Control+v")
            time.sleep(2)
        except Exception as e:
            print(f"警告: 本文の自動入力に失敗しました ({e})")
            print("手動で本文をペーストしてください。")

        # ---- サムネイル（ヘッダー画像）アップロード ----
        if img_file:
            print(f"サムネイルをアップロードしています: {img_file.name}")
            try:
                # ヘッダー画像エリアをクリック
                header_btn = page.locator("text=画像を追加, text=カバー画像, [aria-label*='画像']").first
                header_btn.click(timeout=5000)
                time.sleep(1)

                file_input = page.locator("input[type='file']").first
                file_input.set_input_files(str(img_file))
                time.sleep(3)
            except Exception as e:
                print(f"警告: サムネイルの自動アップロードに失敗しました ({e})")
                print("手動でサムネイルをアップロードしてください。")

        if preview:
            print("\nプレビューモードで停止します。内容を確認して手動で公開してください。")
            input(">>> 完了したらEnterを押してブラウザを閉じます...")
            browser.close()
            return

        if draft:
            # ---- 下書き保存 ----
            print("下書き保存しています...")
            try:
                draft_btn = page.locator("text=下書き保存").first
                draft_btn.click()
                time.sleep(2)
                print("下書き保存完了!")
            except Exception as e:
                print(f"下書き保存に失敗しました: {e}")
        else:
            # ---- 公開フロー ----
            print("公開設定を開いています...")
            try:
                publish_btn = page.locator("text=公開する").first
                publish_btn.click()
                time.sleep(2)

                # 価格設定
                if not free:
                    print(f"価格を ¥{price} に設定しています...")
                    try:
                        price_input = page.locator("input[type='number'], input[name='price']").first
                        price_input.fill(str(price))
                        time.sleep(1)
                    except Exception as e:
                        print(f"警告: 価格設定に失敗しました ({e})")

                # 最終確認
                print(f"\n公開準備完了。タイトル: {title}")
                confirm = input("本当に公開しますか？ [y/N]: ").strip().lower()
                if confirm != "y":
                    print("公開をキャンセルしました。")
                    input(">>> Enterを押してブラウザを閉じます...")
                    browser.close()
                    return

                # 公開ボタン（モーダル内）
                final_publish = page.locator("text=公開する").last
                final_publish.click()
                time.sleep(3)
                print("公開完了!")

                # 公開後URLを取得
                current_url = page.url
                if "note.com" in current_url and "/n/" in current_url:
                    print(f"URL: {current_url}")

            except Exception as e:
                print(f"公開処理に失敗しました: {e}")
                input(">>> 手動で操作してください。完了後Enterを押してください...")

        time.sleep(2)
        browser.close()


def main():
    parser = argparse.ArgumentParser(description="note.com 自動投稿")
    parser.add_argument("number", type=int, nargs="?", help="記事番号 (例: 13)")
    parser.add_argument("--login", action="store_true", help="ログイン & セッション保存")
    parser.add_argument("--draft", action="store_true", help="下書き保存（公開しない）")
    parser.add_argument("--preview", action="store_true", help="内容確認後に手動公開")
    args = parser.parse_args()

    if args.login:
        login_and_save_session()
        return

    if args.number is None:
        parser.print_help()
        sys.exit(1)

    post_article(args.number, draft=args.draft, preview=args.preview)


if __name__ == "__main__":
    main()
