"""Database of popular iOS apps and the domains they use."""

IOS_APPS = {
    # SNS
    "Instagram": {
        "icon": "📷",
        "category": "SNS",
        "domains": [
            "instagram.com",
            "i.instagram.com",
            "graph.instagram.com",
            "cdninstagram.com",
            "scontent.cdninstagram.com",
        ],
    },
    "TikTok": {
        "icon": "🎵",
        "category": "SNS",
        "domains": [
            "tiktok.com",
            "tiktokv.com",
            "ttwstatic.com",
            "musical.ly",
            "byteoversea.com",
            "ibytedtos.com",
            "ipstatp.com",
        ],
    },
    "X (Twitter)": {
        "icon": "🐦",
        "category": "SNS",
        "domains": [
            "twitter.com",
            "x.com",
            "t.co",
            "twimg.com",
            "abs.twimg.com",
            "api.twitter.com",
        ],
    },
    "Facebook": {
        "icon": "👤",
        "category": "SNS",
        "domains": [
            "facebook.com",
            "fb.com",
            "fbcdn.net",
            "facebook.net",
            "graph.facebook.com",
        ],
    },
    "Snapchat": {
        "icon": "👻",
        "category": "SNS",
        "domains": [
            "snapchat.com",
            "snap.com",
            "sc-cdn.net",
            "snapchat.com.cdn.cloudflare.net",
        ],
    },
    "LINE": {
        "icon": "💬",
        "category": "SNS",
        "domains": [
            "line.me",
            "line-apps.com",
            "line-scdn.net",
            "naver.jp",
            "obs.line-apps.com",
        ],
    },
    # 動画
    "YouTube": {
        "icon": "▶️",
        "category": "動画",
        "domains": [
            "youtube.com",
            "youtu.be",
            "googlevideo.com",
            "ytimg.com",
            "yt3.ggpht.com",
            "youtube-nocookie.com",
        ],
    },
    "Netflix": {
        "icon": "🎬",
        "category": "動画",
        "domains": [
            "netflix.com",
            "nflximg.net",
            "nflximg.com",
            "nflxvideo.net",
            "nflxso.net",
        ],
    },
    "TVerなどAbema": {
        "icon": "📺",
        "category": "動画",
        "domains": [
            "abema.tv",
            "abema.io",
            "ameba.jp",
            "hayabusa.io",
        ],
    },
    "Prime Video": {
        "icon": "📦",
        "category": "動画",
        "domains": [
            "primevideo.com",
            "amazon.com",
            "aiv-cdn.net",
            "media-amazon.com",
        ],
    },
    # ゲーム
    "Fortnite": {
        "icon": "🎮",
        "category": "ゲーム",
        "domains": [
            "epicgames.com",
            "fortnite.com",
            "unrealengine.com",
        ],
    },
    "Minecraft": {
        "icon": "⛏️",
        "category": "ゲーム",
        "domains": [
            "minecraft.net",
            "mojang.com",
            "minecraftservices.com",
        ],
    },
    "PUBG Mobile": {
        "icon": "🔫",
        "category": "ゲーム",
        "domains": [
            "pubg.com",
            "pubgmobile.com",
        ],
    },
    # ショッピング
    "Amazon": {
        "icon": "🛒",
        "category": "ショッピング",
        "domains": [
            "amazon.co.jp",
            "amazon.com",
            "amazonwebservices.com",
            "ssl-images-amazon.com",
            "media-amazon.com",
        ],
    },
    "メルカリ": {
        "icon": "🏷️",
        "category": "ショッピング",
        "domains": [
            "mercari.com",
            "mercdn.net",
            "fril.jp",
        ],
    },
    # ニュース
    "Yahoo! Japan": {
        "icon": "🗞️",
        "category": "ニュース",
        "domains": [
            "yahoo.co.jp",
            "yimg.jp",
            "yahooapis.jp",
        ],
    },
    # その他
    "Discord": {
        "icon": "🎧",
        "category": "その他",
        "domains": [
            "discord.com",
            "discordapp.com",
            "discordapp.net",
            "discord.gg",
            "discord.media",
        ],
    },
    "Reddit": {
        "icon": "🤖",
        "category": "その他",
        "domains": [
            "reddit.com",
            "redd.it",
            "redditmedia.com",
            "redditstatic.com",
        ],
    },
    "Spotify": {
        "icon": "🎵",
        "category": "その他",
        "domains": [
            "spotify.com",
            "scdn.co",
            "spotifycdn.com",
        ],
    },
    "Twitch": {
        "icon": "🟣",
        "category": "その他",
        "domains": [
            "twitch.tv",
            "twitchsvc.net",
            "jtvnw.net",
            "twitchapps.com",
        ],
    },
}


def get_all_blocked_domains(app_names: list[str]) -> set[str]:
    """Return all domains for the given app names."""
    domains = set()
    for name in app_names:
        if name in IOS_APPS:
            domains.update(IOS_APPS[name]["domains"])
    return domains


def get_categories() -> dict[str, list[str]]:
    """Return apps grouped by category."""
    cats: dict[str, list[str]] = {}
    for name, info in IOS_APPS.items():
        cat = info["category"]
        cats.setdefault(cat, []).append(name)
    return cats
