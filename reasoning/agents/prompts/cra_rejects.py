from enum import Enum

class CRAReject(Enum):
    TripDoesntExist = "REJECT: Regards Trip {trip_id}. Trip {trip_id} does not exist. Please reallocate."

    def __str__(self):
        return self.value