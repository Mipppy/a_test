from PyQt5.QtWidgets import QWidget, QHBoxLayout
import sys
import os
import math
from PyQt5.QtCore import Qt, QRectF, QTimer, QEvent, QPoint, QPointF
from PyQt5.QtGui import QPixmap, QPainter, QBrush, QPen, QImage, QColor, QKeySequence, QWheelEvent, QResizeEvent
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsEllipseItem, QShortcut, QMenu, QAction

from helpers import original_pos_to_pyqt5, gimmie_data, get_all_ids
from grouping import BasicGrouping
from composite_icon import CompositeIcon
from menu import ButtonPanel
from alerts import AlertsManager


class MapViewer(QGraphicsView):
    def __init__(self, scene: QGraphicsScene):
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setSceneRect(scene.itemsBoundingRect())
        self.setTransformationAnchor(
            QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.current_loaded_ids = []
        self.min_zoom = 0.15
        self.max_zoom = 3.0
        self.current_zoom = 1.0
        self.composite_icons = {}
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.get_new_ids)
        self.timer.start(500)

    def capture_entire_scene(self):
        rect = self.scene().itemsBoundingRect()

        image = QImage(rect.size().toSize(), QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)

        painter = QPainter(image)
        self.scene().render(painter, source=rect, target=QRectF(image.rect()))
        painter.end()

        image.save("entire_map_screenshot.png")
        print("Screenshot saved as 'entire_map_screenshot.png'")

    def load_id(self, _id: int):
        data = gimmie_data(_id)
        self.current_loaded_ids.append(_id)
        icos = []
        levels = set()
        data_len = len(data['point'])
        for i, point in enumerate(data['point']):
            levels.add(point['z_level'])
            new_pos = original_pos_to_pyqt5(point['x_pos'], point['y_pos'])
            image_path = f"images/resources/official/{data['label']['id']}.jpg"
            AlertsManager.create_alert(
                f"Loading", image_path, i, data_len-1, True, 250)
            comps_ico = CompositeIcon("images/map/official/icons/high_res/arrow_pointer.png" if point['z_level'] ==
                                      0 else "images/map/official/icons/high_res/underground_arrow_pointer.png", image_path, new_pos, point, zoom_level=self.current_zoom)
            comps_ico.scale_adjust_zoom(self.current_zoom)
            BasicGrouping.save_object_point(_id, comps_ico)
            icos.append(comps_ico)
            self.scene().addItem(comps_ico)
            QApplication.processEvents()
        self.composite_icons[_id] = icos

    def get_new_ids(self):
        for thing in self.current_loaded_ids[:]:
            if thing not in ButtonPanel.selected_ids:
                BasicGrouping.remove_object_points(thing)
                self.current_loaded_ids.remove(thing)
                for ico in self.composite_icons[thing]:
                    self.scene().removeItem(ico)
        for thing in ButtonPanel.selected_ids:
            if thing not in self.current_loaded_ids:
                self.load_id(thing)

    def wheelEvent(self, event:QWheelEvent):
        factor = 1.2 if event.angleDelta().y() > 0 else 0.8
        new_zoom = self.current_zoom * factor

        if self.min_zoom <= new_zoom <= self.max_zoom:
            self.scale(factor, factor)
            self.current_zoom = new_zoom

        list_ico: list[CompositeIcon] = [item for sublist in list(
            self.composite_icons.values()) for item in sublist]
        for ico in list_ico:
            ico.scale_adjust_zoom(self.current_zoom)

    def plot_origin(self, scene_pos: QPointF):
        radius = 5
        origin_item = QGraphicsEllipseItem(
            QRectF(scene_pos.x() - radius, scene_pos.y() - radius, radius * 2, radius * 2))
        origin_item.setBrush(QBrush(Qt.GlobalColor.red))
        origin_item.setPen(QPen(Qt.GlobalColor.red))
        self.scene().addItem(origin_item)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Map Viewer")
        screen_geo = QApplication.primaryScreen().availableGeometry()
        self.setGeometry(screen_geo)
        AlertsManager.init(self)
        toggle_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Tab), self)
        toggle_shortcut.activated.connect(self.toggle_panel)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        images_directory = "images/map/official/high_res"
        scene = QGraphicsScene(self)
        scene.setBackgroundBrush(QBrush(QColor("#111820")))

        image_files = [f for f in os.listdir(
            images_directory) if f.endswith('.webp')]
        images = []
        for image_file in image_files:
            coords = self.get_coordinates_from_filename(image_file)
            if coords:
                x, y = coords
                images.append((x, y, image_file))

        images.sort()
        self.installEventFilter(self)
        pixmaps: dict[tuple[int, int], QPixmap] = {}
        for x, y, image_file in images:
            image_path = os.path.join(images_directory, image_file)
            image = QImage(image_path)
            pixmap = QPixmap.fromImage(image)
            pixmaps[(x, y)] = pixmap

        tile_width = max(pixmap.width() for pixmap in pixmaps.values())
        tile_height = max(pixmap.height() for pixmap in pixmaps.values())

        for (x, y), pixmap in pixmaps.items():
            item = QGraphicsPixmapItem(pixmap)
            item.setPos(int(x * tile_width), int(y * tile_height))
            scene.addItem(item)

        self.map_view = MapViewer(scene)
        self.btn = ButtonPanel(self)
        self.btn.setParent(self)
        self.btn.setVisible(False)
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.btn)
        layout.addWidget(self.map_view)

        self.setCentralWidget(container)

    def toggle_panel(self):
        self.btn.setVisible(not self.btn.isVisible())

    def get_coordinates_from_filename(self, filename: str):
        try:
            base_name: str = os.path.splitext(filename)[0]
            parts = base_name.split("_")
            if len(parts) >= 2:
                x, y = int(parts[0]), int(parts[1])
                return x, y
        except ValueError:
            return None

    def resizeEvent(self, event : QResizeEvent):
        super().resizeEvent(event)
        _instance = AlertsManager.instance()
        if _instance.overlay and _instance.overlay.isVisible():
            parent_geo = _instance.parent.contentsRect()
            x = parent_geo.x() + int((parent_geo.width() - _instance.overlay.width()) / 2)
            y = parent_geo.y() + 20
            _instance.overlay.move(x, y)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
