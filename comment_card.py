from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QSizePolicy
)
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt, QSize
import asyncio
from async_requests import AsyncRequests
import json

from loaded_data import LoadedData
from async_requests import AsyncPixmapLoader


class CommentCard(QWidget):
    def __init__(self, image_url: str, comment: str, username: str, date: str, auid:str, docid: str, oid: str,  like_count: int = 0, parent=None):
        super().__init__(parent)
        self.setFixedWidth(self.width())

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)
        self.setLayout(main_layout)
        self.auid = auid
        self.oid = oid
        self.docid = docid
        self.image_label = QLabel()
        self.image_label.setFixedHeight(200)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.image_label.setVisible(False)
        main_layout.addWidget(self.image_label)
        self.voted = None
        self.like_count = like_count
        if image_url:
            self.load_pixmap_async(image_url)

        comment_label = QLabel(comment)
        comment_label.setWordWrap(True)
        comment_label.setFont(QFont("Arial", 10))
        comment_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        comment_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
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
        self.like_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.like_btn.clicked.connect(lambda: self.vote('up'))
        self.like_count_label = QLabel(str(self.like_count))

        actions_layout.addWidget(self.like_btn)
        actions_layout.addWidget(self.like_count_label)

        self.dislike_btn = QPushButton()
        self.dislike_btn.setIcon(LoadedData.qicon_cache.get('thumbs_down_dark.png'))
        self.dislike_btn.setIconSize(QSize(20, 20))
        self.dislike_btn.setFlat(True)
        self.dislike_btn.setToolTip("Dislike")
        self.dislike_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.dislike_btn.clicked.connect(lambda: self.vote('down'))

        actions_layout.addWidget(self.dislike_btn)

        meta_label = QLabel(f"- {username} ({date})")
        meta_label.setStyleSheet("color: gray; font-size: 10pt;")
        actions_layout.addWidget(meta_label)
        actions_layout.addStretch()

        main_layout.addLayout(actions_layout)

    def load_pixmap_async(self, url: str):
        self.pixmap_loader = AsyncPixmapLoader(url)
        self.pixmap_loader.finished.connect(self.on_pixmap_loaded)
        self.pixmap_loader.error.connect(self.on_pixmap_error)
        self.pixmap_loader.start()

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


    def vote(self, direction: str):
        vote_map = {"up": 1, "down": -1}
        new_vote = direction if self.voted != direction else None

        delta = vote_map.get(new_vote, 0) - vote_map.get(self.voted, 0)
        self.like_count += delta
        self.voted = new_vote

        self.like_count_label.setText(str(self.like_count))
        self.update_vote_icons()
        self.send_vote_to_server()
        
    def update_vote_icons(self):
        if self.voted == "up":
            self.like_btn.setIcon(LoadedData.qicon_cache.get('thumbs_up_selected.png'))
            self.dislike_btn.setIcon(LoadedData.qicon_cache.get('thumbs_down_dark.png'))
        elif self.voted == "down":
            self.like_btn.setIcon(LoadedData.qicon_cache.get('thumbs_up_dark.png'))
            self.dislike_btn.setIcon(LoadedData.qicon_cache.get('thumbs_down_selected.png'))
        else:
            self.like_btn.setIcon(LoadedData.qicon_cache.get('thumbs_up_dark.png'))
            self.dislike_btn.setIcon(LoadedData.qicon_cache.get('thumbs_down_dark.png'))
    
    def send_vote_to_server(self):
        # If this fails it doesn't really matter.  The user thinks it succeeded and have little way of verifying otherwise.
        try:
            url = f"https://cache-v2-origin.lemonapi.com/comments/v2?app=gim&collection={self.oid}&docId={self.docid}"
            payload = {
                "action": f"{self.voted}Vote",
                "uid": '5rNZCHeYmpJFWLE3', 
                "auid": self.auid
            }
            data_bytes = json.dumps(payload).encode("utf-8")
            headers = {
                "Content-Type": "application/json"
            }

            async def _send():
                try:
                    res = await AsyncRequests.request("PUT", url, data=data_bytes, headers=headers)
                    print(f"[send_vote_to_server] Success: {res}")
                except Exception:
                    None

            asyncio.create_task(_send())
        except Exception:
            None