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
        threading.Thread(
            target=self._worker_loop,
            args=(prompt,),
            daemon=True
        ).start()

    def _worker_loop(self, prompt: Y):
        while True:
            for agent in self._agents.values():
                if not agent.is_working():
                    self._step(agent, prompt)
                    return

            # If no agent is available, don't wait whilst busy as it is futile.
            time.sleep(0.05)

    def demand_agent(self, agent_name : str):
        return self._agents[agent_name]
