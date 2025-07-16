import json
from typing import Dict, List
from PyQt5.QtGui import QIcon
class LoadedData:
    """
    Due to the datasets being 30MB or less, I found it worth it to just load everything into memory.
    This stores all the loaded datasets to avoid accidentally reloading them later.

    Class Attributes:
        official_dataset (dict): The official dataset containing 'point_list'.
        unofficial_dataset (dict): The unofficial dataset containing 'data' list.
        id_oid_dataset (dict): Maps official label IDs to unofficial label OIDs.
        official_id_to_unofficial_id (dict): Maps official object IDs to unofficial ones.
    """

    # Dataset vars
    official_dataset: dict = None
    unofficial_dataset: dict = None
    id_oid_dataset: dict = None
    official_id_to_unofficial_id: dict = None
    unofficial_btn_data: dict = None
    
    # Image vars
    qicon_paths: List[str] = [
        'images/resources/application/thumbs_up.png',
        'images/resources/application/thumbs_down.png'
    ]
    qicon_cache: Dict[str, QIcon] = {}

    @classmethod
    def init(cls):
        # Load and cache datasets
        try:
            with open('data/official/full/full_dataset.json', 'r', encoding='utf-8') as f:
                cls.official_dataset = json.load(f)
        except Exception as e:
            print(f"[error] Failed to load official dataset: {e}")

        try:
            with open('data/unofficial/location_data.json', 'r', encoding='utf-8') as f:
                cls.unofficial_dataset = json.load(f)
        except Exception as e:
            print(f"[error] Failed to load unofficial dataset: {e}")

        try:
            with open('application_data/official_unofficial_ids.json', 'r', encoding='utf-8') as f:
                cls.id_oid_dataset = json.load(f)
        except Exception as e:
            print(f"[warn] ID-OID dataset not loaded: {e}")

        try:
            with open('application_data/map_object_mapping.json', 'r', encoding='utf-8') as f:
                cls.official_id_to_unofficial_id = json.load(f)
        except Exception as e:
            print(f"[warn] Map object mapping not loaded: {e}")

        try:
            with open('data/unofficial/button_data.json', 'r', encoding='utf-8') as f:
                cls.unofficial_btn_data = json.load(f)
        except Exception as e:
            print(f"[error] Failed to load button data: {e}")
            
        try:
        # Load and cache images
            for path in cls.qicon_paths:
                filename = path.split('/')[-1]
                if filename not in cls.qicon_cache:
                    cls.qicon_cache[filename] = QIcon(path)
        except Exception as e:
            print(f"[error] Failed to load icon cache")
            
