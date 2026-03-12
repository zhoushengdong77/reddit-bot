import html
import os
import re
from datetime import datetime, timedelta, timezone
from typing import List, Dict

import requests
from googletrans import Translator

# Telegram
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL = "@BOCAI51"

# YouTube API
YOUTUBE_API_KEY = "AIzaSyDiht_MOJLgsSr18483KwtWtOE4xwtTjfs"

# 搜索关键词
KEYWORDS = [
    "gambling win",
    "casino jackpot",
    "blackjack win",
    "poker highlights",
    "sports betting tips"
]

# 不想要的词
BAD_WORDS = [
    "shorts",
    "#shorts",
    "live stream",
    "livestream"
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
        translated = result.text.strip()
        return translated if translated else text
    except Exception:
        return text


def classify_video(title: str) -> str:
    t = title.lower()

    if any(x in t for x in ["blackjack", "roulette", "slot", "slots", "casino", "jackpot"]):
        return "🎰【赌场赢奖】"
    if any(x in t for x in ["poker", "texas hold", "holdem"]):
        return "🃏【扑克】"
    if any(x in t for x in ["betting", "bet", "prediction", "predictions", "soccer", "football"]):
        return "⚽【体育下注】"
    return "📺【博彩视频】"


def is_good_video(title: str) -> bool:
    t = title.lower()

    for bad in BAD_WORDS:
        if bad in t:
            return False

    if len(t.strip()) < 8:
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

                zh_title = translate_to_chinese(title)

                videos.append({
                    "title_en": title,
                    "title_zh": zh_title,
                    "channel": channel,
                    "link": link,
                    "tag": classify_video(title),
                    "published_at": format_time(published_at)
                })

        except Exception as e:
            videos.append({
                "title_en": f"YouTube抓取失败：{str(e)}",
                "title_zh": f"YouTube抓取失败：{str(e)}",
                "channel": "系统",
                "link": "",
                "tag": "⚠️【错误】",
                "published_at": ""
            })

    return videos[:6]


def build_message(videos: List[Dict]) -> str:
    if not videos:
        return "📺 今日博彩热门视频\n\n最近24小时暂时没有抓到合适内容。"

    lines = ["📺 今日博彩热门视频（最近24小时）\n"]

    for v in videos:
        if v["link"]:
            lines.append(
                f'{v["tag"]}\n'
                f'中文：{v["title_zh"]}\n'
                f'原标题：{v["title_en"]}\n'
                f'频道：{v["channel"]}\n'
                f'时间：{v["published_at"]}\n'
                f'链接：{v["link"]}\n'
            )
        else:
            lines.append(f'{v["tag"]}\n{v["title_zh"]}\n')

    message = "\n".join(lines)

    if len(message) > 4000:
        message = message[:3900] + "\n\n......"

    return message


def send_telegram(message: str) -> None:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": CHANNEL,
        "text": message,
        "disable_web_page_preview": False
    }

    r = requests.post(url, data=data, timeout=20)
    r.raise_for_status()


def main() -> None:
    videos = get_youtube_videos()
    message = build_message(videos)
    send_telegram(message)


if __name__ == "__main__":
    main()
