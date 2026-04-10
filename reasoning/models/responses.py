from typing import List, Optional
from pydantic import BaseModel

from reasoning.models.incident import Incident


class AllocationResponse(BaseModel):
    trip_id : int
    buses : List[int]
    cancel : bool
    rationale : str
    error: Optional[str]

class IncidentResponse(BaseModel):
    incident: Incident
    error: Optional[str]