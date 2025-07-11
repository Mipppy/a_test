import sys
import os
import gc
from PyQt5.QtCore import Qt, QRectF, QTimer, QPointF
from PyQt5.QtGui import QPainter, QImage, QColor
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene,
    QGraphicsItem, QGraphicsPixmapItem
)
from helpers import original_pos_to_pyqt5, CompositeIcon, gimmie_data, get_all_ids
from menu import ButtonPanel
from map import MapViewer, LazyTileItem

class MainWindow(QMainWindow):
    def __init__(self, _btn):
        super().__init__()
        self.setWindowTitle("Map Viewer")
        self.setGeometry(100, 100, 1000, 800)
        self.btn = _btn
        scene = QGraphicsScene(self)
        scene.setBackgroundBrush(QColor("#181c24"))

        tile_layer = LazyTileItem("images/map/official/high_res")
        scene.addItem(tile_layer)

        self.view = MapViewer(scene, self.btn)
        self.setCentralWidget(self.view)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    btn = ButtonPanel()
    btn.show()
    window = MainWindow(btn)
    window.show()
    sys.exit(app.exec_())