import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMainWindow, QApplication, QWidget, QVBoxLayout, QSplitter, QTabWidget, QLabel, QTextEdit
from reasoning.agent_interface.BusAllocatorProtocol import BusAllocatorProtocol
from reasoning.environment.Environment import Environment
from reasoning.environment.IncidentStore import IncidentStore
from simulator.gui.widgets.BusesTable import BusesTable
from simulator.gui.widgets.CallingPatternTable import CallingPatternTable
from simulator.gui.widgets.IncidentsTable import IncidentsTable
from simulator.gui.widgets.ServicesGrid import ServicesGrid
from simulator.gui.widgets.RightPanel import RightPanel
from simulator.SimulationManager import SimulationManager
from simulator.gui.widgets.SystemTracebackTable import SystemTracebackTable
from simulator.gui.widgets.PerformanceProfilerWidget import PerformanceProfilerWidget
import qtawesome as qta
from simulator.gui.widgets.TripsTable import TripsTable
from profiling.PerformanceProfiler import PerformanceProfiler

class MainWindow(QMainWindow):
    def __init__(self, cai : BusAllocatorProtocol, environment : Environment, incident_store : IncidentStore, seed: int = 42, profiler: PerformanceProfiler | None = None):
        super().__init__()

        self._cai = cai
        self._environment = environment
        self._seed = seed

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
        buses_table = BusesTable(self._environment)
        buses_table.expansion_requested.connect(self._open_text_window)
        self._tabs.addTab(buses_table, "Buses")

        services_and_trips = QSplitter(Qt.Orientation.Horizontal)
        services_grid = ServicesGrid(self._environment)
        trips_table = TripsTable(self._environment)
        trips_table.expansion_requested.connect(self._open_calling_pattern_table)
        services_grid.service_clicked.connect(trips_table.show_service)
        services_and_trips.addWidget(services_grid)
        services_and_trips.addWidget(trips_table)
        services_and_trips.setSizes([500, 500])
        self._tabs.addTab(services_and_trips, "Services and Trips")

        incidents_table = IncidentsTable(incident_store)
        incidents_table.expansion_requested.connect(self._open_text_window)
        self._tabs.addTab(incidents_table, "Incidents")

        profiler_tab = PerformanceProfilerWidget(profiler) if profiler is not None else QLabel("No profiler attached.")
        self._tabs.addTab(profiler_tab, "Performance Profiling")
        v_split.addWidget(self._tabs)

        self._tool_table = SystemTracebackTable()
        self._tool_table.rationale_requested.connect(self._open_text_window)
        v_split.addWidget(self._tool_table)
        v_split.setSizes([660, 180])

        self._sim_manager = SimulationManager(environment, cai, seed=seed)
        self._right_panel = RightPanel(cai, self._sim_manager)
        self._right_panel.log_submitted.connect(self._on_log_submitted)
        h_split.addWidget(self._right_panel)
        h_split.setSizes([1180, 220])

    def _on_log_submitted(self, text: str):
        self._cai.send_log(text)
        pass

    def _open_text_window(self, text: str):
        win = QWidget()
        win.setWindowTitle("Additional Information")
        win.setWindowIcon(qta.icon('mdi.information-outline', color='#51F50F'))
        win.resize(600, 375)
        layout = QVBoxLayout(win)

        view = QTextEdit()
        view.setReadOnly(True)
        view.setPlainText(text)
        layout.addWidget(view)
        win.show()

        self._text_window = win

    def _open_calling_pattern_table(self, trip_id: str):
        win = QWidget()
        win.setWindowTitle(f"Calling Pattern for Trip {trip_id}")
        win.setWindowIcon(qta.icon('mdi.bus-stop-covered', color='#51F50F'))
        win.resize(1000, 550)
        layout = QVBoxLayout(win)

        table = CallingPatternTable(self._environment)
        table.show_trip(int(trip_id))
        layout.addWidget(table)
        win.show()

        self.calling_pattern_window = win

    @staticmethod
    def start(cai : BusAllocatorProtocol, environment : Environment, profiler: PerformanceProfiler | None = None, seed: int = 36):
        app = QApplication(sys.argv)
        app.setWindowIcon(qta.icon('mdi.bus', color='#51F50F'))
        window = MainWindow(cai, environment, cai.get_incident_store(), seed=seed, profiler=profiler)
        window.setWindowIcon(qta.icon('mdi.bus', color='#51F50F'))
        window.show()
        window.activateWindow()
        window.raise_()
        sys.exit(app.exec())