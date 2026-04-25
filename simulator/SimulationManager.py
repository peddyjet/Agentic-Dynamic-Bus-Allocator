import random
from datetime import datetime, timedelta
from typing import Optional, List
from events.EventNames import EventNames
from events.event_bus import default_bus
from reasoning.agent_interface.BusAllocatorProtocol import BusAllocatorProtocol
from reasoning.agents.tools.distance_calculator import distance_calculator
from reasoning.environment.Environment import Environment
from reasoning.models.bus import Bus
from reasoning.models.timetabling import Trip
from simulator.surge_generator import surge_generator

PEAK_MULTIPLIERS = {
        7: 3.0, 8: 4.0, 9: 2.0,
        12: 1.5, 13: 1.5,
        15: 2.5, 16: 3.5, 17: 2.5, 18: 2.5,
        19: 1.5, 20: 1.0, 21: 0.75, 22: 0.5, 23: 1.25,
}
MAX_LOADING_HISTORY = 20
ALLOCATION_INTERVAL = timedelta(minutes=10)
ALLOCATION_LOOKAHEAD = timedelta(hours=1)
LOADING_SNAPSHOT_INTERVAL = timedelta(hours=1)
SURGE_INTERVAL_SECONDS = 7200.0
INITIAL_LOADING_SAMPLES = 5
INITIAL_PAX_MIN = 2.0
INITIAL_PAX_MAX = 20.0
TRAFFIC_DELAY_STD = 4.0
TRAFFIC_DELAY_STEP_BASE = 40.0
DEFAULT_AVG_PAX = 8.0
PAX_DEMAND_VARIATION_MIN = 0.5
PAX_DEMAND_VARIATION_MAX = 1.5
PAX_DEMAND_SCALE = 0.3
ALIGHT_FRACTION_MIN = 0.1
ALIGHT_FRACTION_MAX = 0.4
SURGE_TRIGGER_SALT = 1
SURGE_PARAMS_SALT = 2

class SimulationManager:
    def __init__(self, environment: Environment, cai: BusAllocatorProtocol,
                 step_seconds: int = 60, seed: int = 36):
        self._environment = environment
        self._cai = cai
        self._paused = False
        self._force_pause = False
        self.step_seconds = step_seconds
        self._seed = seed
        self._last_allocation_time = environment.current_time
        self._last_loading_update = environment.current_time
        self._stranding_notified: set = set()

        self.__seed_initial_passenger_loadings()

        default_bus.subscribe(EventNames.AGENT_BUSY, self.__assess_agent_business)

    def is_paused(self):
        return self._paused or self._force_pause

    def toggle_pause(self):
        self._paused = not self._paused

    def tick(self):
        if self.is_paused():
            return

        # Increment the time
        self._environment.current_time += timedelta(seconds=self.step_seconds)

        # If ten mins have passed, allocate and trips to the CRA
        if self._environment.current_time - self._last_allocation_time >= ALLOCATION_INTERVAL:
            self._cai.allocate_relevant_trips(ALLOCATION_LOOKAHEAD)
            self._last_allocation_time = self._environment.current_time


        # Accumulate waiting passengers at calling points every tick
        self.__generate_waiting_passengers()

        # Snapshot waiting passengers into loading history once per hour
        if self._environment.current_time - self._last_loading_update >= LOADING_SNAPSHOT_INTERVAL:
            self.__snapshot_calling_point_loadings()
            self._last_loading_update = self._environment.current_time

        # Make buses get delayed
        self.__apply_traffic_variation()

        # Issue a random surge around every two hours
        current_time = self._environment.current_time
        time_salt = current_time.hour * 3600 + current_time.minute * 60 + current_time.second
        surge_rng = self.__rng(time_salt, SURGE_TRIGGER_SALT)
        if surge_rng.random() < self.step_seconds / SURGE_INTERVAL_SECONDS:
            self.__issue_surge()

        self.sync()

    def sync(self):
        current_time = self._environment.current_time
        changed = False

        for bus in self._environment.buses.values():
            if self.__sync_bus(bus, current_time):
                changed = True

        if changed:
            default_bus.emit(EventNames.ENVIRONMENT_CHANGED)

    def __rng(self, *keys: int) -> random.Random:
        h = self._seed
        for k in keys:
            h ^= k * 2654435761
        return random.Random(h & 0xFFFFFFFF)

    def __issue_surge(self):
        current_time = self._environment.current_time
        time_bucket = current_time.hour * 3600 + current_time.minute * 60 + current_time.second
        rng = self.__rng(time_bucket, SURGE_PARAMS_SALT)
        surge_generator(self._cai, self._environment, rng.random(), rng.random(), rng.random())

    def __seed_initial_passenger_loadings(self):
        for trip in self._environment.trips.values():
            for cp in trip.calling_points:
                stop = self._environment.stops.get(cp.stop.id)
                density = stop.density if stop is not None else 1.0
                peak = PEAK_MULTIPLIERS.get(cp.timestamp.hour, 1.0)
                rng = self.__rng(cp.stop.id, trip.id)
                for _ in range(INITIAL_LOADING_SAMPLES):
                    base = DEFAULT_AVG_PAX * density * peak * rng.uniform(PAX_DEMAND_VARIATION_MIN, PAX_DEMAND_VARIATION_MAX) * PAX_DEMAND_SCALE
                    cp.passenger_loadings.append(round(base))

    def __apply_traffic_variation(self):
        current_time = self._environment.current_time
        time_bucket = current_time.hour * 3600 + current_time.minute * 60 + current_time.second

        for bus in self._environment.buses.values():
            if not bus.current_trip_id_queue:
                continue

            density = 1.0
            if bus.current_stop_id is not None:
                stop = self._environment.stops.get(bus.current_stop_id)
                if stop is not None:
                    density = stop.density

            rng = self.__rng(bus.id, time_bucket)
            std = TRAFFIC_DELAY_STD * density * (self.step_seconds / TRAFFIC_DELAY_STEP_BASE)
            delta = rng.gauss(0, std)
            bus.delay_seconds = max(0.0, bus.delay_seconds + delta)

    def __generate_waiting_passengers(self):
        current_time = self._environment.current_time
        peak = PEAK_MULTIPLIERS.get(current_time.hour, 1.0)
        time_slot = current_time.hour * 12 + current_time.minute // 5

        for trip in self._environment.trips.values():
            for cp in trip.calling_points:
                rng = self.__rng(cp.stop.id, trip.id, time_slot)
                base = (cp.average_pax() or DEFAULT_AVG_PAX) * cp.stop.density * peak * rng.uniform(PAX_DEMAND_VARIATION_MIN, PAX_DEMAND_VARIATION_MAX) * PAX_DEMAND_SCALE
                cp.waiting_passengers += base * (self.step_seconds / 3600.0)

    def __snapshot_calling_point_loadings(self):
        for trip in self._environment.trips.values():
            for cp in trip.calling_points:
                cp.passenger_loadings.append(round(cp.waiting_passengers))
                if len(cp.passenger_loadings) > MAX_LOADING_HISTORY:
                    cp.passenger_loadings.pop(0)

    def __assess_agent_business(self, agent: str, queue_depth: int):
        system_status = self._cai.get_system_status()
        self._force_pause = any(v > 0 for v in system_status.values()) if system_status else queue_depth > 0

    def __sync_bus(self, bus: Bus, current_time: datetime):
        original_stop = bus.current_stop_id
        original_queue_len = len(bus.current_trip_id_queue) if bus.current_trip_id_queue else 0

        if not bus.current_trip_id_queue:
            return False

        queue: List[int] = bus.current_trip_id_queue
        delay = timedelta(seconds=bus.delay_seconds)
        current_trip: Optional[Trip] = None

        # Whilst the bus needs to do a trip
        while queue:
            trip = self._environment.trips[queue[0]]
            # If the trip has (or should have) finished,
            if current_time >= trip.end_time(as_date=True) + delay:
                queue.pop(0)
                self._stranding_notified.discard((bus.id, trip.id))
                bus.current_stop_id = trip.calling_points[-1].stop.id
                if queue:
                    # Find how long it will take to deadrun to the start of the next trip, and from it calculate the delay
                    # it will cause.
                    next_trip = self._environment.trips[queue[0]]
                    last_stop = trip.calling_points[-1].stop
                    deadrun_secs = distance_calculator(last_stop, next_trip.calling_points[0].stop)
                    scheduled_depart = next_trip.start_time(as_date=True) - timedelta(seconds=deadrun_secs)
                    late_secs = max(0.0, (current_time - scheduled_depart).total_seconds())
                    bus.delay_seconds = late_secs
                    delay = timedelta(seconds=late_secs)
                else:
                    delay = timedelta(0)
                    bus.delay_seconds = 0.0
            else:
                current_trip = trip
                break

        # If the trip queue still has trips in,
        if queue:
            trip = current_trip or self._environment.trips[queue[0]]
            trip_start = trip.start_time(as_date=True) + delay

            if current_time >= trip_start:
                bus.current_stop_id = self.__find_stop_at_time(trip, current_time, delay)
            else:
                bus.current_stop_id = self.__run_deadrun(bus, trip, current_time)

        new_stop = bus.current_stop_id
        if new_stop is not None and new_stop != original_stop and current_trip is not None:
            self._handle_stop_arrival(bus, new_stop, current_trip)

        return bus.current_stop_id != original_stop or len(queue) != original_queue_len

    def _handle_stop_arrival(self, bus: Bus, stop_id: int, trip: Trip):
        stop = self._environment.stops.get(stop_id)
        if stop is None or stop.is_depot:
            return

        cp = next((c for c in trip.calling_points if c.stop.id == stop_id), None)
        if cp is None:
            return

        cp.passenger_loadings.append(round(cp.waiting_passengers))
        if len(cp.passenger_loadings) > MAX_LOADING_HISTORY:
            cp.passenger_loadings.pop(0)

        default_bus.emit(EventNames.DELAY_RECORDED, delay_seconds=bus.delay_seconds)

        rng = self.__rng(bus.id, stop_id)
        alight_fraction = rng.uniform(ALIGHT_FRACTION_MIN, ALIGHT_FRACTION_MAX)
        bus.current_passengers = round(max(0.0, bus.current_passengers * (1.0 - alight_fraction)))

        remaining = bus.capacity - bus.current_passengers
        boarded = round(min(cp.waiting_passengers, remaining))
        bus.current_passengers += boarded
        cp.waiting_passengers = max(0.0, cp.waiting_passengers - boarded)

        if cp.waiting_passengers > 0 and bus.current_passengers >= bus.capacity:
            left_behind = round(cp.waiting_passengers)
            key = (bus.id, trip.id)
            if key not in self._stranding_notified:
                self._stranding_notified.add(key)
                default_bus.emit(EventNames.ABANDONED_PASSENGER, count=left_behind)
                self._cai.send_log(
                    f"Bus {bus.reg_plate} (ID {bus.id}) left behind {left_behind} passenger(s) at "
                    f"{stop.name} (Stop ID {stop_id}) on route {trip.service.route_name} "
                    f"(Trip ID {trip.id}). Bus was at capacity ({bus.capacity})."
                )

    @staticmethod
    def __find_stop_at_time(trip: Trip, current_time: datetime, delay: timedelta = timedelta(0)):
        last_stop_id = None
        for cp in trip.calling_points:
            if current_time >= cp.timestamp + delay:
                last_stop_id = cp.stop.id
            else:
                break
        return last_stop_id

    def __run_deadrun(self, bus: Bus, trip: Trip, current_time: datetime):
        first_stop = trip.calling_points[0].stop
        trip_start = trip.start_time(as_date=True) + timedelta(seconds=bus.delay_seconds)

        current_stop = (
            self._environment.stops.get(bus.current_stop_id)
            if bus.current_stop_id is not None
            else None
        )

        if current_stop is None:
            travel_seconds = 0.0
        else:
            travel_seconds = distance_calculator(current_stop, first_stop)

        depart_time = trip_start - timedelta(seconds=travel_seconds)

        if current_time >= depart_time:
            return None
        return bus.current_stop_id