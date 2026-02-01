from datetime import datetime, timedelta
from typing import List, Dict
from pydantic import BaseModel
from reasoning.models.bus import Bus
from reasoning.models.timetabling import Service, Trip
from reasoning.models.network_graph import StopNode

class Environment(BaseModel):
    buses: Dict[int, Bus] # Reg plate - Bus
    stops: Dict[int, StopNode] # ID - Stop
    services: Dict[int, Service] # ID - Service
    trips: Dict[int, Trip] # ID - Trip
    current_time: datetime

    def find_buses_on_trips(self):
        organised_buses: Dict[int, List[Bus]] = {}
        for bus in self.buses.values():
            trip_id = bus.current_trip_id_queue[0] if len(bus.current_trip_id_queue) > 0 else -1
            if not organised_buses.get(trip_id):
                organised_buses[trip_id] = []

            organised_buses[trip_id].append(bus)
        return organised_buses