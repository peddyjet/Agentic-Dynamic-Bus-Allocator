from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from reasoning.models.Service import Service
from reasoning.models.network_graph.StopNode import StopNode


class Trip(BaseModel):
    class CallingPoint(BaseModel):
        stop: StopNode
        timestamp: datetime
        passenger_loadings: List[float]

    id: str
    service: Service
    calling_points: List[CallingPoint]
