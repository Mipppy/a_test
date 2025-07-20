from async_requests import AsyncRequests 

class Updater:
    update_url = "https://api.github.com/repos/Mipppy/a_test/releases/latest"
    version_path = "application_data/version"
    VERSION = "v0.0.1-alpha"

    @classmethod
    async def check_for_updates(cls):
        try:
            response_text = await AsyncRequests.get(cls.update_url)
            res_json = None
            import json
            try:
                res_json = json.loads(response_text)
            except Exception as e:
                print(f"Failed to parse update JSON: {e}")
                return

            if res_json and 'name' in res_json and res_json['name'] != cls.VERSION:
                await cls.handle_update(res_json)
            else:
                print("No update found or version matches.")
        except Exception as e:
            print(f"Update check failed: {e}")

    @classmethod
    async def handle_update(cls, json: dict):
        print("Updating...")
