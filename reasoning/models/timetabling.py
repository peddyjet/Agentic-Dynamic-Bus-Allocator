from datetime import datetime
from typing import List
from pydantic import BaseModel
from reasoning.models.network_graph import StopNode

class Service(BaseModel):
    id: int
    route_id: str
    trips: List["Trip"]

class Trip(BaseModel):
    class CallingPoint(BaseModel):
        stop: StopNode
        timestamp: datetime
        passenger_loadings: List[float]

    id: int
    service: Service
    calling_points: List[CallingPoint]


Service.model_rebuild()
Trip.model_rebuild()