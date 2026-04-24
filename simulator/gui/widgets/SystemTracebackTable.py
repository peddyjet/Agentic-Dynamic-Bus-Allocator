from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QTableWidget, QHeaderView, QTableWidgetItem
import datetime
from events.event_bus import default_bus
from events.EventNames import EventNames

class SystemTracebackTable(QTableWidget):
    rationale_requested = pyqtSignal(str)
    _log_received = pyqtSignal(str, str)  # source, message

    def __init__(self, parent=None):
        super().__init__(0, 3, parent)
        self.setHorizontalHeaderLabels(["Time", "Source", "Message"])
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.verticalHeader().setVisible(False)

        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        self._rationales = []
        self.doubleClicked.connect(
            lambda idx: self.rationale_requested.emit(self._rationales[idx.row()])
        )

        self._log_received.connect(self.add_row)
        default_bus.subscribe(EventNames.LOG_MESSAGE,
                              lambda source, message: self._log_received.emit(source, message))

    def add_row(self, source: str, message: str):
        row = self.rowCount()
        self.insertRow(row)
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        for col, val in enumerate([ts, source, message]):
            self.setItem(row, col, QTableWidgetItem(val))
        self._rationales.append(message)
        self.scrollToBottom()