from enum import Enum


class EventNames(Enum):
    ENVIRONMENT_CHANGED = "environment_changed" # Buses and trips
    INCIDENT_ADDED = "incident_added"
    AGENT_BUSY = "agent_busy"
    LOG_MESSAGE = "log_message"
    STEP_COMPLETE = "step_complete"
    ABANDONED_PASSENGER = "abandoned_passenger"
    INTERLINED = "interlined"
    TRIP_CANCELLED = "trip_cancelled"
    DELAY_RECORDED = "delay_recorded"
    NO_SHOW = "no_show"
