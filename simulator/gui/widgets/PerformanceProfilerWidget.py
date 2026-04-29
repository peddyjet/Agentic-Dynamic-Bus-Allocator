import math
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QSplitter)
from PyQt6.QtCore import Qt
from events.event_bus import default_bus
from events.EventNames import EventNames
from profiling.PerformanceProfiler import PerformanceProfiler


def _to_milliseconds(v: float) -> str:
    return f"{v:.2f}"

def _to_seconds(v: float) -> str:
    return f"{v:.1f}"

def _std_dev(s: PerformanceProfiler.Stats) -> float:
    return math.sqrt(s.m2 / s.count) if s.count > 0 else 0.0


class PerformanceProfilerWidget(QWidget):
    _stats_changed = pyqtSignal()

    def __init__(self, profiler: PerformanceProfiler, parent=None):
        super().__init__(parent)
        self._profiler = profiler

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        splitter = QSplitter(Qt.Orientation.Vertical)

        speed_container = QWidget()
        speed_layout = QVBoxLayout(speed_container)
        speed_layout.setContentsMargins(0, 0, 0, 0)
        speed_label = QLabel("Agent Step Timing")
        speed_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        speed_layout.addWidget(speed_label)

        self._speed_table = QTableWidget(0, 6)
        self._speed_table.setHorizontalHeaderLabels(["Agent", "Count", "Min (ms)", "Max (ms)", "Mean (ms)", "Std Dev (ms)"])
        self._speed_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._speed_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._speed_table.verticalHeader().setVisible(False)
        header = self._speed_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in range(1, 6):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        speed_layout.addWidget(self._speed_table)
        splitter.addWidget(speed_container)

        quality_container = QWidget()
        quality_layout = QVBoxLayout(quality_container)
        quality_layout.setContentsMargins(0, 0, 0, 0)
        quality_label = QLabel("Service Quality")
        quality_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        quality_layout.addWidget(quality_label)

        self._quality_table = QTableWidget(0, 7)
        self._quality_table.setHorizontalHeaderLabels(["Metric", "Count", "Total", "Min", "Max", "Mean", "Std Dev"])
        self._quality_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._quality_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._quality_table.verticalHeader().setVisible(False)
        qheader = self._quality_table.horizontalHeader()
        qheader.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in range(1, 7):
            qheader.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        quality_layout.addWidget(self._quality_table)
        splitter.addWidget(quality_container)

        layout.addWidget(splitter)

        self._stats_changed.connect(self._refresh)
        for event in [EventNames.STEP_COMPLETE, EventNames.ABANDONED_PASSENGER,
                      EventNames.INTERLINED, EventNames.TRIP_CANCELLED, EventNames.DELAY_RECORDED,
                      EventNames.NO_SHOW]:
            default_bus.subscribe(event, lambda *a, **k: self._stats_changed.emit())

        self._refresh()

    def _refresh(self):
        self._refresh_speed()
        self._refresh_quality()

    def _refresh_speed(self):
        stats = self._profiler.get_speed_stats()
        self._speed_table.setRowCount(0)
        for agent, s in sorted(stats.items()):
            row = self._speed_table.rowCount()
            self._speed_table.insertRow(row)
            for col, val in enumerate([
                agent,
                str(s.count),
                _to_milliseconds(s.min),
                _to_milliseconds(s.max),
                _to_milliseconds(s.mean),
                _to_milliseconds(_std_dev(s)),
            ]):
                self._speed_table.setItem(row, col, QTableWidgetItem(val))

    def _refresh_quality(self):
        self._quality_table.setRowCount(0)

        def add_count_row(metric: str, count: int):
            row = self._quality_table.rowCount()
            self._quality_table.insertRow(row)
            for col, val in enumerate([metric, str(count), "-", "-", "-", "-", "-"]):
                self._quality_table.setItem(row, col, QTableWidgetItem(val))

        def add_stats_row(metric: str, count: int, total: str,
                          s: PerformanceProfiler.Stats, fmt):
            row = self._quality_table.rowCount()
            self._quality_table.insertRow(row)
            if s.count == 0:
                cells = [metric, str(count), total, "-", "-", "-", "-"]
            else:
                cells = [metric, str(count), total,
                         fmt(s.min), fmt(s.max), fmt(s.mean), fmt(_std_dev(s))]
            for col, val in enumerate(cells):
                self._quality_table.setItem(row, col, QTableWidgetItem(val))

        add_count_row("Interlining", self._profiler.get_interline_count())
        add_count_row("Cancellations", self._profiler.get_cancellation_count())
        add_count_row("No Shows", self._profiler.get_no_show_count())
        add_stats_row(
            "Abandoned Passengers (per incident)",
            self._profiler.get_abandonment_stats().count,
            str(int(self._profiler.get_abandonment_sum())),
            self._profiler.get_abandonment_stats(),
            lambda v: f"{v:.1f}",
        )
        add_stats_row(
            "Stop Delay (s)",
            self._profiler.get_delay_stats().count,
            _to_seconds(self._profiler.get_delay_sum()),
            self._profiler.get_delay_stats(),
            _to_seconds,
        )