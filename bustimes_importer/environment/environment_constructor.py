import numpy as np
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from pydantic import BaseModel
from bustimes_importer.models.TripInstance import TripInstance
from bustimes_importer.models.Vehicle import Vehicle
from reasoning.orchestration.Environment import Environment
import reasoning.models as m

class InternalCallingPoint(BaseModel):
    stop: m.network_graph.StopNode.StopNode
    seconds_to_travel: float
    timestamp: datetime

def construct_environment(vehicles : List[Vehicle], trip_instances : List[TripInstance]) -> Environment:
    buses = {}
    for vehicle in vehicles:
        if vehicle.withdrawn:
            continue

        buses[vehicle.id] = __vehicle_to_bus(vehicle)

    stops, services = __trip_instances_to_stops_and_services(trip_instances)

    return Environment(
        buses=buses,
        stops=stops,
        services=services
    )

def __vehicle_to_bus(vehicle : Vehicle) -> m.Bus.Bus:
    return m.Bus.Bus(
        model = vehicle.vehicle_type.name,
        reg_plate = vehicle.reg,
        capacity = 100, # TODO: find API with access to this data
        power_mode = vehicle.vehicle_type.fuel,
        length = 10, # TODO: find API with access to this data
        double_deck = vehicle.vehicle_type.double_decker,
        coach = vehicle.vehicle_type.coach,
        faults = [],
        current_route = None,
        kilometres_until_empty = 100 # TODO: find API with access to this data
    )


def __trip_instances_to_stops_and_services(instances : List[TripInstance]) -> Tuple[
    Dict[str, m.network_graph.StopNode.StopNode],
    Dict[str, m.Service.Service]]:

    services : Dict[str, m.Service.Service] = {}
    stops : Dict[str, m.network_graph.StopNode.StopNode]= {}

    for instance in instances:
        service_ref = services.get(instance.service.id)
        if service_ref is None:
            services[instance.service.id] = (
                m.Service.Service(
                    id = instance.service.id,
                    route_id = instance.service.line_name,
                    trips = []))

        stop_nodes = __trip_times_to_stop_nodes(instance)

        __create_edges_along_path(stop_nodes)

        calling_points = []
        for calling_point in stop_nodes:
            __consolidate_edges(calling_point.stop)
            calling_points.append(
                m.Trip.Trip.CallingPoint(stop=calling_point.stop,
                                         timestamp=calling_point.timestamp,
                                         passenger_loadings = []
                                         ))
            if stops.get(calling_point.stop.id) is None:
                stops[calling_point.stop.id] = calling_point.stop

        trip = m.Trip.Trip(
            service = services[instance.service.id],
            calling_points = calling_points,
            id = instance.id,
        )

        services[instance.service.id].trips.append(trip)

    return stops, services

def __trip_times_to_stop_nodes(trip : TripInstance) -> List[InternalCallingPoint]:
    stop_nodes : List[InternalCallingPoint] = []
    for time in trip.times:
        node = m.network_graph.StopNode.StopNode(id = time.id,
                                                 name = time.stop.name,
                                                 latitude = time.stop.location[1],
                                                 longitude = time.stop.location[0],
                                                 is_depot = False,
                                                 edges = [])

        arrival = datetime.strptime(time.aimed_arrival_time, "%H:%M:%S")\
            if time.aimed_arrival_time is not None else None

        departure = datetime.strptime(time.aimed_departure_time, "%H:%M:%S") \
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
        edge = m.network_graph.Edge.Edge(source = stop1, target = stop2, seconds_to_travel = path[i].seconds_to_travel)
        stop1.edges.append(edge)
        stop2.edges.append(edge)

def __consolidate_edges(stop : m.network_graph.StopNode.StopNode):
    edge_dict : Dict[str, Tuple[m.network_graph.Edge.Edge, int]] = {} # Name, (Edge, Number of Consolidations)
    for edge in stop.edges:
        edge_name = edge.source.id + " -> " + edge.target.id
        edge_dict_entry = edge_dict.get(edge_name)
        if edge_dict_entry is None:
            edge_dict[edge_name] = (edge, 1)
            continue
        edge_dict_entry[0].seconds_to_travel = \
            (edge_dict_entry[0].seconds_to_travel + edge.seconds_to_travel) / edge_dict_entry[1]

        edge_dict_entry[1] += 1

    stop.edges = list(map(lambda edge_entry: edge_entry[0], edge_dict.values()))