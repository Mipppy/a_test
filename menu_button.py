from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont, QMouseEvent, QFontMetrics
from PyQt5.QtWidgets import (
    QFrame,
    QLabel,
    QMenu,
    QAction,
    QVBoxLayout,
    QSizePolicy
)
from typing import Callable

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
        self.setStyleSheet("""
            QFrame {
                border: 1px solid rgba(200, 200, 200, 100);
                border-radius: 5px;
            }
            QFrame:hover {
                border: 1px solid rgba(255, 255, 255, 180);
                background-color: rgba(255, 255, 255, 10);
            }
        """)
        self._init_shared_menu()

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)
        layout.setContentsMargins(6, 6, 6, 6)
        icon_label = QLabel()
        icon_label.setPixmap(pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setScaledContents(False)  
        icon_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        icon_label.setMaximumSize(64, 64)
        layout.addWidget(icon_label, alignment=Qt.AlignCenter)

        text_label = QLabel(label_text)
        text_label.setWordWrap(True)
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_label.setMaximumWidth(120)
        text_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        text_label.setMaximumWidth(120) 
        font = QFont()
        font.setPointSize(15)
        text_label.setFont(font)

        max_width = 120
        max_height = 200

        metrics = QFontMetrics(font)

        while font.pointSize() > 6:
            rect = metrics.boundingRect(0, 0, max_width, max_height, Qt.TextWordWrap, label_text)
            if rect.height() <= max_height:
                break
            font.setPointSize(font.pointSize() - 1)
            metrics = QFontMetrics(font)
        text_label.setMaximumHeight(150)
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
            self.setStyleSheet("""
                border: 2px solid green; 
                background-color:  #31a207;
                border-radius: 5px;
                color:rgba(200, 200, 200, 255);""")
        else:
            self.setStyleSheet("""
                border: 1px solid rgba(200, 200, 200, 255);
                border-radius: 5px; 
                color:rgba(200, 200, 200, 255); """)

    def find_obj_groups(self, num_of_groups: int = 50, distance=10, mark: bool = False):
        from grouping import BasicGrouping
        groups = BasicGrouping.find_obj_group(
            self.item_id, distance=distance, num=num_of_groups, mark=mark
        )
        if groups:
            self.map_view.centerOn(groups[0][0].pos())