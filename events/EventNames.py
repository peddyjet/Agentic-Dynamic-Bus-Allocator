from enum import Enum


class EventNames(Enum):
    ENVIRONMENT_CHANGED = "environment_changed" # Buses and trips
    INCIDENT_ADDED = "incident_added"
    AGENT_BUSY = "agent_busy"
    LOG_MESSAGE = "log_message"
