from concurrent.futures import as_completed
from concurrent.futures.thread import ThreadPoolExecutor
import requests
from datetime import datetime
from typing import List, Dict, Optional
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

    def __init__(self, national_operator_code: str, date : datetime, uri : str = "https://bustimes.org/api/", log : bool = False):
        self._noc = national_operator_code
        self._uri = uri
        self._date = date
        self.__formatted_time = self._date.strftime("%Y-%m-%d")
        self.log = log

        self._environment = construct_environment(self._get_vehicles(), self._get_trips(), date, log)
        self._vehicle_journeys = self._get_vehicle_journeys()

        if self.log:
            print("     Creating ground truths... (3g/4)")
        self._ground_truths = []
        for journey in self._vehicle_journeys:
            self._ground_truths.append((journey, self._environment.buses[journey.vehicle.id]))

    def _get_vehicles(self) -> List[Vehicle]:
        if self.log:
            print("     Fetching vehicles... (3a/4)")
        vehicles_raw = requests.get(self._uri + f"vehicles/?operator={self._noc}&limit=10000")
        vehicles_raw.raise_for_status()
        vehicles = vehicles_raw.json()["results"]
        vehicles_filtered = [v for v in vehicles if v["vehicle_type"] is not None and v["withdrawn"] is not True]
        return TypeAdapter(list[Vehicle]).validate_python(vehicles_filtered)

    def _get_vehicle_journeys(self) -> List[VehicleJourney]:
        if self.log:
            print("     Fetching vehicle journeys... (3f/4)")

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
        if self.log:
            print("     Fetching trips... (3b/4) [Note: This can take a while]")

        # A slug of various points of data has been paired to the trip ID, to avoid duplicates.
        trip_data_to_id : Dict[str, Optional[int]] = {}
        create_trip_data_slug = lambda r: r["ticket_machine_code"] + r["start"] + r["end"] + r["headsign"]

        trip_request_queue = [self._uri + f"trips/?limit=1000&operator={self._noc}&date={self.__formatted_time}"]
        while len(trip_request_queue) > 0:
            url = trip_request_queue.pop()
            trips_raw = requests.get(url)
            trips_raw.raise_for_status()
            trips_json = trips_raw.json()
            results = trips_json["results"]
            for result in results:
                data_slug = create_trip_data_slug(result)

                if trip_data_to_id.get(data_slug) is None:
                    trip_data_to_id[data_slug] = result["id"]

            if trips_json["next"] is not None:
                trip_request_queue.append(trips_json["next"])

        # Because of how many requests need sending, threading is needed here.
        with ThreadPoolExecutor(max_workers=12) as pool:
            futures = [pool.submit(self._get_trip, t) for t in trip_data_to_id.values()]
        final_results = []
        for f in as_completed(futures):
            final_results.append(f.result())

        return [trip for trip in final_results if trip is not None]

    def _get_trip(self, trip_id : int) -> TripInstance | None:
        trip_raw = requests.get(self._uri + f"trips/{trip_id}")
        trip_raw.raise_for_status()
        trip_json = trip_raw.json()
        if trip_json["service"]["id"] is None:
            return None

        return TypeAdapter(TripInstance).validate_python(trip_json)

    def get_environment(self):
        return self._environment

    def get_ground_truths(self):
        return self._ground_truths
