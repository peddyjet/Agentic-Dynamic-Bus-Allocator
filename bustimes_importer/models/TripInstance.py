from typing import Optional, List
from pydantic import BaseModel

class TripInstance(BaseModel):
    class TripService(BaseModel):
        id: str
        line_name: str

    class TripTime(BaseModel):
        class TripStop(BaseModel):
            name: str
            location: List[float]

        id: str
        stop: TripStop
        aimed_arrival_time: Optional[str]
        aimed_departure_time: Optional[str]
        pick_up: bool
        set_down: bool

    id: str
    start: str
    end: str
    service: TripService
    times: List[TripTime]