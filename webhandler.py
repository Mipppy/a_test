import requests
from typing import List, Dict
import datetime

from loaded_data import LoadedData
from menu import ButtonPanel

class WebHandler:
    """
    Handles interfacing with web sources 
    """
    unofficial_obj_data_cache: Dict[int, List["LoadedUnofficialData"]] = {}
    
    @classmethod
    def load_unofficial_data(cls,  _id: int, label_id:int):
        LoadedUnofficialData(_id=_id, label_id=label_id)
class LoadedUnofficialData:
    def __init__(self, _id: int, label_id:int):
        self.label_id = label_id
        self._id = _id
        self.oid = LoadedData.id_oid_dataset.get(str(self.label_id))
        self.uid = LoadedData.official_id_to_unofficial_id.get(str(self._id))
        self.image_loading_url = "https://game-cdn.appsample.com/"
        self.req = requests.get("https://cache-v2.lemonapi.com/comments/v2", params={"app":"gim","ttl":7000,"collection":{self.oid},"docId":{self.uid},"sort":"","page":1,"pageSize":100}, headers={"Accept":"application/json, text/plain, */*","Origin":"https://genshin-impact-map.appsample.com","Referer":"https://genshin-impact-map.appsample.com/","User-Agent":"Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0"})
        self.parseRequestData(self.req)
    
    def parseRequestData(self, req: requests.Response):
        self.json = req.json()
        for comment in self.json.get("data", {}).get("comments", []):
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

            if image:
                image_path = self.image_loading_url.rstrip('/') + image
                print(image_path)
            else:
                image_path = None 

            ButtonPanel.add_comment_card(image_path, text, username, date, like_count=votes)
