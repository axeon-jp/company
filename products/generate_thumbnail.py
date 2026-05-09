"""
note記事用アイキャッチ画像生成スクリプト
DALL-E 3で背景を生成 → Pillowでテキスト合成 → 1280x670px で保存
"""

import os, sys, urllib.request, tempfile
import openai
from PIL import Image, ImageDraw, ImageFont

FONT_BOLD    = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
FONT_REGULAR = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
OUTPUT_SIZE  = (1280, 670)

def load_env():
    env_path = os.path.join(os.path.dirname(__file__), "../x_api_post/.env")
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

def generate_bg(prompt: str) -> Image.Image:
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    resp = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1792x1024",
        quality="standard",
        n=1,
    )
    url = resp.data[0].url
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    urllib.request.urlretrieve(url, tmp.name)
    img = Image.open(tmp.name).convert("RGBA")
    os.unlink(tmp.name)
    return img.resize(OUTPUT_SIZE, Image.LANCZOS)

def add_overlay(img: Image.Image, title: str, subtitle: str, tag: str) -> Image.Image:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    W, H = img.size

    # 下側グラデーション暗幕
    for i in range(H):
        alpha = int(200 * (i / H) ** 1.5)
        draw.line([(0, i), (W, i)], fill=(10, 10, 20, alpha))

    # 左側にも薄く暗幕
    for i in range(W):
        alpha = int(120 * (1 - i / W) ** 0.8)
        draw.line([(i, 0), (i, H)], fill=(10, 10, 20, alpha))

    img = Image.alpha_composite(img, overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # タグバッジ
    tag_font = ImageFont.truetype(FONT_REGULAR, 22)
    tag_bbox = draw.textbbox((0, 0), tag, font=tag_font)
    tag_w = tag_bbox[2] - tag_bbox[0] + 28
    tag_h = tag_bbox[3] - tag_bbox[1] + 12
    draw.rounded_rectangle([60, H - 200, 60 + tag_w, H - 200 + tag_h],
                            radius=6, fill=(99, 102, 241))
    draw.text((74, H - 200 + 6), tag, font=tag_font, fill=(255, 255, 255))

    # タイトル（2行対応）
    title_font = ImageFont.truetype(FONT_BOLD, 54)
    max_w = W - 120
    lines = []
    line = ""
    for char in title:
        test = line + char
        bbox = draw.textbbox((0, 0), test, font=title_font)
        if bbox[2] - bbox[0] > max_w:
            lines.append(line)
            line = char
        else:
            line = test
    if line:
        lines.append(line)

    y = H - 170 + tag_h + 16
    for l in lines[:2]:
        draw.text((60, y), l, font=title_font, fill=(255, 255, 255),
                  stroke_width=2, stroke_fill=(0, 0, 0))
        bbox = draw.textbbox((60, y), l, font=title_font)
        y += bbox[3] - bbox[1] + 8

    # サブタイトル
    sub_font = ImageFont.truetype(FONT_REGULAR, 26)
    draw.text((62, y + 10), subtitle, font=sub_font,
              fill=(180, 200, 255), stroke_width=1, stroke_fill=(0, 0, 0))

    # ブランド
    brand_font = ImageFont.truetype(FONT_REGULAR, 20)
    draw.text((W - 120, H - 36), "by Axeon", font=brand_font,
              fill=(150, 150, 180))

    return img

ARTICLES = [
    {
        "id": "side_income_story",
        "title": "会社員がAIで副業を始めて3ヶ月でできたこと",
        "subtitle": "収益・ツール・失敗も全部公開 | Claude × X API × note",
        "tag": "体験談 · 無料記事",
        "bg_prompt": (
            "Abstract dark background representing a Japanese office worker's journey into AI side hustle. "
            "Deep charcoal and dark navy gradient, glowing golden coins and upward trending graph lines, "
            "subtle circuit patterns and soft amber accent lights. "
            "Cinematic, warm-cool contrast, motivational mood, no text, no people. 16:9 aspect ratio."
        ),
        "output": "/home/y75a3/company/products/note_articles/01_thumbnail.png",
    },
    {
        "id": "x_auto_post_guide",
        "title": "PythonとClaude APIでX自動投稿システムを作る",
        "subtitle": "コード全公開 · missed slot recovery · cron定期実行 | ¥1,980",
        "tag": "¥1,980 · 技術解説",
        "bg_prompt": (
            "Abstract dark tech background for Python and AI automation article. "
            "Deep dark background with glowing blue-green terminal code streams, "
            "floating Python snake icon outline, circuit board patterns, "
            "subtle cyan and electric blue accent lights, upward data flow. "
            "Cinematic, developer aesthetic, no text, no people. 16:9 aspect ratio."
        ),
        "output": "/home/y75a3/company/products/note_articles/02_thumbnail.png",
    },
    {
        "id": "claude_api_intro",
        "title": "Claude APIを今日から使う【入門ハンズオン】",
        "subtitle": "APIキー取得からコード実行まで30分 · ¥500",
        "tag": "¥500 · 入門",
        "bg_prompt": (
            "Abstract dark background for Claude AI API tutorial article. "
            "Deep dark purple and indigo gradient, glowing Anthropic-style orange amber orb, "
            "floating code brackets and API request symbols, soft warm light rays. "
            "Minimal, elegant, developer aesthetic, no text, no people. 16:9 aspect ratio."
        ),
        "output": "/home/y75a3/company/products/note_articles/03_thumbnail.png",
    },
    {
        "id": "x_growth_strategy",
        "title": "Xフォロワーを増やす投稿戦略まとめ",
        "subtitle": "実録3ヶ月・アルゴリズム攻略・伸びる型を公開 | ¥500",
        "tag": "¥500 · X運用",
        "bg_prompt": (
            "Abstract dark background representing social media growth and X Twitter analytics. "
            "Deep dark navy with glowing upward trending graph lines, follower count numbers floating, "
            "subtle blue and cyan accent lights, rising arrow motifs. "
            "Cinematic, data-driven aesthetic, no text, no people. 16:9 aspect ratio."
        ),
        "output": "/home/y75a3/company/products/note_articles/04_thumbnail.png",
    },
    {
        "id": "vps_cron_automation",
        "title": "VPS+cronで24時間自動化システムを作る",
        "subtitle": "PCなしで動き続ける仕組み・ConoHa対応 | ¥500",
        "tag": "¥500 · インフラ",
        "bg_prompt": (
            "Abstract dark server infrastructure background. "
            "Deep dark background with glowing green terminal output streams, "
            "server rack silhouettes, network connection nodes, "
            "subtle matrix-style data flow, electric green and teal accents. "
            "Cinematic, tech aesthetic, no text, no people. 16:9 aspect ratio."
        ),
        "output": "/home/y75a3/company/products/note_articles/05_thumbnail.png",
    },
    {
        "id": "affiliate_auto_post",
        "title": "アフィリエイト自動投稿システムの作り方",
        "subtitle": "X×A8.net×Claude API コード全公開 | ¥500",
        "tag": "¥500 · アフィリエイト",
        "bg_prompt": (
            "Abstract dark background for affiliate marketing automation article. "
            "Deep dark background with glowing gold coins, upward revenue chart lines, "
            "floating code symbols and gear icons, warm amber and orange accent lights. "
            "Cinematic, wealth and automation aesthetic, no text, no people. 16:9 aspect ratio."
        ),
        "output": "/home/y75a3/company/products/note_articles/06_thumbnail.png",
    },
    {
        "id": "prompt_collection",
        "title": "AIでX運用を10倍速にするプロンプト全集",
        "subtitle": "7カテゴリ・30本 コピペで即使える | ChatGPT・Claude対応",
        "tag": "¥980 · note",
        "bg_prompt": (
            "Abstract dark tech background for Japanese social media article. "
            "Deep navy blue and indigo gradient, floating glowing code symbols, "
            "neural network nodes, subtle purple accent lights. "
            "Cinematic, modern, no text, no people. 16:9 aspect ratio."
        ),
        "output": "/home/y75a3/company/products/note_prompt_collection/thumbnail.png",
    },
    {
        "id": "notion_template",
        "title": "X運用AIダッシュボード Notionテンプレート",
        "subtitle": "投稿・数値・ネタ・プロンプトを1ページで管理 | 即使える",
        "tag": "¥1,500 · note",
        "bg_prompt": (
            "Abstract dark productivity dashboard background. "
            "Deep dark blue with glowing teal and cyan grid lines, "
            "floating minimal UI cards, soft data visualization elements. "
            "Modern, minimal, no text, no people. 16:9 aspect ratio."
        ),
        "output": "/home/y75a3/company/products/notion_template/thumbnail.png",
    },
    {
        "id": "ahamo_hikari_cost_cut",
        "title": "毎月の通信費を半額にした話",
        "subtitle": "ahamo光乗り換えでdポイント2万p還元 | 無料記事",
        "tag": "節約 · 無料",
        "bg_prompt": (
            "Abstract dark background representing smartphone and home internet cost savings in Japan. "
            "Deep dark teal and navy gradient, glowing yen coin symbols, "
            "downward trending cost graph with green highlight, wifi signal rings, "
            "soft cyan and emerald accent lights, minimalist money-saving mood. "
            "Cinematic, no text, no people. 16:9 aspect ratio."
        ),
        "output": "/home/y75a3/company/products/note_articles/07_thumbnail.png",
    },
    {
        "id": "au_hikari_ai_internet",
        "title": "AI副業に必要なネット回線を選んだ話",
        "subtitle": "速度・安定性・コスパ比較 | auひかり | 無料記事",
        "tag": "回線比較 · 無料",
        "bg_prompt": (
            "Abstract dark background representing high-speed fiber optic internet for AI development. "
            "Deep dark navy with glowing blue fiber optic light trails, "
            "speed meter dial at maximum, floating network node connections, "
            "electric blue and white accent lights, stable network aesthetic. "
            "Cinematic, tech infrastructure mood, no text, no people. 16:9 aspect ratio."
        ),
        "output": "/home/y75a3/company/products/note_articles/08_thumbnail.png",
    },
    {
        "id": "video_editor_side_income",
        "title": "動画編集を副業にするためにやったこと",
        "subtitle": "資格あり・顧客紹介あり・スクール選びの基準 | 無料記事",
        "tag": "副業 · 無料",
        "bg_prompt": (
            "Abstract dark background representing video editing as a side business in Japan. "
            "Deep dark background with glowing video timeline tracks, film strip silhouettes, "
            "floating play button icons, soft purple and orange gradient accent lights, "
            "rising income graph overlay, creative and professional mood. "
            "Cinematic, no text, no people. 16:9 aspect ratio."
        ),
        "output": "/home/y75a3/company/products/note_articles/09_thumbnail.png",
    },
    {
        "id": "free_telecom_cost_review",
        "title": "固定費の中で一番削りやすいのは通信費だった",
        "subtitle": "年3万円削減の具体的な方法 | 無料記事",
        "tag": "節約 · 無料",
        "bg_prompt": (
            "Abstract dark background representing monthly fixed cost reduction and household savings. "
            "Deep dark charcoal with glowing golden yen symbols falling like rain, "
            "monthly expense bar chart with one bar dramatically lower, "
            "scissor cutting a chain of coins, warm amber and gold accent lights. "
            "Cinematic, financial optimization mood, no text, no people. 16:9 aspect ratio."
        ),
        "output": "/home/y75a3/company/products/note_articles/10_thumbnail.png",
    },
    {
        "id": "free_internet_comparison",
        "title": "光回線を3社比較して乗り換えた話",
        "subtitle": "速度より安定性で選ぶべき理由 | 無料記事",
        "tag": "比較 · 無料",
        "bg_prompt": (
            "Abstract dark background representing internet speed comparison between three providers. "
            "Deep dark background with three glowing speed meter dials side by side, "
            "one clearly brighter than others, fiber optic light strands, "
            "network stability waveforms, cool blue and white accent lights. "
            "Cinematic, comparison aesthetic, no text, no people. 16:9 aspect ratio."
        ),
        "output": "/home/y75a3/company/products/note_articles/11_thumbnail.png",
    },
    {
        "id": "free_server_comparison",
        "title": "副業ブログを始めるならどのサーバーか比較した",
        "subtitle": "3社比較の結論 | ConoHa WING | 無料記事",
        "tag": "比較 · 無料",
        "bg_prompt": (
            "Abstract dark background representing web hosting server comparison for Japanese blog. "
            "Deep dark background with glowing server rack silhouettes, "
            "floating website window frames, upward speed arrow, "
            "subtle electric blue and violet accent lights, startup blog mood. "
            "Cinematic, tech minimalism aesthetic, no text, no people. 16:9 aspect ratio."
        ),
        "output": "/home/y75a3/company/products/note_articles/12_thumbnail.png",
    },
    {
        "id": "free_video_editor_vs_self",
        "title": "動画編集副業、独学とスクールを比較した",
        "subtitle": "稼げるようになるまでの違い | 無料記事",
        "tag": "比較 · 無料",
        "bg_prompt": (
            "Abstract dark background representing the choice between self-learning and attending a school for video editing. "
            "Split dark background: left side shows solitary glowing laptop screen, right side shows connected network of people nodes, "
            "floating film reel and income graph between them, "
            "warm amber on left, cool blue on right, contrast and decision mood. "
            "Cinematic, no text, no people. 16:9 aspect ratio."
        ),
        "output": "/home/y75a3/company/products/note_articles/13_thumbnail.png",
    },
]

if __name__ == "__main__":
    load_env()
    targets = sys.argv[1:] or [a["id"] for a in ARTICLES]

    for article in ARTICLES:
        if article["id"] not in targets:
            continue
        print(f"[{article['id']}] 背景を生成中...")
        bg = generate_bg(article["bg_prompt"])
        print(f"[{article['id']}] テキストを合成中...")
        result = add_overlay(bg, article["title"], article["subtitle"], article["tag"])
        result.save(article["output"])
        print(f"[{article['id']}] 保存完了 → {article['output']}")
