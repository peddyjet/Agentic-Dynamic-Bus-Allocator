from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QTableWidget, QHeaderView, QTableWidgetItem
from events.event_bus import default_bus
from events.EventNames import EventNames
from reasoning.environment.Environment import Environment


class CallingPatternTable(QTableWidget):
    _env_changed = pyqtSignal()

    def __init__(self, environment: Environment, parent=None):
        super().__init__(0, 5, parent)
        self._environment = environment
        self.setHorizontalHeaderLabels(["ID", "Stop Name", "Timestamp", "Average Passenger Loading", "Current Passenger Loading"])
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.verticalHeader().setVisible(False)

        header = self.horizontalHeader()
        header.setStretchLastSection(False)
        header.setDefaultSectionSize(140)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        self._trip_id: int | None = None

        self._on_env_changed = lambda: self._env_changed.emit()
        self._env_changed.connect(self._refresh)
        default_bus.subscribe(EventNames.ENVIRONMENT_CHANGED, self._on_env_changed)
        self.destroyed.connect(lambda: default_bus.unsubscribe(EventNames.ENVIRONMENT_CHANGED, self._on_env_changed))

    def show_trip(self, trip_id: int):
        self._trip_id = trip_id
        self._refresh()

    def _refresh(self):
        scroll = self.verticalScrollBar().value()
        self.setRowCount(0)

        if self._trip_id is None:
            return

        trip = self._environment.trips.get(self._trip_id)
        if trip is None:
            return

        for calling_point in sorted(trip.calling_points, key=lambda c: c.timestamp):
            row = self.rowCount()
            self.insertRow(row)
            current_load = round(calling_point.waiting_passengers)
            for col, val in enumerate([str(calling_point.stop.id), calling_point.stop.name, calling_point.timestamp.strftime("%H:%M:%S"),
                                       str(calling_point.average_pax()), str(current_load)]):
                self.setItem(row, col, QTableWidgetItem(val))

        self.verticalScrollBar().setValue(scroll)