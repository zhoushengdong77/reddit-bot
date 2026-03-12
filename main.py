import html
import os
import random
import re
from datetime import datetime, timedelta, timezone

import requests
from googletrans import Translator
from PIL import Image, ImageDraw, ImageFont

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL = "@BOCAI51"
YOUTUBE_API_KEY = os.environ["YOUTUBE_API_KEY"]

KEYWORDS = [
    "casino jackpot big win",
    "slot jackpot win",
    "blackjack big win",
    "roulette big win",
    "sports betting picks",
    "poker big hand"
]

BAD_WORDS = [
    "podcast", "episode", "reaction", "news", "update", "interview",
    "strategy guide", "tutorial", "lesson", "review", "compilation",
    "crazy time", "double all"
]

translator = Translator()


def clean_title(title: str) -> str:
    title = html.unescape(title)
    title = re.sub(r"#\S+", "", title)
    title = re.sub(r"\s+", " ", title)
    return title.strip()


def translate(text: str) -> str:
    try:
        return translator.translate(text, dest="zh-cn").text
    except Exception:
        return text


def classify(title: str) -> str:
    t = title.lower()

    if any(x in t for x in ["poker", "holdem", "texas"]):
        return "🃏 扑克"
    if any(x in t for x in ["bet", "betting", "prediction", "sportsbook", "football", "soccer", "parlay"]):
        return "⚽ 体育下注"
    if any(x in t for x in ["jackpot", "big win", "huge win", "won", "massive win"]):
        return "💰 赢钱"
    if any(x in t for x in ["casino", "roulette", "blackjack", "slot", "slots"]):
        return "🎰 赌场"
    return "📺 博彩"


def get_heat_badge(tag: str) -> str:
    if "💰" in tag:
        return random.choice(["赢麻了", "爆", "HOT"])
    if "🎰" in tag:
        return random.choice(["必看", "爆", "HOT"])
    if "⚽" in tag:
        return random.choice(["热门", "焦点", "必看"])
    if "🃏" in tag:
        return random.choice(["高能", "HOT", "必看"])
    return random.choice(["精选", "爆", "HOT"])


def get_hot_headline(videos) -> str:
    tags = [v["tag"] for v in videos]

    if any("💰" in t for t in tags):
        return random.choice([
            "🔥 今日赌场最大赢家",
            "💰 赌徒疯狂赢钱瞬间",
            "🎰 今日最夸张赢钱画面",
            "💥 24小时赢钱热点"
        ])

    if any("⚽" in t for t in tags):
        return random.choice([
            "⚽ 今日热门下注视频",
            "🎯 今日下注焦点合集",
            "📈 博彩圈下注热点",
            "🔥 今日体育下注精选"
        ])

    if any("🃏" in t for t in tags):
        return random.choice([
            "🃏 今日扑克高能片段",
            "♠️ 今日牌局精彩瞬间",
            "🔥 扑克圈热门视频",
            "💥 今日扑克热点"
        ])

    return random.choice([
        "📺 BOCAI51 今日精选",
        "🔥 今日博彩热门视频",
        "💥 博彩圈24小时热点",
        "🎰 今日高热内容合集"
    ])


def get_time() -> str:
    dt = datetime.now(timezone.utc) - timedelta(hours=24)
    return dt.isoformat().replace("+00:00", "Z")


def is_good_video(title: str) -> bool:
    t = title.lower()

    if len(t) < 8:
        return False

    if any(bad in t for bad in BAD_WORDS):
        return False

    good_signals = [
        "win", "won", "jackpot", "casino", "blackjack", "roulette",
        "slot", "bet", "betting", "parlay", "poker"
    ]
    return any(word in t for word in good_signals)


def short_cn_title(text: str, max_len: int = 22) -> str:
    text = re.sub(r"[“”\"']", "", text)
    text = re.sub(r"\s+", "", text)
    return text[:max_len]


def get_videos():
    videos = []
    seen_links = set()
    seen_titles = set()

    for keyword in KEYWORDS:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": keyword,
            "type": "video",
            "maxResults": 8,
            "order": "date",
            "publishedAfter": get_time(),
            "key": YOUTUBE_API_KEY
        }

        try:
            r = requests.get(url, params=params, timeout=20)
            r.raise_for_status()
            data = r.json()

            for item in data.get("items", []):
                raw_title = clean_title(item["snippet"]["title"])
                if not is_good_video(raw_title):
                    continue

                title_cn = short_cn_title(translate(raw_title))
                channel = item["snippet"]["channelTitle"]
                video_id = item["id"]["videoId"]
                link = f"https://youtube.com/watch?v={video_id}"

                title_key = re.sub(r"\W+", "", title_cn.lower())

                if link in seen_links or title_key in seen_titles:
                    continue

                seen_links.add(link)
                seen_titles.add(title_key)

                tag = classify(raw_title)

                videos.append({
                    "title": title_cn,
                    "tag": tag,
                    "heat": get_heat_badge(tag),
                    "link": link,
                    "channel": channel[:20]
                })

        except Exception:
            continue

    return videos[:4]


def split_text(text, max_len=10, max_lines=2):
    lines = []
    current = ""

    for ch in text:
        current += ch
        if len(current) >= max_len:
            lines.append(current)
            current = ""

    if current:
        lines.append(current)

    return "\n".join(lines[:max_lines])


def draw_gradient_background(img, width, height):
    draw = ImageDraw.Draw(img)
    top = (45, 0, 0)
    bottom = (8, 8, 12)

    for y in range(height):
        ratio = y / height
        r = int(top[0] * (1 - ratio) + bottom[0] * ratio)
        g = int(top[1] * (1 - ratio) + bottom[1] * ratio)
        b = int(top[2] * (1 - ratio) + bottom[2] * ratio)
        draw.line((0, y, width, y), fill=(r, g, b))

    draw.ellipse((-120, -100, 520, 280), fill=(100, 40, 0))
    draw.ellipse((860, 420, 1380, 860), fill=(75, 25, 0))


def get_font(size, bold=False):
    paths = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def draw_glow_text(draw, pos, text, font, main_fill, glow_fill):
    x, y = pos
    for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2), (-2, -2), (2, 2), (-2, 2), (2, -2)]:
        draw.text((x + dx, y + dy), text, font=font, fill=glow_fill)
    draw.text((x, y), text, font=font, fill=main_fill)


def draw_badge(draw, x, y, text, font):
    draw.rounded_rectangle((x, y, x + 90, y + 50), radius=18, fill=(255, 215, 0), outline=(255, 245, 180), width=2)
    draw.text((x + 20, y + 9), text, font=font, fill=(100, 20, 0))


def draw_heat_badge(draw, x, y, text, font):
    draw.rounded_rectangle((x, y, x + 110, y + 42), radius=16, fill=(190, 0, 0), outline=(255, 215, 0), width=2)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text((x + (110 - tw) / 2, y + 6), text, font=font, fill=(255, 240, 180))


def draw_card(draw, x, y, video, index_symbol, font_title, font_tag, font_small, font_index, font_heat):
    w = 570
    h = 230

    draw.rounded_rectangle((x, y, x + w, y + h), radius=28, fill=(22, 16, 20), outline=(255, 190, 40), width=4)
    draw.rounded_rectangle((x, y, x + w, y + 52), radius=28, fill=(175, 18, 18))
    draw.rectangle((x, y + 28, x + w, y + 52), fill=(175, 18, 18))

    draw_badge(draw, x + 18, y + 14, index_symbol, font_index)
    draw.text((x + 130, y + 12), video["tag"], font=font_tag, fill=(255, 235, 170))
    draw_heat_badge(draw, x + 438, y + 10, video["heat"], font_heat)

    title = split_text(video["title"], 10, 2)
    draw.multiline_text((x + 24, y + 82), title, font=font_title, fill=(255, 255, 255), spacing=10)

    draw.text((x + 24, y + 192), f'频道: {video["channel"]}', font=font_small, fill=(220, 220, 220))


def create_poster(videos, poster_title):
    width, height = 1280, 720
    img = Image.new("RGB", (width, height), (10, 10, 14))
    draw_gradient_background(img, width, height)
    draw = ImageDraw.Draw(img)

    font_big = get_font(50, bold=True)
    font_title = get_font(28, bold=True)
    font_tag = get_font(22, bold=True)
    font_small = get_font(20, bold=False)
    font_index = get_font(26, bold=True)
    font_brand = get_font(24, bold=True)
    font_heat = get_font(20, bold=True)

    draw.rounded_rectangle((22, 18, 1258, 92), radius=24, fill=(120, 10, 10), outline=(255, 205, 60), width=3)
    draw_glow_text(draw, (40, 26), poster_title, font_big, (255, 255, 255), (255, 180, 0))

    draw.rounded_rectangle((22, 650, 1258, 702), radius=20, fill=(35, 18, 10), outline=(255, 205, 60), width=2)
    draw.text((42, 662), "BOCAI51 · 红金精选海报", font=font_brand, fill=(255, 215, 0))
    draw.text((1010, 662), "24H HOT", font=font_brand, fill=(255, 240, 180))

    positions = [(40, 118), (670, 118), (40, 378), (670, 378)]
    index_symbols = ["①", "②", "③", "④"]

    for i, video in enumerate(videos):
        x, y = positions[i]
        draw_card(draw, x, y, video, index_symbols[i], font_title, font_tag, font_small, font_index, font_heat)

    path = "poster.png"
    img.save(path, quality=95)
    return path


def build_caption(videos, poster_title):
    index_symbols = ["①", "②", "③", "④"]
    lines = [poster_title, ""]

    for i, v in enumerate(videos):
        lines.append(f'{index_symbols[i]} {v["heat"]} {v["tag"]} {v["title"]}')
        lines.append(v["link"])
        lines.append("")

    return "\n".join(lines)[:1000]


def send(photo, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    with open(photo, "rb") as f:
        files = {"photo": f}
        data = {"chat_id": CHANNEL, "caption": caption}
        r = requests.post(url, data=data, files=files, timeout=30)
        r.raise_for_status()


def send_text(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    r = requests.post(url, data={"chat_id": CHANNEL, "text": message}, timeout=20)
    r.raise_for_status()


def main():
    videos = get_videos()

    if not videos:
        send_text("📺 今日暂无可用的博彩热门视频。")
        return

    poster_title = get_hot_headline(videos)
    poster = create_poster(videos, poster_title)
    caption = build_caption(videos, poster_title)
    send(poster, caption)


if __name__ == "__main__":
    main()
