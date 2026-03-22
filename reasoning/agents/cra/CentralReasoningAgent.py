import asyncio
import json
from datetime import datetime
from typing import List
from camel.agents import ChatAgent
from camel.models import BaseModelBackend
from camel.toolkits import FunctionTool
from reasoning.agents.QueueAgent import QueueAgent
from reasoning.agents.prompts.cra_rejects import CRAReject
from reasoning.agents.prompts.system_messages import SYSTEM_MESSAGES
from reasoning.agents.tools.environment_tools import environment_tools, allocated_buses_tool
from reasoning.models.agent_exposed_data import AgentExposedData
from reasoning.models.inputs import CRAInput


class CentralReasoningAgent(QueueAgent):
    def __init__(self, model: BaseModelBackend, data: AgentExposedData):
        super().__init__(agent=ChatAgent(
            system_message=SYSTEM_MESSAGES["cra"],
            model=model,
            tools=environment_tools(self) + [allocated_buses_tool(self),
                                             self.__incident_tool(),
                                             self.__allocate_bus_tool(),
                                             self.__log_incident_tool()]
        ), on_decided_step_handlers=[], name="CRA")
        self.__environment = data.environment
        self.__incidents = data.incident_store

        # Events
        self.refer_asa = None
        self.refer_ihsa = None

    def allocate_bus(self, trip_ids: List[int], time: datetime):
        cra_input = CRAInput(content=f"[ALLOX] {" ".join(str(i) for i in trip_ids)}", time=time.isoformat())
        prompt = json.dumps(cra_input.model_dump())
        future = asyncio.get_event_loop().create_future()
        self._queue.put_nowait(("step", prompt, future))
        self._ensure_worker_running()
        return future

    def send_log(self, log : str, time: datetime, by_agent : bool = False):
        cra_input = CRAInput(content=f"[{'LOG' if not by_agent else 'REPORT'}] {log}", time=time.isoformat())
        prompt = json.dumps(cra_input.model_dump())
        future = asyncio.get_event_loop().create_future()
        self._queue.put_nowait(("step", prompt, future))
        self._ensure_worker_running()
        return future

    def reject(self, reason: CRAReject, trip_id: int):
        name = str(reason).format(trip_id=trip_id)
        future = asyncio.get_event_loop().create_future()
        self._queue.put_nowait(("step", name, future))
        self._ensure_worker_running()
        return future

    def __incident_tool(self):
        @FunctionTool
        def incidents():
            """
            Provides a list of all incidents that are in the incident store
            :return: every time-stamped incident in the incident store
            """
            return self.__incidents.get_incidents()
        return incidents

    def __allocate_bus_tool(self):
        @FunctionTool
        def allocate_bus(trip_id : int, notes : str = ""):
            """
            Will delegate the allocation of a trip to an Allocation Subagent, passing notes as additional context.
            :param trip_id: The ID of the trip to allocate
            :param notes: Additional context to pass to the Allocation Subagent
            :return Nothing if everything went well, otherwise an error message
            """

            err = self.refer_asa(trip_id, True, notes)
            if err is not None: return str(err).format(trip_id=trip_id)
            return None
        return allocate_bus


    def __log_incident_tool(self):
        @FunctionTool
        def log_incident(incident : str):
            """
            Will delegate the reporting and handling of an incident to an Incident Handling Subagent
            :param incident: a concise description of the incident
            :return Nothing if everything went well, otherwise an error message
            """

            return self.refer_ihsa(incident)
        return log_incident