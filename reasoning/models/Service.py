from typing import Optional, List
from pydantic import BaseModel
from reasoning.models.Trip import Trip

class Service(BaseModel):
    id: str
    route_id: str
    trips: List[Trip]
