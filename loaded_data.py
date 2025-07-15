import json, time

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

    official_dataset: dict = None
    unofficial_dataset: dict = None
    id_oid_dataset: dict = None
    official_id_to_unofficial_id: dict = None
    unofficial_btn_data: dict = None

    @classmethod
    def init(cls,
             official_path: str = 'data/official/full/full_dataset.json',
             unofficial_path: str = 'data/unofficial/location_data.json',
             id_oid_path: str = 'application_data/official_unofficial_ids.json',
             object_id_map_path: str = 'application_data/map_object_mapping.json',
             unofficial_btn_path:str = 'data/unofficial/button_data.json'
             ):
        with open(official_path, 'r', encoding='utf-8') as f:
            cls.official_dataset = json.load(f)

        with open(unofficial_path, 'r', encoding='utf-8') as f:
            cls.unofficial_dataset = json.load(f)
        try:
            with open(id_oid_path, 'r', encoding='utf-8') as f:
                cls.id_oid_dataset = json.load(f)
        except:
            None
        with open(object_id_map_path, 'r', encoding='utf-8') as f:
            cls.official_id_to_unofficial_id = json.load(f)
        
        with open(unofficial_btn_path, 'r', encoding='utf-8') as f:
            cls.unofficial_btn_data = json.load(f)
