import os
from PyQt5.QtCore import Qt, QEvent, QPointF
from PyQt5.QtGui import QPixmap, QFont, QColor, QPalette, QMouseEvent
from PyQt5.QtWidgets import (
    QWidget, QGridLayout, QLabel, QScrollArea,
    QVBoxLayout, QHBoxLayout, QFrame, QPushButton, QAction, QMenu, QMainWindow
)
from functools import partial
from typing import List, Dict,Tuple, Union, Sequence, Callable

from helpers import get_all_ids

from alerts import AlertsManager

from menu_button import ClickableIcon

class ButtonPanel(QWidget):
    selected_ids: list[int] = []
    def __init__(self, parent: QMainWindow):
        super().__init__()
        self.window_view = parent
        self.setWindowTitle("Control Panel")
        self.setFixedSize(400, 600)
        self.container_widget = QWidget()
        self.main_layout = QHBoxLayout(self)
        menu_layout = QVBoxLayout()
        content_layout = QVBoxLayout()
        content_scroll_area = QScrollArea()
        content_scroll_area.setWidgetResizable(True)
        content_container_widget = QWidget()
        content_container_widget.setLayout(content_layout)
        content_scroll_area.setWidget(content_container_widget)

        self.ids = get_all_ids()
        self.section_widgets = {}

        for idx, (key, value) in enumerate(self.ids.items()):
            menu_button = QPushButton(key)
            menu_button.clicked.connect(
                lambda _, idx=idx: self.scroll_to_group(idx))
            menu_layout.addWidget(menu_button)

            section = self.create_group_section(key, value)
            self.section_widgets[idx] = section
            content_layout.addWidget(section)

        self.main_layout.addLayout(menu_layout, 1)
        self.main_layout.addWidget(content_scroll_area, 3)
        self.content_scroll_area = content_scroll_area

    def create_group_section(self, group_name: str, data: List[Union[Tuple[str, str], Sequence[str]]]) -> QWidget:
        section_widget = QWidget()
        section_layout = QVBoxLayout()

        b_f = QFont()
        b_f.setBold(True)
        title_label = QLabel(group_name)
        title_label.setFont(b_f)
        section_layout.addWidget(title_label)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(5)

        for i, item in enumerate(data):
            row, col = divmod(i, 3)
            image_path = f"images/resources/official/{item[0]}.jpg"
            pixmap = QPixmap(image_path).scaled(
                30, 30, Qt.AspectRatioMode.KeepAspectRatio)
            button = ClickableIcon(
                item[0], item[1], pixmap, self.toggle_selection, parent=self.window_view.map_view)
            grid_layout.addWidget(button, row, col)

        section_layout.addLayout(grid_layout)
        section_widget.setLayout(section_layout)
        return section_widget

    def toggle_selection(self, id: int, widget: ClickableIcon) -> None:
        if id in self.selected_ids:
            self.selected_ids.remove(id)
            widget.set_selected(False)
        else:
            self.selected_ids.append(id)
            widget.set_selected(True)

    def scroll_to_group(self, group_idx: int) -> None:
        section: QWidget = self.section_widgets[group_idx]
        self.content_scroll_area.verticalScrollBar().setValue(section.y())
