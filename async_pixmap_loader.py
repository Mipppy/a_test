from PyQt5.QtCore import QObject, pyqtSignal, QThread
from PyQt5.QtGui import QPixmap
import requests

class PixmapLoader(QObject):
    finished = pyqtSignal(QPixmap)
    error = pyqtSignal(str)

    def __init__(self, url: str):
        super().__init__()
        self.url = url

    def run(self):
        try:
            if not self.url:
                self.finished.emit(QPixmap())
                return
            response = requests.get(self.url)
            response.raise_for_status()
            pixmap = QPixmap()
            if pixmap.loadFromData(response.content):
                self.finished.emit(pixmap)
            else:
                self.error.emit("Failed to load image data")
        except Exception as e:
            self.error.emit(str(e))