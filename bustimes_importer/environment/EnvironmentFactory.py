import json

import requests
from datetime import datetime
from typing import List
from pydantic import TypeAdapter
from bustimes_importer.environment.environment_constructor import construct_environment
from bustimes_importer.models.TripInstance import TripInstance
from bustimes_importer.models.Vehicle import Vehicle
from bustimes_importer.models.VehicleJourney import VehicleJourney

class EnvironmentFactory:
    """
    Fetches real-world bus data using the BusTimes API, under the MPL-2.0 and Open Government Licenses.
    These are then converted into the environment which can be understood by the agent orchestrator.

    Where available, ground truth data is pulled from the API, usable as an evaluation metric.

    The National Operator Code required by the constructor corresponds to the four-character code issued to bus companies
    to identify themselves in the Bus Open Data Service (BODS). For example, Brylaine Travel (the local operator of Boston,
    England) uses the code "BRYL".
    """

    def __init__(self, national_operator_code: str, date : datetime, uri : str = "https://bustimes.org/api/"):
        self._noc = national_operator_code
        self._uri = uri
        self._date = date
        self.__formatted_time = self._date.strftime("%Y-%m-%-d")

        self._environment = construct_environment(self._get_vehicles(), self._get_trips())
        self._vehicle_journeys = self._get_vehicle_journeys()

        self._ground_truths = []
        for journey in self._vehicle_journeys:
            self._ground_truths.append((journey, self._environment.buses[journey.vehicle.id]))

    def _get_vehicles(self) -> List[Vehicle]:
        vehicles_raw = requests.get(self._uri + f"vehicles/?operator={self._noc}&limit=10000")
        vehicles_raw.raise_for_status()
        vehicles = vehicles_raw.json()["results"]
        return TypeAdapter(list[Vehicle]).validate_python(vehicles)

    def _get_vehicle_journeys(self) -> List[VehicleJourney]:
        journeys = []
        for bus in self._environment.buses.keys():
            journeys_raw = requests.get(self._uri +
                                        f"vehiclejourneys/?limit=10000&vehicle={bus}&datetime={self.__formatted_time}")
            journeys_raw.raise_for_status()
            journeys_json = journeys_raw.json()["results"]
            journeys.extend(TypeAdapter(list[VehicleJourney]).validate_python(journeys_json))
        pass

        return journeys

    def _get_trips(self) -> List[TripInstance]:
        trips = []

        trip_request_queue = [self._uri + f"trips/?limit=1000&operator={self._noc}&date={self.__formatted_time}"]
        while len(trip_request_queue) > 0:
            url = trip_request_queue.pop()
            trips_raw = requests.get(url)
            trips_raw.raise_for_status()
            trips_json = trips_raw.json()
            trips.extend(TypeAdapter(list[TripInstance]).validate_python(trips_json["results"]))

            if trips_json["next"] is not None:
                trip_request_queue.append(trips_json["next"])

        return trips

    def get_environment(self):
        return self._environment

    def get_ground_truths(self):
        return self._ground_truths
