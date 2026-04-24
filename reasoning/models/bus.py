from typing import Optional, List
from pydantic import BaseModel
from reasoning.models.timetabling import Trip


class BaseBus(BaseModel):
    id: int
    model: str
    reg_plate: str
    capacity: int
    power_mode: str # electric, hybrid, diesel or hydrogen
    length: float # in metres
    height: float # in metres
    double_deck: bool
    coach: bool

class Bus(BaseBus):
    faults : List[str] # Any problems detected with the bus which need addressing
    current_trip_id_queue : Optional[List[int]]
    current_stop_id : Optional[int]
    delay_seconds : float = 0.0
    current_passengers : float = 0.0