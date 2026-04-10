import re

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton, QFrame
import qtawesome as qta

from reasoning.agent_interface.ComputationalAgentInterface import ComputationalAgentInterface
from simulator.gui.gui_util import icon_label, find_relevant_icon


class RightPanel(QWidget):
    log_submitted = pyqtSignal(str)

    def __init__(self, cai : ComputationalAgentInterface, parent=None):
        super().__init__(parent)
        self.setFixedWidth(220)
        layout = QVBoxLayout(self)
        self._cai = cai

        layout.addWidget(QLabel("Send log to CRA"))
        self.log_input = QTextEdit()
        self.log_input.setFixedHeight(90)
        layout.addWidget(self.log_input)

        btn = QPushButton("Submit Log")
        btn.clicked.connect(self._submit)
        btn.setIcon(qta.icon("mdi.send"))
        layout.addWidget(btn)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line)

        layout.addWidget(QLabel("System Status"))
        self.status_labels = {}
        for name, items in cai.get_system_status().items():
            lbl = icon_label(find_relevant_icon(name),
                             f"{name.upper()}: "
                             + ("free" if items == 0 else "busy")
                             + f" ({items} job{'s' if items != 1 else ''})")

            lbl.setFont(QFont("Courier New", 8))
            layout.addWidget(lbl)
            self.status_labels[name] = lbl

        layout.addStretch()

    def _submit(self):
        text = self.log_input.toPlainText().strip()
        if text:
            self.log_submitted.emit(text)
            self.log_input.clear()

    def set_agent_status(self, name: str, busy: bool, jobs: int = 0):
        if name in self.status_labels:
            status = f"Busy ({jobs} job{'s' if jobs != 1 else ''})" if busy else "Free"
            self.status_labels[name].setText(f"{name}: {status}")

