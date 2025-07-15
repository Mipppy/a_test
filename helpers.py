from PyQt5.QtCore import Qt, QRectF, QPointF, QPoint, QSize
from PyQt5.QtGui import QPixmap, QPainter, QBrush, QPen, QImage, QColor, QFontMetrics, QFont
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsPixmapItem,
    QGraphicsEllipseItem,
    QGraphicsItemGroup,
    QLabel,
    QProgressBar,
    QWidget,
    QGraphicsRectItem,
    QGraphicsTextItem
)
import os
import json
import sys
import time
import typing
import math
from typing import Dict, List, Union, Optional, Any, cast
from collections import OrderedDict

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
    with open('data/official/full_dataset.json', "r") as file:
        data = json.load(file)

    return [[label['id'], label['name']] for label in data["label_list"]]


def get_all_ids() -> Dict[str, List[List[Union[int, str]]]]:
    full_data = {}
    for filename in os.listdir('data/official/'):
        if filename.endswith('.json') and 'full_dataset' not in filename:
            file_path = os.path.join('data/official/', filename)

            with open(file_path, 'r') as file:
                data = json.load(file)
            full_data[data['name']] = [[_id['id'], _id['name']]
                                       for _id in data['data']['label_list']]
    return full_data



def gimmie_data(id: int) -> Dict[str, Optional[Any]]:
    with open('data/official/full/full_dataset.json', "r") as file:
        data: Dict[str, Dict[Any]] = json.load(file)

    label_data: Optional[Dict[str, Any]] = next(
        (label for label in data["label_list"] if cast(dict, label).get("id") == id), None)

    pos_data: List[Dict[str, Any]] = [
        point for point in data["point_list"] if cast(dict, point).get("label_id") == id
    ]

    output_data: Dict[str, Optional[Any]] = {
        "label": label_data,
        "point": pos_data
    }

    # save_resource_to_cache(output_data, label_data['id'] if label_data else None)

    return output_data


def reverse_linear_mapping(x: int | float, min_val: int | float=0.01, max_val: int | float =40, x_min: int | float=0.02, x_max=1.75):
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


