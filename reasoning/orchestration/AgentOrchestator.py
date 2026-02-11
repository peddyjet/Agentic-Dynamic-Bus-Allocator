import datetime
import json
from typing import List
from camel.agents import ChatAgent
from camel.models import BaseModelBackend
from camel.toolkits import FunctionTool
from pydantic import TypeAdapter
from reasoning.models.errors import ReprimandableError, FatalError
from reasoning.models.responses import ErrorResponse, DefaultResponse, Allocation
from reasoning.orchestration.Environment import Environment
from reasoning.orchestration.distance_calculator import distance_calculator
from reasoning.prompts.system_message import SYSTEM_MESSAGE

class AgentOrchestrator:

    def __init__(self, model_factory : BaseModelBackend, environment : Environment):
        self.__log = []
        self.__log_listeners = []
        self.__environment = environment
        self.__model_factory = model_factory
        self.__agent = ChatAgent(
            system_message=SYSTEM_MESSAGE,
            model=self.__model_factory,
            tools=[
                self.__trip_info(),
                self.__service_info(),
                self.__buses(),
                self.__future_trips(),
                self.__calculate_distance(),
                self.__get_time(),
                self.__allocated_buses()
            ]
        )

        pass

    def get_log(self):
        return self.__log.copy()

    def log_subscribe(self, func):
        self.__log_listeners.append(func)

    def __log_message(self, msg):
        self.__log.append(msg)
        for listener in self.__log_listeners:
            listener(msg)

    def get_environment(self):
        return self.__environment

    def send_allox(self, allox):
        id_list = ""
        for selected_id in allox:
            id_list += f"{selected_id},"

        if id_list[len(id_list) - 1] == ",":
            id_list = id_list[:-1]

        response = self.__agent.step(f"[ALLOX] {id_list}")
        self.__parse_cra_response(response.msg.content,
                                  self.__handle_default_response,
                                  lambda e: self.__log_message(e.message))

    def send_log(self, msg : str, bus_ids : List[int]=(), service_ids : List[int]=(), trip_ids : List[int]=()):
        id_list = ""
        for selected_id in bus_ids:
            id_list += f"B{selected_id},"

        for selected_id in service_ids:
            id_list += f"S{selected_id},"

        for selected_id in trip_ids:
            id_list += f"T{selected_id},"

        if id_list == "":
            id_list = "*"

        if id_list[len(id_list) - 1] == ",":
            id_list = id_list[:-1]

        response = self.__agent.step(f"[LOG] {id_list} {msg}")
        self.__parse_cra_response(response.msg.content,
                                  self.__handle_default_response,
                                  lambda e: self.__log_message(e.message))

    def send_msg(self, msg):
        response = self.__agent.step(msg)
        self.__parse_cra_response(response.msg.content,
                                  self.__handle_default_response,
                                  lambda e: self.__log_message(e.message))

    def step_time(self, delta : datetime.timedelta):
        self.__environment.current_time += delta
        self.compute_required_allox()

    def compute_required_allox(self):
        within_next_hour = []
        buses_on_trips = self.__environment.find_buses_on_trips()
        for t in self.__environment.trips.values():
            if (t.calling_points[0].timestamp < self.__environment.current_time + datetime.timedelta(hours=1))\
                    and not buses_on_trips.get(t.id):
                within_next_hour.append(t.id)

        if len(within_next_hour) == 0:
            return

        self.__log_message("The following trips are being allocated: " + str(within_next_hour))
        self.send_allox(within_next_hour)

    def __handle_default_response(self, response : DefaultResponse):
        self.__actuate_environment(response.allocations)
        self.__log_message("Rationale Given: " + response.rationale)

    def __actuate_environment(self, actions : List[Allocation]):
        buses = self.__environment.find_buses_on_trips()

        for action in actions:
            # Check all critical fields are populated
            if action.bus_id is None and action.bus_reg is None and action.trip_id is None:
                raise ReprimandableError(f"All fields inside the instruction "
                                         f"with rationale {action.rationale} were null.")

            # Check bus ID is real
            if action.bus_id is not None and not self.__environment.buses.get(action.bus_id):
                raise ReprimandableError("An invalid bus ID was provided in the instruction " + str(action))

            # Check bus ID is real
            if action.trip_id is not None and not self.__environment.trips.get(action.trip_id):
                raise ReprimandableError("An invalid trip ID was provided in the instruction " + str(action))

            # Check if cancellation
            if action.bus_id is None and action.bus_reg is None:
                self.__log_message(f"Trip {action.trip_id} has been cancelled, "
                                   f"with rationale {action.rationale}")
                for bus in buses[action.trip_id]:
                    bus.current_trip_id_queue.remove(action.trip_id)
                continue

            # Check if bus is to be relieved
            if action.trip_id is None:
                self.__log_message(f"Bus {action.bus_id} ({action.bus_reg}) has been relieved,"
                                   f" with rationale {action.rationale}")
                self.__environment.buses[action.bus_id].current_trip_id_queue = []
                continue

            # Else, assume the bus is being allocated
            self.__log_message(f"Bus {action.bus_id} ({action.bus_reg}) has been allocated to trip {action.trip_id}, "
                               f"with rationale {action.rationale}")

            self.__environment.buses[action.bus_id].current_trip_id_queue.append(action.trip_id)

    def __handle_reprimand(self, reprimand : ReprimandableError, on_default, on_error):
        self.__log_message(f"CRA has been reprimanded with the following error message: {reprimand.message}")
        output = self.__agent.step(str(reprimand))
        def failure_condition(_):
            conclusion = self.__agent.step("[DEV] You have met the failure condition for not responding correctly to a reprimand. "
                                       "Consequently, the program will be terminated. Please provide a rationale for what "
                                       "may have led to this conclusion.")
            raise FatalError("Failure condition met for excessive reprimands.", conclusion.msg.content)
        self.__parse_cra_response(output.msg.content, on_default, on_error, failure_condition)


    def __parse_cra_response(self, response_string : str, on_default, on_error, on_reprimand = None):
        if on_reprimand is None:
            on_reprimand = self.__handle_reprimand

        try:
            obj = json.loads(response_string)
            if obj.get("message"):
                on_error(TypeAdapter(ErrorResponse).validate_python(obj))
            else: on_default(TypeAdapter(DefaultResponse).validate_python(obj))

        except ReprimandableError as err:
            on_reprimand(err, on_default, on_error)

    # Hereon out is the tools used by the Central Reasoning Agent

    def __trip_info(self):
        @FunctionTool
        def trip_info(trip_id : str):
            """
            Returns the information corresponding to a trip in the timetable, including its calling pattern, times of
            departure, arrival, and what service it correlates to.
            :param trip_id: The ID of the trip being searched for.
            :return: Either a string, explaining an error in finding the trip, or an object of type {
                  "id": int,
                  "service_id": int,
                  "route_name": string,
                  "start_time": string,
                  "end_time": string,
                  "calling_points": {
                    "stop_id": int,
                    "stop_name": string,
                    "timestamp": string,
                    "average_passenger_load": float,
                  }[]
            }
            """
            self.__log_message("CRA Invoked trip_info with param " + trip_id)

            try:
                trip = self.__environment.trips.get(int(trip_id))

                if trip is None:
                    raise IndexError(f"The trip id {trip_id} doesn't exist")
            except Exception as e:
                return f"The trip id could not be found. Your input returned the error: {e}"

            return trip.make_llm_friendly()
        return trip_info

    def __service_info(self):
        @FunctionTool
        def service_info(service_id : str):
            """
            Returns the information corresponding to a service in the timetable, including the IDs of the trips it
            corresponds to as well as its route name.
            :param service_id: The ID of the service being searched for.
            :return: Either a string, explaining an error in finding the service, or an object of type {
                  "id": int,
                  "route_name": string,
                  "trips": int[]
            }
            """

            self.__log_message("CRA Invoked service_info with param " + service_id)

            try:
                service = self.__environment.services.get(int(service_id))

                if service is None:
                    raise IndexError(f"The service id {service_id} doesn't exist")
            except Exception as e:
                return f"The service id could not be found. Your input returned the error: {e}"

            return service.make_llm_friendly()
        return service_info

    def __buses(self):
        @FunctionTool
        def buses():
            """
            Fetches the fleet list of the bus network, in its entirety.
            :return: An object of type {
              "id": int,
              "model": string,
              "reg_plate": string,
              "capacity": int,
              "power_mode": string,  // "electric", "hybrid", "diesel" or "hydrogen"
              "length": float,       // in metres
              "height": float,       // in metres
              "double_deck": bool,
              "coach": bool,
              "faults": [string],    // list of any pre-existing problems
              "current_trip_id": int | null,
              "current_stop_id": int | null
            }[]
            """
            self.__log_message("CRA Invoked buses")
            return list(self.__environment.buses.values())
        return buses

    def __allocated_buses(self):
        @FunctionTool
        def allocated_buses():
            """
            Fetches the buses which have currently been allocated.
            :return: A list of key value pairs, with the key corresponding to a trip ID and the value being of type {
              "id": int,
              "model": string,
              "reg_plate": string,
              "capacity": int,
              "power_mode": string,  // "electric", "hybrid", "diesel" or "hydrogen"
              "length": float,       // in metres
              "height": float,       // in metres
              "double_deck": bool,
              "coach": bool,
              "faults": [string],    // list of any pre-existing problems
              "current_trip_id": int | null,
              "current_stop_id": int | null
            }[]. If the key is set to -1, the bus is currently not operating any trip.
            """
            self.__log_message("CRA Invoked allocated buses")
            return list(self.__environment.find_buses_on_trips())
        return allocated_buses

    def __get_time(self):
        @FunctionTool
        def get_time():
            """
            Returns the current time of day
            :return: The current time of day
            """
            self.__log_message("CRA Invoked get_time")
            return self.__environment.current_time.time().strftime("%H:%M:%S")
        return get_time

    def __future_trips(self):
        @FunctionTool
        def future_trips(hour_of_day : int):
            """
            Gets all trips in the future from now
            :param hour_of_day: The hour of the day to search for trips on
            :return: An object of type {
                  "id": int,
                  "service_id": int,
                  "route_name": string,
                  "start_time": string,
                  "end_time": string,
                  "calling_points": {
                    "stop_id": int,
                    "stop_name": string,
                    "timestamp": string,
                    "average_passenger_load": float,
                  }[]
            """
            self.__log_message("CRA Invoked future_trips with param " + str(hour_of_day))
            all_trips = self.__environment.trips.values()
            return [
                t.make_llm_friendly() for t in all_trips if t.calling_points[0].timestamp.time() >=
                    self.__environment.current_time.time() and t.calling_points[0].timestamp.hour == hour_of_day
            ]
        return future_trips

    def __calculate_distance(self):
        @FunctionTool
        def calculate_distance(stop_a_id : str, stop_b_id : str):
            """
            Calculates the seconds it takes to travel between the two stops, taking the shortest path possible.

            :param stop_a_id: The ID of the stop to travel from
            :param stop_b_id: The ID of the stop to travel to
            :return: Either a string message, explaining an error, or a float corresponding to the seconds to travel
                between the two stops.
            """
            self.__log_message(f"CRA Invoked calculate_distance between {stop_a_id} and {stop_b_id}")

            try:
                stop_a = self.__environment.stops.get(int(stop_a_id))

                if stop_a is None:
                    raise IndexError(f"The Stop A's ID {stop_a_id} doesn't exist")
            except Exception as e:
                return f"Stop A's ID could not be found. Your input returned the error: {e}"

            try:
                stop_b = self.__environment.stops.get(int(stop_b_id))

                if stop_b is None:
                    raise IndexError(f"The Stop B's ID {stop_b_id} doesn't exist")
            except Exception as e:
                return f"Stop B's ID could not be found. Your input returned the error: {e}"

            return distance_calculator(stop_a , stop_b)
        return calculate_distance