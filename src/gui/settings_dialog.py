import os

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
)


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(400)

        self.settings = QSettings("AIFileManager", "AIFileManager")

        layout = QFormLayout(self)

        self.lm_url_input = QLineEdit(self.settings.value("lm_url", os.getenv("LLM_BASE_URL", "http://127.0.0.1:1234/v1")))
        self.model_input = QLineEdit(self.settings.value("model", os.getenv("LLM_MODEL", "glm-4.7-flash")))
        self.output_input = QLineEdit(self.settings.value("output_path", "result.csv"))

        layout.addRow("LM Studio URL:", self.lm_url_input)
        layout.addRow("Model:", self.model_input)
        layout.addRow("Output CSV:", self.output_input)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _save(self):
        self.settings.setValue("lm_url", self.lm_url_input.text())
        self.settings.setValue("model", self.model_input.text())
        self.settings.setValue("output_path", self.output_input.text())
        self.accept()
