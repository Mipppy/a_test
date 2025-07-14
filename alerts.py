from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QProgressBar,
    QGraphicsOpacityEffect, QApplication, QSizePolicy, QMainWindow
)
from PyQt5.QtGui import QPixmap, QFont, QFontMetrics, QPainter, QColor
from PyQt5.QtCore import Qt, QTimer, QObject
from collections import OrderedDict
import sys
import os

from helpers import CustomRoundedProgressBar 

class AlertOverlay(QWidget):
    MAX_WIDTH = 150
    MAX_HEIGHT = 80
    PADDING = 5

    def __init__(self, parent: QMainWindow):
        super().__init__(parent)

        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(self.PADDING, self.PADDING, self.PADDING, self.PADDING)
        self.layout.setSpacing(4)

        self.top_layout = QHBoxLayout()
        self.top_layout.setSpacing(8)

        self.image_label = QLabel()
        self.image_label.setStyleSheet("background: transparent;")
        self.image_label.setScaledContents(True)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.text_label = QLabel()
        self.text_label.setStyleSheet("background: transparent; margin: 0; padding: 0;")
        self.text_label.setWordWrap(False)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.text_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.top_layout.addWidget(self.image_label)
        self.top_layout.addWidget(self.text_label)

        self.progress = CustomRoundedProgressBar()
        self.progress.setTextVisible(True)
        self.progress.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress.setFixedHeight(18)
        self.progress.setFont(QFont("Arial", weight=QFont.Weight.Bold))
        self.progress.setFormat("%p%")  
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #aaa;
                border-radius: 6px;
                background-color: #f0f0f0;
                text-align: center;
                color: black;
            }
QProgressBar::chunk {
    background-color: #007bff;
    border-top-left-radius: 6px;
    border-bottom-left-radius: 6px;
    border-top-right-radius: 0px;
    border-bottom-right-radius: 0px;
    margin: 0px;
}

        """)

        self.layout.addLayout(self.top_layout)
        self.layout.addWidget(self.progress)

        self.hide_all()


    def hide_all(self):
        self.image_label.hide()
        self.text_label.hide()
        self.progress.hide()

    def set_content(self, text="", image=None, current=None, maximum=None):
        if image:
            self.image_label.setPixmap(image)
            self.image_label.show()
            pix = self.image_label.pixmap()
            if pix:
                max_img_h = self.MAX_HEIGHT - self.PADDING * 6
                scale_factor = max_img_h / pix.height()
                new_w = int(pix.width() * scale_factor)
                self.image_label.setFixedSize(new_w, max_img_h)
                self.image_label.setContentsMargins(0, -self.PADDING, 0, 0)
        else:
            self.image_label.hide()
            self.image_label.setFixedSize(0, 0)

        if text:
            self.text_label.setText(text)
            self.text_label.show()
            self._scale_text()
        else:
            self.text_label.hide()

        if current is not None and maximum is not None:
            self.progress.setRange(0, maximum)
            self.progress.setValue(current)
            self.progress.show()
        else:
            self.progress.hide()

        self.adjustSize()
        
        self.setFixedSize(min(self.width(), self.MAX_WIDTH), min(self.height(), self.MAX_HEIGHT))

    def _scale_text(self):
        base_font_size = 10
        font = self.text_label.font()
        font.setPointSize(base_font_size)
        self.text_label.setFont(font)

        space_for_text = self.MAX_WIDTH - self.PADDING * 2
        if self.image_label.isVisible():
            space_for_text -= self.image_label.width() + self.layout.spacing()
        if self.progress.isVisible():
            space_for_text -= self.progress.sizeHint().width() + self.layout.spacing()

        fm = QFontMetrics(font)
        text_width = fm.horizontalAdvance(self.text_label.text())
        max_font_size = 14
        while text_width < space_for_text and font.pointSize() < max_font_size:
            font.setPointSize(font.pointSize() + 1)
            fm = QFontMetrics(font)
            text_width = fm.horizontalAdvance(self.text_label.text())

        if text_width > space_for_text:
            font.setPointSize(font.pointSize() - 1)

        self.text_label.setFont(font)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(0, 0, 0, 180)
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        rect = self.rect()
        radius = 12
        painter.drawRoundedRect(rect, radius, radius)
        super().paintEvent(event)

        
class AlertsManager(QObject):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.parent = parent
        self.parent.installEventFilter(self)
        self.overlay = None
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide_overlay)
        self.image_cache = {}

    def create_alert(self, text: str = "", image: QPixmap | str | None = None,
                        current_progress: int | None = None, max_progress: int | None = None,
                        override: bool = False, duration: int = 3000):


            if self.overlay is None or not override:
                self.overlay = AlertOverlay(self.parent)
                self.overlay.setParent(self.parent)
                self.overlay.setWindowFlags(
                    Qt.WindowType.Widget | Qt.WindowType.FramelessWindowHint)
                self.overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
                self.overlay.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
                self.overlay.setStyleSheet(
                    "background: rgba(0, 0, 0, 180); border-radius: 3px; color: white; padding: 20px;"
                )

            if isinstance(image, str):
                pixmap = self._load_image(image)
            elif isinstance(image, QPixmap):
                pixmap = image
            else:
                pixmap = None

            self.overlay.set_content(text=text, image=pixmap,
                                    current=current_progress, maximum=max_progress)

            def _show_overlay():
                self.overlay.adjustSize()
                parent_geo = self.parent.contentsRect()
                x = parent_geo.x() + int((parent_geo.width() - self.overlay.width()) / 2)
                y = parent_geo.y() + 20
                self.overlay.move(x, y)
                self.overlay.raise_()
                self.overlay.show()
                self.reposition_overlay()

            QTimer.singleShot(0, _show_overlay)
            self.timer.start(duration)


    def _load_image(self, path: str) -> QPixmap | None:
        if path in self.image_cache:
            return self.image_cache[path]
        if not os.path.isfile(path):
            print(f"[AlertsManager] Image file not found: {path}")
            return None
        pixmap = QPixmap(path)
        if pixmap.isNull():
            print(f"[AlertsManager] Failed to load image: {path}")
            return None
        self.image_cache[path] = pixmap
        return pixmap

    def reposition_overlay(self):
        if self.overlay and self.overlay.isVisible():
            x = int((self.parent.width() - self.overlay.width()) / 2)
            y = 20
            self.overlay.move(x, y)

    def hide_overlay(self):
        if self.overlay:
            self.overlay.hide()

    def eventFilter(self, obj, event):
        if obj == self.parent and event.type() in (event.Resize, event.Move):
            self.reposition_overlay()
        return super().eventFilter(obj, event)
