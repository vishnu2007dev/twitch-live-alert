"""Send a Discord message when a Twitch channel goes live (on GTA by default)."""
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

CHANNEL = os.environ.get("CHANNEL", "asianjeff")
GAME_FILTER = os.environ.get("GAME_FILTER", "Grand Theft Auto")  # empty = alert for any game
STATE = Path("state.txt")  # remembers which stream we already alerted for


def http(url, data=None, headers=None):
    headers = {"User-Agent": "twitch-live-alert/1.0", **(headers or {})}
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as r:
        body = r.read()
        return json.loads(body) if body else {}


client_id = os.environ["TWITCH_CLIENT_ID"]
token = http("https://id.twitch.tv/oauth2/token", data=urllib.parse.urlencode({
    "client_id": client_id,
    "client_secret": os.environ["TWITCH_CLIENT_SECRET"],
    "grant_type": "client_credentials",
}).encode())["access_token"]

streams = http(f"https://api.twitch.tv/helix/streams?user_login={CHANNEL}",
               headers={"Client-Id": client_id, "Authorization": f"Bearer {token}"})["data"]

if not streams:
    print(f"{CHANNEL} is offline")
    raise SystemExit

s = streams[0]
print(f"{CHANNEL} is live: {s['game_name']} | {s['title']}")

if GAME_FILTER and GAME_FILTER.lower() not in s["game_name"].lower():
    print("live, but not on the right game yet")
    raise SystemExit

if STATE.exists() and STATE.read_text().strip() == s["id"]:
    print("already alerted for this stream")
    raise SystemExit

message = {"content": f"🔴 **{s['user_name']} is LIVE on {s['game_name']}!**\n"
                      f"{s['title']}\nhttps://twitch.tv/{CHANNEL}"}
http(os.environ["DISCORD_WEBHOOK_URL"], data=json.dumps(message).encode(),
     headers={"Content-Type": "application/json"})
STATE.write_text(s["id"])
print("alert sent")
