from typing import Optional, List
from pydantic import BaseModel

from reasoning.models.Trip import Trip


class BaseBus(BaseModel):
    model: str
    reg_plate: str
    capacity: int
    power_mode: str # electric, hybrid, diesel or hydrogen
    length: float # in metres
    double_deck: bool
    coach: bool

class Bus(BaseBus):
    faults : List[str] # Any problems detected with the bus which need addressing
    current_route : Optional[Trip]
    kilometres_until_empty: int
