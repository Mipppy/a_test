from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QSizePolicy
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QSize

from loaded_data import LoadedData
from helpers import get_pixmap_from_url

class CommentCard(QWidget):
    def __init__(self, image_path: str, comment: str, username: str, date: str, like_count: int = 0, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        self.setLayout(main_layout)

        image_label = QLabel()
        image_label.setFixedHeight(200)
        image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        pixmap = get_pixmap_from_url(image_path)
        if pixmap:
            image_label.setPixmap(pixmap.scaledToHeight(200, Qt.TransformationMode.SmoothTransformation))
            image_label.setStyleSheet("border-radius: 8px; background-color: rgba(0, 0, 0, 0.06);")
        else:
            image_label.setVisible(False)
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(image_label)

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
