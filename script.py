from loaded_data import LoadedData
from helpers import map_all_ids_by_xpos
from PyQt5.QtGui import QGuiApplication
import sys
app = QGuiApplication(sys.argv)
LoadedData.init()

map_all_ids_by_xpos()# Required for QPixmap/QIcon

