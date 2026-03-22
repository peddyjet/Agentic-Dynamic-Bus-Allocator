import json
from datetime import datetime
from typing import List, Dict, Tuple
from pydantic import BaseModel
from bustimes_importer.models.TripInstance import TripInstance
from bustimes_importer.models.Vehicle import Vehicle
from reasoning.environment.Environment import Environment
import reasoning.models as m

with (open("bustimes_importer/data/additional_bus_specs.json", "r", encoding="utf-8") as f):
    bus_specs = json.loads(f.read())["buses"]
    ADDITIONAL_BUS_SPECS = {}
    for bus in bus_specs:
        ADDITIONAL_BUS_SPECS[bus["name"]] = bus

class InternalCallingPoint(BaseModel):
    stop: m.network_graph.StopNode
    seconds_to_travel: float
    timestamp: datetime

def construct_environment(vehicles : List[Vehicle], trip_instances : List[TripInstance], date : datetime, log : bool = False) -> Environment:
    if log:
        print("     Converting vehicles to buses (3c/4)")
    buses = {}
    for vehicle in vehicles:
        if vehicle.withdrawn:
            continue

        buses[vehicle.id] = __vehicle_to_bus(vehicle)

    if log:
        print("     Converting trips to stops and services... (3d/4)")
    stops, services = __trip_instances_to_stops_and_services(trip_instances, date)

    if log:
        print("     Decomposing trips (3d/4)")
    trips = {}
    for service in services.values():
        for trip in service.trips:
            trips[trip.id] = trip

    starting_time = datetime(date.year, date.month, date.day, hour = 4, minute = 30, second = 0)

    if log:
        print("     Constructing Environment (3e/4)")
    return Environment(
        buses=buses,
        stops=stops,
        services=services,
        trips=trips,
        current_time=starting_time
    )

def __vehicle_to_bus(vehicle : Vehicle) -> m.bus.Bus:
    return m.bus.Bus(
        model = vehicle.vehicle_type.name,
        reg_plate = vehicle.reg,
        capacity = ADDITIONAL_BUS_SPECS[vehicle.vehicle_type.name]["capacity"],
        power_mode = vehicle.vehicle_type.fuel,
        length = ADDITIONAL_BUS_SPECS[vehicle.vehicle_type.name]["length"],
        double_deck = vehicle.vehicle_type.double_decker,
        coach = vehicle.vehicle_type.coach,
        faults = [],
        current_trip_id_queue = [],
        current_stop_id = None,
        height = ADDITIONAL_BUS_SPECS[vehicle.vehicle_type.name]["height"],
        id = vehicle.id
    )


def __trip_instances_to_stops_and_services(instances : List[TripInstance], date : datetime) -> Tuple[
    Dict[int, m.network_graph.StopNode],
    Dict[int, m.timetabling.Service]]:

    services : Dict[int, m.timetabling.Service] = {}
    stops : Dict[int, m.network_graph.StopNode]= {}

    for instance in instances:
        service_ref = services.get(instance.service.id)
        if service_ref is None:
            services[instance.service.id] = (
                m.timetabling.Service(
                    id = instance.service.id,
                    route_name = instance.service.line_name,
                    trips = []))

        stop_nodes = __trip_times_to_stop_nodes(instance)

        __create_edges_along_path(stop_nodes)

        calling_points = []
        for calling_point in stop_nodes:
            __consolidate_edges(calling_point.stop)
            calling_points.append(
                m.timetabling.Trip.CallingPoint(stop=calling_point.stop,
                                                timestamp=datetime(year=date.year, month=date.month, day=date.day,
                                                                   hour=calling_point.timestamp.hour,
                                                                   minute=calling_point.timestamp.minute,
                                                                   second=calling_point.timestamp.second),
                                                passenger_loadings = []
                                                ))
            if stops.get(calling_point.stop.id) is None:
                stops[calling_point.stop.id] = calling_point.stop

        trip = m.timetabling.Trip(
            service = services[instance.service.id],
            calling_points = calling_points,
            id = instance.id,
        )

        services[instance.service.id].trips.append(trip)

    return stops, services
#TODO: Currently the stop graphs are disparate, and never intertwine. This needs fixing so interlining can occur.
# Solving this will likely require finding stops with the same name and letting them share edges. This is not the cleanest
# solution, however would solve the problem without too many performance penalties.
def __trip_times_to_stop_nodes(trip : TripInstance) -> List[InternalCallingPoint]:
    stop_nodes : List[InternalCallingPoint] = []
    for time in trip.times:
        node = m.network_graph.StopNode(id = time.id,
                                                 name = time.stop.name,
                                                 latitude = time.stop.location[1],
                                                 longitude = time.stop.location[0],
                                                 is_depot = False,
                                                 edges = [])

        arrival = datetime.strptime(time.aimed_arrival_time, "%H:%M")\
            if time.aimed_arrival_time is not None else None

        departure = datetime.strptime(time.aimed_departure_time, "%H:%M") \
            if time.aimed_departure_time is not None else None

        seconds_to_travel = ((departure - arrival).total_seconds()
                                if arrival is not None and departure is not None else 0)

        timestamp = departure if departure is not None else arrival

        stop_nodes.append(InternalCallingPoint(stop=node,
                                               seconds_to_travel=seconds_to_travel,
                                               timestamp=timestamp))
    return stop_nodes

def __create_edges_along_path(path : List[InternalCallingPoint]):
    for i in range(len(path) - 1):
        stop1 = path[i].stop
        stop2 = path[i + 1].stop
        edge = m.network_graph.Edge(source = stop1, target = stop2, seconds_to_travel = path[i].seconds_to_travel)
        stop1.edges.append(edge)
        stop2.edges.append(edge)

def __consolidate_edges(stop : m.network_graph.StopNode):
    edge_dict : Dict[str, Tuple[m.network_graph.Edge, int]] = {} # Name, (Edge, Number of Consolidations)
    for edge in stop.edges:
        edge_name = str(edge.source.id) + "-" + str(edge.target.id)
        edge_dict_entry = edge_dict.get(edge_name)
        if edge_dict_entry is None:
            edge_dict[edge_name] = (edge, 1)
            continue
        edge_dict_entry[0].seconds_to_travel = \
            (edge_dict_entry[0].seconds_to_travel + edge.seconds_to_travel) / edge_dict_entry[1]

        edge_dict_entry[1] += 1

    stop.edges = list(map(lambda edge_entry: edge_entry[0], edge_dict.values()))