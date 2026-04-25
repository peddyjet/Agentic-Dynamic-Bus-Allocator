import asyncio
import threading
import time
from datetime import timedelta
from typing import List, Dict, Tuple

import numpy as np
from haversine import haversine

from events.EventNames import EventNames
from events.event_bus import default_bus
from reasoning.agents.tools.distance_calculator import distance_calculator
from reasoning.environment.IncidentStore import IncidentStore
from reasoning.models.agent_exposed_data import AgentExposedData
from reasoning.models.bus import Bus
from reasoning.models.network_graph import StopNode
from reasoning.models.timetabling import Trip


class DeterministicBusAllocator:

    def __init__(self, data: AgentExposedData, name: str = "DBA"):
        self._data = data
        self._name = name
        self._allocation_thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def allocate_relevant_trips(self, time_threshold: timedelta):
        allocated_buses = self._data.environment().find_buses_on_trips()
        trips = [t for t in self._data.environment().trips.values()
                 if t.start_time(True) < time_threshold + self._data.environment().current_time
                 and t.end_time(True) > self._data.environment().current_time
                 and not allocated_buses.get(t.id)]
        if not trips: return
        self.__start_allocation_thread(trips)

    def allocate_buses(self, trip_ids: List[int]):
        trips = [t for t in (self._data.environment().trips.get(tid) for tid in trip_ids) if t is not None]
        if not trips: return
        self.__start_allocation_thread(trips)

    def __start_allocation_thread(self, trips: List[Trip]):
        default_bus.emit(EventNames.AGENT_BUSY, agent=self._name, queue_depth=len(trips))
        self._allocation_thread = threading.Thread(target=self.__run_allocations, args=(trips,), daemon=True)
        self._allocation_thread.start()

    def send_log(self, msg: str):
        pass

    async def wait_for_agents(self):
        while self._allocation_thread is not None and self._allocation_thread.is_alive():
            await asyncio.sleep(0.05)

    def get_system_status(self) -> Dict[str, int]:
        return {}

    def get_incident_store(self) -> IncidentStore:
        return self._data.incident_store()

    def __run_allocations(self, trips: List[Trip]):
        for trip in trips:
            step_start_time = time.monotonic()
            self.__allocate_bus(trip)
            duration_ms = (time.monotonic() - step_start_time) * 1000
            default_bus.emit(EventNames.STEP_COMPLETE, agent=self._name, duration_ms=duration_ms)
        default_bus.emit(EventNames.AGENT_BUSY, agent=self._name, queue_depth=0)

    def __allocate_bus(self, trip: Trip):
        buses = list(self._data.environment().buses.values())
        if not buses: return

        components: List[Tuple[Bus, float, float, float]] = [
            (bus, *self.__heuristics(bus, trip)) for bus in buses
        ]

        max_dist  = max(c[1] for c in components) or 1.0
        max_cap   = max(c[2] for c in components) or 1.0
        max_delay = max(c[3] for c in components) or 1.0

        best_bus, best_score = None, None
        for bus, dist, cap, delay in components:
            score = np.sqrt((dist / max_dist) ** 2 + (cap / max_cap) ** 2 + (delay / max_delay) ** 2)
            if best_bus is None or score < best_score:
                best_bus, best_score = bus, score

        if best_bus is None: return

        with self._lock:
            if best_bus.current_trip_id_queue is None:
                best_bus.current_trip_id_queue = []
            best_bus.current_trip_id_queue.append(trip.id)

        default_bus.emit(EventNames.ENVIRONMENT_CHANGED)

    def __heuristics(self, bus: Bus, trip: Trip):
        pos = self.__final_position(bus)
        trip_start = trip.calling_points[0].stop
        distance = haversine((pos.latitude, pos.longitude), (trip_start.latitude, trip_start.longitude))
        cap_diff = abs(bus.capacity - trip.average_passenger_loading())
        delay = self.__predicted_delay_seconds(bus, trip)
        return distance, cap_diff, delay

    def __final_position(self, bus: Bus):
        if bus.current_trip_id_queue:
            last_trip = self._data.environment().trips.get(bus.current_trip_id_queue[-1])
            if last_trip and last_trip.calling_points:
                return last_trip.calling_points[-1].stop
        fallback = self._data.environment().stops.get(bus.current_stop_id)
        return fallback or next(iter(self._data.environment().stops.values()))

    def __predicted_delay_seconds(self, bus: Bus, trip: Trip):
        if not bus.current_trip_id_queue:
            return 0.0

        last_trip = self._data.environment().trips.get(bus.current_trip_id_queue[-1])

        if not last_trip or not last_trip.calling_points:
            return 0.0

        deadrun_secs = distance_calculator(last_trip.calling_points[-1].stop, trip.calling_points[0].stop)
        earliest_arrival = last_trip.end_time(as_date=True) + timedelta(seconds=deadrun_secs)
        return max(0.0, (earliest_arrival - trip.start_time(as_date=True)).total_seconds())