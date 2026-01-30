from dataclasses import dataclass
from typing import Optional, List

@dataclass(frozen=True)
class BaseBus:
    model: str
    reg_plate: str
    capacity: int
    power_mode: str # electric, hybrid, diesel or hydrogen
    length: float # in metres
    double_deck: bool
    max_speed: float
    year: int

@dataclass(frozen=True)
class Bus(BaseBus):
    faults : List[str] # Any problems detected with the bus which need addressing
    current_route : None
    kilometres_until_empty: int
