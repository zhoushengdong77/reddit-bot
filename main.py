import os
BOT_TOKEN = os.environ["BOT_TOKEN"]

# 你的频道
CHANNEL = "@BOCAI51"

# 要抓取的 Reddit 板块
subreddits = [
    "sportsbook",
    "gambling",
    "problemgambling"
]


def get_posts():
    posts = []

    for sub in subreddits:
        url = f"https://www.reddit.com/r/{sub}/hot.json?limit=5"

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        try:
            r = requests.get(url, headers=headers)
            data = r.json()

            for p in data["data"]["children"]:
                title = p["data"]["title"]
                link = "https://reddit.com" + p["data"]["permalink"]

                posts.append(f"📌 {title}\n{link}")

        except:
            continue

    return posts[:5]


def send_telegram(text):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": CHANNEL,
        "text": text,
        "disable_web_page_preview": False
    }

    requests.post(url, data=data)


posts = get_posts()

message = "📊 Reddit 博彩讨论热点\n\n"

for p in posts:
    message += p + "\n\n"

send_telegram(message)
