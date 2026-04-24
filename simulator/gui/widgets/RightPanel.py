from PyQt6.QtCore import pyqtSignal, QTimer, Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton, QFrame
import qtawesome as qta
from events.event_bus import default_bus
from events.EventNames import EventNames
from reasoning.agent_interface.ComputationalAgentInterface import ComputationalAgentInterface
from simulator.SimulationManager import SimulationManager
from simulator.gui.gui_util import icon_label, find_relevant_icon


class RightPanel(QWidget):
    log_submitted = pyqtSignal(str)
    _agent_status_changed = pyqtSignal(str, int)  # agent name, queue_depth
    _time_changed = pyqtSignal()

    def __init__(self, cai: ComputationalAgentInterface, sim_manager: SimulationManager, parent=None):
        super().__init__(parent)
        self.setFixedWidth(220)
        layout = QVBoxLayout(self)
        self._cai = cai
        self._sim_manager = sim_manager

        # Simulation Control System
        layout.addWidget(QLabel("Simulation Controls"))

        ## Clock display
        self.clock_label = QLabel("00:00")
        self.clock_label.setFont(QFont("Courier New", 24, QFont.Weight.Bold))
        self.clock_label.setStyleSheet("QLabel { padding: 5px; border-radius: 3px; }")
        self.clock_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.clock_label)

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._tick)
        self.clock_timer.start(1000)

        ## Pause/Resume button
        self._pause_btn = QPushButton("Pause")
        self._pause_btn.setIcon(qta.icon("mdi.pause"))
        self._pause_btn.clicked.connect(self._toggle_pause)
        layout.addWidget(self._pause_btn)

        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line1)

        # Log submitting system
        layout.addWidget(QLabel("Send log to CRA"))
        self.log_input = QTextEdit()
        self.log_input.setFixedHeight(90)
        layout.addWidget(self.log_input)

        log_submit_btn = QPushButton("Submit Log")
        log_submit_btn.clicked.connect(self._submit)
        log_submit_btn.setIcon(qta.icon("mdi.send"))
        layout.addWidget(log_submit_btn)

        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line2)

        # System Status System
        layout.addWidget(QLabel("System Status"))
        self.status_labels = {}
        for name, items in cai.get_system_status().items():
            container = icon_label(find_relevant_icon(name),
                                   f"{name.upper()}: "
                                   + ("Free" if items == 0 else "Busy")
                                   + f" ({items} job{'s' if items != 1 else ''})")
            text_lbl = container.layout().itemAt(1).widget()
            text_lbl.setFont(QFont("Courier New", 8))
            layout.addWidget(container)
            self.status_labels[name] = text_lbl

        layout.addStretch()

        self._agent_status_changed.connect(self._on_agent_status_changed)
        self._time_changed.connect(self._update_clock_display)
        default_bus.subscribe(EventNames.AGENT_BUSY,
                              lambda agent, queue_depth: self._agent_status_changed.emit(agent, queue_depth))
        default_bus.subscribe(EventNames.ENVIRONMENT_CHANGED,
                              lambda: self._time_changed.emit())

        self._update_clock_display()

    def _tick(self):
        self._sim_manager.tick()
        if not self._sim_manager.is_paused():
            self._update_clock_display()

    def _toggle_pause(self):
        self._sim_manager.toggle_pause()
        if self._sim_manager.is_paused():
            self._pause_btn.setText("Resume")
            self._pause_btn.setIcon(qta.icon("mdi.play"))
        else:
            self._pause_btn.setText("Pause")
            self._pause_btn.setIcon(qta.icon("mdi.pause"))

    def _update_clock_display(self):
        t = self._sim_manager._environment.current_time
        self.clock_label.setText(t.strftime("%H:%M"))

    def _submit(self):
        text = self.log_input.toPlainText().strip()
        if text:
            self.log_submitted.emit(text)
            self.log_input.clear()

    def _on_agent_status_changed(self, agent: str, queue_depth: int):
        self.set_agent_status(agent, queue_depth > 0, queue_depth)

    def set_agent_status(self, name: str, busy: bool, jobs: int = 0):
        if name in self.status_labels:
            status = f"Busy ({jobs} job{'s' if jobs != 1 else ''})" if busy else "Free (0 jobs)"
            self.status_labels[name].setText(f"{name}: {status}")