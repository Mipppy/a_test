from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QSizePolicy
)
from PyQt5.QtGui import QFont, QPixmap, QCursor, QTextCursor
from PyQt5.QtCore import Qt, QSize, QThread

from loaded_data import LoadedData
from helpers import get_pixmap_from_url
from async_pixmap_loader import PixmapLoader


class CommentCard(QWidget):
    def __init__(self, image_path: str, comment: str, username: str, date: str, like_count: int = 0, parent=None):
        super().__init__(parent)
        self.setFixedWidth(self.width())
        self.loader_thread = None
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)

        self.image_label = QLabel()
        self.image_label.setFixedHeight(200)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        main_layout.addWidget(self.image_label)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.load_pixmap_async(image_path)


        comment_label = QLabel(comment)
        comment_label.setWordWrap(True)
        comment_label.setFont(QFont("Arial", 10))
        comment_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        comment_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignLeft)

        comment_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        comment_label.setCursor(Qt.CursorShape.IBeamCursor)

        comment_label.setStyleSheet("padding: 4px 50px 4px 4px;")

        main_layout.addWidget(comment_label)
        actions_layout = QHBoxLayout()

        self.like_btn = QPushButton()
        self.like_btn.setIcon(LoadedData.qicon_cache.get('thumbs_up_dark.png'))
        self.like_btn.setIconSize(QSize(20, 20))
        self.like_btn.setFlat(True)
        self.like_btn.setToolTip("Like")
        self.like_count_label = QLabel(str(like_count))
        self.like_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        actions_layout.addWidget(self.like_btn)
        actions_layout.addWidget(self.like_count_label)

        self.dislike_btn = QPushButton()
        self.dislike_btn.setIcon(LoadedData.qicon_cache.get('thumbs_down_dark.png'))
        self.dislike_btn.setIconSize(QSize(20, 20))
        self.dislike_btn.setFlat(True)
        self.dislike_btn.setToolTip("Dislike")
        self.dislike_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        actions_layout.addWidget(self.dislike_btn)


        meta_label = QLabel(f"- {username} ({date})")
        meta_label.setStyleSheet("color: gray; font-size: 10pt;")
        actions_layout.addWidget(meta_label)
        actions_layout.addStretch()

        main_layout.addLayout(actions_layout)

    def load_pixmap_async(self, url: str):
        if self.loader_thread and self.loader_thread.isRunning():
            self.loader_thread.quit()
            self.loader_thread.wait()

        self.loader_thread = QThread(self) 
        self.loader = PixmapLoader(url)
        self.loader.moveToThread(self.loader_thread)

        self.loader_thread.started.connect(self.loader.run)
        self.loader.finished.connect(self.on_pixmap_loaded)
        self.loader.error.connect(self.on_pixmap_error)

        self.loader.finished.connect(self.loader_thread.quit)
        self.loader.finished.connect(self.loader.deleteLater)
        self.loader_thread.finished.connect(self.loader_thread.deleteLater)

        self.loader_thread.start()
        
    def closeEvent(self, event):
        if hasattr(self, "loader_thread"):
            if self.loader_thread.isRunning():
                self.loader_thread.quit()
                self.loader_thread.wait()
        super().closeEvent(event)
        
    def on_pixmap_loaded(self, pixmap: QPixmap):
        if not pixmap.isNull():
            self.image_label.setVisible(True)
            label_size = self.image_label.size()
            pixmap_size = pixmap.size()

            if pixmap_size.width() > label_size.width() or pixmap_size.height() > label_size.height():
                scaled_pixmap = pixmap.scaled(
                    label_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            else:
                scaled_pixmap = pixmap

            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.setStyleSheet("border-radius: 8px; background-color: rgba(0, 0, 0, 0.06);")
        else:
            self.image_label.clear()  
            self.image_label.setVisible(False)

    
    def on_pixmap_error(self, msg: str):
        print(f"Image load error: {msg}")
        self.image_label.setVisible(False)
