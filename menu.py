import os
from PyQt5.QtCore import Qt, QSize, QThread
from PyQt5.QtGui import QPixmap, QFont, QIcon
from PyQt5.QtWidgets import (
    QWidget, QGridLayout, QLabel, QScrollArea,
    QVBoxLayout, QHBoxLayout, QPushButton,
    QToolButton, QMainWindow, QSizePolicy
)
from typing import List, Union, Tuple, Sequence, Optional

from helpers import get_all_ids
from menu_button import ClickableIcon
from comment_card import CommentCard
from loaded_data import LoadedData


class ButtonPanel(QWidget):
    selected_ids: list[int] = []
    instance: Optional['ButtonPanel'] = None

    def __init__(self, parent: QMainWindow):
        super().__init__()
        self.setObjectName("ButtonPanel")
        self.window_view = parent
        ButtonPanel.instance = self
        self.setWindowTitle("Control Panel")
        print(self.window_view.height())
        self.setFixedHeight(self.window_view.height())
        self.setSizePolicy(QSizePolicy.Policy.Preferred,
                           QSizePolicy.Policy.Expanding)
        # self.setStyleSheet("""
        #     QWidget {
        #         background-color: rgba(40, 40, 40, 180);  /* semi-transparent dark grey */
        #         color: rgba(255, 255, 255, 200);          /* soft white text */
        #     }
        #     QLabel, QPushButton, QToolButton {
        #         color: rgba(255, 255, 255, 200);          /* enforce for child widgets */
        #     }
        #     QScrollArea {
        #         background-color: transparent;           /* no extra background */
        #     }
        #     QScrollBar:horizontal {
        #         height: 0px;                              /* hide horizontal scrollbar */
        #     }
        # """)

        self.main_layout = QVBoxLayout(self)

        self.navbar_widget = QWidget()
        self.navbar_widget.setObjectName("NavbarWidget")
        self.navbar = QHBoxLayout(self.navbar_widget)
        self.navbar.setContentsMargins(3, 3, 3, 3)
        self.navbar.setSpacing(2)
        self.main_layout.addWidget(self.navbar_widget)

        self.nav_buttons = {}
        buttons_info = [
            ("Location Data", "images/resources/official/3.jpg"),
            ("Web", "images/resources/official/52.jpg"),
            ("Settings", "images/resources/official/558.jpg`"),
        ]

        for name, icon_path in buttons_info:
            btn = QToolButton()
            btn.setObjectName('NavButton')
            btn.setIcon(QIcon(icon_path))
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
            btn.setCheckable(True)
            btn.setFixedSize(60, 60)
            btn.setIconSize(QSize(48, 48))
            btn.setAutoExclusive(True)
            btn.clicked.connect(lambda checked, n=name: self.on_nav_clicked(n))
            self.navbar.addWidget(btn)
            self.nav_buttons[name] = btn

        self.nav_buttons["Location Data"].setChecked(True)

        self.views = {}

        self.location_view = QWidget()
        location_layout = QHBoxLayout(self.location_view)

        self.menu_layout = QVBoxLayout()
        location_layout.addLayout(self.menu_layout, 1)

        self.content_scroll_area = QScrollArea()
        self.content_scroll_area.setWidgetResizable(True)
        self.content_container_widget = QWidget()
        self.content_container_widget.setObjectName('ContentContainer')
        self.content_layout_inside = QVBoxLayout(self.content_container_widget)
        self.content_scroll_area.setWidget(self.content_container_widget)
        location_layout.addWidget(self.content_scroll_area, 3)

        self.views["Location Data"] = self.location_view

        self.web_view = QWidget()
        self.web_view.setObjectName('WebView')
        web_layout = QVBoxLayout(self.web_view)

        self.web_scroll = QScrollArea()
        self.web_scroll.setWidgetResizable(True)

        self.web_content = QWidget()
        self.web_layout_inside = QVBoxLayout(self.web_content)
        self.web_content.setObjectName('WebContent')
        self.web_layout_inside.setContentsMargins(8, 8, 8, 8)
        self.web_layout_inside.setSpacing(12)

        self.web_content.setLayout(self.web_layout_inside)
        self.web_scroll.setWidget(self.web_content)

        web_layout.addWidget(self.web_scroll)
        self.views["Web"] = self.web_view

        self.settings_view = QWidget()
        settings_layout = QVBoxLayout(self.settings_view)
        settings_layout.addWidget(QLabel("<h2>Settings View (empty)</h2>"))
        self.views["Settings"] = self.settings_view

        for view in self.views.values():
            self.main_layout.addWidget(view)
            view.hide()

        self.location_view.show()

        self.ids = LoadedData.all_official_ids
        self.section_widgets = {}
        self.content_scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.web_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.content_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        for idx, (key, value) in enumerate(self.ids.items()):
            menu_button = QPushButton(key)
            menu_button.setObjectName('LocationMenuButton')
            menu_button.setContentsMargins(0, 0, 0, 0)
            menu_button.clicked.connect(
                lambda _, idx=idx: self.scroll_to_group(idx))
            self.menu_layout.addWidget(menu_button)

            section = self.create_group_section(key, value)
            self.section_widgets[idx] = section
            self.content_layout_inside.addWidget(section)
        self.setStyleSheet("""
            QWidget {
                color: rgba(255, 255, 255, 200);
            }
            QLabel, QPushButton, QToolButton {
                color: rgba(255, 255, 255, 200);
            }
            QScrollArea {
                background-color: transparent;
            }
            QScrollBar:horizontal {
                height: 0px;
            }  
            #NavbarWidget {
            }
            #LocationMenuButton {
                background-color: rgba(60, 60, 60, 255);
                border: 1px solid black;
                margin: 0px;
                padding: 8px 12px;
                color: rgba(255, 255, 255, 200);
                font-weight: bold;
            }

            #LocationMenuButton:hover {
                background-color: rgba(60, 60, 60, 255);
                border: 1px solid white;  
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                width: 0px;
                height: 0px;
                background: transparent;
            }
            #NavButton {
                background-color: rgba(60, 60, 60, 255);
                border: 1px solid black;
            }
            #NavButton:hover {
                background-color: rgba(40, 40, 40, 255);
                border: 1px solid white;
            }
            #WebView, #WebContent, #ContentContainer {
                background-color: rgba(60, 60, 60, 255);
            }
        """)

    def on_nav_clicked(self, name: str):
        for view in self.views.values():
            view.hide()
        self.views[name].show()

    def create_group_section(
        self, group_name: str, data: List[Union[Tuple[str, str], Sequence[str]]]
    ) -> QWidget:
        section_widget = QWidget()
        section_layout = QVBoxLayout()
        section_widget.setObjectName('SectionWidget')
        section_widget.setStyleSheet("""
            #SectionWidget {
                background-color: rgba(40,40,40,200)
            }                           
        """)
        b_f = QFont()
        b_f.setBold(True)
        title_label = QLabel(group_name)
        title_label.setFont(b_f)
        section_layout.addWidget(title_label)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(5)

        for i, item in enumerate(data):
            row, col = divmod(i, 3)
            pixmap = LoadedData.btn_pixmaps.get(int(item[0])).scaled(
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

    @classmethod
    def add_comment_card(cls, image_path: str, comment: str, username: str, date: str, like_count: int = 0):
        if cls.instance is None:
            raise RuntimeError("ButtonPanel instance is not initialized.")

        card = CommentCard(image_path, comment, username, date, like_count)
        cls.instance.web_layout_inside.addWidget(card)

    @classmethod
    def clear_comment_cards(cls):
        if cls.instance is None:
            raise RuntimeError("ButtonPanel instance is not initialized.")

        layout = cls.instance.web_layout_inside
        while layout.count():
            item = layout.takeAt(0)
            widget: Optional["ButtonPanel"] = item.widget()
            if widget is not None:
                loader_thread: None | QThread = getattr(widget, 'thread', None)
                if loader_thread and hasattr(loader_thread, 'isRunning'):
                    try:
                        if loader_thread.isRunning():
                            loader_thread.quit()
                            loader_thread.wait()
                    except RuntimeError:
                        pass

                widget.setParent(None)
                widget.deleteLater()
