from enum import Enum

CAPACITY_ERROR_THRESHOLD = 0.5

class ASAReject(Enum):
    BusWithdrawn = "REJECT: Regards Trip {trip_id}. Bus {bus_id} is withdrawn. Your allocation was therefore denied, and no trips were allocated. Please reallocate."
    BusDoesntExist = "REJECT: Regards Trip {trip_id}. Bus {bus_id} does not exist. Your allocation was therefore denied, and no trips were allocated. Please reallocate."
    BusTooSmall = "REJECT: Regards Trip {trip_id}. Bus {bus_id} has too low capacity. Your allocation was therefore denied, and no trips were allocated. Please reallocate."
    BusWontFit = "REJECT: Regards Trip {trip_id}. Bus {bus_id} won't fit in the smaller areas of the route. Your allocation was therefore denied, and no trips were allocated. Please reallocate."
    BusConflict = ("REJECT: Regards Trip {trip_id}. Another ASA allocated Bus {bus_id} at the same time as you, to trip {conflicting_trip_id}. Your allocation was therefore denied, and no trips were allocated. "
                   "This is not your fault. Please Reallocate.")
    CannotDeadrun = ("REJECT: Regards Trip {trip_id}. Bus {bus_id} cannot deadrun from trip {conflicting_trip_id} to trip {trip_id}, due to the distance between stops."
                     " Your allocation was therefore denied, and no trips were allocated. Please reallocate.")

    def __str__(self):
        return self.value