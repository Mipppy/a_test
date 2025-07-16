import requests


class Updater:
    update_url = "https://api.github.com/repos/Mipppy/a_test/releases/latest"
    version_path = "application_data/version"
    VERSION = "v0.0.1-alpha"
    @classmethod
    def check_for_updates(cls):
        res = requests.get(cls.update_url)
        res_json:dict = res.json()
        if res.ok:
            if res_json['name'] != cls.VERSION:
                cls.handle_update(res_json)
    
    @classmethod
    def handle_update(cls, json: dict):
        print('updating')