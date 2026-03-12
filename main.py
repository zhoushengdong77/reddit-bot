import requests
import os

# Telegram
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL = "@BOCAI51"

# YouTube API
YOUTUBE_API_KEY = "AIzaSyDiht_MOJLgsSr18483KwtWtOE4xwtTjfs"

# 搜索关键词
KEYWORDS = [
    "gambling win",
    "casino big win",
    "sports betting tips",
    "poker highlights",
    "blackjack strategy"
]


def get_youtube_videos():

    videos = []

    for keyword in KEYWORDS:

        url = "https://www.googleapis.com/youtube/v3/search"

        params = {
            "part": "snippet",
            "q": keyword,
            "type": "video",
            "maxResults": 2,
            "key": YOUTUBE_API_KEY
        }

        try:

            r = requests.get(url, params=params)
            data = r.json()

            for item in data["items"]:

                title = item["snippet"]["title"]
                channel = item["snippet"]["channelTitle"]
                video_id = item["id"]["videoId"]

                link = f"https://youtube.com/watch?v={video_id}"

                text = f"🎥 {title}\n频道：{channel}\n{link}"

                videos.append(text)

        except Exception as e:
            videos.append(f"⚠️ YouTube抓取失败: {str(e)}")

    return videos[:5]


def send_telegram(message):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": CHANNEL,
        "text": message,
        "disable_web_page_preview": False
    }

    requests.post(url, data=data)


videos = get_youtube_videos()

message = "📺 今日博彩热门视频\n\n"

for v in videos:
    message += v + "\n\n"

send_telegram(message)
