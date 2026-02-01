from datetime import datetime
from typing import List

import numpy as np
from pydantic import BaseModel
from reasoning.models.network_graph import StopNode

class Service(BaseModel):
    id: int
    route_name: str
    trips: List["Trip"]

class Trip(BaseModel):
    class CallingPoint(BaseModel):
        stop: StopNode
        timestamp: datetime
        passenger_loadings: List[float]

    id: int
    service: Service
    calling_points: List[CallingPoint]
    
    def make_llm_friendly(self):
        start_time = self.calling_points[0].timestamp.strftime("%H:%M:%S") \
            if len(self.calling_points) > 0 else (datetime(year=1970, month=1, day=1)).strftime("%H:%M:%S")
        end_time = self.calling_points[len(self.calling_points) - 1].timestamp.strftime("%H:%M:%S") \
            if len(self.calling_points) > 0 else (datetime(year=1970, month=1, day=1)).strftime("%H:%M:%S")


        return LLMFriendlyTrip(
            id=self.id,
            service_id=self.service.id,
            route_name=self.service.route_name,
            start_time=start_time,
            end_time=end_time,
            calling_points=list(map(lambda c: LLMFriendlyTrip.CallingPoint
            (stop_id=c.stop.id,
             stop_name=c.stop.name,
             timestamp=c.timestamp.strftime("%H:%M:%S"),
             average_passenger_load=float(np.mean(c.passenger_loadings) if len(c.passenger_loadings) > 0 else 0)
             ), self.calling_points))
        )

class LLMFriendlyTrip(BaseModel):
    class CallingPoint(BaseModel):
        stop_id : int
        stop_name : str
        timestamp : str
        average_passenger_load : float

    id: int
    service_id: int
    route_name: str
    start_time: str
    end_time: str
    calling_points: List[CallingPoint]


Service.model_rebuild()
Trip.model_rebuild()