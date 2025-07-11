import sys
import keyboard
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget

class TransparentWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)  
        self.setGeometry(QRect(0, 0, QApplication.desktop().screenGeometry().width(), QApplication.desktop().screenGeometry().height()))

    def paintEvent(self, event):
        """Make the background fully transparent."""
        painter = QPainter(self)
        painter.setCompositionMode(QPainter.CompositionMode_Clear)
        painter.fillRect(self.rect(), Qt.transparent)

class ButtonWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setGeometry(100, 100, 300, 200)

        layout = QVBoxLayout()
        button = QPushButton("Click me", self)
        layout.addWidget(button)
        container = QWidget(self)
        container.setLayout(layout)
        self.setCentralWidget(container)
        
        self.setAttribute(Qt.WA_OpaquePaintEvent)

    def paintEvent(self, event):
        """Make the background fully transparent but with visible buttons."""
        painter = QPainter(self)
        painter.setCompositionMode(QPainter.CompositionMode_Clear)
        painter.fillRect(self.rect(), Qt.transparent)

class Application:
    def __init__(self):
        self.app = QApplication(sys.argv)

        self.transparent_window = TransparentWindow()
        self.button_window = ButtonWindow()

        self.transparent_window.showFullScreen()

    def listen_for_ctrl_1(self):
        """Listen for the Ctrl+1 key combination globally."""
        print("Listening for 'Ctrl+1' key press...")

        keyboard.add_hotkey('ctrl+1', self.toggle_button_window)

        keyboard.wait()  

    def toggle_button_window(self):
        """Toggle the visibility of the button window."""
        if self.button_window.isVisible():
            self.button_window.hide()
        else:
            self.button_window.show()

if __name__ == "__main__":
    app = Application()

    app.listen_for_ctrl_1()

    sys.exit(app.app.exec_())  
