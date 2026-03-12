import os
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL = "@BOCAI51"

SUBREDDITS = [
    "sportsbook",
    "gambling",
    "problemgambling"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def get_posts():
    posts = []

    for sub in SUBREDDITS:
        url = f"https://www.reddit.com/r/{sub}/hot.json?limit=5"

        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            r.raise_for_status()
            data = r.json()

            children = data.get("data", {}).get("children", [])

            for item in children:
                post_data = item.get("data", {})
                title = post_data.get("title", "").strip()
                permalink = post_data.get("permalink", "").strip()

                if title and permalink:
                    link = "https://reddit.com" + permalink
                    posts.append(f"📌 {title}\n{link}")

        except Exception as e:
            posts.append(f"⚠️ r/{sub} 抓取失败：{e}")

    return posts[:5]


def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": CHANNEL,
        "text": text,
        "disable_web_page_preview": False
    }

    r = requests.post(url, data=data, timeout=20)
    r.raise_for_status()


def main():
    posts = get_posts()

    if not posts:
        message = "📊 Reddit 热门讨论\n\n今天暂时没有抓到内容。"
    else:
        message = "📊 Reddit 热门讨论\n\n" + "\n\n".join(posts)

    if len(message) > 4000:
        message = message[:3900] + "\n\n......"

    send_telegram(message)


if __name__ == "__main__":
    main()
