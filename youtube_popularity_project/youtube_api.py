"""Fetch public video metadata using the official YouTube Data API v3."""
import json
import re
from urllib.parse import urlparse, parse_qs, urlencode
from urllib.request import urlopen
from urllib.error import HTTPError, URLError

VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")

def extract_video_id(value):
    value = value.strip()
    if VIDEO_ID_RE.fullmatch(value):
        return value
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    if host == "youtu.be":
        candidate = parsed.path.strip("/").split("/")[0]
    elif host in ("youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"):
        parts = parsed.path.strip("/").split("/")
        candidate = (parse_qs(parsed.query).get("v") or [""])[0] if parts[0] == "watch" else (parts[1] if len(parts)>1 and parts[0] in ("shorts", "live", "embed") else "")
    else:
        candidate = ""
    if not VIDEO_ID_RE.fullmatch(candidate):
        raise ValueError("Enter a valid YouTube watch, Shorts, live or youtu.be URL.")
    return candidate

def fetch_video(url, api_key):
    video_id = extract_video_id(url)
    endpoint = "https://www.googleapis.com/youtube/v3/videos?" + urlencode({"part":"snippet,statistics,contentDetails", "id":video_id,"key":api_key})
    try:
        with urlopen(endpoint, timeout=15) as response:
            data = json.load(response)
    except HTTPError as exc:
        try:
            message = json.load(exc).get("error",{}).get("message",str(exc))
        except Exception:
            message = str(exc)
        raise ValueError("YouTube API error: " + message) from exc
    except (URLError,TimeoutError) as exc:
        raise ValueError("Could not connect to YouTube API: " + str(exc)) from exc
    items = data.get("items",[])
    if not items:
        raise ValueError("Video not found or not accessible with this API key.")
    item=items[0]
    stats=item.get("statistics",{})
    snippet=item.get("snippet",{})
    details=item.get("contentDetails",{})
    return {"id":video_id,"title":snippet.get("title","Untitled"),"channel":snippet.get("channelTitle","Unknown"),"published":snippet.get("publishedAt",""),"thumbnail":snippet.get("thumbnails",{}).get("high",{}).get("url"),"views":int(stats.get("viewCount",0)),"likes":int(stats["likeCount"]) if "likeCount" in stats else None,"comments":int(stats["commentCount"]) if "commentCount" in stats else None,"duration":details.get("duration",""),"tags":snippet.get("tags",[]),"url":"https://www.youtube.com/watch?v="+video_id}
