from PyQt5.QtCore import Qt, QPointF, QPoint
from PyQt5.QtGui import QPixmap, QFontMetrics, QIcon
from PyQt5.QtWidgets import (
    QLabel
)
import os
import json
from typing import Dict, List, Union, Optional, Any, cast
import requests

from loaded_data import LoadedData

"""
These are 100% magic numbers, but before you get mad at me and say: "Gasp! Magic Numbers! The Horror!"
hear me out.  These are neccessary.

So when pulling the data from the Hoyolab's interactive map, I knew that coordinates would be an issue.
The coordinate plane that Hoyolab on the HTML canvas was of course going to be different than the one provided by PYQT5.
So, to avoid going through and manually editting all the data, it would be easier to simply get something rendered, and then compare how off it was
My 2 points of reference were the teleport waypoint in Sumeru city, as it allowed me to make a rough idea, but to get the final values,
I compared the positions of Crimson Agate #9631 on the Hoyolab Interactive map to mine, eventually getting the magic numbers here.
"""
MYSTICAL_MAGICAL_X = 15595
MYSTICAL_MAGICAL_Y = 8430


def original_pos_to_pyqt5(x: int | float, y: int | float, use_floats: bool = False) -> QPoint | QPointF:
    x_real = x + MYSTICAL_MAGICAL_X
    y_real = y + MYSTICAL_MAGICAL_Y

    if use_floats:
        return QPointF(x_real, y_real)
    else:
        return QPoint(round(x_real), round(y_real))


def save_resource_to_cache(_json: dict, id: str | int) -> None:
    with open(f"cache/{id}.json", "w") as output_file:
        json.dump(_json, output_file, indent=4)


def clear_cache() -> None:
    for filename in os.listdir('cache/'):
        file_path = os.path.join('cache/', filename)
        if os.path.isfile(file_path):
            os.remove(file_path)


def get_all_ids_large_list() -> List[List[Union[int, str]]]:
    return [
        [label['id'], label['name']]
        for label in LoadedData.official_dataset.get("label_list", [])
    ]


def get_all_ids() -> Dict[str, List[List[Union[int, str]]]]:
    # FUTURE .40s TIME SAVE BY CREATING A FILE WITH IDS MAPPED TO NAMES.
    full_data = {}
    for filename in os.listdir('data/official/'):
        if filename.endswith('.json') and 'full_dataset' not in filename:
            file_path = os.path.join('data/official/', filename)
            with open(file_path, 'r') as file:
                data = json.load(file)
            full_data[data['name']] = [[_id['id'], _id['name']]
                                       for _id in data['data']['label_list']]
    return full_data


def gimmie_data(label_id: int) -> Dict[str, Optional[Any]]:
    """
    Given a label ID, returns its metadata and associated point data from memory.
    """
    LoadedData.init()
    full_data = LoadedData.official_dataset

    label_data = next(
        (label for label in full_data.get("label_list", []) if cast(dict, label).get("id") == label_id),
        None
    )

    pos_data = [
        point for point in full_data.get("point_list", [])
        if cast(dict, point).get("label_id") == label_id
    ]

    return {
        "label": label_data,
        "point": pos_data
    }


def reverse_linear_mapping(x: int | float, min_val: int | float = 0.01, max_val: int | float = 40, x_min: int | float = 0.02, x_max=1.75):
    x_clamped = max(x_min, min(x_max, x))
    normalized = (x_max - x_clamped) / (x_max - x_min)
    return min_val + normalized * (max_val - min_val)


def resize_font_to_fit(label: QLabel, text: str, max_width: int):
    font = label.font()
    font_size = font.pointSize()

    while font_size > 1:
        font.setPointSize(font_size)
        metrics = QFontMetrics(font)
        if metrics.boundingRect(label.rect(), Qt.TextFlag.TextWordWrap, text).width() <= max_width:
            break
        font_size -= 1

    label.setFont(font)


from difflib import get_close_matches

def generate_id_to_oid_mapping(dataset1_path: str, dataset2_path: str, output_path: str) -> None:

    name_to_oid = {name: oid for oid, name in LoadedData.unofficial_btn_data.items() if isinstance(name, str)}

    id_to_oid = {}
    unmatched_labels = []
    label_list = LoadedData.official_dataset.get("label_list", [])
    for entry in label_list:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        id_ = entry.get("id")
        if name in name_to_oid:
            id_to_oid[str(id_)] = name_to_oid[name]
        else:
            unmatched_labels.append((id_, name))

    used_oids = set(id_to_oid.values())
    remaining_names = [name for name in name_to_oid if name_to_oid[name] not in used_oids]

    still_unmatched = []
    for id_, name in unmatched_labels:
        matches = get_close_matches(name, remaining_names, n=1, cutoff=0.5)
        if matches:
            best = matches[0]
            id_to_oid[str(id_)] = name_to_oid[best]
            remaining_names.remove(best)
        else:
            still_unmatched.append((id_, name))

    for id_, name in still_unmatched:
        if not remaining_names:
            print(f"[WARN] Out of fallback names for id {id_} ('{name}')")
            continue
        forced = remaining_names.pop(0)
        id_to_oid[str(id_)] = name_to_oid[forced]
        print(f"[FORCED] Assigned '{name}' (id {id_}) to fallback '{forced}'")

    with open(output_path, 'w', encoding='utf-8') as fout:
        json.dump(id_to_oid, fout, indent=2, ensure_ascii=False)

    print(f"[✔] Saved {len(id_to_oid)} entries to {output_path}")
    print(f"[ℹ] Total input entries: {len(label_list)}, Mapped: {len(id_to_oid)}")

def convert_id_or_oid(value: Union[int, str]) -> Union[int, str, None]:
    if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
        return LoadedData.id_oid_dataset.get(str(value))
    elif isinstance(value, str):
        for k, v in LoadedData.id_oid_dataset.items():
            if v == value:
                return int(k)
    return None

def transform_x_to_y(x: float) -> float:
    a = -0.9954
    b = 94203.8
    return a * x + b



def map_all_ids_by_xpos(
    output_path: str = "application_data/map_object_mapping.json",
) -> Dict[int, int]:
    """
    Loops through all unique label_ids in dataset A, converts each to unofficial type using convert_id_or_oid,
    and maps each A.id to B.id by sorting by x_pos and breaking ties by y_pos. Saves combined mapping to file.
    """
    points_a = LoadedData.official_dataset.get("point_list", [])
    points_b = LoadedData.unofficial_dataset.get("data", [])

    full_mapping = {}
    label_ids = sorted({p['label_id'] for p in points_a})

    for label_id in label_ids:
        converted = convert_id_or_oid(label_id)
        if not isinstance(converted, str):
            continue
        converted = converted.replace('btn-', '')

        filtered_a = [p for p in points_a if p['label_id'] == label_id]
        filtered_b = [r for r in points_b if len(r) > 1 and r[1] == converted and r[2] == 2]
        if not filtered_a or not filtered_b:
            print(f"[skip] No matches for label_id {label_id} -> {converted} (A: {len(filtered_a)}, B: {len(filtered_b)})")
            continue

        print(f"Mapping label_id={label_id} to {converted} with {len(filtered_a)} A items and {len(filtered_b)} B items")

        # Sort A by x_pos, y_pos
        sorted_a = sorted(filtered_a, key=lambda obj: (obj['x_pos'], obj.get('y_pos', 0)))
        # Sort B by lng (index 4)
        sorted_b = sorted(filtered_b, key=lambda arr: arr[4])

        if len(sorted_a) != len(sorted_b):
            print(f"[warning] Length mismatch for label_id {label_id}: A={len(sorted_a)}, B={len(sorted_b)}")

        for i, (a_obj, b_arr) in enumerate(zip(sorted_a, sorted_b)):
            print(f"Mapping {i}: A.id={a_obj['id']} -> B.id={b_arr[0]} (x_pos={a_obj['x_pos']}, y_pos={a_obj.get('y_pos', 'n/a')}, lng={b_arr[4]})")
            full_mapping[a_obj['id']] = b_arr[0]

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(full_mapping, f, ensure_ascii=False, indent=2)

    print(f"\nTotal mapped: {len(full_mapping)}")
    return full_mapping


def get_icon_from_url(url) -> QIcon:
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.content
        pixmap = QPixmap()
        pixmap.loadFromData(data)
        return QIcon(pixmap)
    except Exception as e:
        print(f"Failed to load icon from URL {url}: {e}")
        return None



def get_pixmap_from_url(url: str) -> QPixmap | None:
    try:
        if not url:
            return None
        response = requests.get(url)
        response.raise_for_status()
        image_data = response.content
        pixmap = QPixmap()
        if pixmap.loadFromData(image_data):
            return pixmap
        else:
            return None
    except Exception as e:
        return None

