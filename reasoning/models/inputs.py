from typing import List, Optional, Dict
from pydantic import BaseModel
from reasoning.models.bus import Bus
from reasoning.models.incident import Incident, TimeStampedIncident
from reasoning.models.timetabling import LLMFriendlyTrip, LLMFriendlyService


class SimplifiedAllocationContext(BaseModel):
    trip_id: int
    note: Optional[str] = None
    time: str

class AllocationContext(SimplifiedAllocationContext):
    trip_info: LLMFriendlyTrip
    bus_dict: Dict[int, List[Bus]]
    incidents: List[TimeStampedIncident]

class IncidentHandlingContext(BaseModel):
    incident: str
    services: List[LLMFriendlyService]
    bus_dict: Dict[int, List[Bus]]
    incidents: List[TimeStampedIncident]
    time: str

class IncidentHandlingReferral(BaseModel):
    incident: str

class CRAInput(BaseModel):
    content : str
    time : str