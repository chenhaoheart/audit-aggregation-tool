# -*- coding: utf-8 -*-
import os
import tempfile
import time

from PySide6.QtCore import QThread, Signal

from services.section_chart_service import SectionChartService, get_feature_keywords
from services.section_html_builder import generate_chart_html


class LoadDataThread(QThread):
    progress_signal = Signal(int, int, str)
    finished_signal = Signal(dict)
    error_signal = Signal(str)

    def __init__(self, service: SectionChartService, directory: str, parent=None):
        super().__init__(parent)
        self.service = service
        self.directory = directory

    def run(self):
        try:
            result = self.service.load_from_directory(
                self.directory,
                progress_callback=lambda cur, total, name: self.progress_signal.emit(cur, total, name)
            )
            self.finished_signal.emit(result)
        except Exception as e:
            self.error_signal.emit(str(e))


class SectionCheckService:
    def __init__(self):
        self.chart_service = SectionChartService()
        self.load_thread = None

    def start_load(self, directory: str, on_progress, on_finished, on_error, parent=None):
        get_feature_keywords()
        self.load_thread = LoadDataThread(self.chart_service, directory, parent)
        self.load_thread.progress_signal.connect(on_progress)
        self.load_thread.finished_signal.connect(on_finished)
        self.load_thread.error_signal.connect(on_error)
        self.load_thread.start()

    def get_chart_service(self) -> SectionChartService:
        return self.chart_service

    def generate_chart_html(self, sec: dict) -> str:
        return generate_chart_html(sec)

    def render_chart_to_temp(self, section_key: str, sec: dict) -> str:
        html = generate_chart_html(sec)
        tmp_dir = os.path.join(tempfile.gettempdir(), "section_charts")
        os.makedirs(tmp_dir, exist_ok=True)
        safe_key = section_key or "default"
        for c in '<>:"/\\|?* ':
            safe_key = safe_key.replace(c, "_")
        ts = int(time.time() * 1000)
        tmp_path = os.path.join(tmp_dir, f"chart_{safe_key}_{ts}.html")
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(html)
        for old in os.listdir(tmp_dir):
            if old.startswith(f"chart_{safe_key}_") and old != os.path.basename(tmp_path):
                try:
                    os.remove(os.path.join(tmp_dir, old))
                except OSError:
                    pass
        return tmp_path

    def open_chart_external(self, section_key: str, sec: dict) -> str:
        html = generate_chart_html(sec)
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
        os.makedirs(output_dir, exist_ok=True)
        safe_name = sec.get("name", "chart").replace("/", "_").replace("\\", "_").replace(" ", "_")
        output_path = os.path.join(output_dir, f"断面成图_{safe_name}.html")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        os.startfile(output_path)
        return output_path

    def export_report(self, output_path: str):
        self.chart_service.export_validation_report(output_path)

    def export_anomaly_html(self, output_path: str):
        return self.chart_service.export_anomaly_html(output_path)

    def export_all_html(self, output_path: str):
        return self.chart_service.export_all_html(output_path)

    def get_excel_preview_info(self, section_key: str):
        sec = self.chart_service.get_section_detail(section_key)
        if not sec:
            return None
        return {
            "source_file": sec.get("source_file", ""),
            "sheet_name": sec.get("sheet_name", ""),
        }

    def get_stats(self):
        return self.chart_service.get_stats()

    def get_tree_data(self):
        return self.chart_service.get_tree_data()

    def get_section_detail(self, section_key: str):
        return self.chart_service.get_section_detail(section_key)

    def recalculate_sections(self):
        self.chart_service.recalculate_sections()
