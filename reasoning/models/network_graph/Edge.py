from pydantic import BaseModel
from reasoning.models.network_graph.StopNode import StopNode


class Edge(BaseModel):
    source: StopNode
    target: StopNode
    seconds_to_travel: float