from camel.toolkits import FunctionTool

from reasoning.agents.tools.distance_calculator import distance_calculator


def trip_info_tool(self):
    @FunctionTool
    def trip_info(trip_id: str):
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
        self._log_message("Invoked trip_info with param " + trip_id)

        try:
            trip = self.__environment.trips.get(int(trip_id))

            if trip is None:
                raise IndexError(f"The trip id {trip_id} doesn't exist")
        except Exception as e:
            return f"The trip id could not be found. Your input returned the error: {e}"

        return trip.make_llm_friendly()

    return trip_info


def service_info_tool(self):
    @FunctionTool
    def service_info(service_id: str):
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

        self._log_message("Invoked service_info with param " + service_id)

        try:
            service = self.__environment.services.get(int(service_id))

            if service is None:
                raise IndexError(f"The service id {service_id} doesn't exist")
        except Exception as e:
            return f"The service id could not be found. Your input returned the error: {e}"

        return service.make_llm_friendly()

    return service_info


def buses_tool(self):
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
        self._log_message("Invoked buses")
        return list(self.__environment.buses.values())

    return buses


def allocated_buses_tool(self):
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
        self._log_message("Invoked allocated buses")
        return list(self.__environment.find_buses_on_trips())

    return allocated_buses


def get_time_tool(self):
    @FunctionTool
    def get_time():
        """
        Returns the current time of day
        :return: The current time of day
        """
        self._log_message("Invoked get_time")
        return self.__environment.current_time.time().strftime("%H:%M:%S")

    return get_time


def future_trips_tool(self):
    @FunctionTool
    def future_trips(hour_of_day: int):
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
        self._log_message("Invoked future_trips with param " + str(hour_of_day))
        all_trips = self.__environment.trips.values()
        return [
            t.make_llm_friendly() for t in all_trips if t.calling_points[0].timestamp.time() >=
                                                        self.__environment.current_time.time() and t.calling_points[
                                                            0].timestamp.hour == hour_of_day
        ]

    return future_trips

def trips_tool(self):
    @FunctionTool
    def trips(hour_of_day: int):
        """
        Gets all trips plus or minus one hour from the time specified
        :param hour_of_day: The hour of the day to search for trips around
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
        self._log_message("Invoked trips with param " + str(hour_of_day))
        all_trips = self.__environment.trips.values()
        return [
            t.make_llm_friendly() for t in all_trips
            if abs(t.calling_points[0].timestamp.hour - hour_of_day) <= 1
        ]

    return trips


def calculate_distance_tool(self):
    @FunctionTool
    def calculate_distance(stop_a_id: str, stop_b_id: str):
        """
        Calculates the seconds it takes to travel between the two stops, taking the shortest path possible.

        :param stop_a_id: The ID of the stop to travel from
        :param stop_b_id: The ID of the stop to travel to
        :return: Either a string message, explaining an error, or a float corresponding to the seconds to travel
            between the two stops.
        """
        self._log_message(f"Invoked calculate_distance between {stop_a_id} and {stop_b_id}")

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

        return distance_calculator(stop_a, stop_b)

    return calculate_distance

def environment_tools(self):
    """
    Returns all the tools used by the ASA
    :param self: the current agent. This requires a __environment and __log_message function
    :return: an array of tools
    """
    return [trip_info_tool(self),
            service_info_tool(self),
            future_trips_tool(self),
            calculate_distance_tool(self)]