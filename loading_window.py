from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QApplication

class LoadingWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Loading Univeral Resonance Stone...")
        self.setModal(False) 
        self.setFixedSize(300, 120)
        layout = QVBoxLayout()
        self.label = QLabel("Initializing...")
        self.progress = QProgressBar()
        layout.addWidget(self.label)
        layout.addWidget(self.progress)
        self.setLayout(layout)

    def update_text(self, text: str, value: int, maximum: int):
        self.label.setText(text)
        self.progress.setMaximum(maximum)
        self.progress.setValue(value)
        QApplication.processEvents()