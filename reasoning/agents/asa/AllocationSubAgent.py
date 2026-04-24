import json
import random
from datetime import datetime
from typing import Optional
from camel.agents import ChatAgent
from camel.models import BaseModelBackend
from reasoning.agents.QueueAgent import QueueAgent
from reasoning.agents.prompts.asa_rejects import ASAReject
from reasoning.agents.prompts.system_messages import SYSTEM_MESSAGES
from reasoning.agents.tools.environment_tools import environment_tools
from reasoning.environment.Environment import Environment
from reasoning.models.agent_exposed_data import AgentExposedData
from reasoning.models.inputs import AllocationContext
from reasoning.models.responses import AllocationResponse


class AllocationSubAgent(QueueAgent):
    def __init__(self, name: str, model: BaseModelBackend, data : AgentExposedData):
        super().__init__(agent=ChatAgent(
            system_message=SYSTEM_MESSAGES["asa"],
            model=model,
            tools=environment_tools(self)
        ), on_decided_step_handlers=[self.__on_step_complete], name=name, agent_response=AllocationResponse, stateless=True)
        self._environment = data.environment
        self._incidents = data.incident_store

        # Events
        self.actuate_allox = None
        self.cancel_trip = None

    def allocate_bus(self, trip_id: int, time: str, note=""):
        future = self._create_future()
        self._enqueue(("step", lambda: self.__get_prompt(trip_id, datetime.fromisoformat(time), note).model_dump_json(), future))
        return future

    def reject(self, reason: ASAReject, bus_id: int, trip_id: int, conflicting_trip_id: int | None = None):
        note = str(reason).format(bus_id=bus_id, trip_id=trip_id, conflicting_trip_id=conflicting_trip_id)
        return self.allocate_bus(trip_id, self._environment().current_time.isoformat(), note)

    def __get_prompt(self, trip_id: int, time: datetime, note=""):
        raw = self._environment().find_buses_on_trips()
        buckets = [(k, random.sample(v, len(v))) for k, v in raw.items()]
        random.shuffle(buckets)
        return AllocationContext(
            trip_id=trip_id,
            trip_info=self._environment().trips[trip_id].make_llm_friendly(),
            incidents=self._incidents().get_incidents(trip_id, time),
            note=note if note != "" else None,
            time=time.strftime("%H:%M"),
            bus_dict=dict(buckets)
        )

    def __on_step_complete(self, _, result : AllocationResponse):
        if result.cancel:
            error : Optional[ASAReject] = self.cancel_trip(result.trip_id)
            if error is not None:
                self._log_message(f"Rejecting cancellation due to {error.name}")
                self.reject(error, result.buses[0], result.trip_id)
                return
            return

        for bus_id in result.buses:
            error, error_trip = self.actuate_allox(bus_id, result.trip_id)
            if error is not None:
                self._log_message(f"Rejecting bus {bus_id} due to {error.name}")
                self.reject(error, bus_id, result.trip_id, error_trip)
