import html
import os
import re
from datetime import datetime, timedelta, timezone
from typing import List, Dict

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
    "parlay win",
    "poker highlights"
]

BAD_WORDS = [
    "shorts",
    "#shorts",
    "live stream",
    "livestream",
    "podcast",
    "episode",
    "reaction",
    "news",
    "update",
    "interview"
]

GOOD_WORDS = [
    "win",
    "won",
    "jackpot",
    "casino",
    "blackjack",
    "roulette",
    "slot",
    "slots",
    "betting",
    "parlay",
    "poker"
]

translator = Translator()


def clean_title(title: str) -> str:
    title = html.unescape(title)
    title = re.sub(r"#\S+", "", title)
    title = re.sub(r"\s+", " ", title).strip(" -|")
    return title


def translate_to_chinese(text: str) -> str:
    try:
        result = translator.translate(text, dest="zh-cn")
        return result.text.strip() or text
    except Exception:
        return text


def classify_video(title: str) -> str:
    t = title.lower()

    if any(x in t for x in ["betting", "parlay", "prediction", "predictions", "soccer", "football", "sportsbook"]):
        return "⚽ 体育下注"
    if any(x in t for x in ["poker", "holdem", "texas hold"]):
        return "🃏 扑克/牌局"
    if any(x in t for x in ["jackpot", "win", "won", "huge win", "big win"]):
        return "💰 赢钱/大奖"
    if any(x in t for x in ["blackjack", "roulette", "casino", "slot", "slots"]):
        return "🎰 赌场实战"
    return "📺 博彩视频"


def is_good_video(title: str) -> bool:
    t = title.lower().strip()

    if len(t) < 8:
        return False

    for bad in BAD_WORDS:
        if bad in t:
            return False

    if not any(good in t for good in GOOD_WORDS):
        return False

    return True


def get_published_after_24h() -> str:
    dt = datetime.now(timezone.utc) - timedelta(hours=24)
    return dt.isoformat(timespec="seconds").replace("+00:00", "Z")


def format_time(iso_time: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return iso_time


def get_youtube_videos() -> List[Dict]:
    videos = []
    seen_links = set()
    published_after = get_published_after_24h()

    for keyword in KEYWORDS:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": keyword,
            "type": "video",
            "maxResults": 8,
            "order": "date",
            "publishedAfter": published_after,
            "key": YOUTUBE_API_KEY,
        }

        try:
            r = requests.get(url, params=params, timeout=20)
            r.raise_for_status()
            data = r.json()

            for item in data.get("items", []):
                raw_title = item["snippet"]["title"]
                title = clean_title(raw_title)
                channel = html.unescape(item["snippet"]["channelTitle"])
                published_at = item["snippet"].get("publishedAt", "")
                video_id = item["id"]["videoId"]
                link = f"https://youtube.com/watch?v={video_id}"

                if link in seen_links:
                    continue
                if not is_good_video(title):
                    continue

                seen_links.add(link)

                videos.append({
                    "title_en": title,
                    "title_zh": translate_to_chinese(title),
                    "channel": channel,
                    "link": link,
                    "tag": classify_video(title),
                    "published_at": format_time(published_at)
                })

        except Exception:
            continue

    return videos[:5]


def wrap_text(text: str, line_length: int = 16) -> str:
    lines = []
    current = ""
    for ch in text:
        current += ch
        if len(current) >= line_length:
            lines.append(current)
            current = ""
    if current:
        lines.append(current)
    return "\n".join(lines[:4])


def create_cover_image(video: Dict, output_path: str = "cover.png") -> str:
    width, height = 1280, 720
    img = Image.new("RGB", (width, height), color=(14, 14, 18))
    draw = ImageDraw.Draw(img)

    # 背景装饰
    draw.rectangle((0, 0, width, 90), fill=(185, 28, 28))
    draw.rectangle((0, height - 90, width, height), fill=(120, 20, 20))
    draw.rectangle((70, 130, 1210, 610), outline=(255, 215, 0), width=4)

    # 字体
    try:
        font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 54)
        font_mid = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 34)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 26)
    except Exception:
        font_big = ImageFont.load_default()
        font_mid = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # 标题
    draw.text((60, 22), "BOCAI51", font=font_mid, fill=(255, 255, 255))

    # 中间标题
    title = wrap_text(video["title_zh"], 16)
    draw.multiline_text((110, 210), title, font=font_big, fill=(255, 255, 255), spacing=16)

    # 标签
    draw.rounded_rectangle((100, 560, 360, 620), radius=18, fill=(255, 215, 0))
    draw.text((120, 575), video["tag"], font=font_small, fill=(20, 20, 20))

    # 时间
    draw.text((930, 575), "24H HOT", font=font_mid, fill=(255, 255, 255))

    # 频道名
    channel_text = f'频道: {video["channel"][:28]}'
    draw.text((100, 645), channel_text, font=font_small, fill=(210, 210, 210))

    img.save(output_path)
    return output_path


def send_photo_with_caption(image_path: str, caption: str) -> None:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    with open(image_path, "rb") as photo:
        files = {"photo": photo}
        data = {
            "chat_id": CHANNEL,
            "caption": caption[:1024]
        }
        r = requests.post(url, data=data, files=files, timeout=30)
        r.raise_for_status()


def main() -> None:
    videos = get_youtube_videos()

    if not videos:
        fallback = "📺 今日博彩热门视频（最近24小时）\n\n最近24小时暂时没有抓到更精准的内容。"
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHANNEL, "text": fallback}, timeout=20).raise_for_status()
        return

    for i, video in enumerate(videos, 1):
        image_path = create_cover_image(video, f"cover_{i}.png")
        caption = (
            f'{video["tag"]}\n'
            f'标题：{video["title_zh"]}\n'
            f'频道：{video["channel"]}\n'
            f'时间：{video["published_at"]}\n'
            f'链接：{video["link"]}'
        )
        send_photo_with_caption(image_path, caption)


if __name__ == "__main__":
    main()
