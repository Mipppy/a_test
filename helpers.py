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
    QProgressBar
)
import os, json, sys, time, typing, math
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

def original_pos_to_pyqt5(x: int | float, y: int | float, use_floats:bool = False) -> QPoint | QPointF:
    x_real = x + MYSTICAL_MAGICAL_X
    y_real = y + MYSTICAL_MAGICAL_Y
    
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

class ImageCacheManager:
    _max_cache_size = 25
    _overlay_cache = OrderedDict()
    _base_cache = OrderedDict()

    @classmethod
    def _get_pixmap(cls, cache, image_path: str, target_size: QSize) -> QPixmap:
        key = (image_path, target_size.width(), target_size.height())

        if key in cache:
            cache.move_to_end(key)
            return cache[key]

        image = QImage(image_path)
        if image.isNull():
            print(f"Error: Failed to load image {image_path}")
            return QPixmap()

        pixmap = QPixmap.fromImage(image).scaled(
            target_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        cache[key] = pixmap
        if len(cache) > cls._max_cache_size:
            cache.popitem(last=False)
        return pixmap

    @classmethod
    def get_base_pixmap(cls, image_path: str, target_size: QSize) -> QPixmap:
        return cls._get_pixmap(cls._base_cache, image_path, target_size)

    @classmethod
    def get_overlay_pixmap(cls, image_path: str, target_size: QSize) -> QPixmap:
        return cls._get_pixmap(cls._overlay_cache, image_path, target_size)
class CompositeIcon(QGraphicsItemGroup):
    def __init__(self, base_image_path: str, overlay_image_path: str, position: QPointF, item_data=None, size=100, zoom_level: float = 1):
        super().__init__()
        self.setFlags(QGraphicsItemGroup.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)

        self.anchor_offset = QPointF(63.5, 110)
        base_target_size = QSize(size, size)
        base_pixmap = ImageCacheManager.get_base_pixmap(base_image_path, base_target_size)

        if base_pixmap.isNull():
            print(f"Error: Failed to load base pixmap {base_image_path}")
            return

        original_width = base_pixmap.width()
        original_height = base_pixmap.height()

        scale_factor = size / max(original_width, original_height)
        self.scaled_anchor = self.anchor_offset * scale_factor

        self.base_item = QGraphicsPixmapItem(base_pixmap)
        self.addToGroup(self.base_item)

        overlay_size = QSize(int(size * 0.65), int(size * 0.65))
        overlay_pixmap = ImageCacheManager.get_overlay_pixmap(overlay_image_path, overlay_size)

        self.overlay_item = QGraphicsPixmapItem(overlay_pixmap)
        self.overlay_item.setParentItem(self.base_item)

        overlay_x = (base_pixmap.width() - overlay_pixmap.width()) / 2
        overlay_y = ((base_pixmap.height() - overlay_pixmap.height()) / 2) - (base_pixmap.height() / 10)
        self.overlay_item.setPos(overlay_x, overlay_y)

        self.addToGroup(self.overlay_item)

        self.base_width = base_pixmap.width()
        self.base_height = base_pixmap.height()
        self.item_data = item_data

        self.min_scale = 0.02
        self.max_scale = 1.75
        self.current_scale = scale_factor
        self.setTransformOriginPoint(self.anchor_offset)
        self.setScale(scale_factor)
        self.zoom_level = zoom_level
        
        self.logical_anchor_pos = position
        self.update_position()

    def update_position(self):
        # A reverse linear function seems to correct the displacement from the zoom.
        # Why I need to divide by 2 for the x is beyond me, but looking at the pixel placements it appears to be correct.
        adjusted_x = reverse_linear_mapping(self.zoom_level)
        self.setPos(self.logical_anchor_pos - self.anchor_offset + QPointF(adjusted_x / 2, adjusted_x))

    def scale_adjust_zoom(self, zoom_level):
        scale_factor = max(self.min_scale, min(0.5 / (zoom_level), self.max_scale))
        self.setScale(scale_factor)
        self.zoom_level = zoom_level
        self.update_position()

    def mousePressEvent(self, event):
        self.setSelected(True)
        max_z = max((item.zValue() for item in self.scene().items()), default=0)
        self.setZValue(max_z + 1)
        super().mousePressEvent(event)


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

def print_progress_bar(iteration, total, prefix='', suffix='', length=50, fill='█'):
    percent = ("{0:.1f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end='', flush=True)  
    if iteration == total:
        print()  

def reverse_linear_mapping(x, min_val=0.01, max_val=40, x_min=0.02, x_max=1.75):
    x_clamped = max(x_min, min(x_max, x))
    normalized = (x_max - x_clamped) / (x_max - x_min)
    return min_val + normalized * (max_val - min_val)

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
    
class CustomRoundedProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextVisible(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFont(QFont("Arial", weight=QFont.Weight.Bold))
        self.setMinimumHeight(18)
        self.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #f0f0f0;
                color: black;
            }
        """)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        radius = 6
        bar_rect = self.rect().adjusted(1, 1, -1, -1)
        chunk_color = QColor("#007bff")
        bg_color = QColor("#f0f0f0")

        painter.setBrush(bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(bar_rect, radius, radius)

        progress_ratio = (self.value() - self.minimum()) / (self.maximum() - self.minimum() or 1)
        chunk_width = int(bar_rect.width() * progress_ratio)

        if chunk_width > 0:
            chunk_rect = QRectF(bar_rect.left(), bar_rect.top(), chunk_width, bar_rect.height())

            if self.value() >= self.maximum():
                painter.setBrush(chunk_color)
                painter.drawRoundedRect(chunk_rect, radius, radius)
            else:
                path = QRectF(chunk_rect)
                painter.setBrush(chunk_color)
                painter.setPen(Qt.PenStyle.NoPen)

                painter.save()
                painter.setClipRect(chunk_rect)
                painter.drawRoundedRect(chunk_rect.adjusted(0, 0, radius, 0), radius, radius)
                painter.restore()

        if self.isTextVisible():
            text = self.text()
            painter.setPen(QColor("black"))
            painter.setFont(self.font())
            painter.drawText(bar_rect, Qt.AlignmentFlag.AlignCenter, text)


class BasicGrouping:
    _removed_obj_cache: dict = {}
    def __init__(self):
        pass
        
    @classmethod
    def save_object_point(cls, obj_id: int, obj_pos: QPoint | QPointF):
        cls._removed_obj_cache[obj_id] = (cls._removed_obj_cache.get(obj_id, []) + [obj_pos])
    
    @classmethod
    def remove_object_points(cls, obj_id: int):
        cls._removed_obj_cache[obj_id] = []
    
    @classmethod
    def find_obj_group(cls, obj_id:int, num: int, radius: int, mark: bool):
        None
    