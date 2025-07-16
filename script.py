"""
This file is used for testing small scripts or preforming actions on files that isn't needed in the main code.
"""

from loaded_data import LoadedData
from helpers import map_all_ids_by_xpos
from PyQt5.QtGui import QGuiApplication
import sys
app = QGuiApplication(sys.argv)
LoadedData.init()

map_all_ids_by_xpos()

