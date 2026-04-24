from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QTableWidget, QHeaderView, QTableWidgetItem
from events.event_bus import default_bus
from events.EventNames import EventNames
from reasoning.environment.Environment import Environment


class TripsTable(QTableWidget):
    expansion_requested = pyqtSignal(str)
    _env_changed = pyqtSignal()

    def __init__(self, environment: Environment, parent=None):
        super().__init__(0, 3, parent)
        self._environment = environment
        self.setHorizontalHeaderLabels(["ID", "Start Time", "End Time"])
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.verticalHeader().setVisible(False)

        header = self.horizontalHeader()
        header.setStretchLastSection(False)
        header.setDefaultSectionSize(140)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        self._service_id: int | None = None

        self.doubleClicked.connect(
            lambda idx: self.expansion_requested.emit(self.item(idx.row(), 0).text())
        )

        self._env_changed.connect(self._refresh)
        default_bus.subscribe(EventNames.ENVIRONMENT_CHANGED, lambda: self._env_changed.emit())

    def show_service(self, service_id: int):
        self._service_id = service_id
        self._refresh()

    def _refresh(self):
        scroll = self.verticalScrollBar().value()
        self.setRowCount(0)

        if self._service_id is None:
            return

        service = self._environment.services.get(self._service_id)
        if service is None:
            return

        for trip in sorted(service.trips, key=lambda t: t.start_time(as_date=True)):
            row = self.rowCount()
            self.insertRow(row)
            for col, val in enumerate([str(trip.id), trip.start_time(False), trip.end_time(False)]):
                self.setItem(row, col, QTableWidgetItem(val))

        self.verticalScrollBar().setValue(scroll)