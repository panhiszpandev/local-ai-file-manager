import csv
import os
from pathlib import Path

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QColor, QPalette
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
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.db_manager import get_all
from src.gui.worker import AnalysisWorker


ANALYZE_COLUMNS = ["Name", "Extension", "Status", "Category", "Suggested Name", "Summary", "Error"]
HISTORY_COLUMNS = ["Name", "Extension", "Status", "Category", "Suggested Name", "Summary", "Path", "Error"]

# Column index maps
_A_NAME, _A_EXT, _A_STATUS, _A_CAT, _A_SUGGESTED, _A_SUMMARY, _A_ERROR = range(7)
_H_NAME, _H_EXT, _H_STATUS, _H_CAT, _H_SUGGESTED, _H_SUMMARY, _H_PATH, _H_ERROR = range(8)

ROW_BASE_COLOR = QColor("#1A1A1A")
ROW_ALT_COLOR = QColor("#252525")


def _configure_table(table: QTableWidget, stretch_cols: list[int], fixed_cols: list[int]) -> None:
    header = table.horizontalHeader()
    for col in stretch_cols:
        header.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
    for col in fixed_cols:
        header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    table.setAlternatingRowColors(True)
    table.setWordWrap(False)
    table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
    table.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)

    palette = table.palette()
    palette.setColor(QPalette.ColorRole.Base, ROW_BASE_COLOR)
    palette.setColor(QPalette.ColorRole.AlternateBase, ROW_ALT_COLOR)
    palette.setColor(QPalette.ColorRole.Text, QColor("#FFFFFF"))
    table.setPalette(palette)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI File Manager")
        self.setMinimumSize(960, 560)
        self.worker = None
        self._path_to_row: dict[str, int] = {}

        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_analyze_tab(), "Analyze")
        self.tabs.addTab(self._build_history_tab(), "History")
        layout.addWidget(self.tabs)

        self.selected_path: Path | None = None

    # ------------------------------------------------------------------ #
    # Analyze tab
    # ------------------------------------------------------------------ #

    def _build_analyze_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

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

        self.analyze_table = QTableWidget(0, len(ANALYZE_COLUMNS))
        self.analyze_table.setHorizontalHeaderLabels(ANALYZE_COLUMNS)
        _configure_table(
            self.analyze_table,
            stretch_cols=[_A_NAME, _A_SUGGESTED, _A_SUMMARY],
            fixed_cols=[_A_EXT, _A_STATUS, _A_CAT, _A_ERROR],
        )
        layout.addWidget(self.analyze_table)

        bottom = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_label = QLabel("")
        bottom.addWidget(self.progress_bar, 1)
        bottom.addWidget(self.status_label)
        layout.addLayout(bottom)

        return widget

    # ------------------------------------------------------------------ #
    # History tab
    # ------------------------------------------------------------------ #

    def _build_history_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        toolbar = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._load_history)
        self.export_btn = QPushButton("Export CSV…")
        self.export_btn.clicked.connect(self._export_csv)
        self.history_status = QLabel("")
        toolbar.addWidget(self.refresh_btn)
        toolbar.addWidget(self.export_btn)
        toolbar.addStretch()
        toolbar.addWidget(self.history_status)
        layout.addLayout(toolbar)

        self.history_table = QTableWidget(0, len(HISTORY_COLUMNS))
        self.history_table.setHorizontalHeaderLabels(HISTORY_COLUMNS)
        _configure_table(
            self.history_table,
            stretch_cols=[_H_NAME, _H_SUGGESTED, _H_SUMMARY, _H_PATH],
            fixed_cols=[_H_EXT, _H_STATUS, _H_CAT, _H_ERROR],
        )
        layout.addWidget(self.history_table)

        return widget

    def _load_history(self):
        records = get_all()
        self.history_table.setRowCount(len(records))
        for row, r in enumerate(records):
            self.history_table.setItem(row, _H_NAME, QTableWidgetItem(r.name))
            self.history_table.setItem(row, _H_EXT, QTableWidgetItem(r.extension))

            status_item = QTableWidgetItem(r.status)
            if r.status == "DONE":
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            elif r.status == "FAILED":
                status_item.setForeground(Qt.GlobalColor.red)
            self.history_table.setItem(row, _H_STATUS, status_item)

            self.history_table.setItem(row, _H_CAT, QTableWidgetItem(r.category or ""))
            self.history_table.setItem(row, _H_SUGGESTED, QTableWidgetItem(r.suggested_name or ""))
            self.history_table.setItem(row, _H_SUMMARY, QTableWidgetItem(r.summary or ""))
            self.history_table.setItem(row, _H_PATH, QTableWidgetItem(r.path))
            self.history_table.setItem(row, _H_ERROR, QTableWidgetItem(r.error or ""))

        self.history_status.setText(f"{len(records)} records")

    def _export_csv(self):
        records = get_all()
        if not records:
            return

        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "history.csv", "CSV files (*.csv)")
        if not path:
            return

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["path", "name", "extension", "size_bytes", "status",
                             "summary", "category", "suggested_name", "error"])
            for r in records:
                writer.writerow([r.path, r.name, r.extension, r.size_bytes, r.status,
                                 r.summary or "", r.category or "",
                                 r.suggested_name or "", r.error or ""])

        self.history_status.setText(f"Exported {len(records)} records to {Path(path).name}")

    # ------------------------------------------------------------------ #
    # Analysis flow
    # ------------------------------------------------------------------ #

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

        self.analyze_table.setRowCount(0)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.analyze_btn.setEnabled(False)
        self.browse_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("Scanning…")

        self.worker = AnalysisWorker(self.selected_path, lm_url, model)
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
        self.analyze_table.setRowCount(len(records))
        self._path_to_row = {data["path"]: i for i, data in enumerate(records)}
        for row, data in enumerate(records):
            self._set_analyze_row(row, data)
        pending = sum(1 for r in records if r["status"] == "NEW")
        self.status_label.setText(f"Found {len(records)} files ({pending} pending)")

    def _on_progress(self, current: int, total: int):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_label.setText(f"Analyzing {current + 1}/{total}…")

    def _on_file_updated(self, path: str, data: dict):
        row = self._path_to_row.get(path)
        if row is not None:
            self._set_analyze_row(row, data)
            self.analyze_table.scrollToItem(self.analyze_table.item(row, 0))

    def _set_analyze_row(self, row: int, data: dict):
        self.analyze_table.setItem(row, _A_NAME, QTableWidgetItem(data["name"]))
        self.analyze_table.setItem(row, _A_EXT, QTableWidgetItem(data["extension"]))

        status_item = QTableWidgetItem(data["status"])
        if data["status"] == "DONE":
            status_item.setForeground(Qt.GlobalColor.darkGreen)
        elif data["status"] == "FAILED":
            status_item.setForeground(Qt.GlobalColor.red)
        self.analyze_table.setItem(row, _A_STATUS, status_item)

        self.analyze_table.setItem(row, _A_CAT, QTableWidgetItem(data["category"]))
        self.analyze_table.setItem(row, _A_SUGGESTED, QTableWidgetItem(data["suggested_name"]))
        self.analyze_table.setItem(row, _A_SUMMARY, QTableWidgetItem(data["summary"]))
        self.analyze_table.setItem(row, _A_ERROR, QTableWidgetItem(data["error"]))

    def _on_error(self, message: str):
        self.status_label.setText(f"Error: {message}")
        self._reset_controls()

    def _on_finished(self):
        total = self.analyze_table.rowCount()
        done = sum(
            1 for r in range(total)
            if self.analyze_table.item(r, _A_STATUS) and self.analyze_table.item(r, _A_STATUS).text() == "DONE"
        )
        failed = sum(
            1 for r in range(total)
            if self.analyze_table.item(r, _A_STATUS) and self.analyze_table.item(r, _A_STATUS).text() == "FAILED"
        )
        self.status_label.setText(f"Done — {done} done, {failed} failed, {total} total")
        self.progress_bar.setValue(self.progress_bar.maximum())
        self._reset_controls()
        self._load_history()

    def _reset_controls(self):
        self.analyze_btn.setEnabled(True)
        self.browse_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def closeEvent(self, event):
        event.ignore()
        self.hide()
