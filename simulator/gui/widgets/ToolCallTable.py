from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QTableWidget, QHeaderView, QTableWidgetItem


class ToolCallTable(QTableWidget):
    rationale_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(0, 4, parent)
        self.setHorizontalHeaderLabels(["Time", "Agent", "Tool", "Summary"])
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.setMaximumHeight(180)
        self._rationales = []
        self.doubleClicked.connect(
            lambda idx: self.rationale_requested.emit(self._rationales[idx.row()])
        )

    def add_row(self, agent: str, tool: str, summary: str, rationale: str = ""):
        import datetime
        row = self.rowCount()
        self.insertRow(row)
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        for col, val in enumerate([ts, agent, tool, summary]):
            self.setItem(row, col, QTableWidgetItem(val))
        self._rationales.append(rationale or summary)
        self.scrollToBottom()