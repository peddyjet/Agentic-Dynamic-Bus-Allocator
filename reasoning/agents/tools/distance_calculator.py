from typing import List, Optional, Dict
import numpy as np
from reasoning.models.network_graph import StopNode, Edge
import heapq

def a_star(start : StopNode, goal : StopNode) -> Optional[List[Edge]]:
    def heuristic(this_node : StopNode) -> float:
        return np.sqrt((this_node.longitude - goal.longitude)**2 + (this_node.latitude - goal.latitude)**2)

    frontier = []
    heapq.heappush(frontier, (heuristic(start) + 0, (0, start))) # g + h : (g, node)

    explored = []
    came_from : Dict[StopNode, Edge] = {}

    while len(frontier) > 0:
        _, (g, node) = heapq.heappop(frontier)
        if node == goal:
            path = []
            retrace_node = node
            while retrace_node != start:
                edge = came_from[retrace_node]
                path.append(edge)
                retrace_node = edge.source

            return path

        explored.append(node)
        edges = node.edges
        for edge in edges:
            if not edge in explored:
                came_from[edge.target] = edge
                heapq.heappush(frontier,
                               (heuristic(edge.target) + g + edge.seconds_to_travel,
                                (g + edge.seconds_to_travel, edge.target)))
    return None

def distance_calculator(start : StopNode, goal : StopNode) -> float:
    path = a_star(start, goal)
    return np.sum([edge.seconds_to_travel for edge in path])