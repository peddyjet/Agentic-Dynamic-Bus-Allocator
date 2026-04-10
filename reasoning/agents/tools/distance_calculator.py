from typing import List, Optional, Dict
import numpy as np
from reasoning.models.network_graph import StopNode, Edge
import heapq

def a_star(start : StopNode, goal : StopNode) -> Optional[List[Edge]]:
    def heuristic(this_node : StopNode) -> float:
        return np.sqrt((this_node.longitude - goal.longitude)**2 + (this_node.latitude - goal.latitude)**2)

    counter = 0
    frontier = []
    heapq.heappush(frontier, (heuristic(start), counter, 0, start)) # f, tiebreak, g, node

    explored : set = set()
    came_from : Dict[int, Edge] = {}

    while len(frontier) > 0:
        _, _, g, node = heapq.heappop(frontier)
        if node.id == goal.id:
            path = []
            retrace_node = node
            while retrace_node.id != start.id:
                edge = came_from[retrace_node.id]
                path.append(edge)
                retrace_node = edge.source

            return path

        if node.id in explored:
            continue
        explored.add(node.id)

        for edge in node.edges:
            if edge.target.id not in explored:
                counter += 1
                came_from[edge.target.id] = edge
                heapq.heappush(frontier,
                               (heuristic(edge.target) + g + edge.seconds_to_travel,
                                counter,
                                g + edge.seconds_to_travel,
                                edge.target))
    return None

def distance_calculator(start : StopNode, goal : StopNode) -> float:
    path = a_star(start, goal)
    return np.sum([edge.seconds_to_travel for edge in path])