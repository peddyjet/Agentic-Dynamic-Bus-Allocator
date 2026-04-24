from typing import List, Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QTableWidget, QHeaderView, QTableWidgetItem
from events.event_bus import default_bus
from events.EventNames import EventNames
from reasoning.environment.Environment import Environment
from reasoning.environment.IncidentStore import IncidentStore
from reasoning.models.incident import TimeStampedIncident, Incident
from simulator.gui.gui_util import icon_label


class IncidentsTable(QTableWidget):
    expansion_requested = pyqtSignal(str)
    _env_changed = pyqtSignal()

    def __init__(self, incident_store: IncidentStore, parent=None):
        super().__init__(0, 5, parent)
        self._store = incident_store
        self.setHorizontalHeaderLabels(["Time", "Summary", "Expiry", "Specific Buses Affected", "Specific Trips Affected"])
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

        self.doubleClicked.connect(
            lambda idx: self.expansion_requested.emit(self._incident_detail(idx.row()))
        )

        self._env_changed.connect(self._refresh)
        default_bus.subscribe(EventNames.INCIDENT_ADDED, lambda: self._env_changed.emit())

        self._refresh()

    def _incident_detail(self, row: int) -> str:
        time_item = self.item(row, 0)
        if time_item is None:
            return "No data."
        incident_time = time_item.text()
        incidents : List[TimeStampedIncident] = self._store.get_incidents()

        incident : Optional[TimeStampedIncident] = None
        for i in incidents:
            if i.time == incident_time:
                incident = i
                break

        if incident is None:
            return f"Incident {incident_time} not found."

        return (
            f"Description:             {incident.description}\n\n"
            f"Actions To Be Taken:      {incident.actions}\n"
        )

    def _refresh(self):
        scroll = self.verticalScrollBar().value()
        self.setRowCount(0)

        for incident in sorted(self._store.get_incidents(), key=lambda i: i.time):
            row = self.rowCount()
            self.insertRow(row)

            buses = "; ".join(str(b) for b in incident.buses) if incident.buses else "None"
            trips = "; ".join(str(t) for t in incident.trips) if incident.trips else "None"

            for col, val in enumerate([incident.time, incident.summary, f"{incident.expiry}h", buses, trips]):
                if val is not None:
                    self.setItem(row, col, QTableWidgetItem(val))

        self.verticalScrollBar().setValue(scroll)