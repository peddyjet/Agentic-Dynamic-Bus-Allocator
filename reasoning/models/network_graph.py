from pydantic import BaseModel
from typing import List

class Edge(BaseModel):
    source: "StopNode"
    target: "StopNode"
    seconds_to_travel: float

class StopNode(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    is_depot : bool
    edges: List[Edge]

Edge.model_rebuild()
StopNode.model_rebuild()