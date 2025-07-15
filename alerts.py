from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QProgressBar,
    QGraphicsOpacityEffect, QSizePolicy,
)
from PyQt5.QtGui import QPixmap, QFont, QFontMetrics, QPainter, QColor
from PyQt5.QtCore import Qt, QObject,QTimer, QPropertyAnimation
import os

class AlertOverlay(QWidget):
    MAX_WIDTH = 150
    MAX_HEIGHT = 80
    PADDING = 5

    def __init__(self, parent):
        super().__init__(parent)

        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(1.0)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(self.PADDING, self.PADDING, self.PADDING, self.PADDING)
        self.layout.setSpacing(4)

        self.top_layout = QHBoxLayout()
        self.top_layout.setSpacing(8)

        self.image_label = QLabel()
        self.image_label.setStyleSheet("background: transparent;")
        self.image_label.setScaledContents(True)
        self.image_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.text_label = QLabel()
        self.text_label.setStyleSheet("background: transparent; color: white;")
        self.text_label.setWordWrap(False)
        self.text_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.text_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.top_layout.addWidget(self.image_label)
        self.top_layout.addWidget(self.text_label)

        self.progress = QProgressBar()
        self.progress.setTextVisible(True)
        self.progress.setFixedHeight(16)
        self.progress.setFont(QFont("Arial", weight=QFont.Bold))
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid gray;
                border-radius: 5px;
                background-color: #eee;
                text-align: center;
                color: black;
            }
            QProgressBar::chunk {
                background-color: #0078d7;
                width: 1px;
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
        font = self.text_label.font()
        font.setPointSize(10)
        self.text_label.setFont(font)

        space_for_text = self.MAX_WIDTH - self.PADDING * 2
        if self.image_label.isVisible():
            space_for_text -= self.image_label.width() + self.layout.spacing()
        fm = QFontMetrics(font)
        text_width = fm.horizontalAdvance(self.text_label.text())

        while text_width > space_for_text and font.pointSize() > 6:
            font.setPointSize(font.pointSize() - 1)
            fm = QFontMetrics(font)
            text_width = fm.horizontalAdvance(self.text_label.text())

        self.text_label.setFont(font)

    def set_opacity(self, value: float):
        self.opacity_effect.setOpacity(value)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(0, 0, 0, 180))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 12, 12)
        super().paintEvent(event)

class AlertsManager(QObject):
    _instance = None
    @classmethod
    def instance(cls) -> "AlertsManager":
        return cls._instance
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.parent = parent
        self.overlay = None
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._start_fade_out)
        self.image_cache = {}
        self.fade_duration = 0
        self.fade_anim = None
        self.parent.installEventFilter(self)

    @classmethod
    def init(cls, parent: QWidget):
        if not cls._instance:
            cls._instance = AlertsManager(parent)
        return cls._instance

    @classmethod
    def create_alert(cls, text: str = "", image: QPixmap | str | None = None,
                     current_progress: int | None = None, max_progress: int | None = None,
                     override: bool = False, duration: int = 3000):
        self = cls.init(parent=cls._instance.parent if cls._instance else None)

        if self.overlay is None or not override:
            self.overlay = AlertOverlay(self.parent)
            self.overlay.setParent(self.parent)
            self.overlay.setWindowFlags(Qt.WindowType.Widget | Qt.WindowType.FramelessWindowHint)
            self.overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            self.overlay.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

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
            self.overlay.set_opacity(0.0)
            self._start_fade_in()
            self.reposition_overlay()

        QTimer.singleShot(0, _show_overlay)
        self.timer.start(duration)

    def _start_fade_in(self):
        if self.fade_anim:
            self.fade_anim.stop()
        self.fade_anim = QPropertyAnimation(self.overlay.opacity_effect, b"opacity")
        self.fade_anim.setDuration(self.fade_duration)
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.start()

    def _start_fade_out(self):
        if self.fade_anim:
            self.fade_anim.stop()
        self.fade_anim = QPropertyAnimation(self.overlay.opacity_effect, b"opacity")
        self.fade_anim.setDuration(self.fade_duration)
        self.fade_anim.setStartValue(1.0)
        self.fade_anim.setEndValue(0.0)
        self.fade_anim.finished.connect(self.hide_overlay)
        self.fade_anim.start()

    def hide_overlay(self):
        if self.overlay:
            self.overlay.hide()

    def reposition_overlay(self):
        if self.overlay and self.overlay.isVisible():
            x = int((self.parent.width() - self.overlay.width()) / 2)
            y = 20
            self.overlay.move(x, y)

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

    def eventFilter(self, obj, event):
        if obj == self.parent and event.type() in (event.Resize, event.Move):
            self.reposition_overlay()
        return super().eventFilter(obj, event)
