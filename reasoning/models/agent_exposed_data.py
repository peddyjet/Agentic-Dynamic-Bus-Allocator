from threading import RLock
from contextlib import contextmanager
from typing import Iterator
from reasoning.environment.Environment import Environment
from reasoning.environment.IncidentStore import IncidentStore


class AgentExposedData:
    def __init__(self, environment: Environment, incident_store: IncidentStore):
        self._environment = environment
        self._incident_store = incident_store
        self._lock = RLock()

    @contextmanager
    def locked(self) -> Iterator[None]:
        with self._lock:
            yield

    def environment(self):
        with self._lock:
            return self._environment

    def incident_store(self):
        with self._lock:
            return self._incident_store