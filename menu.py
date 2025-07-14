import os
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont, QColor, QPalette
from PyQt5.QtWidgets import (
    QWidget, QGridLayout, QLabel, QScrollArea,
    QVBoxLayout, QHBoxLayout, QFrame, QPushButton
)
from helpers import get_all_ids
from alerts import AlertsManager
class ClickableIcon(QFrame):
    def __init__(self, item_id, label_text, pixmap, click_callback):
        super().__init__()
        self.item_id = item_id
        self.callback = click_callback
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFixedSize(70, 85)
        self.setStyleSheet("border: 1px solid lightgray; border-radius: 5px;")

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

    def mousePressEvent(self, event):
        self.callback(self.item_id, self)

    def set_selected(self, selected: bool):
        if selected:
            self.setStyleSheet("border: 2px solid green; background-color: #c7f0c4; border-radius: 5px;")
        else:
            self.setStyleSheet("border: 1px solid lightgray; border-radius: 5px;")
class ButtonPanel(QWidget):
    def __init__(self, alert_manager: AlertsManager):
        super().__init__()
        self.setWindowTitle("Control Panel")
        self.setFixedSize(400, 600)
        self.selected_ids = []
        self.container_widget = QWidget()
        self.main_layout = QHBoxLayout(self)
        self.alert_manager = alert_manager
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

    def create_group_section(self, group_name, data):
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
            pixmap = QPixmap(image_path).scaled(30, 30, Qt.AspectRatioMode.KeepAspectRatio)
            button = ClickableIcon(item[0], item[1], pixmap, self.toggle_selection)
            grid_layout.addWidget(button, row, col)

        section_layout.addLayout(grid_layout)
        section_widget.setLayout(section_layout)
        return section_widget

    def toggle_selection(self, id: int, widget:ClickableIcon) -> None:
        if id in self.selected_ids:
            self.selected_ids.remove(id)
            widget.set_selected(False)
        else:
            self.selected_ids.append(id)
            widget.set_selected(True)

    def scroll_to_group(self, group_idx:int) -> None:
        section: QWidget = self.section_widgets[group_idx]
        self.content_scroll_area.verticalScrollBar().setValue(section.y())
