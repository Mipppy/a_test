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
from collections import OrderedDict, defaultdict

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
        def is_close(p1: QPointF, p2: QPointF) -> bool:
            return (p1 - p2).manhattanLength() <= distance  # Faster approximation

        all_objs = cls._comp_ico_pointers.get(obj_id, [])
        if not all_objs:
            return []

        cls.clear_group_boxes()
        visited = set()
        icon_positions = {icon: icon.pos() for icon in all_objs}

        # Grid hashing
        cell_size = distance
        grid = defaultdict(list)
        for icon, pos in icon_positions.items():
            key = (int(pos.x()) // cell_size, int(pos.y()) // cell_size)
            grid[key].append(icon)

        def get_neighbors(icon):
            pos = icon_positions[icon]
            cx, cy = int(pos.x()) // cell_size, int(pos.y()) // cell_size
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for neighbor in grid.get((cx + dx, cy + dy), []):
                        if neighbor != icon and is_close(icon_positions[icon], icon_positions[neighbor]):
                            yield neighbor

        groups = []
        for icon in all_objs:
            if icon in visited:
                continue
            queue = [icon]
            group = set()

            while queue:
                current = queue.pop()
                if current in visited:
                    continue
                visited.add(current)
                group.add(current)
                queue.extend(n for n in get_neighbors(current) if n not in visited)

            if len(group) >= 2:
                groups.append(group)

        merged = True
        while merged:
            merged = False
            new_groups = []
            while groups:
                current = groups.pop()
                for i, g in enumerate(groups):
                    if any(is_close(icon_positions[a], icon_positions[b]) for a in current for b in g):
                        current |= g
                        groups.pop(i)
                        merged = True
                        break
                new_groups.append(current)
            groups = new_groups

        groups = [list(g) for g in groups if g]
        groups.sort(key=len, reverse=True)

        if mark:
            for group in groups:
                for icon in group:
                    icon.setSelected(True)
                cls.mark_group(group)

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