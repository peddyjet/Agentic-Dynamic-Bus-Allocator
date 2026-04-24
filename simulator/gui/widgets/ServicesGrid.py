from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont, QResizeEvent
from PyQt6.QtWidgets import QWidget, QScrollArea, QGridLayout, QPushButton, QSizePolicy, QVBoxLayout, QLabel
from events.event_bus import default_bus
from events.EventNames import EventNames
from reasoning.environment.Environment import Environment

COLUMNS = 6
SPACING = 8
MIN_BUTTON_SIZE = 50


class ServicesGrid(QScrollArea):
    service_clicked = pyqtSignal(int)
    _env_changed = pyqtSignal()

    def __init__(self, environment: Environment, parent=None):
        super().__init__(parent)
        self._environment = environment

        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self._container = QWidget()
        self._service_selection_grid = QGridLayout(self._container)
        self._service_selection_grid.setSpacing(SPACING)
        self._service_selection_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.setWidget(self._container)

        self._env_changed.connect(self._refresh)
        default_bus.subscribe(EventNames.ENVIRONMENT_CHANGED, lambda: self._env_changed.emit())

        self._refresh()

    def _button_size(self) -> int:
        available = self.viewport().width() - SPACING * (COLUMNS + 1)
        return max(MIN_BUTTON_SIZE, available // COLUMNS)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        size = self._button_size()
        for i in range(self._service_selection_grid.count()):
            item = self._service_selection_grid.itemAt(i)
            btn = item.widget() if item else None
            if btn:
                btn.setFixedSize(size, size)
                inner = btn.findChild(QWidget)
                if inner:
                    inner.setGeometry(0, 0, size, size)

    def _refresh(self):
        while self._service_selection_grid.count():
            item = self._service_selection_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        size = self._button_size()
        for i, service in enumerate(sorted(self._environment.services.values(), key=lambda s: s.route_name)):
            service_button = QPushButton()
            service_button.setFixedSize(size, size)
            service_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            service_button.clicked.connect(lambda _, sid=service.id: self.service_clicked.emit(sid))

            button_widget = QWidget(service_button)
            button_widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            button_layout = QVBoxLayout(button_widget)
            button_layout.setContentsMargins(4, 4, 4, 4)
            button_layout.setSpacing(2)
            button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            route_name_label = QLabel(service.route_name)
            route_name_label.setFont(QFont("Courier New", 14, QFont.Weight.Bold))
            route_name_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            route_name_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

            id_label = QLabel(f"#{service.id}")
            id_label.setFont(QFont("Courier New", 7))
            id_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            id_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

            button_layout.addWidget(route_name_label)
            button_layout.addWidget(id_label)
            button_widget.setGeometry(0, 0, size, size)

            self._service_selection_grid.addWidget(service_button, i // COLUMNS, i % COLUMNS)