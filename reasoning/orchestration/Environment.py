from typing import List, Dict
from pydantic import BaseModel
from reasoning.models.Bus import Bus
from reasoning.models.Service import Service
from reasoning.models.network_graph.StopNode import StopNode


class Environment(BaseModel):
    buses: Dict[str, Bus] # Reg plate - Bus
    stops: Dict[str, StopNode] # ID - Stop
    services: Dict[str, Service] # ID - Service