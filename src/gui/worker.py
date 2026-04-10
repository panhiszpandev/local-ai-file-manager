import traceback
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from src.agent import Agent
from src.csv_manager import update_record
from src.llm_client import LLMClient
from src.scanner import scan
from src.tools import init_tools


class AnalysisWorker(QThread):
    """Background thread that runs scan + agent analysis loop."""

    scan_done = Signal(list)  # list of dicts for all discovered files
    progress = Signal(int, int)  # (current, total)
    file_updated = Signal(int, dict)  # (row index in pending, updated data)
    error = Signal(str)
    finished_all = Signal()

    def __init__(self, root: Path, output_csv: Path, lm_url: str, model: str):
        super().__init__()
        self.root = root
        self.output_csv = output_csv
        self.lm_url = lm_url
        self.model = model
        self._stop_requested = False

    def stop(self):
        self._stop_requested = True

    def run(self):
        try:
            all_records = scan(self.root, self.output_csv)
            pending = [r for r in all_records if r.status == "NEW"]

            self.scan_done.emit([
                {
                    "name": r.name,
                    "extension": r.extension,
                    "status": r.status,
                    "category": r.category or "",
                    "suggested_name": r.suggested_name or "",
                    "error": r.error or "",
                }
                for r in all_records
            ])

            if not pending:
                self.finished_all.emit()
                return

            # Map pending record paths to their row index in all_records
            path_to_row = {r.path: i for i, r in enumerate(all_records)}

            llm = LLMClient(base_url=self.lm_url, model=self.model)
            init_tools(llm)
            agent = Agent(llm)

            for i, record in enumerate(pending):
                if self._stop_requested:
                    break

                self.progress.emit(i, len(pending))

                try:
                    result = agent.process(record)
                except Exception as e:
                    record.status = "FAILED"
                    record.error = str(e)
                    result = record

                update_record(self.output_csv, result)
                row = path_to_row[result.path]
                self.file_updated.emit(row, {
                    "name": result.name,
                    "extension": result.extension,
                    "status": result.status,
                    "category": result.category or "",
                    "suggested_name": result.suggested_name or "",
                    "error": result.error or "",
                })

            self.finished_all.emit()

        except Exception:
            tb = traceback.format_exc()
            print(tb, flush=True)
            self.error.emit(tb)
