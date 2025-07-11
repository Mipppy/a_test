from PyQt5.QtCore import Qt, QRectF, QPointF, QPoint
from PyQt5.QtGui import QPixmap, QPainter, QBrush, QPen, QImage, QColor, QFontMetrics
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsPixmapItem,
    QGraphicsEllipseItem,
    QGraphicsItemGroup,
    QLabel
)
import os, json, sys, time, typing
from typing import Dict, List, Union, Optional, Any, cast

def original_pos_to_pyqt5(x: int | float, y: int | float, use_floats:bool = False) -> QPoint | QPointF:
    x_real = x+15588.5
    y_real = y+8428
    
    if use_floats:
        return QPointF(x_real, y_real) 
    else:
        return QPoint(round(x_real), round(y_real))

def save_resource_to_cache(_json: dict,id: str | int) -> None:
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

    return [[label['id'],label['name']] for label in data["label_list"] ]

def get_all_ids() -> Dict[str, List[List[Union[int, str]]]]:
    full_data = {}
    for filename in os.listdir('data/official/'):
        if filename.endswith('.json') and 'full_dataset' not in filename:
            file_path = os.path.join('data/official/', filename)

            with open(file_path, 'r') as file:
                data = json.load(file)
            full_data[data['name']] = [[_id['id'], _id['name']] for _id in data['data']['label_list']]
    return full_data

class CompositeIcon(QGraphicsItemGroup):
    def __init__(self, base_image_path:str, overlay_image_path:str, position: QPoint | QPointF, item_data, size=100):
        super().__init__()
        self.setFlags(QGraphicsItemGroup.ItemIsSelectable)  
        self.setAcceptHoverEvents(True)  
        base_image = QImage(base_image_path)
        if base_image.isNull():
            print(f"Error: Failed to load base image {base_image_path}")
            return  

        base_pixmap = QPixmap.fromImage(base_image).scaled(
            size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        self.base_item = QGraphicsPixmapItem(base_pixmap)
        self.addToGroup(self.base_item)

        overlay_image = QImage(overlay_image_path)
        if overlay_image.isNull():
            print(f"Error: Failed to load overlay image {overlay_image_path}")
            return

        overlay_pixmap = QPixmap.fromImage(overlay_image).scaled(
            size // 2, size // 2, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        self.overlay_item = QGraphicsPixmapItem(overlay_pixmap)
        self.overlay_item.setPos(size // 5, size // 8)
        self.addToGroup(self.overlay_item)
        self.max_scale = 1.75
        self.min_scale = 0.02
        self.base_width = base_pixmap.width()
        self.base_height = base_pixmap.height()
        self.setPos(position.x() - (self.base_width / 2.5), position.y() - (self.base_height / 1.25))
        self.original_pos_x = position.x() - (self.base_width / 2.5)
        self.original_pos_y = position.y() - (self.base_height / 1.25)

    def mousePressEvent(self, event):
        print(f"Icon clicked at: {self.pos().x()}, {self.pos().y()}")
        self.setSelected(True)  
        max_z = max((item.zValue() for item in self.scene().items()), default=0)
        self.setZValue(max_z + 1)

        super().mousePressEvent(event)
    
    def scale_adjust_zoom(self, zoom_level):
        new_factor = max(self.min_scale, min(0.5 / (zoom_level), self.max_scale))
        scale_variable = 1 + (new_factor - self.min_scale) * (2 - 1) / (self.max_scale - self.min_scale)
        self.setScale(new_factor)
        self.setPos(self.original_pos_x - ((self.base_width*new_factor)-(53+(60*(scale_variable-1)))) + 5 , self.original_pos_y - ((self.base_height*new_factor)-(80+(45*(scale_variable-1)))) - 2)


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

    save_resource_to_cache(output_data, label_data['id'] if label_data else None)

    return output_data

def print_progress_bar(iteration, total, prefix='', suffix='', length=50, fill='█'):
    percent = ("{0:.1f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end='', flush=True)  
    if iteration == total:
        print()  

def resize_font_to_fit(label: QLabel, text: str, max_width:int):
    font = label.font()
    font_size = font.pointSize()

    while font_size > 1:
        font.setPointSize(font_size)
        metrics = QFontMetrics(font)
        if metrics.boundingRect(label.rect(), Qt.TextFlag.TextWordWrap, text).width() <= max_width:
            break
        font_size -= 1

    label.setFont(font)