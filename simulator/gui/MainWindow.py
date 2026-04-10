import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMainWindow, QApplication, QWidget, QVBoxLayout, QSplitter, QTabWidget, QLabel, QTextEdit
from reasoning.agent_interface.ComputationalAgentInterface import ComputationalAgentInterface
from reasoning.environment.Environment import Environment
from simulator.gui.widgets.LogBridge import LogBridge
from simulator.gui.widgets.RightPanel import RightPanel
from simulator.gui.widgets.ToolCallTable import ToolCallTable
import qtawesome as qta


class MainWindow(QMainWindow):
    def __init__(self, bridge: LogBridge, cai : ComputationalAgentInterface, environment : Environment):
        super().__init__()

        self._cai = cai
        self._environment = environment

        self.bridge = bridge
        self.setWindowTitle("Agentic DBA Simulator")
        self.resize(1400, 860)
        self.setWindowIcon(qta.icon('mdi.bus', color='#51F50F'))

        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        h_split = QSplitter(Qt.Orientation.Horizontal)
        root_layout.addWidget(h_split, stretch=1)

        v_split = QSplitter(Qt.Orientation.Vertical)
        h_split.addWidget(v_split)

        self._tabs = QTabWidget()
        self._tabs.addTab(QLabel("Network graph goes here"), "Network Graph")
        self._tabs.addTab(QLabel("Buses"), "Buses")
        self._tabs.addTab(QLabel("Services and Trips"), "Services and Trips")
        self._tabs.addTab(QLabel("Incidents"), "Incidents")
        self._tabs.addTab(QLabel("Performance Profiling"), "Performance Profiling")
        v_split.addWidget(self._tabs)

        self._tool_table = ToolCallTable()
        self._tool_table.rationale_requested.connect(self._show_rationale)
        v_split.addWidget(self._tool_table)
        v_split.setSizes([660, 180])

        self._right_panel = RightPanel(cai)
        self._right_panel.log_submitted.connect(self._on_log_submitted)
        h_split.addWidget(self._right_panel)
        h_split.setSizes([1180, 220])

    def _on_log_submitted(self, text: str):
        pass  # wire to self._cai.send_log(text)

    def _show_rationale(self, text: str):
        win = QWidget()
        win.setWindowTitle("Rationale")
        win.resize(400, 250)
        layout = QVBoxLayout(win)
        view = QTextEdit()
        view.setReadOnly(True)
        view.setPlainText(text)
        layout.addWidget(view)
        win.show()
        self._rationale_win = win

    @staticmethod
    def start(cai : ComputationalAgentInterface, environment : Environment):
        bridge = LogBridge()
        app = QApplication(sys.argv)
        app.setWindowIcon(qta.icon('mdi.bus', color='#51F50F'))
        window = MainWindow(bridge, cai, environment)
        window.show()
        sys.exit(app.exec())