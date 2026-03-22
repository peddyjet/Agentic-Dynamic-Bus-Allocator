from enum import Enum

CAPACITY_ERROR_THRESHOLD = 0.5

class ASAReject(Enum):
    BusWithdrawn = "REJECT: Regards Trip {trip_id}. Bus {bus_id} is withdrawn. Please reallocate."
    BusDoesntExist = "REJECT: Regards Trip {trip_id}. Bus {bus_id} does not exist. Please reallocate."
    BusTooSmall = "REJECT: Regards Trip {trip_id}. Bus {bus_id} has too low capacity. Please reallocate."
    BusWontFit = "REJECT: Regards Trip {trip_id}. Bus {bus_id} won't fit in the smaller areas of the route. Please reallocate."
    BusConflict = ("REJECT: Regards Trip {trip_id}. Another ASA allocated Bus {bus_id} at the same time as you, to trip {conflicting_trip_id}. "
                   "This is not your fault. Please Reallocate.")

    def __str__(self):
        return self.value