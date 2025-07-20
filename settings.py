import json
import os
import re
from typing import Any, Dict, List, Union

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QCheckBox, QSpinBox, QDoubleSpinBox, QSlider, QPushButton,
    QHBoxLayout, QLabel, QColorDialog, QSizePolicy, QVBoxLayout, QFrame
)
from PyQt5.QtGui import QColor, QFont, QCursor


class SettingsManager:
    settings_data: Dict[str, Dict[str, Any]] = {}
    _json_path: str

    @classmethod
    def init(cls, path: str):
        cls._json_path = path
        if not os.path.exists(path):
            raise FileNotFoundError(f"Settings file not found: {path}")
        with open(path, "r") as f:
            cls.settings_data = json.load(f)

    @classmethod
    def update_setting(cls, setting_key: str, new_value: Any):
        if setting_key in cls.settings_data:
            cls.settings_data[setting_key]["value"] = new_value
            cls.save_to_file()
        else:
            print(f"[SettingsManager] Key '{setting_key}' not found")

    @classmethod
    def reset_settings(cls):
        for key, meta in cls.settings_data.items():
            meta["value"] = meta.get("default")
        cls.save_to_file()

    @classmethod
    def save_to_file(cls):
        print(f"[SettingsManager] Saving to {cls._json_path}")
        with open(cls._json_path, "w") as f:
            json.dump(cls.settings_data, f, indent=4)

    @classmethod
    def generate_ui(cls) -> List[QWidget]:
        widgets = []
        for key, meta in cls.settings_data.items():
            wrapper = QWidget()
            wrapper_layout = QVBoxLayout()
            wrapper_layout.setSpacing(4)
            wrapper_layout.setContentsMargins(4, 4, 4, 4)

            label = QLabel(meta.get("name", key))
            label.setFont(QFont("Arial", 11, QFont.Bold))
            label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            wrapper_layout.addWidget(label)

            description = QLabel(meta.get("description", ""))
            description.setWordWrap(True)
            description.setFont(QFont("Arial", 9))
            description.setStyleSheet("color: gray;")
            description.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            wrapper_layout.addWidget(description)

            control = cls._create_control(key, meta)
            control.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            wrapper_layout.addWidget(control)

            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setFrameShadow(QFrame.Sunken)
            line.setStyleSheet("color: #aaa;")
            wrapper_layout.addWidget(line)

            wrapper.setLayout(wrapper_layout)
            widgets.append(wrapper)

        return widgets
    
    @classmethod
    def _create_control(cls, key: str, meta: Dict[str, Any]) -> Union[QWidget, None]:
        value = meta.get("value", meta.get("default"))
        setting_type = meta.get("data_type")

        def on_change(val, key=key):
            cls.update_setting(key, val)

        if setting_type == "bool":
            checkbox = QCheckBox()
            checkbox.setChecked(bool(value))
            checkbox.stateChanged.connect(lambda state, key=key: on_change(state == Qt.CheckState.Checked, key))
            return checkbox

        elif setting_type == "int":
            spinbox = QSpinBox()
            spinbox.setValue(int(value))
            spinbox.setMinimum(meta.get("min", 0))
            spinbox.setMaximum(meta.get("max", 100))
            spinbox.setSingleStep(meta.get("step", 1))
            spinbox.valueChanged.connect(lambda val, key=key: on_change(val, key))
            spinbox.setStyleSheet("color: black;")
            return spinbox

        elif setting_type == "float":
            dsp = QDoubleSpinBox()
            dsp.setValue(float(value))
            dsp.setMinimum(meta.get("mins", 0.0))
            dsp.setMaximum(meta.get("max", 1000.0))
            dsp.setSingleStep(meta.get("step", 0.1))
            dsp.setDecimals(meta.get("decimals", 3))
            dsp.valueChanged.connect(lambda val, key=key: on_change(val, key))
            dsp.setStyleSheet("color: black;")
            return dsp

        elif setting_type == "slider":
            slider = QSlider(Qt.Horizontal)
            slider.setMinimum(meta.get("min", 0))
            slider.setMaximum(meta.get("max", 100))
            slider.setValue(int(value))
            slider.valueChanged.connect(lambda val, key=key: on_change(val, key))
            slider.setStyleSheet("""
                QSlider::handle:horizontal {
                    background: black;
                }
                QSlider::groove:horizontal {
                    background: lightgray;
                }
            """)
            return slider


        elif setting_type == "color":
            btn = QPushButton()
            btn.setFixedSize(100, 24)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

            color_val = value if isinstance(value, str) else meta.get("default", "rgba(255,255,255,255)")
            btn.setStyleSheet(f"background-color: {color_val}; border: 1px solid #888;")
            btn.setText("") 

            btn.clicked.connect(lambda _, b=btn, k=key: cls._open_color_dialog(b, k))
            return btn

        return QLabel(f"Invalid setting: {key}?")

    @classmethod
    def _open_color_dialog(cls, button: QPushButton, key: str):

        style = button.styleSheet()
        match = re.search(r'rgba\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)', style)
        if match:
            r, g, b, a = map(int, match.groups())
            initial_color = QColor(r, g, b, a)
        else:
            initial_color = QColor(255, 255, 255, 255)

        col = QColorDialog.getColor(initial_color, None, "Select Color", QColorDialog.ColorDialogOption.ShowAlphaChannel)
        if col.isValid():
            rgba_str = f"rgba({col.red()}, {col.green()}, {col.blue()}, {col.alpha()})"
            button.setStyleSheet(f"background-color: {rgba_str}; border: 1px solid #888;")
            cls.update_setting(key, rgba_str)
    
    @classmethod
    def get_setting_value(cls, key:str):
        return cls.settings_data.get(key).get('value')