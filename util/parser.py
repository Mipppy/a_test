import json

from helpers import save_resource_to_cache

def gimmie_data(id: int) -> dict:
    with open('data/official/full_dataset.json', "r") as file:
        data = json.load(file)

    label_data = next((label for label in data["label_list"] if label.get("id") == id), None)

    pos_data = [point for point in data["point_list"] if point.get("label_id") == id]

    output_data = {
        "label": label_data,
        "point": pos_data
    }

    save_resource_to_cache(output_data,label_data['id'])

    return output_data

