from PyQt5.QtCore import Qt, QRectF, QPointF, QPoint, QSize, QTimer
from PyQt5.QtGui import QPixmap, QPainter, QBrush, QPen, QImage, QColor, QFontMetrics, QFont, QMouseEvent
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QGraphicsView,
    QGraphicsScene,
    QFrame,
    QGraphicsEllipseItem,
    QGraphicsItemGroup,
    QLabel,
    QProgressBar,
    QWidget,
    QGraphicsRectItem,
    QGraphicsTextItem,
    QMenu,
    QAction,
    QVBoxLayout,
)
from typing import Dict, List, Union, Optional, Any, cast, Callable
from collections import OrderedDict

from grouping import BasicGrouping

class ClickableIcon(QFrame):
    _shared_menu = None
    _action_groups = None
    _action_delete = None

    @classmethod
    def _init_shared_menu(cls):
        if cls._shared_menu is None:
            cls._shared_menu = QMenu()
            cls._action_groups = QAction("Find Groups")
            cls._action_delete = QAction("Delete")
            cls._shared_menu.addAction(cls._action_groups)
            cls._shared_menu.addAction(cls._action_delete)

    def __init__(self, item_id: int, label_text: str, pixmap: QPixmap, click_callback: Callable, parent):
        super().__init__()
        self.item_id = item_id
        self.callback = click_callback
        self.selected = False
        self.map_view = parent
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFixedSize(70, 85)
        self.setStyleSheet("border: 1px solid lightgray; border-radius: 5px;")

        self._init_shared_menu()

        layout = QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(3)

        icon_label = QLabel()
        icon_label.setPixmap(pixmap)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        text_label = QLabel(label_text)
        text_label.setWordWrap(True)
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        font = QFont()
        font.setPointSize(8)
        text_label.setFont(font)

        layout.addWidget(text_label)
        self.setLayout(layout)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.RightButton:
            if not self.selected:
                self.callback(self.item_id, self)

            try:
                self._action_groups.triggered.disconnect()
            except TypeError:
                pass  

            self._action_groups.triggered.connect(
                lambda: self.find_obj_groups(num_of_groups=999, distance=25, mark=True)
            )

            self._shared_menu.exec_(event.globalPos())

            QTimer.singleShot(0, lambda: self._action_groups.triggered.disconnect())
        else:
            self.callback(self.item_id, self)

    def set_selected(self, selected: bool):
        self.selected = selected
        if selected:
            self.setStyleSheet(
                "border: 2px solid green; background-color: #c7f0c4; border-radius: 5px;")
        else:
            self.setStyleSheet(
                "border: 1px solid lightgray; border-radius: 5px;")

    def find_obj_groups(self, num_of_groups: int = 50, distance=10, mark: bool = False):
        groups = BasicGrouping.find_obj_group(
            self.item_id, distance=distance, num=num_of_groups, mark=mark
        )
        if groups:
            self.map_view.centerOn(groups[0][0].pos())