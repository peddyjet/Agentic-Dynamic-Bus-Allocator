from enum import Enum

class IHSAReject(Enum):
    BusDoesntExist = "REJECT: Regards Trip {trip_id}. Bus {bus_id} does not exist. Please reallocate."
    TripDoesntExist = "REJECT: Regards Trip {trip_id}. Trip {trip_id} does not exist. Please reallocate."
    BusNotOnTrip = "REJECT: Bus {bus_id} is not assigned to trip {trip_id}."

    def __str__(self):
        return self.value