from typing import List, Dict
from pydantic import BaseModel
from reasoning.models.bus import Bus
from reasoning.models.timetabling import Service
from reasoning.models.network_graph import StopNode

class Environment(BaseModel):
    buses: Dict[int, Bus] # Reg plate - Bus
    stops: Dict[int, StopNode] # ID - Stop
    services: Dict[int, Service] # ID - Service