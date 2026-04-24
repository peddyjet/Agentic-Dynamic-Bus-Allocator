from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QTableWidget, QHeaderView, QTableWidgetItem
from events.event_bus import default_bus
from events.EventNames import EventNames
from reasoning.environment.Environment import Environment
from simulator.gui.gui_util import icon_label


def _fmt_delay(seconds: float) -> str:
    if seconds <= 0:
        return "None"
    m, s = divmod(int(seconds), 60)
    return f"{m}m {s}s" if m else f"{s}s"


class BusesTable(QTableWidget):
    expansion_requested = pyqtSignal(str)
    _env_changed = pyqtSignal()

    def __init__(self, environment: Environment, parent=None):
        super().__init__(0, 8, parent)
        self._environment = environment
        self.setHorizontalHeaderLabels(["ID", "Reg Plate", "Model", "Faults", "Current Trip IDs", "Current Stop", "Delay", "Passengers"])
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.verticalHeader().setVisible(False)

        header = self.horizontalHeader()
        header.setStretchLastSection(False)
        header.setDefaultSectionSize(140)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)

        self.doubleClicked.connect(
            lambda idx: self.expansion_requested.emit(self._bus_detail(idx.row()))
        )

        self._env_changed.connect(self._refresh)
        default_bus.subscribe(EventNames.ENVIRONMENT_CHANGED, lambda: self._env_changed.emit())

        self._refresh()

    def _bus_detail(self, row: int) -> str:
        id_item = self.item(row, 0)
        if id_item is None:
            return "No data."
        bus_id = int(id_item.text())
        bus = self._environment.buses.get(bus_id)
        if bus is None:
            return f"Bus {bus_id} not found."

        trips = ", ".join(str(t) for t in bus.current_trip_id_queue) if bus.current_trip_id_queue else "Unallocated"
        stop = str(bus.current_stop_id) if bus.current_stop_id is not None else "Currently in Depot"
        faults = "\n  ".join(bus.faults) if bus.faults else "None"

        return (
            f"ID:             {bus.id}\n"
            f"Reg Plate:      {bus.reg_plate}\n"
            f"Model:          {bus.model}\n"
            f"Capacity:       {bus.capacity}\n"
            f"Power Mode:     {bus.power_mode}\n"
            f"Length:         {bus.length}m\n"
            f"Height:         {bus.height}m\n"
            f"Double Deck:    {bus.double_deck}\n"
            f"Coach:          {bus.coach}\n"
            f"Current Stop:   {stop}\n"
            f"Trip Queue:     {trips}\n"
            f"Faults:  {'\n' if len(faults) > 0 else ''}{faults}"
        )

    def _refresh(self):
        scroll = self.verticalScrollBar().value()
        self.setRowCount(0)

        for bus in sorted(self._environment.buses.values(), key=lambda b: b.model):
            row = self.rowCount()
            self.insertRow(row)

            faults = "; ".join(bus.faults) if bus.faults else "None"

            trips = ", ".join(f"{t} ({self._environment.trips[t].service.route_name})"
                              for t in bus.current_trip_id_queue) \
                if bus.current_trip_id_queue else "Unallocated"

            stop = str(self._environment.stops[bus.current_stop_id].name) \
                if bus.current_stop_id is not None else "Currently in Depot"

            passengers = f"{int(bus.current_passengers)} / {bus.capacity}"

            for col, val in enumerate([str(bus.id), bus.reg_plate, None, faults, trips, stop,
                                       _fmt_delay(bus.delay_seconds), passengers]):
                if val is not None:
                    self.setItem(row, col, QTableWidgetItem(val))

            if bus.capacity <= 16:
                icon = "mdi.van-passenger"
            elif bus.double_deck:
                icon = "mdi.bus-double-decker"
            else:
                icon = "mdi.bus-side"

            self.setCellWidget(row, 2, icon_label(icon, bus.model))

        self.verticalScrollBar().setValue(scroll)