from typing import List, Callable, TypeVar, Generic, Dict
from pydantic import BaseModel
from reasoning.agents.QueueAgent import QueueAgent
import threading
import time

T = TypeVar('T', bound=QueueAgent)
Y = TypeVar('Y', bound=BaseModel)

class AgentPool(Generic[T, Y]):
    def __init__(self, agents: List[T], step_function: Callable[[T, Y], None]):
        self._agents : Dict[str, T] = {a.get_name(): a for a in agents}
        self._step = step_function

    def step(self, prompt: Y):
        best_fit = None
        best_fit_score = float('inf')
        for agent in self._agents.values():
            score = agent.queue_size()
            if agent.is_working():
                score += 1

            if score < best_fit_score:
                best_fit = agent
                best_fit_score = score

        self._step(best_fit, prompt)

    def demand_agent(self, agent_name : str):
        return self._agents[agent_name]

    def demand_all_agents(self):
        return self._agents

    def any_working(self):
        return any(agent.is_working() for agent in self._agents.values())