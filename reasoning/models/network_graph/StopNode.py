from typing import List
from pydantic import BaseModel
from reasoning.models.network_graph.Edge import Edge

class StopNode(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float
    is_depot : bool
    edges: List[Edge]