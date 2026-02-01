import datetime
import numpy as np
from camel.agents import ChatAgent
from camel.models import BaseModelBackend
from camel.toolkits import FunctionTool
from reasoning.models.timetabling import LLMFriendlyTrip
from reasoning.orchestration.Environment import Environment
from reasoning.orchestration.distance_calculator import distance_calculator
from reasoning.prompts.system_message import SYSTEM_MESSAGE

class AgentOrchestrator:

    def __init__(self, model_factory : BaseModelBackend, environment : Environment, log = False):
        self.log = log
        self.__environment = environment
        self.__model_factory = model_factory
        self.__agent = ChatAgent(
            system_message=SYSTEM_MESSAGE,
            model=self.__model_factory,
            tools=[
                self.__trip_info(),
                self.__buses(),
                self.__future_trips(),
                self.__calculate_distance()
            ]
        )

        pass

    def get_environment(self):
        return self.__environment

    def get_bus_allox(self, timetable_entry):
        response = self.__agent.step(timetable_entry)
        print(response.msg.content)
        pass

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
            if self.log:
                print("(Log) CRA Invoked trip_info with param " + trip_id)

            try:
                trip = self.__environment.trips.get(int(trip_id))

                if trip is None:
                    raise IndexError(f"The trip id {trip_id} doesn't exist")
            except Exception as e:
                return f"The trip id could not be found. Your input returned the error: {e}"

            return trip.make_llm_friendly()
        return trip_info

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
            if self.log:
                print("(Log) CRA Invoked buses")
            return list(self.__environment.buses.values())
        return buses

    def __future_trips(self):
        @FunctionTool
        def future_trips():
            """
            Gets all trips in the future from now
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
            if self.log:
                print("(Log) CRA Invoked future_trips")
            all_trips = self.__environment.trips.values()
            return [
                t.make_llm_friendly() for t in all_trips if t.calling_points[0].timestamp.time() >=
                    self.__environment.current_time.time()
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
            if self.log:
                print(f"(Log) CRA Invoked calculate_distance between {stop_a_id} and {stop_b_id}")

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