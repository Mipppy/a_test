from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QSizePolicy
)
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt, QSize, QThread

from loaded_data import LoadedData
from helpers import get_pixmap_from_url
from async_pixmap_loader import PixmapLoader


class CommentCard(QWidget):
    def __init__(self, image_path: str, comment: str, username: str, date: str, like_count: int = 0, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        self.setLayout(main_layout)

        self.image_label = QLabel()
        self.image_label.setFixedHeight(200)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        main_layout.addWidget(self.image_label)

        self.load_pixmap_async(image_path)


        comment_label = QLabel(comment)
        comment_label.setWordWrap(True)
        comment_label.setFont(QFont("Arial", 10))
        main_layout.addWidget(comment_label)

        actions_layout = QHBoxLayout()

        self.like_btn = QPushButton()
        self.like_btn.setIcon(LoadedData.qicon_cache.get('thumbs_up.png'))
        self.like_btn.setIconSize(QSize(20, 20))
        self.like_btn.setFlat(True)
        self.like_btn.setToolTip("Like")
        self.like_count_label = QLabel(str(like_count))
        actions_layout.addWidget(self.like_btn)
        actions_layout.addWidget(self.like_count_label)

        self.dislike_btn = QPushButton()
        self.dislike_btn.setIcon(LoadedData.qicon_cache.get('thumbs_down.png'))
        self.dislike_btn.setIconSize(QSize(20, 20))
        self.dislike_btn.setFlat(True)
        self.dislike_btn.setToolTip("Dislike")
        actions_layout.addWidget(self.dislike_btn)

        actions_layout.addStretch()

        meta_label = QLabel(f"- {username} ({date})")
        meta_label.setStyleSheet("color: gray; font-size: 10pt;")
        actions_layout.addWidget(meta_label)

        main_layout.addLayout(actions_layout)

    def load_pixmap_async(self, url: str):
        self.thread = QThread()
        self.loader = PixmapLoader(url)
        self.loader.moveToThread(self.thread)

        self.thread.started.connect(self.loader.run)
        self.loader.finished.connect(self.on_pixmap_loaded)
        self.loader.error.connect(self.on_pixmap_error)
        self.loader.finished.connect(self.thread.quit)
        self.loader.finished.connect(self.loader.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def on_pixmap_loaded(self, pixmap: QPixmap):
        if not pixmap.isNull():
            self.image_label.setPixmap(pixmap.scaledToHeight(
                200, Qt.TransformationMode.SmoothTransformation))
            self.image_label.setStyleSheet(
                "border-radius: 8px; background-color: rgba(0, 0, 0, 0.06);")
        else:
            self.image_label.setVisible(False)

    def on_pixmap_error(self, msg: str):
        print(f"Image load error: {msg}")
        self.image_label.setVisible(False)
