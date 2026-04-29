from enum import Enum

class CRAReject(Enum):
    TripDoesntExist = "REJECT: Regards Trip {trip_id}. Trip {trip_id} does not exist. Please reallocate."
    TripsParsedIncorrectly = "REJECT: Regards Trip List {trip_ids}. The list is malformed. Please provide a comma-separated list of integer trip IDs."

    def __str__(self):
        return self.value