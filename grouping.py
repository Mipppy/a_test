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
import math
from typing import Dict, List, Union, Optional, Any, cast
from collections import OrderedDict

from composite_icon import CompositeIcon

class BasicGrouping:
    _comp_ico_pointers: Dict[int, List[CompositeIcon]] = {}
    _group_boxes: List[QGraphicsRectItem] = []  # Keep track of group overlays

    def __init__(self):
        pass

    @classmethod
    def save_object_point(cls, obj_id: int, comp_ico_pointer: CompositeIcon):
        cls._comp_ico_pointers[obj_id] = (
            cls._comp_ico_pointers.get(obj_id, []) + [comp_ico_pointer])

    @classmethod
    def remove_object_points(cls, obj_id: int):
        cls._comp_ico_pointers[obj_id] = []

    @classmethod
    def clear_group_boxes(cls):
        for box in cls._group_boxes:
            if box.scene():
                box.scene().removeItem(box)
        cls._group_boxes.clear()

    @classmethod
    def find_obj_group(cls, obj_id: int, num: int = 5, distance: int = 100, mark: bool = False) -> list:
        def is_close(a: QPointF, b: QPointF, threshold: float) -> bool:
            return math.hypot(a.x() - b.x(), a.y() - b.y()) <= threshold

        all_objs = cls._comp_ico_pointers.get(obj_id, [])
        if not all_objs:
            return []

        cls.clear_group_boxes()
        visited = set()
        groups = []

        for obj in all_objs:
            if obj in visited:
                continue
            group = set()
            queue = [obj]

            while queue:
                current = queue.pop()
                if current in visited:
                    continue
                visited.add(current)
                group.add(current)

                current_pos = current.pos()
                for neighbor in all_objs:
                    if neighbor not in visited and is_close(current_pos, neighbor.pos(), distance):
                        queue.append(neighbor)

            if len(group) >= 2:
                groups.append(group)

        merged = True
        while merged:
            merged = False
            for i in range(len(groups)):
                for j in range(i + 1, len(groups)):
                    if groups[i] is None or groups[j] is None:
                        continue
                    if any(is_close(a.pos(), b.pos(), distance * 1.5) for a in groups[i] for b in groups[j]):
                        groups[i].update(groups[j])
                        groups[j] = None
                        merged = True
            groups = [g for g in groups if g is not None]

        groups = [list(g) for g in groups]
        groups.sort(key=len, reverse=True)

        if mark:
            for group in groups:
                for icon in group:
                    icon.setSelected(True)
                cls.mark_group(group)
                QApplication.processEvents()

        return groups[:num] if not mark else groups


    @classmethod
    def mark_group(cls, group: list):
        positions = []
        for icon in group:
            base_scene_rect = icon.base_item.sceneBoundingRect()
            overlay_scene_rect = icon.overlay_item.sceneBoundingRect()
            combined_rect = base_scene_rect.united(overlay_scene_rect)
            positions.append(combined_rect)


        if not positions:
            return

        min_x = min(rect.left() for rect in positions)
        min_y = min(rect.top() for rect in positions)
        max_x = max(rect.right() for rect in positions)
        max_y = max(rect.bottom() for rect in positions)

        padding = 2
        bounding_rect = QRectF(
            min_x - padding, min_y - padding,
            (max_x - min_x) + 2 * padding,
            (max_y - min_y) + 2 * padding
        )

        rect_item = QGraphicsRectItem(bounding_rect)
        pen = QPen(QColor("blue"))
        pen.setWidth(2)
        brush = QColor(0, 0, 255, 30)
        rect_item.setPen(pen)
        rect_item.setBrush(brush)
        rect_item.setZValue(9999)

        text = QGraphicsTextItem(str(len(group)))
        text.setDefaultTextColor(QColor("black"))
        text.setZValue(10000)
        text.setFont(QFont("Arial", 14, QFont.Bold))
        text.setPos(bounding_rect.topLeft() + QPointF(4, -20))  # Position slightly above the box

        scene = group[0].scene()
        if scene:
            scene.addItem(rect_item)
            scene.addItem(text)
            cls._group_boxes.append(rect_item)
            cls._group_boxes.append(text)