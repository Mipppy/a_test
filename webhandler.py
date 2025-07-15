import requests
from typing import List, Dict

class WebHandler:
    """
    Handles interfacing with web sources 
    """
    unofficial_obj_data_cache: Dict[int |str, List["LoadedUnofficialData"]] = {}
    
    @classmethod
    def load_unofficial_data(oid: str, _id: int|str):
        LoadedUnofficialData(oid=oid, _id=_id)

class LoadedUnofficialData:
    def __init__(self, oid: str, _id:str|int):
        self.oid = oid
        self._id = _id
    
    