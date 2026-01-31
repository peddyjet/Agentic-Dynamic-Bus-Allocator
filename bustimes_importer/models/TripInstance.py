from typing import Optional, List
from pydantic import BaseModel

class TripService(BaseModel):
    id: int
    line_name: str

class TripStop(BaseModel):
    name: str
    location: List[float]

class TripTime(BaseModel):
    id: int
    stop: TripStop
    aimed_arrival_time: Optional[str]
    aimed_departure_time: Optional[str]
    pick_up: bool
    set_down: bool

class TripInstance(BaseModel):
    id: int
    start: str
    end: str
    service: TripService
    times: List[TripTime]