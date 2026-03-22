from enum import Enum

class IHSAReject(Enum):
    BusDoesntExist = "REJECT: Regards Trip {trip_id}. Bus {bus_id} does not exist. Please reallocate."
    TripDoesntExist = "REJECT: Regards Trip {trip_id}. Trip {trip_id} does not exist. Please reallocate."

    def __str__(self):
        return self.value