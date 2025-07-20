import datetime
import json
from async_requests import AsyncRequests
from menu import ButtonPanel
from loaded_data import LoadedData

class UnofficialDataLoader:
    image_loading_url = "https://game-cdn.appsample.com/"
    
    @classmethod
    async def load_unofficial_data(cls, _id: int, label_id: int):
        oid = LoadedData.id_oid_dataset.get(str(label_id))
        uid = LoadedData.official_id_to_unofficial_id.get(str(_id))
        if not oid or not uid:
            print(f"Invalid OID or UID for label_id={label_id}, _id={_id}")
            return
        print(oid)
        url = "https://cache-v2.lemonapi.com/comments/v2"
        params = {
            "app": "gim",
            "ttl": 7000,
            "collection": oid,
            "docId": uid,
            "sort": "",
            "page": 1,
            "pageSize": 100
        }
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://genshin-impact-map.appsample.com",
            "Referer": "https://genshin-impact-map.appsample.com/",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0"
        }

        from urllib.parse import urlencode
        query_str = urlencode({k: list(v) if isinstance(v, set) else v for k, v in params.items()})
        full_url = f"{url}?{query_str}"

        try:
            response_text = await AsyncRequests.get(full_url, headers=headers)
            data = json.loads(response_text)
        except Exception as e:
            print(f"Failed to load unofficial data: {e}")
            return
        comments = data.get("data", {}).get("comments", [])
        for comment in comments:
            username = comment.get("aname", "Anonymous")
            text = comment.get("content", "")
            time_raw = comment.get("time", "")
            votes = comment.get("vote", 0)
            image = comment.get("image", "")

            try:
                dt = datetime.datetime.fromisoformat(time_raw.replace("Z", "+00:00"))
                date = dt.strftime("%Y-%m-%d")
            except Exception:
                date = "Unknown"

            image_path = cls.image_loading_url.rstrip('/') + image if image else None
            ButtonPanel.add_comment_card(image_path, text, username, date, like_count=votes)
