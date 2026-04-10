import os
from pathlib import Path

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.gui.worker import AnalysisWorker


COLUMNS = ["Name", "Extension", "Status", "Category", "Suggested Name", "Error"]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI File Manager")
        self.setMinimumSize(900, 500)
        self.worker = None

        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Top bar: folder picker + analyze button
        top = QHBoxLayout()
        self.path_label = QLabel("No folder selected")
        self.path_label.setMinimumWidth(300)
        self.browse_btn = QPushButton("Browse…")
        self.browse_btn.clicked.connect(self._browse)
        self.analyze_btn = QPushButton("Analyze")
        self.analyze_btn.clicked.connect(self._start_analysis)
        self.analyze_btn.setEnabled(False)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self._stop_analysis)
        self.stop_btn.setEnabled(False)

        top.addWidget(self.path_label, 1)
        top.addWidget(self.browse_btn)
        top.addWidget(self.analyze_btn)
        top.addWidget(self.stop_btn)
        layout.addLayout(top)

        # Table
        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

        # Bottom bar: progress
        bottom = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_label = QLabel("")
        bottom.addWidget(self.progress_bar, 1)
        bottom.addWidget(self.status_label)
        layout.addLayout(bottom)

        self.selected_path: Path | None = None

    def _browse(self):
        folder = QFileDialog.getExistingDirectory(self, "Select folder to analyze")
        if folder:
            self.selected_path = Path(folder)
            self.path_label.setText(str(self.selected_path))
            self.analyze_btn.setEnabled(True)

    def _start_analysis(self):
        if not self.selected_path:
            return

        settings = QSettings("AIFileManager", "AIFileManager")
        lm_url = settings.value("lm_url", os.getenv("LLM_BASE_URL", "http://127.0.0.1:1234/v1"))
        model = settings.value("model", os.getenv("LLM_MODEL", "glm-4.7-flash"))
        output = Path(settings.value("output_path", "result.csv"))

        self.table.setRowCount(0)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.analyze_btn.setEnabled(False)
        self.browse_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("Scanning…")

        self.worker = AnalysisWorker(self.selected_path, output, lm_url, model)
        self.worker.scan_done.connect(self._on_scan_done)
        self.worker.progress.connect(self._on_progress)
        self.worker.file_updated.connect(self._on_file_updated)
        self.worker.error.connect(self._on_error)
        self.worker.finished_all.connect(self._on_finished)
        self.worker.start()

    def _stop_analysis(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.status_label.setText("Stopping…")

    def _on_scan_done(self, records: list):
        self.table.setRowCount(len(records))
        for row, data in enumerate(records):
            self._set_row(row, data)
        total = len(records)
        pending = sum(1 for r in records if r["status"] == "NEW")
        self.status_label.setText(f"Found {total} files ({pending} pending)")

    def _on_progress(self, current: int, total: int):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_label.setText(f"Analyzing {current + 1}/{total}…")

    def _on_file_updated(self, row: int, data: dict):
        self._set_row(row, data)
        self.table.scrollToItem(self.table.item(row, 0))

    def _set_row(self, row: int, data: dict):
        self.table.setItem(row, 0, QTableWidgetItem(data["name"]))
        self.table.setItem(row, 1, QTableWidgetItem(data["extension"]))

        status_item = QTableWidgetItem(data["status"])
        if data["status"] == "DONE":
            status_item.setForeground(Qt.GlobalColor.darkGreen)
        elif data["status"] == "FAILED":
            status_item.setForeground(Qt.GlobalColor.red)
        self.table.setItem(row, 2, status_item)

        self.table.setItem(row, 3, QTableWidgetItem(data["category"]))
        self.table.setItem(row, 4, QTableWidgetItem(data["suggested_name"]))
        self.table.setItem(row, 5, QTableWidgetItem(data["error"]))

    def _on_error(self, message: str):
        self.status_label.setText(f"Error: {message}")
        self._reset_controls()

    def _on_finished(self):
        total = self.table.rowCount()
        done = sum(
            1 for r in range(total)
            if self.table.item(r, 2) and self.table.item(r, 2).text() == "DONE"
        )
        failed = sum(
            1 for r in range(total)
            if self.table.item(r, 2) and self.table.item(r, 2).text() == "FAILED"
        )
        self.status_label.setText(f"Done — {done} done, {failed} failed, {total} total")
        self.progress_bar.setValue(self.progress_bar.maximum())
        self._reset_controls()

    def _reset_controls(self):
        self.analyze_btn.setEnabled(True)
        self.browse_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def closeEvent(self, event):
        event.ignore()
        self.hide()
