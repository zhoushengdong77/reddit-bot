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
    "casino jackpot",
    "big casino win",
    "blackjack win",
    "roulette win",
    "slot jackpot",
    "sports betting tips",
    "poker highlights"
]

translator = Translator()


def clean_title(title):
    title = html.unescape(title)
    title = re.sub(r"#\S+", "", title)
    title = re.sub(r"\s+", " ", title)
    return title.strip()


def translate(text):
    try:
        return translator.translate(text, dest="zh-cn").text
    except Exception:
        return text


def classify(title):
    t = title.lower()

    if "poker" in t:
        return "🃏 扑克"
    if "bet" in t or "prediction" in t or "sportsbook" in t or "football" in t or "soccer" in t:
        return "⚽ 体育下注"
    if "jackpot" in t or "win" in t or "won" in t:
        return "💰 赢钱"
    if "casino" in t or "roulette" in t or "blackjack" in t or "slot" in t:
        return "🎰 赌场"

    return "📺 博彩"


def get_heat_badge(tag):
    if "💰" in tag:
        return random.choice(["赢麻了", "爆", "HOT"])
    if "🎰" in tag:
        return random.choice(["必看", "爆", "HOT"])
    if "⚽" in tag:
        return random.choice(["热门", "必看", "焦点"])
    if "🃏" in tag:
        return random.choice(["高能", "必看", "HOT"])
    return random.choice(["HOT", "爆", "精选"])


def get_time():
    dt = datetime.now(timezone.utc) - timedelta(hours=24)
    return dt.isoformat().replace("+00:00", "Z")


def get_hot_headline(videos):
    tags = [v["tag"] for v in videos]

    if any("💰" in t for t in tags):
        pool = [
            "🔥 今日赌场最大赢家",
            "💰 赌徒疯狂赢钱瞬间",
            "🎰 今日最夸张赢钱画面",
            "💥 24小时赌场爆热视频"
        ]
        return random.choice(pool)

    if any("⚽" in t for t in tags):
        pool = [
            "⚽ 今日热门下注视频",
            "🔥 体育下注内容精选",
            "📈 今日博彩圈关注焦点",
            "🎯 今日下注热点合集"
        ]
        return random.choice(pool)

    if any("🃏" in t for t in tags):
        pool = [
            "🃏 今日扑克高能片段",
            "🔥 扑克圈热门视频",
            "♠️ 今日牌局精彩瞬间",
            "💥 扑克高手内容精选"
        ]
        return random.choice(pool)

    pool = [
        "📺 BOCAI51 今日精选",
        "🔥 今日博彩热门视频",
        "💥 博彩圈24小时热点",
        "🎰 今日高热内容合集"
    ]
    return random.choice(pool)


def get_videos():
    videos = []
    seen = set()

    for keyword in KEYWORDS:
        url = "https://www.googleapis.com/youtube/v3/search"

        params = {
            "part": "snippet",
            "q": keyword,
            "type": "video",
            "maxResults": 5,
            "order": "date",
            "publishedAfter": get_time(),
            "key": YOUTUBE_API_KEY
        }

        try:
            r = requests.get(url, params=params, timeout=20)
            r.raise_for_status()
            data = r.json()

            for item in data.get("items", []):
                title = clean_title(item["snippet"]["title"])
                title_cn = translate(title)
                channel = item["snippet"]["channelTitle"]
                video_id = item["id"]["videoId"]
                link = f"https://youtube.com/watch?v={video_id}"

                if link in seen:
                    continue

                seen.add(link)

                tag = classify(title)

                videos.append({
                    "title": title_cn[:40],
                    "tag": tag,
                    "heat": get_heat_badge(tag),
                    "link": link,
                    "channel": channel[:22]
                })
        except Exception:
            continue

    return videos[:4]


def split_text(text, max_len=14, max_lines=2):
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

    top = (35, 0, 0)
    bottom = (8, 8, 12)

    for y in range(height):
        ratio = y / height
        r = int(top[0] * (1 - ratio) + bottom[0] * ratio)
        g = int(top[1] * (1 - ratio) + bottom[1] * ratio)
        b = int(top[2] * (1 - ratio) + bottom[2] * ratio)
        draw.line((0, y, width, y), fill=(r, g, b))

    draw.ellipse((-120, -100, 520, 280), fill=(90, 40, 0))
    draw.ellipse((860, 420, 1380, 860), fill=(70, 25, 0))


def draw_glow_text(draw, pos, text, font, main_fill, glow_fill):
    x, y = pos
    for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2), (-2, -2), (2, 2), (-2, 2), (2, -2)]:
        draw.text((x + dx, y + dy), text, font=font, fill=glow_fill)
    draw.text((x, y), text, font=font, fill=main_fill)


def draw_badge(draw, x, y, text, font):
    draw.rounded_rectangle((x, y, x + 92, y + 52), radius=18, fill=(255, 215, 0), outline=(255, 245, 180), width=2)
    draw.text((x + 18, y + 10), text, font=font, fill=(80, 20, 0))


def draw_heat_badge(draw, x, y, text, font):
    draw.rounded_rectangle((x, y, x + 110, y + 44), radius=16, fill=(200, 0, 0), outline=(255, 215, 0), width=2)
    tw = draw.textbbox((0, 0), text, font=font)[2]
    draw.text((x + (110 - tw) / 2, y + 8), text, font=font, fill=(255, 240, 180))


def draw_card(draw, x, y, video, index_symbol, font_title, font_tag, font_small, font_index, font_heat):
    w = 570
    h = 230

    draw.rounded_rectangle(
        (x, y, x + w, y + h),
        radius=28,
        fill=(26, 18, 22),
        outline=(255, 190, 40),
        width=4
    )

    draw.rounded_rectangle(
        (x, y, x + w, y + 52),
        radius=28,
        fill=(170, 20, 20)
    )
    draw.rectangle((x, y + 28, x + w, y + 52), fill=(170, 20, 20))

    draw_badge(draw, x + 18, y + 14, index_symbol, font_index)
    draw.text((x + 130, y + 14), video["tag"], font=font_tag, fill=(255, 235, 170))
    draw_heat_badge(draw, x + 438, y + 10, video["heat"], font_heat)

    title = split_text(video["title"], 15, 2)
    draw.multiline_text(
        (x + 24, y + 82),
        title,
        font=font_title,
        fill=(255, 255, 255),
        spacing=12
    )

    channel_text = f'频道: {video["channel"]}'
    draw.text((x + 24, y + 192), channel_text, font=font_small, fill=(220, 220, 220))


def create_poster(videos, poster_title):
    width = 1280
    height = 720

    img = Image.new("RGB", (width, height), (10, 10, 14))
    draw_gradient_background(img, width, height)
    draw = ImageDraw.Draw(img)

    try:
        font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 50)
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
        font_tag = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
        font_index = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
        font_brand = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        font_heat = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    except Exception:
        font_big = ImageFont.load_default()
        font_title = ImageFont.load_default()
        font_tag = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_index = ImageFont.load_default()
        font_brand = ImageFont.load_default()
        font_heat = ImageFont.load_default()

    draw.rounded_rectangle((22, 18, 1258, 92), radius=24, fill=(120, 10, 10), outline=(255, 205, 60), width=3)
    draw_glow_text(draw, (40, 30), poster_title, font_big, (255, 255, 255), (255, 180, 0))

    draw.rounded_rectangle((22, 650, 1258, 702), radius=20, fill=(35, 18, 10), outline=(255, 205, 60), width=2)
    draw.text((42, 664), "BOCAI51 · 红金精选海报", font=font_brand, fill=(255, 215, 0))
    draw.text((1010, 664), "24H HOT", font=font_brand, fill=(255, 240, 180))

    positions = [
        (40, 118),
        (670, 118),
        (40, 378),
        (670, 378)
    ]

    index_symbols = ["①", "②", "③", "④"]

    for i, video in enumerate(videos):
        x, y = positions[i]
        draw_card(
            draw,
            x,
            y,
            video,
            index_symbols[i],
            font_title,
            font_tag,
            font_small,
            font_index,
            font_heat
        )

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
        data = {
            "chat_id": CHANNEL,
            "caption": caption
        }
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
