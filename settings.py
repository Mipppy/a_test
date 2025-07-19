import json
import os
from typing import Any, Dict, List, Union

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QCheckBox, QSpinBox, QDoubleSpinBox, QSlider, QPushButton,
    QHBoxLayout, QLabel, QColorDialog, QSizePolicy, QVBoxLayout
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
            wrapper_layout.setSpacing(2)              
            wrapper_layout.setContentsMargins(2, 2, 2, 2) 

            top_row = QWidget()
            top_layout = QHBoxLayout()
            top_layout.setContentsMargins(0, 0, 0, 0)
            top_layout.setSpacing(6)

            label = QLabel(meta.get("name", key))
            label_font = QFont("Arial", 10, QFont.Bold)
            label.setFont(label_font)
            label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

            tooltip_btn = QPushButton("?")
            tooltip_btn.setFixedSize(18, 18)
            tooltip_btn.setFont(QFont("Arial", 9, QFont.Bold))
            tooltip_btn.setStyleSheet(
                "QPushButton {"
                " border: none;"
                " background-color: #ccc;"
                " border-radius: 9px;"
                " color: black;"
                "}"
                "QPushButton::hover { background-color: #aaa; }"
            )
            tooltip_btn.setToolTip(meta.get("description", ""))
            tooltip_btn.setCursor(QCursor(Qt.PointingHandCursor))

            control = cls._create_control(key, meta)
            control.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

            top_layout.addWidget(label)
            top_layout.addWidget(tooltip_btn)
            top_layout.addWidget(control)
            top_row.setLayout(top_layout)

            wrapper_layout.addWidget(top_row)
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
            checkbox.stateChanged.connect(lambda state, key=key: on_change(state == Qt.Checked, key))
            return checkbox

        elif setting_type == "int":
            spinbox = QSpinBox()
            spinbox.setValue(int(value))
            spinbox.setMinimum(meta.get("min", 0))
            spinbox.setMaximum(meta.get("max", 100))
            spinbox.setSingleStep(meta.get("step", 1))
            spinbox.valueChanged.connect(lambda val, key=key: on_change(val, key))
            return spinbox

        elif setting_type == "float":
            dsp = QDoubleSpinBox()
            dsp.setValue(float(value))
            dsp.setMinimum(meta.get("min", 0.0))
            dsp.setMaximum(meta.get("max", 1000.0))
            dsp.setSingleStep(meta.get("step", 0.1))
            dsp.setDecimals(meta.get("decimals", 3))
            dsp.valueChanged.connect(lambda val, key=key: on_change(val, key))
            return dsp

        elif setting_type == "slider":
            slider = QSlider(Qt.Horizontal)
            slider.setMinimum(meta.get("min", 0))
            slider.setMaximum(meta.get("max", 100))
            slider.setValue(int(value))
            slider.valueChanged.connect(lambda val, key=key: on_change(val, key))
            return slider

        elif setting_type == "color":
            btn = QPushButton()
            btn.setText(value)
            btn.setStyleSheet(f"background-color: {value};")
            btn.clicked.connect(lambda _, b=btn, k=key: cls._open_color_dialog(b, k))
            return btn

        return QLabel("Unsupported")

    @classmethod
    def _open_color_dialog(cls, button: QPushButton, key: str):
        current_color = button.text()
        col = QColorDialog.getColor(QColor(current_color), button, f"Select color for {key}")
        if col.isValid():
            rgba_str = f"rgba({col.red()}, {col.green()}, {col.blue()}, {col.alpha()})"
            button.setText(rgba_str)
            button.setStyleSheet(f"background-color: {rgba_str};")
            cls.update_setting(key, rgba_str)
