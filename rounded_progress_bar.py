from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QColor, QFont
from PyQt5.QtWidgets import (
    QProgressBar,
    QWidget,
)


class CustomRoundedProgressBar(QProgressBar):
    def __init__(self, parent: QWidget | None=None):
        super().__init__(parent)
        self.setTextVisible(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFont(QFont("Arial", weight=QFont.Weight.Bold))
        self.setMinimumHeight(18)
        self.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #f0f0f0;
                color: black;
            }
        """)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        radius = 6
        bar_rect = self.rect().adjusted(1, 1, -1, -1)
        chunk_color = QColor("#007bff")
        bg_color = QColor("#f0f0f0")

        painter.setBrush(bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(bar_rect, radius, radius)

        progress_ratio = (self.value() - self.minimum()) / \
            (self.maximum() - self.minimum() or 1)
        chunk_width = int(bar_rect.width() * progress_ratio)

        if chunk_width > 0:
            chunk_rect = QRectF(bar_rect.left(), bar_rect.top(),
                                chunk_width, bar_rect.height())

            if self.value() >= self.maximum():
                painter.setBrush(chunk_color)
                painter.drawRoundedRect(chunk_rect, radius, radius)
            else:
                path = QRectF(chunk_rect)
                painter.setBrush(chunk_color)
                painter.setPen(Qt.PenStyle.NoPen)

                painter.save()
                painter.setClipRect(chunk_rect)
                painter.drawRoundedRect(chunk_rect.adjusted(
                    0, 0, radius, 0), radius, radius)
                painter.restore()

        if self.isTextVisible():
            text = self.text()
            painter.setPen(QColor("black"))
            painter.setFont(self.font())
            painter.drawText(bar_rect, Qt.AlignmentFlag.AlignCenter, text)
