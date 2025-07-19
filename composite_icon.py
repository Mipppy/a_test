from PyQt5.QtCore import Qt, QPointF, QSize
from PyQt5.QtGui import QPixmap, QImage,QPainter, QPainterPath
from PyQt5.QtWidgets import (
    QGraphicsPixmapItem,
    QGraphicsItemGroup,
    QGraphicsSceneMouseEvent
)
from collections import OrderedDict

from helpers import reverse_linear_mapping, circular_crop_pixmap
from loaded_data import LoadedData
from webhandler import WebHandler
from menu import ButtonPanel
class CompositeIcon(QGraphicsItemGroup):
    _global_z_counter = 1

    @classmethod
    def raise_to_top(cls, item: QGraphicsItemGroup):
        cls._global_z_counter += 1
        item.setZValue(cls._global_z_counter)

    def __init__(self, base_image_path: str, overlay_image_path: str, position: QPointF, item_data=None, size=100, zoom_level: float = 1):
        super().__init__()
        self.setFlags(QGraphicsItemGroup.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)

        self.anchor_offset = QPointF(63.5, 110)
        base_target_size = QSize(size, size)
        base_pixmap = ImageCacheManager.get_base_pixmap(
            base_image_path, base_target_size)

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
        overlay_pixmap = ImageCacheManager.get_overlay_pixmap(
            overlay_image_path, overlay_size)

        overlay_pixmap = circular_crop_pixmap(overlay_pixmap)

        self.overlay_item = QGraphicsPixmapItem(overlay_pixmap)
        self.overlay_item.setParentItem(self.base_item)

        overlay_x = (base_pixmap.width() - overlay_pixmap.width()) / 2
        overlay_y = ((base_pixmap.height() - overlay_pixmap.height()
                      ) / 2) - (base_pixmap.height() / 10)
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
        self.label_id = self.item_data['label_id']
        self._id = self.item_data['label_id']
        self.oid = LoadedData.id_oid_dataset.get(str(self.label_id))
        self.uid = LoadedData.official_id_to_unofficial_id.get(str(self._id))
        self.logical_anchor_pos = position
        self.update_position()

    def update_position(self):
        # A reverse linear function seems to correct the displacement from the zoom.
        # Why I need to divide by 2 for the x is beyond me, but looking at the pixel placements it appears to be correct.
        adjusted_x = reverse_linear_mapping(self.zoom_level)
        self.setPos(self.logical_anchor_pos - self.anchor_offset +
                    QPointF(adjusted_x / 2, adjusted_x))

    def scale_adjust_zoom(self, zoom_level:float):
        scale_factor = max(self.min_scale, min(
            0.5 / (zoom_level), self.max_scale))
        self.setScale(scale_factor)
        self.zoom_level = zoom_level
        self.update_position()

    def mousePressEvent(self, event:QGraphicsSceneMouseEvent):
        self.setSelected(True)
        ButtonPanel.clear_comment_cards()
        WebHandler.load_unofficial_data(self.item_data['id'], self.item_data['label_id'])
        CompositeIcon.raise_to_top(self)
        super().mousePressEvent(event)

class ImageCacheManager:
    _max_cache_size = 25
    _overlay_cache = OrderedDict()
    _base_cache = OrderedDict()

    @classmethod
    def _get_pixmap(cls, cache: OrderedDict, image_path: str, target_size: QSize) -> QPixmap:
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